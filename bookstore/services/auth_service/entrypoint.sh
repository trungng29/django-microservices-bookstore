#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL at $DB_HOST:$DB_PORT ..."

# Dùng nc (netcat) để check TCP port trước - đơn giản và chắc chắn hơn psycopg2
MAX_TRIES=30
COUNT=0
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_TRIES ]; then
        echo "❌ PostgreSQL not available after ${MAX_TRIES} tries. Exiting."
        exit 1
    fi
    echo "  Attempt $COUNT/$MAX_TRIES — waiting 2s..."
    sleep 2
done

echo "✅ TCP port open, waiting for PostgreSQL to accept connections..."
sleep 3

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "🚀 Starting Gunicorn on 0.0.0.0:8001 ..."
exec gunicorn auth_service.wsgi:application \
    --bind 0.0.0.0:8001 \
    --workers 2 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
