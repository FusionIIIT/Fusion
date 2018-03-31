import xlrd
import os
from applications.central_mess.models import Menu

menuexcel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/mess/menu.xlsx'))
z = menuexcel.sheet_by_index(0)

for i in range(5, 19):
	try:
		
		day = z.cell(i, 1).value
		
		
		for j in range(1, 4):
			#print(day)
			time = z.cell(4, j+1).value
			#print(time)
			
			if day == 'Thursday' or day == 'Sunday' :
				#print(day.upper())
				meal_time = day.upper()[0:2]+time[0]
			
			else :
				meal_time = day[0]+time[0]
				
			#print(meal_time)
			#print(z.cell(i, j+1).value)
			#print(z.cell(i,5).value)
				
			menu = Menu.objects.create(
				mess_option = z.cell(i,5).value,
				meal_time = meal_time,
				dish = z.cell(i, j+1).value,
			
			)
				
		print (str(i) + "done")
	
	except Exception as e:
		print(e)
		print(i)
## exec(open('dbinsertscripts/mess/menu_Script.py').read())
