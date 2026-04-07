import json

from django.test import TestCase

from .models import LibraryEntry


class PruebasApiCrearEntradaBiblioteca(TestCase):
    ruta = "/api/library/entries/"

    def _postear(self, datos):
        return self.client.post(
            self.ruta,
            data=json.dumps(datos),
            content_type="application/json",
        )

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
        self.assertEqual(respuesta.status_code, 400)

    def test_devuelve_400_cuando_status_no_es_string(self):
        datos = {
            "external_game_id": "steam-100",
            "status": 10,
            "hours_played": 1,
        }

        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 400)

    def test_devuelve_400_cuando_status_no_esta_permitido(self):
        datos = {
            "external_game_id": "steam-101",
            "status": "paused",
            "hours_played": 1,
        }

        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 400)

    def test_devuelve_400_cuando_hours_played_no_es_integer(self):
        datos = {
            "external_game_id": "steam-102",
            "status": "wishlist",
            "hours_played": "7",
        }

        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 400)

    def test_devuelve_400_cuando_hours_played_es_negativo(self):
        datos = {
            "external_game_id": "steam-103",
            "status": "completed",
            "hours_played": -1,
        }

        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 400)

    def test_devuelve_400_cuando_hours_played_es_bool(self):
        datos = {
            "external_game_id": "steam-104",
            "status": "dropped",
            "hours_played": True,
        }

        respuesta = self._postear(datos)
        self.assertEqual(respuesta.status_code, 400)
