import json
import urllib.error
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .catalog_service import CatalogService, CatalogServiceError, CatalogServiceUnavailable
from .email_service import EmailService, EmailServiceError, EmailServiceUnavailable
from .models import LibraryEntry


class PruebasApiCrearEntradaBiblioteca(TestCase):
    ruta = "/api/library/entries/"
    mensaje_error_validacion = "Datos de entrada invalidos"
    mensaje_error_duplicado = "El juego ya existe en la biblioteca"

    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="createuser",
            password="testpassword123",
        )
        self.client.force_login(self.usuario)
        self.catalog_patch = patch("library.views.CatalogService")
        self.catalog_service_class = self.catalog_patch.start()
        self.catalog_service_class.return_value.external_game_id_exists.return_value = True
        self.addCleanup(self.catalog_patch.stop)

    def _postear(self, datos):
        return self.client.post(
            self.ruta,
            data=json.dumps(datos),
            content_type="application/json",
        )

    def _assert_error_validacion(self, respuesta, detalles_esperados=None):
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "validation_error")
        self.assertEqual(cuerpo["message"], self.mensaje_error_validacion)
        self.assertIn("details", cuerpo)

        if detalles_esperados is None:
            return

        for campo, motivo in detalles_esperados.items():
            self.assertEqual(cuerpo["details"].get(campo), motivo)

    def _assert_error_duplicado(self, respuesta):
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "duplicate_entry")
        self.assertEqual(cuerpo["message"], self.mensaje_error_duplicado)
        self.assertEqual(cuerpo["details"], {"external_game_id": "duplicate"})

    def test_devuelve_201_cuando_el_payload_es_valido(self):
        datos = {
            "external_game_id": "steam-12345",
            "status": "playing",
            "hours_played": 12,
        }

        respuesta = self._postear(datos)

        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["external_game_id"], datos["external_game_id"])
        self.assertEqual(cuerpo["status"], datos["status"])
        self.assertEqual(cuerpo["hours_played"], datos["hours_played"])
        self.assertIn("id", cuerpo)
        self.assertTrue(
            LibraryEntry.objects.filter(external_game_id="steam-12345").exists()
        )

    def test_devuelve_400_cuando_el_body_es_objeto_vacio(self):
        respuesta = self._postear({})
        self._assert_error_validacion(
            respuesta, {"body": "El JSON no puede estar vacio."}
        )

    def test_devuelve_400_cuando_el_json_esta_mal_formado(self):
        respuesta = self.client.post(
            self.ruta,
            data='{"external_game_id":',
            content_type="application/json",
        )
        self._assert_error_validacion(respuesta, {"body": "JSON mal formado."})

    def test_devuelve_400_cuando_status_no_es_string(self):
        datos = {
            "external_game_id": "steam-100",
            "status": 10,
            "hours_played": 1,
        }

        respuesta = self._postear(datos)
        self._assert_error_validacion(respuesta, {"status": "Debe ser string."})

    def test_devuelve_400_cuando_status_no_esta_permitido(self):
        datos = {
            "external_game_id": "steam-101",
            "status": "paused",
            "hours_played": 1,
        }

        respuesta = self._postear(datos)
        self._assert_error_validacion(
            respuesta,
            {"status": "Debe ser uno de: wishlist, playing, completed, dropped."},
        )

    def test_devuelve_400_cuando_hours_played_no_es_integer(self):
        datos = {
            "external_game_id": "steam-102",
            "status": "wishlist",
            "hours_played": "7",
        }

        respuesta = self._postear(datos)
        self._assert_error_validacion(respuesta, {"hours_played": "Debe ser integer."})

    def test_devuelve_400_cuando_hours_played_es_negativo(self):
        datos = {
            "external_game_id": "steam-103",
            "status": "completed",
            "hours_played": -1,
        }

        respuesta = self._postear(datos)
        self._assert_error_validacion(
            respuesta, {"hours_played": "Debe ser mayor o igual que 0."}
        )

    def test_devuelve_400_cuando_hours_played_es_bool(self):
        datos = {
            "external_game_id": "steam-104",
            "status": "dropped",
            "hours_played": True,
        }

        respuesta = self._postear(datos)
        self._assert_error_validacion(respuesta, {"hours_played": "Debe ser integer."})

    def test_devuelve_400_cuando_faltan_campos_obligatorios(self):
        datos = {"status": "playing"}
        respuesta = self._postear(datos)

        self._assert_error_validacion(
            respuesta,
            {
                "external_game_id": "Campo obligatorio.",
                "hours_played": "Campo obligatorio.",
            },
        )

    def test_devuelve_400_cuando_external_game_id_esta_duplicado(self):
        datos = {
            "external_game_id": "steam-duplicate-1",
            "status": "playing",
            "hours_played": 2,
        }

        primera_respuesta = self._postear(datos)
        self.assertEqual(primera_respuesta.status_code, 201)

        segunda_respuesta = self._postear(datos)
        self._assert_error_duplicado(segunda_respuesta)

        self.assertEqual(
            LibraryEntry.objects.filter(external_game_id="steam-duplicate-1").count(),
            1,
        )


