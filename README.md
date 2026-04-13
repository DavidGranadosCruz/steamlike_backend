steamlike_backend
Backend Django para el proyecto que se realizará en DWES de 2º DAW.
Arranque del proyecto
1) Levantar contenedores
```
docker compose up --build
```
2) Migraciones
Para crear las migraciones:
```
docker compose exec web python manage.py makemigrations
```
Para aplicar las migraciones:
```
docker compose exec web python manage.py migrate
```
3) Crear superusuario (admin)
```
docker compose exec web python manage.py createsuperuser
```
4) Abrir el admin
Admin: `http://localhost:8000/admin/`
5) Health-check
`GET http://localhost:8000/health/`
Comandos útiles dentro del contenedor
Entrar en una shell del contenedor web
```
docker compose exec web bash
```
Crear una nueva app (ej.: auth_api)
```
docker compose exec web python manage.py startapp auth_api
```
> Recuerda: después hay que añadir la app a `INSTALLED_APPS` y crear/incluir sus `urls.py` si aplica.
Variables de entorno (.env)
El proyecto carga variables desde `.env` (usado por `docker-compose.yml`).  
En desarrollo, por defecto CORS permite:
`http://frontend:3000`
`http://localhost:3000`
Si cambias el frontend, ajusta `DJANGO_CORS_ALLOWED_ORIGINS` y `DJANGO_CSRF_TRUSTED_ORIGINS`.
Estructura inicial
`core`: health-check y configuración base
`library`: modelo `LibraryEntry`
> No hay endpoints API predefinidos (salvo `admin/` y `health/`).
---
Optativa
Ejecución de los tests
El proyecto se ejecuta dentro de contenedores. Por tanto, los tests deben lanzarse desde el contenedor del backend.
1) Levantar los contenedores (si no están levantados)
```
docker compose up -d
```
2) Ejecutar todos los tests
La forma habitual es ejecutar `manage.py test` dentro del servicio del backend:
```
docker compose exec web python manage.py test
```
3) Ejecutar solo una parte (opcional)
Ejecutar solo los tests de una app:
```
docker compose exec web python manage.py test library
```
Ejecutar una clase de tests concreta (ejemplo):
```
docker compose exec web python manage.py test library.tests.test_models.LibraryEntryExternalIdLengthTests
```
Ejecución de tests con coverage
Este comando ejecuta todos los tests del proyecto y recoge información de cobertura:
```
docker compose exec web coverage run manage.py test
```
Si algún test falla, el comando terminará mostrando el error correspondiente.
---
Ver el informe de coverage en texto
Una vez ejecutados los tests, se puede ver un resumen de la cobertura en la consola:
```
docker compose exec web coverage report
```
---
Generar el informe HTML de coverage
Para generar un informe visual en HTML:
```
docker compose exec web coverage html
```
Este comando crea una carpeta llamada `htmlcov/`. Puedes visualizar el archivo `htmlconv/index.html` que tendrá los resultados.
---
Nota importante
El coverage es una métrica orientativa,
pero no mide la calidad de los tests.