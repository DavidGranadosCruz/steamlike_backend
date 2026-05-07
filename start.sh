#!/usr/bin/env sh
set -e

if [ ! -f frontend/dist/index.html ]; then
  echo "Frontend build missing; building Nexus frontend..."
  npm ci --prefix frontend
  npm run build --prefix frontend
  python manage.py collectstatic --no-input
fi

python manage.py migrate --no-input
exec gunicorn steamlike_backend.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
