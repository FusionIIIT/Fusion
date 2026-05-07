#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
until python -c "import psycopg2; conn = psycopg2.connect(host='$DB_HOST', user='$DB_USER', password='$DB_PASSWORD', dbname='$DB_NAME'); conn.close()" 2>/dev/null; do
  echo "Waiting for database connection..."
  sleep 2
done

# Apply database migrations
echo "Apply database migrations"
python FusionIIIT/manage.py makemigrations
python FusionIIIT/manage.py migrate

# Start server
echo "Starting server"
python FusionIIIT/manage.py runserver 0.0.0.0:8000
