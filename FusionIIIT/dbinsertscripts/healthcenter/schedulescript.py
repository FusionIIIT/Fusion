import xlrd

from datetime import datetime,time
import os
from applications.health_center.models import Schedule,Doctor,Constants

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/healthcenter/Doctor-Schedule.xlsx'))
z = excel.sheet_by_index(0)

for i in range(1, 19):
    try:
        doc_name = str(z.cell(i,0).value)
        print(doc_name)
        do=Doctor.objects.filter(doctor_name=doc_name)
        doc_id = do[0]
        print(doc_id)
        day = str(z.cell(i,1).value)
        days = Constants.DAYS_OF_WEEK
        for p,d in days:
            if d==day:
                da=p
        print(da)
        x=z.cell(i,2).value
        x=int(x*24*3600)
        from_time=time(x//3600,(x%3600)//60,x%60)
        print(from_time)
        print(from_time)
        y=z.cell(i,3).value
        y=int(y*24*3600)
        to_time=time(y//3600,(y%3600)//60,y%60)
        print(to_time)
        room=int(z.cell(i,4).value)
        u = Schedule.objects.create(
                    doctor_id = doc_id,
                    day = da,
                    from_time=from_time,
                    to_time=to_time,
                    room=room,
                    date=datetime.now()
        )
        print("Schedule done -> ")
    except Exception as e:
        print(e)
        print(i)

#exec(open("dbinsertscripts/healthcenter/schedulescript.py").read())
