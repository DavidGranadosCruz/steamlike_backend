# steamlike_backend

Proyecto con backend Django y frontend React conectado a autenticacion por sesion y biblioteca real.

## Arranque completo (backend + frontend)

```bash
docker compose up --build
```

Servicios:
- Frontend: http://localhost:3000
- Backend Django: http://localhost:8000
- Admin Django: http://localhost:8000/admin/
- Health-check: http://localhost:8000/api/health/

## Arranque solo frontend

```bash
docker compose -f docker-compose.frontend.yml up --build
```

Servicio:
- Frontend: http://localhost:3000

Nota:
- Este modo solo levanta el cliente. Para login, sesion y biblioteca, el backend debe estar disponible en `http://localhost:8000`.

## Migraciones backend

Crear migraciones:

```bash
docker compose exec web python manage.py makemigrations
```

Aplicar migraciones:

```bash
docker compose exec web python manage.py migrate
```

Crear superusuario:

```bash
docker compose exec web python manage.py createsuperuser
```

## Comandos utiles en el contenedor backend

Entrar en shell:

```bash
docker compose exec web bash
```

Crear una app Django (ejemplo `auth_api`):

```bash
docker compose exec web python manage.py startapp auth_api
```

## Variables de entorno

El proyecto usa `.env` a traves de `docker-compose.yml` para el backend.

Si el frontend consume backend en desarrollo, revisa:
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

Variables para envio de email con Maileroo:
- `MAILEROO_API_KEY`: Sending Key de Maileroo.
- `MAILEROO_FROM_ADDRESS`: remitente verificado en Maileroo.
- `MAILEROO_FROM_NAME`: nombre visible del remitente, por defecto `Nexus Play`.
- `MAILEROO_API_URL`: endpoint de envio, por defecto `https://smtp.maileroo.com/api/v2/emails`.
- `MAILEROO_TIMEOUT`: timeout en segundos, por defecto `5`.

## Estructura base backend

- `core`: health-check y configuracion base
- `library`: modelo `LibraryEntry`

## Frontend

Codigo frontend:
- `frontend/` (React + Vite + Docker multistage con Nginx)
- Usa `POST /api/auth/login/`, `GET /api/users/me/` y `GET/POST/PATCH /api/library/entries/`

Comandos locales frontend (sin Docker):

```bash
cd frontend
npm install
npm run dev
```
