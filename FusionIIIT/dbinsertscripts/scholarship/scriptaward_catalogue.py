import xlrd
import os
from applications.scholarships.models import Award_and_scholarship

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/scholarship/Award Catalogue.xlsx'))
z = excel.sheet_by_index(0)
#print(z.cell(5,0))
#print(z.cell(12,2).value)
#file = xlrd.open_workbook(excel,'r')
for i in range(1, 9):
    try:
        award_name = str(z.cell(i,1).value)
        catalog = str(z.cell(i,50).value)

        print(award_name, catalog)

        u = Award_and_scholarship.objects.create(
            award_name = award_name,
            catalog = catalog,
        )
        print('done')
        print(i)
    except Exception as e:
        print(e)
        print(i)

#exec(open("dbinsertscripts/academics/scholarship/scriptaward_catalogue.py").read())