class PruebasApiListadoYDetalleBiblioteca(TestCase):
    ruta_listado = "/api/library/entries/"
    mensaje_not_found = "La entrada solicitada no existe"

    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="listuser",
            password="testpassword123",
        )
        self.client.force_login(self.usuario)
        self.entrada_1 = LibraryEntry.objects.create(
            user=self.usuario,
            external_game_id="steam-list-1",
            status="playing",
            hours_played=5,
        )
        self.entrada_2 = LibraryEntry.objects.create(
            user=self.usuario,
            external_game_id="steam-list-2",
            status="wishlist",
            hours_played=0,
        )

    def test_listado_devuelve_200_con_formato_esperado(self):
        respuesta = self.client.get(self.ruta_listado)

        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertEqual(len(cuerpo), 2)

        esperado = [
            {
                "id": self.entrada_1.id,
                "external_game_id": "steam-list-1",
                "status": "playing",
                "hours_played": 5,
            },
            {
                "id": self.entrada_2.id,
                "external_game_id": "steam-list-2",
                "status": "wishlist",
                "hours_played": 0,
            },
        ]
        self.assertEqual(cuerpo, esperado)

        for item in cuerpo:
            self.assertEqual(
                set(item.keys()),
                {"id", "external_game_id", "status", "hours_played"},
            )

    def test_detalle_existente_devuelve_200_con_formato_esperado(self):
        respuesta = self.client.get(f"{self.ruta_listado}{self.entrada_1.id}/")

        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertEqual(
            set(cuerpo.keys()),
            {"id", "external_game_id", "status", "hours_played"},
        )
        self.assertEqual(
            cuerpo,
            {
                "id": self.entrada_1.id,
                "external_game_id": "steam-list-1",
                "status": "playing",
                "hours_played": 5,
            },
        )

    def test_detalle_inexistente_devuelve_404_con_json_exacto(self):
        respuesta = self.client.get(f"{self.ruta_listado}999999/")

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(
            respuesta.json(),
            {
                "error": "not_found",
                "message": self.mensaje_not_found,
            },
        )


