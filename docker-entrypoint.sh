#!/bin/bash

# Apply database migrations
echo "Apply database migrations"
# python3 FusionIIIT/manage.py makemigrations
# python3 FusionIIIT/manage.py migrate

# Start server
echo "Starting server"
python FusionIIIT/manage.py runserver 0.0.0.0:8000