import xlrd

from datetime import datetime
import os
from applications.health_center.models import Stock,Stockinventory

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/healthcenter/Medicine-Stock.xlsx'))
z = excel.sheet_by_index(0)

for i in range(0, 86):
    try:
        med_name = str(z.cell(i, 0).value)
        print(med_name)
        qty = int(z.cell(i,1).value)
        threshold = int(z.cell(i,2).value)
        u = Stock.objects.create(
                    medicine_name = med_name,
                    quantity = qty,
                    threshold = threshold
        )
        print("Stock done -> ")
        q = Stockinventory.objects.create(
            medicine_id = u,
            quantity=qty,
            date=datetime.now()
        )
        print("StockInventory Done")
    except Exception as e:
        print(e)
        print(i)

#exec(open("dbinsertscripts/healthcenter/medicinescript.py").read())
