echo "Apply database migrations"
python FusionIIIT/manage.py makemigrations &&
python FusionIIIT/manage.py migrate &&
echo "Starting server"
python FusionIIIT/manage.py runserver 0.0.0.0:8000