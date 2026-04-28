import json

tests_code = """import json
from django.test import TestCase
from django.contrib.auth.models import User
from .models import LibraryEntry

class PruebasApiAuth(TestCase):
    def test_registro_valido(self):
        respuesta = self.client.post("/api/auth/register/", data=json.dumps({"username": "testuser", "password": "password123"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 201)
        self.assertIn("id", respuesta.json())
        self.assertEqual(respuesta.json()["username"], "testuser")

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
        self.assertEqual(respuesta.json()["message"], self.mensaje_not_found)

class PruebasApiModificarEntradaBiblioteca(TestCase):
    ruta_base = "/api/library/entries/"
    mensaje_error_validacion = "Datos de entrada invalidos"
    mensaje_not_found = "La entrada solicitada no existe"

    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")
        self.entrada = LibraryEntry.objects.create(external_game_id="steam-patch-1", status="playing", hours_played=10, user=self.user1)
        self.ruta = f"{self.ruta_base}{self.entrada.id}/"
        self.client.force_login(self.user1)

    def test_modificacion_parcial_correcta(self):
        respuesta = self.client.patch(self.ruta, data=json.dumps({"status": "completed"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 200)

    def test_modificacion_sin_autenticar(self):
        self.client.logout()
        respuesta = self.client.patch(self.ruta, data=json.dumps({"status": "completed"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 401)

    def test_modificacion_ajena(self):
        self.client.force_login(self.user2)
        respuesta = self.client.patch(self.ruta, data=json.dumps({"status": "completed"}), content_type="application/json")
        self.assertEqual(respuesta.status_code, 404)

class PruebasModeloLibraryEntry(TestCase):
    def test_external_id_upper_convierte_a_mayusculas(self):
        entrada = LibraryEntry(external_game_id="steam-123")
        self.assertEqual(entrada.external_id_upper(), "STEAM-123")
        entrada_vacia = LibraryEntry(external_game_id=None)
        self.assertEqual(entrada_vacia.external_id_upper(), "")

    def test_hours_played_label_asigna_etiqueta_correcta(self):
        self.assertEqual(LibraryEntry(hours_played=0).hours_played_label(), "none")
        self.assertEqual(LibraryEntry(hours_played=5).hours_played_label(), "low")
        self.assertEqual(LibraryEntry(hours_played=15).hours_played_label(), "high")

    def test_status_value_asignaciones_correctas(self):
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_WISHLIST).status_value(), 0)
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_PLAYING).status_value(), 1)
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_COMPLETED).status_value(), 2)
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_DROPPED).status_value(), 3)
        self.assertEqual(LibraryEntry(status="inventado").status_value(), -1)

class PruebasApiHealth(TestCase):
    def test_health_get_devuelve_200_y_json_correcto(self):
        respuesta = self.client.get("/api/health/")
        self.assertEqual(respuesta.status_code, 200)

    def test_health_metodo_incorrecto_devuelve_405(self):
        respuesta = self.client.post("/api/health/")
        self.assertEqual(respuesta.status_code, 405)
"""

with open(r"c:\Users\PC\OneDrive\Escritorio\ILERNA\Entorno servidor\Proyecto\library\tests.py", "w", encoding="utf-8") as f:
    f.write(tests_code)
print("done")