class PruebasApiActualizarEntradaBiblioteca(TestCase):
    ruta_base = "/api/library/entries/"
    mensaje_error_validacion = "Datos de entrada invalidos"
    mensaje_not_found = "La entrada solicitada no existe"

    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="patchuser",
            password="testpassword123",
        )
        self.client.force_login(self.usuario)
        self.entrada = LibraryEntry.objects.create(
            user=self.usuario,
            external_game_id="steam-patch-1",
            status="wishlist",
            hours_played=0,
        )

    def _patchear(self, entry_id, datos):
        return self.client.patch(
            f"{self.ruta_base}{entry_id}/",
            data=json.dumps(datos),
            content_type="application/json",
        )

    def _assert_error_validacion(self, respuesta, detalles_esperados=None):
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "validation_error")
        self.assertEqual(cuerpo["message"], self.mensaje_error_validacion)
        self.assertIn("details", cuerpo)

        if detalles_esperados is None:
            return

        for campo, motivo in detalles_esperados.items():
            self.assertEqual(cuerpo["details"].get(campo), motivo)

    def test_patch_devuelve_200_cuando_el_payload_es_valido(self):
        respuesta = self._patchear(
            self.entrada.id,
            {"status": "playing", "hours_played": 7},
        )

        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["id"], self.entrada.id)
        self.assertEqual(cuerpo["external_game_id"], "steam-patch-1")
        self.assertEqual(cuerpo["status"], "playing")
        self.assertEqual(cuerpo["hours_played"], 7)

        self.entrada.refresh_from_db()
        self.assertEqual(self.entrada.status, "playing")
        self.assertEqual(self.entrada.hours_played, 7)

    def test_patch_devuelve_400_cuando_body_vacio(self):
        respuesta = self._patchear(self.entrada.id, {})
        self._assert_error_validacion(
            respuesta, {"body": "El JSON no puede estar vacio."}
        )

    def test_patch_devuelve_400_cuando_status_invalido(self):
        respuesta = self._patchear(self.entrada.id, {"status": "paused"})
        self._assert_error_validacion(
            respuesta,
            {"status": "Debe ser uno de: wishlist, playing, completed, dropped."},
        )

    def test_patch_devuelve_400_cuando_hours_played_es_negativo(self):
        respuesta = self._patchear(self.entrada.id, {"hours_played": -5})
        self._assert_error_validacion(
            respuesta, {"hours_played": "Debe ser mayor o igual que 0."}
        )

    def test_patch_devuelve_400_cuando_llega_campo_desconocido(self):
        respuesta = self._patchear(self.entrada.id, {"titulo": "nuevo titulo"})
        self._assert_error_validacion(
            respuesta, {"titulo": "Campo no permitido."}
        )

    def test_patch_devuelve_404_cuando_id_no_existe(self):
        respuesta = self._patchear(999999, {"status": "playing"})
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(
            respuesta.json(),
            {
                "error": "not_found",
                "message": self.mensaje_not_found,
            },
        )

# Ejercicio 4
class PruebasApiSustituirEntradaBiblioteca(TestCase):
    ruta_base = "/api/library/entries/"
    mensaje_error_validacion = "Datos de entrada invalidos"

    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(username="testuser", password="testpassword123")
        self.otro_usuario = User.objects.create_user(username="otheruser", password="testpassword123")

        self.entrada = LibraryEntry.objects.create(
            user=self.usuario,
            external_game_id="steam-put-1",
            status="wishlist",
            hours_played=0,
        )

    def _putear(self, entry_id, datos):
        return self.client.put(
            f"{self.ruta_base}{entry_id}/",
            data=json.dumps(datos),
            content_type="application/json",
        )

    def test_put_devuelve_200_y_sustituye_todo(self):
        self.client.force_login(self.usuario)
        datos_nuevos = {
            "external_game_id": "steam-put-2",
            "status": "completed",
            "hours_played": 10
        }
        respuesta = self._putear(self.entrada.id, datos_nuevos)
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["external_game_id"], "steam-put-2")
        self.assertEqual(cuerpo["status"], "completed")
        self.assertEqual(cuerpo["hours_played"], 10)

    def test_put_devuelve_400_si_faltan_datos(self):
        self.client.force_login(self.usuario)
        datos_incompletos = {
            "status": "playing"
            # faltan external_game_id y hours_played
        }
        respuesta = self._putear(self.entrada.id, datos_incompletos)
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "validation_error")

    def test_put_devuelve_401_si_no_esta_autenticado(self):
        # No usamos force_login
        datos_nuevos = {
            "external_game_id": "steam-put-3",
            "status": "completed",
            "hours_played": 10
        }
        respuesta = self._putear(self.entrada.id, datos_nuevos)
        self.assertEqual(respuesta.status_code, 401)

    def test_put_devuelve_404_si_recurso_es_ajeno_o_no_existe(self):
        # Logueado como otro usuario
        self.client.force_login(self.otro_usuario)
        datos_nuevos = {
            "external_game_id": "steam-put-4",
            "status": "completed",
            "hours_played": 10
        }
        respuesta = self._putear(self.entrada.id, datos_nuevos)
        self.assertEqual(respuesta.status_code, 404)

        # Logueado como dueño pero intentando id inexistente
        self.client.force_login(self.usuario)
        respuesta_no_existe = self._putear(99999, datos_nuevos)
        self.assertEqual(respuesta_no_existe.status_code, 404)


