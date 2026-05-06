import json
import logging
import socket
import urllib.error
import urllib.parse
import urllib.request

import redis
from django.conf import settings


logger = logging.getLogger(__name__)


class CatalogServiceUnavailable(Exception):
    pass


class CatalogServiceError(Exception):
    pass


class CatalogService:
    def __init__(
        self,
        redis_client=None,
        api_url=None,
        timeout=None,
        cache_ttl=None,
        stale_cache_ttl=None,
    ):
        self.redis = redis_client if redis_client is not None else redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        self.api_url = api_url if api_url is not None else settings.CHEAPSHARK_API_URL
        self.timeout = timeout if timeout is not None else settings.CHEAPSHARK_TIMEOUT
        self.cache_ttl = (
            cache_ttl if cache_ttl is not None else settings.CATALOG_SEARCH_CACHE_TTL_SECONDS
        )
        self.stale_cache_ttl = (
            stale_cache_ttl
            if stale_cache_ttl is not None
            else settings.CATALOG_SEARCH_STALE_CACHE_TTL_SECONDS
        )

    def search_games(self, query):
        normalized_query = self._normalize_query(query)
        fresh_key = self._search_cache_key(normalized_query)
        stale_key = self._stale_search_cache_key(normalized_query)

        cached = self._cache_get(fresh_key, action="catalog_search")
        if cached is not None:
            logger.info(
                "catalog action=catalog_search origin=redis result=ok decision=cache_hit q=%s",
                normalized_query,
            )
            return cached

        try:
            logger.info(
                "catalog action=catalog_search origin=cheapshark result=start decision=provider_request q=%s",
                normalized_query,
            )
            results = self._fetch_games_by_title(normalized_query)
        except (CatalogServiceUnavailable, CatalogServiceError):
            fallback = self._cache_get(stale_key, action="catalog_search_fallback")
            if fallback is not None:
                logger.warning(
                    "catalog action=catalog_search origin=redis result=ok decision=redis_fallback_after_provider_error q=%s",
                    normalized_query,
                )
                return fallback
            raise

        self._cache_set(fresh_key, results, self.cache_ttl, action="catalog_search")
        self._cache_set(stale_key, results, self.stale_cache_ttl, action="catalog_search_stale")
        logger.info(
            "catalog action=catalog_search origin=cheapshark result=ok decision=provider_response q=%s count=%s",
            normalized_query,
            len(results),
        )
        return results

    def resolve_games(self, external_game_ids):
        data = self._fetch_games_by_ids(external_game_ids)
        results = []
        for external_game_id in external_game_ids:
            game = data.get(external_game_id)
            if game is None:
                continue
            results.append(self._serialize_resolved_game(external_game_id, game))
        return results

    def external_game_id_exists(self, external_game_id):
        try:
            data = self._fetch_games_by_ids([external_game_id])
        except CatalogServiceError as exc:
            if getattr(exc, "not_found", False):
                return False
            raise

        game = data.get(external_game_id)
        if game is None:
            return False

        self._serialize_resolved_game(external_game_id, game)
        return True

    def _fetch_games_by_title(self, title):
        data = self._request_cheapshark({"title": title})
        if not isinstance(data, list):
            raise CatalogServiceError

        results = []
        for game in data:
            if not isinstance(game, dict):
                raise CatalogServiceError

            game_id = game.get("gameID")
            game_title = game.get("external")
            thumb = game.get("thumb", "")
            if (
                not isinstance(game_id, str)
                or not isinstance(game_title, str)
                or not isinstance(thumb, str)
            ):
                raise CatalogServiceError

            results.append(
                {
                    "external_game_id": game_id,
                    "title": game_title,
                    "thumb": thumb,
                }
            )
        return results

    def _fetch_games_by_ids(self, external_game_ids):
        data = self._request_cheapshark({"ids": ",".join(external_game_ids)})
        if not isinstance(data, dict):
            raise CatalogServiceError
        return data

    def _request_cheapshark(self, params):
        query = urllib.parse.urlencode(params, safe=",")
        url = f"{self.api_url}?{query}"

        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error = CatalogServiceError()
            if exc.code == 404:
                error.not_found = True
            logger.warning(
                "catalog action=provider_request origin=cheapshark result=error type=http status=%s",
                exc.code,
            )
            raise error
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            logger.warning(
                "catalog action=provider_request origin=cheapshark result=error type=network reason=%s",
                exc.__class__.__name__,
            )
            raise CatalogServiceUnavailable
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning(
                "catalog action=provider_request origin=cheapshark result=error type=invalid_json"
            )
            raise CatalogServiceError
        except Exception:
            logger.warning(
                "catalog action=provider_request origin=cheapshark result=error type=unexpected"
            )
            raise CatalogServiceError

    def _serialize_resolved_game(self, external_game_id, game):
        if not isinstance(game, dict):
            raise CatalogServiceError

        info = game.get("info")
        if not isinstance(info, dict):
            raise CatalogServiceError

        title = info.get("title")
        thumb = info.get("thumb", "")
        if not isinstance(title, str) or not isinstance(thumb, str):
            raise CatalogServiceError

        return {
            "external_game_id": external_game_id,
            "title": title,
            "thumb": thumb,
        }

    def _cache_get(self, key, action):
        logger.info(
            "catalog action=%s origin=redis result=start decision=cache_lookup key=%s",
            action,
            key,
        )
        try:
            raw = self.redis.get(key)
        except redis.RedisError as exc:
            logger.warning(
                "catalog action=%s origin=redis result=error decision=cache_unavailable reason=%s key=%s",
                action,
                exc.__class__.__name__,
                key,
            )
            return None

        if raw is None:
            logger.info(
                "catalog action=%s origin=redis result=miss decision=cache_miss key=%s",
                action,
                key,
            )
            return None

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(
                "catalog action=%s origin=redis result=error decision=cache_invalid_json key=%s",
                action,
                key,
            )
            return None

        if not isinstance(data, list):
            logger.warning(
                "catalog action=%s origin=redis result=error decision=cache_invalid_payload key=%s",
                action,
                key,
            )
            return None

        logger.info(
            "catalog action=%s origin=redis result=hit decision=cache_hit key=%s",
            action,
            key,
        )
        return data

    def _cache_set(self, key, data, ttl, action):
        try:
            self.redis.setex(key, ttl, json.dumps(data))
        except redis.RedisError as exc:
            logger.warning(
                "catalog action=%s origin=redis result=error decision=cache_write_failed reason=%s key=%s",
                action,
                exc.__class__.__name__,
                key,
            )
            return

        logger.info(
            "catalog action=%s origin=redis result=ok decision=cache_write key=%s ttl=%s",
            action,
            key,
            ttl,
        )

    def _normalize_query(self, query):
        return query.strip().lower()

    def _search_cache_key(self, query):
        return f"catalog:search:{query}"

    def _stale_search_cache_key(self, query):
        return f"catalog:search:stale:{query}"
