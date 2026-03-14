#!/bin/sh
set -e
echo "⏳ Waiting for PostgreSQL at $DB_HOST:$DB_PORT ..."
MAX=30; C=0
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
  C=$((C+1)); [ $C -ge $MAX ] && echo "❌ DB timeout" && exit 1
  echo "  [$C/$MAX] retrying..."; sleep 2
done
echo "✅ DB ready — migrating..."
python manage.py migrate --noinput
echo "🚀 Starting on port 8003..."
exec gunicorn shop_service.wsgi:application --bind 0.0.0.0:8003 --workers 2 --timeout 120 --log-level info --access-logfile - --error-logfile -
