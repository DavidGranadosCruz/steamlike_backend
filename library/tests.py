import json

from django.test import TestCase

from .models import LibraryEntry


class PruebasApiCrearEntradaBiblioteca(TestCase):
    ruta = "/api/library/entries/"
    mensaje_error_validacion = "Datos de entrada invalidos"
    mensaje_error_duplicado = "El juego ya existe en la biblioteca"

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
        # Aqui preparo 2 entradas para probar listado y detalle.
        self.entrada_1 = LibraryEntry.objects.create(
            external_game_id="steam-list-1",
            status="playing",
            hours_played=5,
        )
        self.entrada_2 = LibraryEntry.objects.create(
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
        # Aqui creo una entrada base para probar PATCH.
        self.entrada = LibraryEntry.objects.create(
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
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(
            respuesta.json(),
            {
                "error": "not_found",
                "message": self.mensaje_not_found,
            },
        )

from django.contrib.auth import get_user_model

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
