import xlrd
import os
from applications.visitor_hostel.models import RoomDetail
from django.contrib.auth.models import User
excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/vh/Room_information.xlsx'))
z = excel.sheet_by_index(0)


for i in range(1, 25):
    try:
        room_number= str(z.cell(i, 0).value)
        room_type = str(z.cell(i, 1).value)
        room_floor= str(z.cell(i, 2).value)
        room_status =str(z.cell(i, 3).value)
        print(room_number,room_type,room_floor,room_status)

        u = RoomDetail.objects.create(
            room_number=room_number,
            room_type=room_type,
               room_floor=   room_floor,
            room_status=room_status,
        )
        print('done')
        print(i)
    except Exception as e:
        print(e)
        print(i)

#exec(open('dbinsertscripts/vh/room_details.py').read())
