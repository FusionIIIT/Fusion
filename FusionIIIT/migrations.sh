echo -----------------------------------------Making migrations--------------------------------------------------

python3 manage.py makemigrations globals
python3 manage.py makemigrations leave
python3 manage.py makemigrations eis
python3 manage.py makemigrations academic_information
python3 manage.py makemigrations academic_procedures
python3 manage.py makemigrations gymkhana
python3 manage.py makemigrations office_module
python3 manage.py makemigrations central_mess
python3 manage.py makemigrations complaint_system
python3 manage.py makemigrations filetracking
python3 manage.py makemigrations feeds
python3 manage.py makemigrations finance_accounts
python3 manage.py makemigrations health_center
python3 manage.py makemigrations notifications
python3 manage.py makemigrations online_cms
python3 manage.py makemigrations placement_cell
python3 manage.py makemigrations scholarships
python3 manage.py makemigrations visitor_hostel

echo -----------------------------------------Applying the changes-------------------------------------------------

python3 manage.py migrate

