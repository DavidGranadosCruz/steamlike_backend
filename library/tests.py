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


class PruebasModeloLibraryEntry(TestCase):
    def test_external_id_upper_convierte_a_mayusculas(self):
        entrada = LibraryEntry(external_game_id="steam-123")
        self.assertEqual(entrada.external_id_upper(), "STEAM-123")
        
        # Caso limite: None
        entrada_vacia = LibraryEntry(external_game_id=None)
        self.assertEqual(entrada_vacia.external_id_upper(), "")

    def test_hours_played_label_asigna_etiqueta_correcta(self):
        # 0 horas -> "none"
        entrada_none = LibraryEntry(hours_played=0)
        self.assertEqual(entrada_none.hours_played_label(), "none")
        
        # < 10 horas -> "low"
        entrada_low = LibraryEntry(hours_played=5)
        self.assertEqual(entrada_low.hours_played_label(), "low")
        
        # >= 10 horas -> "high"
        entrada_high = LibraryEntry(hours_played=15)
        self.assertEqual(entrada_high.hours_played_label(), "high")

    def test_status_value_asignaciones_correctas(self):
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_WISHLIST).status_value(), 0)
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_PLAYING).status_value(), 1)
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_COMPLETED).status_value(), 2)
        self.assertEqual(LibraryEntry(status=LibraryEntry.STATUS_DROPPED).status_value(), 3)
        self.assertEqual(LibraryEntry(status="inventado").status_value(), -1)


class PruebasApiHealth(TestCase):
    ruta = "/api/health/"

    def test_health_get_devuelve_200_y_json_correcto(self):
        respuesta = self.client.get(self.ruta)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"status": "ok"})

    def test_health_metodo_incorrecto_devuelve_405(self):
        # Se comprueba que falla si enviamos otro metodo HTTP
        respuesta = self.client.post(self.ruta)
        self.assertEqual(respuesta.status_code, 405)

