#!/usr/bin/env sh
# Render build script
set -e

pip install --upgrade pip
pip install -r requirements.txt

npm ci --prefix frontend
npm run build --prefix frontend

# Clean up old conflicting migration record if it exists
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'steamlike_backend.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"DELETE FROM django_migrations WHERE app='library' AND name='0002_libraryentry_user'\")
    print(f'Cleaned {cursor.rowcount} old migration record(s)')
" 2>/dev/null || echo "No old migration records to clean"

python manage.py migrate --no-input
python manage.py collectstatic --no-input
