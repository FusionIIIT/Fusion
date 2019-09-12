Write-Host "Making Migrations"

python manage.py makemigrations globals
python manage.py makemigrations leave
python manage.py makemigrations eis
python manage.py makemigrations academic_information
python manage.py makemigrations academic_procedures
python manage.py makemigrations gymkhana
python manage.py makemigrations office_module
python manage.py makemigrations central_mess
python manage.py makemigrations complaint_system
python manage.py makemigrations filetracking
python manage.py makemigrations feeds
python manage.py makemigrations finance_accounts
python manage.py makemigrations health_center
python manage.py makemigrations notifications
python manage.py makemigrations online_cms
python manage.py makemigrations placement_cell
python manage.py makemigrations scholarships
python manage.py makemigrations visitor_hostel