# Ejercicio 6
class PruebasApiLogout(TestCase):
    ruta_logout = "/api/auth/logout/"
    ruta_me = "/api/users/me/"

    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(username="testuser", password="testpassword123")

    def test_logout_estando_autenticado(self):
        self.client.force_login(self.usuario)
        # Comprobar que esta logueado
        resp_me = self.client.get(self.ruta_me)
        self.assertEqual(resp_me.status_code, 200)

        # Hacer logout
        resp_logout = self.client.post(self.ruta_logout)
        self.assertEqual(resp_logout.status_code, 204)
        self.assertFalse(resp_logout.content) # body vacio

        # Comprobar que ya no esta logueado
        resp_me_despues = self.client.get(self.ruta_me)
        self.assertEqual(resp_me_despues.status_code, 401)

    def test_logout_sin_estar_autenticado(self):
        resp_logout = self.client.post(self.ruta_logout)
        self.assertEqual(resp_logout.status_code, 204)
        self.assertFalse(resp_logout.content)


# Ejercicio 2
class PruebasApiCambiarContrasena(TestCase):
    ruta_cambiar_pass = "/api/users/me/password/"

    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(username="testuser", password="oldpassword123")

    def _postear(self, datos):
        return self.client.post(
            self.ruta_cambiar_pass,
            data=json.dumps(datos),
            content_type="application/json",
        )

    def test_cambio_correcto_devuelve_200(self):
        self.client.force_login(self.usuario)
        datos = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123"
        }
        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"ok": True})
        
        # Verificar que la contrasena ha cambiado
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("newpassword123"))

    def test_devuelve_400_si_contrasena_actual_es_incorrecta(self):
        self.client.force_login(self.usuario)
        datos = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "validation_error")

    def test_devuelve_400_si_contrasena_nueva_es_corta(self):
        self.client.force_login(self.usuario)
        datos = {
            "current_password": "oldpassword123",
            "new_password": "short"
        }
        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 400)

    def test_devuelve_400_si_json_vacio(self):
        self.client.force_login(self.usuario)
        respuesta = self._postear({})
        self.assertEqual(respuesta.status_code, 400)

    def test_devuelve_401_si_no_esta_autenticado(self):
        datos = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123"
        }
        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 401)


