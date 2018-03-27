import django
import xlrd
from django.contrib.auth.models import User


class Data:
    def __init__(self, excel_file, row):
        self.file = xlrd.open_workbook(excel_file)
        self.row = row
        self.sheet = self.getSheet()

    def getSheet(self):
        return self.file.sheet_by_index(0)


    def fillUser(self):
        for i in range (1,self.row+1):
            ##self.sheet.cell(i,3).value.strip()
            try:
                username = str(int(self.sheet.cell(i,1).value))
                name = self.sheet.cell(i,2).value.strip()
                name = name.split()
                first_name = name[0]
                last_name = ' '.join(name[1:])
                email = 'demo@gmail.com'
                User.objects.create_user(
                    username = username,
                    password = 'hello123',
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
                )
                print('saved')
            except:
                print(username,'unsucessful')

d = Data('dbinsertscripts/placement/B.Tech 2012.xlsx',131)
d.fillUser()
# exec(open('dbinsertscripts/placement/user_feed.py').read())
