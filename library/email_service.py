import json
import logging
import socket
import urllib.error
import urllib.request

from django.conf import settings


logger = logging.getLogger(__name__)


class EmailServiceUnavailable(Exception):
    pass


class EmailServiceError(Exception):
    pass


class EmailService:
    def __init__(
        self,
        api_key=None,
        from_address=None,
        from_name=None,
        api_url=None,
        timeout=None,
    ):
        self.api_key = api_key if api_key is not None else settings.MAILEROO_API_KEY
        self.from_address = (
            from_address if from_address is not None else settings.MAILEROO_FROM_ADDRESS
        )
        self.from_name = from_name if from_name is not None else settings.MAILEROO_FROM_NAME
        self.api_url = api_url if api_url is not None else settings.MAILEROO_API_URL
        self.timeout = timeout if timeout is not None else settings.MAILEROO_TIMEOUT

    def send_email(self, to, subject, text, html=None, action="send_email", user=None):
        user_label = self._user_label(user)
        logger.info(
            "email intento de envio action=%s user=%s to=%s",
            action,
            user_label,
            to,
        )

        if not self.api_key or not self.from_address:
            logger.error(
                "email fallo por respuesta del proveedor action=%s user=%s to=%s result=error type=configuration",
                action,
                user_label,
                to,
            )
            raise EmailServiceError

        payload = self._build_payload(to=to, subject=subject, text=text, html=html)
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = response.status
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            logger.error(
                "email fallo por respuesta del proveedor action=%s user=%s to=%s result=error status=%s",
                action,
                user_label,
                to,
                exc.code,
            )
            raise EmailServiceError
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            logger.error(
                "email fallo por timeout/red action=%s user=%s to=%s result=error reason=%s",
                action,
                user_label,
                to,
                exc.__class__.__name__,
            )
            raise EmailServiceUnavailable

        if status < 200 or status >= 300:
            logger.error(
                "email fallo por respuesta del proveedor action=%s user=%s to=%s result=error status=%s",
                action,
                user_label,
                to,
                status,
            )
            raise EmailServiceError

        try:
            data = json.loads(response_body)
        except (json.JSONDecodeError, TypeError):
            logger.error(
                "email fallo por respuesta del proveedor action=%s user=%s to=%s result=error type=invalid_json",
                action,
                user_label,
                to,
            )
            raise EmailServiceError

        if not isinstance(data, dict) or data.get("success") is not True:
            logger.error(
                "email fallo por respuesta del proveedor action=%s user=%s to=%s result=error type=invalid_response",
                action,
                user_label,
                to,
            )
            raise EmailServiceError

        reference_id = None
        response_data = data.get("data")
        if isinstance(response_data, dict):
            reference_id = response_data.get("reference_id")

        logger.info(
            "email envio OK action=%s user=%s to=%s result=ok reference_id=%s",
            action,
            user_label,
            to,
            reference_id or "-",
        )
        return data

    def _build_payload(self, to, subject, text, html=None):
        sender = {"address": self.from_address}
        if self.from_name:
            sender["display_name"] = self.from_name

        payload = {
            "from": sender,
            "to": [{"address": to}],
            "subject": subject,
            "plain": text,
        }
        if html is not None:
            payload["html"] = html

        return payload

    def _user_label(self, user):
        if user is None:
            return "-"

        user_id = getattr(user, "id", None)
        username = getattr(user, "username", None)
        if user_id is None and username is None:
            return "-"

        return f"id={user_id};username={username}"
