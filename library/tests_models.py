from django.test import TestCase

from library.models import LibraryEntry

class DemoTest(TestCase):
    def test_demo(self):
        # Comprueba que dos valores son exactamente iguales.
        self.assertEqual(4, 2+2)
        # Comprueba si una condición se cumple o no.
        self.assertTrue(4 == 4)
        self.assertFalse(5 == 4)
        # Permiten distinguir entre None y otros valores como cadenas vacías o ceros.
        self.assertIsNone(None)
        # Comprueba que una acción provoca un error concreto.
        with self.assertRaises(ZeroDivisionError):
            # Codigo que lanza la excepcion
            4/0

class LibraryEntryExternalIdLengthTests(TestCase):
    def test_external_id_length_counts_regular_string(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="abc")

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 3)

    def test_external_id_length_counts_empty_string_as_zero(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="")

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 0)

    def test_external_id_length_counts_whitespace(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="   ")

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 3)

    def test_external_id_length_counts_max_length_boundary_100(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="x" * 100)

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 100)

    def test_external_id_length_raises_type_error_if_not_string_or_none(self):
        # Caso anómalo: asignación indebida en memoria.
        # Precondiciones
        entry = LibraryEntry(external_game_id=123)

        # Llamada
        # Comprobaciones
        with self.assertRaises(TypeError):
            entry.external_id_length()

class LibraryEntryExternalIdUpperTests(TestCase):
    def test_external_id_upper_returns_uppercase(self):
        #precondiciones
        entry = LibraryEntry(external_game_id="abC-123")
        # comprobaciones
        self.assertEqual(entry.external_id_upper(), "ABC-123")

    def test_external_id_upper_returns_empty_string_cuando_external_id_is_none(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="temp")
        # Llamada
        entry.external_game_id = None
        # Comprobaciones
        self.assertEqual(entry.external_id_upper(), "")

    def test_external_id_upper_returns_empty_string_cuando_external_id_is_empty(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="")
        # Comprobaciones
        self.assertEqual(entry.external_id_upper(), "")

class LibraryEntryHoursPlayedLabelTests(TestCase):
    def test_hours_played_Label_devuelve_none_horas_jugadas_cero(self):
        #precondiciones
        entry = LibraryEntry(hours_played=0)

        #comprobaciones
        self.assertEqual(entry.hours_played_label(), "none")    



    