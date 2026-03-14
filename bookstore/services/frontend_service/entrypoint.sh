#!/bin/sh
set -e

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "🚀 Starting gunicorn on port 8000..."
exec gunicorn frontend_service.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