class PruebasCatalogoSemana4(TestCase):
    ruta_search = "/api/catalog/search/"
    ruta_resolve = "/api/catalog/resolve/"
    ruta_library = "/api/library/entries/"

    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="cataloguser",
            password="testpassword123",
        )

    def _post_json(self, ruta, datos):
        return self.client.post(
            ruta,
            data=json.dumps(datos),
            content_type="application/json",
        )

    def test_search_devuelve_formato_estable(self):
        catalog_response = [
            {"gameID": "1", "external": "Mario Test", "thumb": "https://img.test/1.jpg"}
        ]

        with patch("library.views.CatalogService") as service_class:
            service_class.return_value.search_games.return_value = [
                {
                    "external_game_id": game["gameID"],
                    "title": game["external"],
                    "thumb": game["thumb"],
                }
                for game in catalog_response
            ]
            respuesta = self.client.get(f"{self.ruta_search}?q=mario")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json(),
            [
                {
                    "external_game_id": "1",
                    "title": "Mario Test",
                    "thumb": "https://img.test/1.jpg",
                }
            ],
        )

    def test_search_sin_q_devuelve_validation_error(self):
        respuesta = self.client.get(self.ruta_search)

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")

    def test_search_con_q_vacio_devuelve_validation_error(self):
        respuesta = self.client.get(f"{self.ruta_search}?q=")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")

    def test_resolve_devuelve_formato_estable(self):
        catalog_response = {
            "1": {"info": {"title": "Game One", "thumb": "https://img.test/1.jpg"}},
            "2": {"info": {"title": "Game Two", "thumb": "https://img.test/2.jpg"}},
        }

        expected_response = [
            {
                "external_game_id": "1",
                "title": "Game One",
                "thumb": "https://img.test/1.jpg",
            },
            {
                "external_game_id": "2",
                "title": "Game Two",
                "thumb": "https://img.test/2.jpg",
            },
        ]

        with patch("library.views.CatalogService") as service_class:
            service_class.return_value.resolve_games.return_value = expected_response
            respuesta = self._post_json(
                self.ruta_resolve,
                {"external_game_ids": ["1", "2"]},
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json(),
            expected_response,
        )

    def test_resolve_con_lista_vacia_devuelve_validation_error(self):
        respuesta = self._post_json(self.ruta_resolve, {"external_game_ids": []})

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")

    def test_resolve_sin_external_game_ids_devuelve_validation_error(self):
        respuesta = self._post_json(self.ruta_resolve, {})

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")

    def test_503_si_no_hay_respuesta_del_catalogo(self):
        with patch(
            "library.views.CatalogService",
        ) as service_class:
            service_class.return_value.search_games.side_effect = CatalogServiceUnavailable
            respuesta = self.client.get(f"{self.ruta_search}?q=mario")

        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(
            respuesta.json(),
            {
                "error": "external_service_unavailable",
                "message": "El catálogo externo no está disponible. Inténtalo más tarde.",
            },
        )

    def test_502_si_el_catalogo_responde_datos_invalidos(self):
        with patch(
            "library.views.CatalogService",
        ) as service_class:
            service_class.return_value.resolve_games.side_effect = CatalogServiceError
            respuesta = self._post_json(
                self.ruta_resolve,
                {"external_game_ids": ["1"]},
            )

        self.assertEqual(respuesta.status_code, 502)
        self.assertEqual(
            respuesta.json(),
            {
                "error": "external_service_error",
                "message": "Error al consultar el catálogo externo.",
            },
        )

    def test_post_library_sin_autenticar_devuelve_401(self):
        respuesta = self._post_json(
            self.ruta_library,
            {"external_game_id": "1", "status": "wishlist", "hours_played": 0},
        )

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()["error"], "unauthorized")

    def test_post_library_con_id_inexistente_devuelve_invalid_external_game_id(self):
        self.client.force_login(self.usuario)

        with patch("library.views.CatalogService") as service_class:
            service_class.return_value.external_game_id_exists.return_value = False
            respuesta = self._post_json(
                self.ruta_library,
                {"external_game_id": "not_found", "status": "wishlist", "hours_played": 0},
            )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json(),
            {
                "error": "invalid_external_game_id",
                "message": "El juego indicado no existe en el catálogo externo.",
                "details": {"external_game_id": "not_found"},
            },
        )

    def test_flujo_completo_search_create_list_resolve(self):
        self.client.force_login(self.usuario)
        search_response = [
            {"external_game_id": "flow-1", "title": "Flow Game", "thumb": "https://img.test/flow.jpg"}
        ]
        resolve_response = [
            {
                "external_game_id": "flow-1",
                "title": "Flow Game",
                "thumb": "https://img.test/flow.jpg",
            }
        ]

        with patch("library.views.CatalogService") as service_class:
            service_class.return_value.search_games.return_value = search_response
            search = self.client.get(f"{self.ruta_search}?q=mario")

        with patch("library.views.CatalogService") as service_class:
            service_class.return_value.external_game_id_exists.return_value = True
            create = self._post_json(
                self.ruta_library,
                {"external_game_id": "flow-1", "status": "wishlist", "hours_played": 0},
            )

        listado = self.client.get(self.ruta_library)

        with patch("library.views.CatalogService") as service_class:
            service_class.return_value.resolve_games.return_value = resolve_response
            resolve = self._post_json(
                self.ruta_resolve,
                {"external_game_ids": ["flow-1"]},
            )

        self.assertEqual(search.status_code, 200)
        self.assertEqual(create.status_code, 201)
        self.assertEqual(listado.status_code, 200)
        self.assertEqual(resolve.status_code, 200)
        self.assertNotIn("title", listado.json()[0])
        self.assertEqual(resolve.json()[0]["title"], "Flow Game")


