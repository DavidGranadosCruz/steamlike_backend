import os
import sys
sys.argv.append("test")
import django
import json

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
    
    # Crear un usuario de prueba si no existe
    user, created = User.objects.get_or_create(username='testuser_ejercicios')
    if created:
        user.set_password('password123')
        user.save()

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
    # search ya lo hicimos y sabemos que funciona
    game_id_to_add = "128" # Mario o algo existente, 128 es Batman en cheapshark
    resp_add = client.post('/api/library/entries/', json.dumps({
        "external_game_id": game_id_to_add, 
        "status": "playing", 
        "hours_played": 10
    }), content_type="application/json")
    print(f"create status: {resp_add.status_code}")
    
    resp_list = client.get('/api/library/entries/')
    print(f"list status: {resp_list.status_code}")
    data = resp_list.json()
    print(f"list size: {len(data)}")
    
    ids_to_resolve = [entry["external_game_id"] for entry in data]
    resp_res = client.post('/api/catalog/resolve/', json.dumps({"external_game_ids": ids_to_resolve}), content_type="application/json")
    print(f"resolve status: {resp_res.status_code}")
    print(f"resolve body: {resp_res.json()[:1]}")

    print("\nIntentos fallidos de Ejercicio 5:")
    client.logout()
    resp_unauth = client.post('/api/library/entries/', json.dumps({
        "external_game_id": "128", 
        "status": "playing", 
        "hours_played": 10
    }), content_type="application/json")
    print(f"unauth status: {resp_unauth.status_code}")
    print(f"unauth body: {resp_unauth.json()}")

if __name__ == '__main__':
    run_tests()
