import os
import sys
sys.argv.append("test")
import django
import json
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "steamlike_backend.settings")
django.setup()

from django.test import Client
from django.core.management import call_command
from library.models import LibraryEntry
from django.contrib.auth import get_user_model

def run_tests():
    call_command("migrate", verbosity=0)
    client = Client(SERVER_NAME='localhost')
    User = get_user_model()

    username = f"testuser_ejercicios_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, password='password123')

    print("--- Ejercicio 2 ---")
    # 1. GET /api/catalog/search/?q=mario
    resp1 = client.get('/api/catalog/search/?q=mario')
    print(f"1. status: {resp1.status_code}")
    if resp1.status_code == 200:
        print(f"   body: {resp1.json()[:1]}")
    else:
        print(f"   body: {resp1.content}")

    # 2. GET /api/catalog/search/?q=
    resp2 = client.get('/api/catalog/search/?q=')
    print(f"2. status: {resp2.status_code}")
    print(f"   body: {resp2.json()}")

    # 3. GET /api/catalog/search/ (sin q)
    resp3 = client.get('/api/catalog/search/')
    print(f"3. status: {resp3.status_code}")
    print(f"   body: {resp3.json()}")

    print("\n--- Ejercicio 3 ---")
    # 1. POST /api/catalog/resolve/ con {"external_game_ids":["1","2"]}
    resp4 = client.post('/api/catalog/resolve/', json.dumps({"external_game_ids":["1","2"]}), content_type="application/json")
    print(f"1. status: {resp4.status_code}")
    print(f"   body: {resp4.json()}")

    # 2. POST /api/catalog/resolve/ con {"external_game_ids":[]}
    resp5 = client.post('/api/catalog/resolve/', json.dumps({"external_game_ids":[]}), content_type="application/json")
    print(f"2. status: {resp5.status_code}")
    print(f"   body: {resp5.json()}")

    # 3. POST /api/catalog/resolve/ con {}
    resp6 = client.post('/api/catalog/resolve/', json.dumps({}), content_type="application/json")
    print(f"3. status: {resp6.status_code}")
    print(f"   body: {resp6.json()}")

    print("\n--- Ejercicio 4 ---")
    # 1. POST /api/library/entries/ con un external_game_id inexistente (usando autenticacion)
    client.force_login(user)
    resp7 = client.post('/api/library/entries/', json.dumps({
        "external_game_id": "99999999999",
        "status": "playing",
        "hours_played": 10
    }), content_type="application/json")
    print(f"1. status: {resp7.status_code}")
    print(f"   body: {resp7.json()}")

    print("\n--- Ejercicio 5 ---")
    print("Flujo completo (search, create, list, resolve):")
    search_data = resp1.json() if resp1.status_code == 200 else []
    game_id_to_add = None
    for game in search_data:
        candidate = game.get("external_game_id")
        if candidate and not LibraryEntry.objects.filter(external_game_id=candidate).exists():
            game_id_to_add = candidate
            break

    if game_id_to_add is None:
        resp_zelda = client.get('/api/catalog/search/?q=zelda')
        if resp_zelda.status_code == 200:
            for game in resp_zelda.json():
                candidate = game.get("external_game_id")
                if candidate and not LibraryEntry.objects.filter(external_game_id=candidate).exists():
                    game_id_to_add = candidate
                    break

    if game_id_to_add is None:
        print("create status: SKIP (no hay gameID libre para la prueba en la BD local)")
        resp_add = None
    else:
        resp_add = client.post('/api/library/entries/', json.dumps({
            "external_game_id": game_id_to_add,
            "status": "playing",
            "hours_played": 10
        }), content_type="application/json")
        print(f"create status: {resp_add.status_code}")
        if resp_add.status_code != 201:
            print(f"create body: {resp_add.json()}")

    resp_list = client.get('/api/library/entries/')
    print(f"list status: {resp_list.status_code}")
    data = resp_list.json()
    print(f"list size: {len(data)}")

    ids_to_resolve = [entry["external_game_id"] for entry in data]
    if ids_to_resolve:
        resp_res = client.post('/api/catalog/resolve/', json.dumps({"external_game_ids": ids_to_resolve}), content_type="application/json")
        print(f"resolve status: {resp_res.status_code}")
        print(f"resolve body: {resp_res.json()[:1]}")
    else:
        print("resolve status: SKIP (sin entradas creadas)")

    print("\nIntentos fallidos de Ejercicio 5:")
    client.logout()
    resp_unauth = client.post('/api/library/entries/', json.dumps({
        "external_game_id": game_id_to_add or "1",
        "status": "playing",
        "hours_played": 10
    }), content_type="application/json")
    print(f"unauth status: {resp_unauth.status_code}")
    print(f"unauth body: {resp_unauth.json()}")

    user.delete()

if __name__ == '__main__':
    run_tests()
