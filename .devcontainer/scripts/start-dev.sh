#!/usr/bin/env sh
set -eu

python .devcontainer/scripts/wait_for_tcp.py db 5432 60
python manage.py migrate --no-input
exec python manage.py runserver 0.0.0.0:8000