class PruebasCatalogServiceRedis(TestCase):
    def test_dos_busquedas_iguales_usan_redis_en_la_segunda(self):
        fake_redis = FakeRedis()
        service = CatalogService(redis_client=fake_redis, cache_ttl=300, stale_cache_ttl=600)
        provider_response = [
            {
                "external_game_id": "1",
                "title": "Mario Test",
                "thumb": "https://img.test/1.jpg",
            }
        ]

        with patch.object(
            service,
            "_fetch_games_by_title",
            return_value=provider_response,
        ) as provider:
            primera = service.search_games("mario")
            segunda = service.search_games("mario")

        self.assertEqual(primera, segunda)
        self.assertEqual(provider.call_count, 1)
        self.assertIn("catalog:search:mario", fake_redis.data)

    def test_fallo_proveedor_con_cache_stale_devuelve_redis(self):
        fake_redis = FakeRedis()
        service = CatalogService(redis_client=fake_redis, cache_ttl=300, stale_cache_ttl=600)
        cached_response = [
            {
                "external_game_id": "1",
                "title": "Mario Test",
                "thumb": "https://img.test/1.jpg",
            }
        ]
        fake_redis.data["catalog:search:stale:mario"] = json.dumps(cached_response)

        with patch.object(
            service,
            "_fetch_games_by_title",
            side_effect=CatalogServiceUnavailable,
        ):
            with self.assertLogs("library.catalog_service", level="WARNING") as logs:
                respuesta = service.search_games("mario")

        self.assertEqual(respuesta, cached_response)
        self.assertIn("redis_fallback_after_provider_error", "\n".join(logs.output))

    def test_fallo_proveedor_sin_cache_propaga_503(self):
        service = CatalogService(redis_client=FakeRedis())

        with patch.object(
            service,
            "_fetch_games_by_title",
            side_effect=CatalogServiceUnavailable,
        ):
            with self.assertRaises(CatalogServiceUnavailable):
                service.search_games("mario")

    def test_fallo_proveedor_sin_cache_propaga_502(self):
        service = CatalogService(redis_client=FakeRedis())

        with patch.object(
            service,
            "_fetch_games_by_title",
            side_effect=CatalogServiceError,
        ):
            with self.assertRaises(CatalogServiceError):
                service.search_games("mario")


class FakeEmailResponse:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.body.encode("utf-8")


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.setex_calls = []
        self.get_calls = []

    def get(self, key):
        self.get_calls.append(key)
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.setex_calls.append((key, ttl, value))
        self.data[key] = value


@override_settings(
    MAILEROO_API_KEY="test-key",
    MAILEROO_FROM_ADDRESS="sender@example.com",
    MAILEROO_FROM_NAME="Nexus Play",
    MAILEROO_API_URL="https://smtp.maileroo.com/api/v2/emails",
    MAILEROO_TIMEOUT=1,
)
class PruebasEmailService(TestCase):
    def test_envio_correcto_registra_logs_y_payload(self):
        fake_response = FakeEmailResponse(
            '{"success": true, "data": {"reference_id": "ref-123"}}'
        )

        with patch("library.email_service.urllib.request.urlopen", return_value=fake_response) as mocked_urlopen:
            with self.assertLogs("library.email_service", level="INFO") as logs:
                result = EmailService().send_email(
                    "destino@example.com",
                    "Asunto",
                    "Texto",
                    action="send_email",
                )

        self.assertTrue(result["success"])
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["from"]["address"], "sender@example.com")
        self.assertEqual(payload["to"], [{"address": "destino@example.com"}])
        self.assertIn("email intento de envio", "\n".join(logs.output))
        self.assertIn("email envio OK", "\n".join(logs.output))
        self.assertNotIn("test-key", "\n".join(logs.output))

    def test_timeout_o_red_lanza_error_controlado_503(self):
        with patch(
            "library.email_service.urllib.request.urlopen",
            side_effect=urllib.error.URLError("network down"),
        ):
            with self.assertLogs("library.email_service", level="ERROR") as logs:
                with self.assertRaises(EmailServiceUnavailable):
                    EmailService().send_email(
                        "destino@example.com",
                        "Asunto",
                        "Texto",
                        action="send_email",
                    )

        self.assertIn("fallo por timeout/red", "\n".join(logs.output))

    def test_respuesta_invalida_lanza_error_controlado_502(self):
        fake_response = FakeEmailResponse('{"success": false}', status=200)

        with patch("library.email_service.urllib.request.urlopen", return_value=fake_response):
            with self.assertLogs("library.email_service", level="ERROR") as logs:
                with self.assertRaises(EmailServiceError):
                    EmailService().send_email(
                        "destino@example.com",
                        "Asunto",
                        "Texto",
                        action="send_email",
                    )

        self.assertIn("fallo por respuesta del proveedor", "\n".join(logs.output))


