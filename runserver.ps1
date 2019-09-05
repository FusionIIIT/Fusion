Write-Host "Starting Server"

. ./env/scripts/activate
Set-Location .\FusionIIIT\
python manage.py runserver