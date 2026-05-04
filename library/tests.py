import json
from django.test import TestCase
from django.contrib.auth.models import User
from .models import LibraryEntry

class PruebasApiAuth(TestCase):
    def test_registro_valido(self):
        respuesta = self.client.post("/api/auth/register/", data=json.dumps({"username": "testuser", "password": "password123"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 201)
        self.assertIn("id", respuesta.json())
        self.assertEqual(respuesta.json()["username"], "usuario_FALLO")

    def test_registro_invalido(self):
        # Vacio
        respuesta = self.client.post("/api/auth/register/", data=json.dumps({}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        
        # Falta campo
        respuesta = self.client.post("/api/auth/register/", data=json.dumps({"username": "user2"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        
        # Pass corta
        respuesta = self.client.post("/api/auth/register/", data=json.dumps({"username": "user3", "password": "123"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        
        # Username repetido
        User.objects.create_user(username="testuser", password="password123")
        respuesta = self.client.post("/api/auth/register/", data=json.dumps({"username": "testuser", "password": "password123"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)

    def test_login_valido(self):
        User.objects.create_user(username="testuser", password="password123")
        respuesta = self.client.post("/api/auth/login/", data=json.dumps({"username": "testuser", "password": "password123"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 200)

    def test_login_invalido(self):
        User.objects.create_user(username="testuser", password="password123")
        respuesta = self.client.post("/api/auth/login/", data=json.dumps({"username": "testuser", "password": "wrongpassword"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()["message"], "Credenciales incorrectas")

    def test_me_valido(self):
        user = User.objects.create_user(username="testuser", password="password123")
        self.client.force_login(user)
        respuesta = self.client.get("/api/users/me/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["username"], "testuser")

    def test_me_invalido(self):
        respuesta = self.client.get("/api/users/me/")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()["message"], "No autenticado")

class PruebasApiCrearEntradaBiblioteca(TestCase):
    ruta = "/api/library/entries/"
    mensaje_error_validacion = "Datos de entrada invalidos"
    mensaje_error_duplicado = "El juego ya existe en la biblioteca"

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.force_login(self.user)

    def _postear(self, datos):
        return self.client.post(self.ruta, data=json.dumps(datos), content_type="application/json")

    def test_sin_autenticar(self):
        self.client.logout()
        respuesta = self._postear({"external_game_id": "steam-12345", "status": "playing", "hours_played": 12})
        self.assertEqual(respuesta.status_code, 401)

    def test_aislamiento(self):
        self._postear({"external_game_id": "steam-123", "status": "playing", "hours_played": 12})
        user2 = User.objects.create_user(username="user2", password="password123")
        self.client.force_login(user2)
        respuesta = self.client.get(self.ruta)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.json()), 0) # Lo creado por testuser no lo ve user2

    def test_devuelve_201_cuando_el_payload_es_valido(self):
        datos = {"external_game_id": "steam-12345", "status": "playing", "hours_played": 12}
        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["external_game_id"], datos["external_game_id"])
        self.assertTrue(LibraryEntry.objects.filter(external_game_id="steam-12345", user=self.user).exists())

    def test_devuelve_400_cuando_faltan_campos_obligatorios(self):
        respuesta = self._postear({"status": "playing"})
        self.assertEqual(respuesta.status_code, 400)

class PruebasApiListadoYDetalleBiblioteca(TestCase):
    ruta_listado = "/api/library/entries/"
    mensaje_not_found = "La entrada solicitada no existe"

    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")
        self.entrada_1 = LibraryEntry.objects.create(external_game_id="steam-list-1", status="playing", hours_played=5, user=self.user1)
        self.entrada_2 = LibraryEntry.objects.create(external_game_id="steam-list-2", status="wishlist", hours_played=0, user=self.user2)
        self.client.force_login(self.user1)

    def test_listado_sin_autenticar(self):
        self.client.logout()
        respuesta = self.client.get(self.ruta_listado)
        self.assertEqual(respuesta.status_code, 401)

    def test_listado_aislamiento(self):
        # User 1 solo ve entrada 1
        respuesta = self.client.get(self.ruta_listado)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.json()), 1)
        self.assertEqual(respuesta.json()[0]["id"], self.entrada_1.id)

    def test_detalle_sin_autenticar(self):
        self.client.logout()
        respuesta = self.client.get(f"{self.ruta_listado}{self.entrada_1.id}/")
        self.assertEqual(respuesta.status_code, 401)

    def test_detalle_ajeno_devuelve_404(self):
        respuesta = self.client.get(f"{self.ruta_listado}{self.entrada_2.id}/")
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
        self.user = User.objects.create_user(username="testuser_patch", password="password123")
        self.client.force_login(self.user)
        self.entrada = LibraryEntry.objects.create(
            user=self.user,
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
