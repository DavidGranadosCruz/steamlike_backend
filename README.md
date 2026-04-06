# steamlike_backend

Backend Django para el proyecto que se realizará en DWES de 2º DAW.

## Arranque del proyecto

### 1) Levantar contenedores
```
docker compose up --build
```

### 2) Migraciones
Para crear las migraciones:
```
docker compose exec web python manage.py makemigrations
```

Para aplicar las migraciones:
```
docker compose exec web python manage.py migrate
```

### 3) Crear superusuario (admin)
```
docker compose exec web python manage.py createsuperuser
```

### 4) Abrir el admin
- Admin: `http://localhost:8000/admin/`

### 5) Health-check
- `GET http://localhost:8000/health/`

## Comandos útiles dentro del contenedor

### Entrar en una shell del contenedor web
```
docker compose exec web bash
```

### Crear una nueva app (ej.: auth_api)
```
docker compose exec web python manage.py startapp auth_api
```

> Recuerda: después hay que añadir la app a `INSTALLED_APPS` y crear/incluir sus `urls.py` si aplica.

## Variables de entorno (.env)
El proyecto carga variables desde `.env` (usado por `docker-compose.yml`).  
En desarrollo, por defecto CORS permite:
- `http://frontend:3000`
- `http://localhost:3000`

Si cambias el frontend, ajusta `DJANGO_CORS_ALLOWED_ORIGINS` y `DJANGO_CSRF_TRUSTED_ORIGINS`.

## Estructura inicial
- `core`: health-check y configuración base
- `library`: modelo `LibraryEntry`

> No hay endpoints API predefinidos (salvo `admin/` y `health/`).
