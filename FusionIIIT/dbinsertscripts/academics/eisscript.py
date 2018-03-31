import xlrd
import os
from applications.globals.models import ExtraInfo, Faculty, HoldsDesignation, Designation, DepartmentInfo
from applications.eis.models import faculty_about
from django.contrib.auth.models import User

k = ExtraInfo.objects.all()
for z in k:
    if(z.user_type==str('faculty')):
        try:
            k = faculty_about.objects.create(
                            user = z.user,
                            about = "Data Not Available!",
                            doj = "2012-02-23",
                            education = "Data Not Available!",
                            interest = "Data Not Available!",
                            contact = 9999999999)
            print('hogaya')
        except:
            print('nahihua')
#exec(open("dbinsertscripts/academics/facultyscript.py").read())