class PruebasDebugEmail(TestCase):
    ruta = "/api/debug/email/test/"

    def _post_json(self, datos):
        return self.client.post(
            self.ruta,
            data=json.dumps(datos),
            content_type="application/json",
        )

    @override_settings(DEBUG=True)
    def test_envio_correcto_devuelve_ok(self):
        with patch("library.views.EmailService") as service_class:
            respuesta = self._post_json(
                {"to": "destino@example.com", "subject": "Asunto", "text": "Texto"}
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"ok": True})
        service_class.return_value.send_email.assert_called_once_with(
            to="destino@example.com",
            subject="Asunto",
            text="Texto",
            action="send_email",
        )

    @override_settings(DEBUG=True)
    def test_json_vacio_devuelve_validation_error(self):
        respuesta = self._post_json({})

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")

    @override_settings(DEBUG=True)
    def test_falta_to_devuelve_validation_error(self):
        respuesta = self._post_json({"subject": "Asunto", "text": "Texto"})

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")
        self.assertEqual(respuesta.json()["details"]["to"], "Campo obligatorio.")

    @override_settings(DEBUG=True)
    def test_to_no_string_devuelve_validation_error(self):
        respuesta = self._post_json({"to": 123, "subject": "Asunto", "text": "Texto"})

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")
        self.assertEqual(respuesta.json()["details"]["to"], "Debe ser string.")

    @override_settings(DEBUG=True)
    def test_fallo_red_devuelve_503(self):
        with patch("library.views.EmailService") as service_class:
            service_class.return_value.send_email.side_effect = EmailServiceUnavailable
            respuesta = self._post_json(
                {"to": "destino@example.com", "subject": "Asunto", "text": "Texto"}
            )

        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(respuesta.json()["error"], "external_service_unavailable")

    @override_settings(DEBUG=True)
    def test_fallo_proveedor_devuelve_502(self):
        with patch("library.views.EmailService") as service_class:
            service_class.return_value.send_email.side_effect = EmailServiceError
            respuesta = self._post_json(
                {"to": "destino@example.com", "subject": "Asunto", "text": "Texto"}
            )

        self.assertEqual(respuesta.status_code, 502)
        self.assertEqual(respuesta.json()["error"], "external_service_error")

    @override_settings(DEBUG=False)
    def test_si_no_hay_debug_devuelve_404(self):
        respuesta = self._post_json(
            {"to": "destino@example.com", "subject": "Asunto", "text": "Texto"}
        )

        self.assertEqual(respuesta.status_code, 404)


@override_settings(
    MAILEROO_API_KEY="test-key",
    MAILEROO_FROM_ADDRESS="sender@example.com",
    MAILEROO_FROM_NAME="Nexus Play",
    MAILEROO_API_URL="https://smtp.maileroo.com/api/v2/emails",
    MAILEROO_TIMEOUT=1,
)
class PruebasRegistroConEmail(TestCase):
    ruta = "/api/auth/register/"

    def _post_json(self, datos):
        return self.client.post(
            self.ruta,
            data=json.dumps(datos),
            content_type="application/json",
        )

    def test_registro_requiere_email(self):
        respuesta = self._post_json(
            {"username": "nuevo", "password": "password123"}
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")
        self.assertEqual(respuesta.json()["details"]["email"], "Campo obligatorio.")

    def test_registro_valida_formato_email(self):
        respuesta = self._post_json(
            {"username": "nuevo", "password": "password123", "email": "sin-arroba"}
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "validation_error")
        self.assertEqual(
            respuesta.json()["details"]["email"],
            "Debe tener un formato valido.",
        )

    def test_registro_correcto_envia_bienvenida_y_devuelve_email(self):
        fake_response = FakeEmailResponse(
            '{"success": true, "data": {"reference_id": "welcome-1"}}'
        )

        with patch("library.email_service.urllib.request.urlopen", return_value=fake_response):
            with self.assertLogs("library.email_service", level="INFO") as logs:
                respuesta = self._post_json(
                    {
                        "username": "nuevo",
                        "password": "password123",
                        "email": "nuevo@example.com",
                    }
                )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["email"], "nuevo@example.com")
        self.assertIn("register_welcome", "\n".join(logs.output))
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="nuevo").exists())

    def test_registro_crea_usuario_aunque_falle_el_email(self):
        with override_settings(MAILEROO_API_KEY=""):
            with self.assertLogs("library.email_service", level="ERROR") as logs:
                respuesta = self._post_json(
                    {
                        "username": "nuevo",
                        "password": "password123",
                        "email": "nuevo@example.com",
                    }
                )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["email"], "nuevo@example.com")
        self.assertIn("register_welcome", "\n".join(logs.output))
        self.assertIn("type=configuration", "\n".join(logs.output))
