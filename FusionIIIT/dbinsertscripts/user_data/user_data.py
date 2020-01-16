import sys
import os
import django   
import xlsxwriter
import string
from random import *

sys.path.append(r'/home/fusion/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()

from django.contrib.auth.models import User

workbook = xlsxwriter.Workbook('UserData.xlsx') 
worksheet = workbook.add_worksheet() 
user_list = list(User.objects.all())
row = 0
print("Length for User passsword")
length = int(input())


for user in user_list:
    characters = string.ascii_letters + string.punctuation  + string.digits
    password =  "".join(choice(characters) for x in range(length))
    user.set_password(password)
    user.save()
    worksheet.write(row, 0, user.username)
    worksheet.write(row, 1, password) 
    print(user.username)
    print(password)
    row+=1

workbook.close() 



