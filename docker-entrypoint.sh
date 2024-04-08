#!/bin/bash
# Apply database migrations
echo "Apply database migrations"
# python FusionIIIT/manage.py makemigrations
# python FusionIIIT/manage.py migrate
# Start server
# IP="0.0.0.0"
# PORT="8000"
echo "Starting server"
python FusionIIIT/manage.py runserver