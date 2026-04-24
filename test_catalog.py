import os
import django
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "steamlike_backend.settings")
django.setup()

client = Client(HTTP_HOST='localhost')

#PRUEBA EXITOSA
print("1. GET /api/catalog/search/?q=mario")
resp1 = client.get("/api/catalog/search/?q=mario")
print("Status:", resp1.status_code)
print("Body:", resp1.json() if resp1.status_code != 400 or resp1.content.startswith(b'{') else resp1.content)

#PRUEBA ERROR
print("\n2. GET /api/catalog/search/?q=")
resp2 = client.get("/api/catalog/search/?q=")
print("Status:", resp2.status_code)
print("Body:", resp2.json() if resp2.status_code != 400 or resp2.content.startswith(b'{') else resp2.content)

#PRUEBA ERROR POR NO TENER PARAMETRO
print("\n3. GET /api/catalog/search/ (sin q)")
resp3 = client.get("/api/catalog/search/")
print("Status:", resp3.status_code)
print("Body:", resp3.json() if resp3.status_code != 400 or resp3.content.startswith(b'{') else resp3.content)
