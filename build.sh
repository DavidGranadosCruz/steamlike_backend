#!/usr/bin/env sh
# Render build script
set -e

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
