#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL at $DB_HOST:$DB_PORT ..."
MAX=30; C=0
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
  C=$((C+1)); [ $C -ge $MAX ] && echo "❌ DB timeout" && exit 1
  echo "  [$C/$MAX] retrying..."; sleep 2
done

echo "✅ DB ready"
echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "🌱 Seeding roles & permissions..."
python manage.py seed_permissions

echo "🚀 Starting Gunicorn on 0.0.0.0:8001 ..."
exec gunicorn auth_service.wsgi:application \
    --bind 0.0.0.0:8001 \
    --workers 2 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
