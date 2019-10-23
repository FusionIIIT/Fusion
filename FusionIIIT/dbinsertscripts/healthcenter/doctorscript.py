import xlrd
import os
import django

sys.path.append(r'/mnt/g/Documents/django-projects/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()
from datetime import datetime
from applications.health_center.models import Doctor

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'Doctor-List.xlsx'))
z = excel.sheet_by_index(0)

for i in range(1, 5):
    try:
        name = str(z.cell(i,0).value)
        print(name)
        phone = str(int(z.cell(i,1).value))
        print(phone)
        spl = str(z.cell(i,2).value)
        u = Doctor.objects.create(
                    doctor_name = name,
                    doctor_phone = phone,
                    specialization=spl
        )
        print("Doctor done -> ")
    except Exception as e:
        print(e)
        print(i)

#exec(open("dbinsertscripts/healthcenter/doctorscript.py").read())
