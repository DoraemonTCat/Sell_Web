#!/bin/sh
# ===========================================
# Backend Entrypoint Script
# 1. Wait for PostgreSQL
# 2. Create migration files (if needed)
# 3. Apply migrations
# 4. Start the server
# ===========================================

set -e

echo "Waiting for PostgreSQL..."
while ! python -c "import psycopg2; psycopg2.connect(
    dbname='${POSTGRES_DB}',
    user='${POSTGRES_USER}',
    password='${POSTGRES_PASSWORD}',
    host='${POSTGRES_HOST}',
    port='${POSTGRES_PORT}'
)" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready!"

echo "Creating migrations..."
python manage.py makemigrations --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
