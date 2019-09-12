Write-Host "Starting Server"

. ./env/scripts/activate
Set-Location .\FusionIIIT\
python manage.py makemigrations globals
python manage.py migrate globals
#python manage.py makemigrations leave
python manage.py makemigrations eis
python manage.py migrate eis
python manage.py makemigrations academic_information
python manage.py migrate academic_information
python manage.py makemigrations academic_procedures
python manage.py migrate academic_procedures
python manage.py makemigrations library
python manage.py migrate library
python manage.py makemigrations gymkhana
python manage.py migrate gymkhana
#python manage.py makemigrations office_module
python manage.py makemigrations central_mess
python manage.py migrate central_mess
python manage.py makemigrations complaint_system
python manage.py migrate complaint_system
python manage.py makemigrations filetracking
python manage.py migrate filetracking
python manage.py makemigrations finance_accounts
python manage.py migrate finance_accounts
python manage.py makemigrations health_center
python manage.py migrate health_center
python manage.py makemigrations notifications
python manage.py migrate notifications
python manage.py makemigrations online_cms
python manage.py migrate online_cms
python manage.py makemigrations placement_cell
python manage.py migrate placement_cell
python manage.py makemigrations scholarships
python manage.py migrate scholarships
python manage.py makemigrations visitor_hostel
python manage.py migrate visitor_hostel
python manage.py makemigrations allauth
python manage.py migrate allauth
python manage.py makemigrations pagedown
python manage.py migrate pagedown
python manage.py makemigrations markdown_deux
python manage.py migrate markdown_deux