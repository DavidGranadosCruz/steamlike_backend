#!/usr/bin/env sh
set -e

python manage.py migrate --no-input
exec gunicorn steamlike_backend.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
