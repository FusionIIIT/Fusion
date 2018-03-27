import django
import xlrd
from applications.placement_cell.models import PlacementRecord


class Data:
    def __init__(self, excel_file, row):
        self.file = xlrd.open_workbook(excel_file)
        self.row = row
        self.sheet = self.getSheet()

    def getSheet(self):
        return self.file.sheet_by_index(0)


    def fillPlacementrecord(self):
        for i in range (1,self.row):
            ##self.sheet.cell(i,3).value.strip()
            try:
                PlacementRecord.objects.get(name=self.sheet.cell(i,4).value.strip())
                print('already exists')
            except:
                add=PlacementRecord()
                add.name = self.sheet.cell(i,4).value.strip()
                add.year = 2016
                add.placement_type = 'PLACEMENT'
                add.save()
                print('saved')

d = Data('dbinsertscripts/placement/B.Tech 2012.xlsx',132)
d.fillPlacementrecord()
# exec(open('dbinsertscripts/placement/placement_record_feed.py').read())
