# Nexus Play Frontend

Frontend profesional tipo Steam, construido con React + Vite y conectado al backend Django existente.

## Que usa

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/users/me/`
- `GET/POST /api/library/entries/`
- `GET/PATCH /api/library/entries/<id>/`

## Desarrollo local

```bash
cd frontend
npm install
npm run dev
```

Abrir: http://localhost:5173

Por defecto el frontend apunta a `http://localhost:8000`.

## Build produccion

```bash
cd frontend
npm run build
npm run preview
```

## Docker (solo frontend)

Desde la raiz del proyecto:

```bash
docker compose -f docker-compose.frontend.yml up --build
```

Abrir: http://localhost:3000

Este modo espera que el backend Django ya este disponible en `http://localhost:8000`.

## Docker (stack actual con backend + frontend)

```bash
docker compose up --build
```

Frontend: http://localhost:3000
Backend: http://localhost:8000
