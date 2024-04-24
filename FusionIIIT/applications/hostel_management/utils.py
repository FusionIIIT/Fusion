from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.http import HttpResponse
from django.db import transaction
from datetime import datetime
from .models import *
import re
   
def get_caretaker_hall(hall_caretakers,user):
    """
    This function returns hall number corresponding to a caretaker.
    """
    for caretaker in hall_caretakers:
        if caretaker.staff.id.user==user:
            return caretaker.hall
            

def remove_from_room(student):
    """Removes the student from his current room"""
    if (student is None) or student.room_no is None:
        return
    room = re.findall('[0-9]+',str(student.room_no))
    room_num=str(room[0])
    block = str(student.room_no[0])
    hall=Hall.objects.get(hall_id="hall"+str(student.hall_no))
    Room=HallRoom.objects.get(hall=hall,block_no=block,room_no=room_num)
    Room.room_occupied=Room.room_occupied-1
    Room.save()
    student.room_no = None
    student.save()

def add_to_room(student, new_room, new_hall):
    """Adds the student to his new room"""
    if (student is None) or (new_room is None) or (new_hall is None):
        return
    block=str(new_room[0])
    room = re.findall('[0-9]+', new_room)
    student.room_no=str(block)+"-"+str(room[0])
    student.hall_no = int(new_hall[-1])
    student.save()
    hall=Hall.objects.get(hall_id="hall"+str(student.hall_no))
    Room=HallRoom.objects.get(hall=hall,block_no=block,room_no=str(room[0]))
    Room.room_occupied=Room.room_occupied+1
    Room.save()

def render_to_pdf(template_src, context_dict={}):
    """
    This fuction returns a converts a template into pdf and returns it.
    """
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None    

def save_worker_report_sheet(excel, sheet, user_id):
    """
    This function saves details of worker report sheet into the database.
    """
    try:
        # Iterate over each row in the sheet
        for row in range(0, sheet.nrows):
            worker_id = str(sheet.cell_value(row, 0))
            worker_name = str(sheet.cell_value(row, 1))
            # Initialize present days counter
            present = 0
            
            # Loop through columns starting from the third column (index 2)
            for col in range(2, sheet.ncols):
                # Check if the cell value is 1 (indicating the worker was present)
                if int(sheet.cell_value(row, col)) == 1:
                    present += 1
            
            # Calculate total working days
            working_days = sheet.ncols - 2
            
            # Calculate the number of days the worker was absent
            absent = working_days - present
            
            # Get today's date, month, and year
            today_date = datetime.today()
            month = today_date.month
            year = today_date.year

            # Get the hall associated with the current user
            hall_no = HallCaretaker.objects.get(staff__id=user_id).hall
            # print("hall no ~~~~ ",hall_no)
            # print("month ~~~~ ",month, year)
            # Save the data in a transaction
            with transaction.atomic():
                # Create and save a new WorkerReport instance
                new_report = WorkerReport.objects.create(worker_id=worker_id, hall=hall_no, worker_name=worker_name,
                                                          month=month, year=year, absent=absent, total_day=working_days, remark="none")
                new_report.save()
    except Exception as e:
        print("Error:", e)
        # Handle the error here, such as logging it or displaying a message to the user

# def save_worker_report_sheet(excel,sheet,user_id):
#     """
#     This function saves details of worker report sheet into the database.
#     """
#     month = excel.sheet_names()[0][:2]
#     year = excel.sheet_names()[0][3:]
#     for row in range(1, sheet.nrows):
#         worker_id = str(sheet.cell(row,0).value)
#         worker_name = str(sheet.cell(row,1).value)
#         present = 0
#         for col in range(2, sheet.ncols):
#             if int(sheet.cell(row,col).value) == 1:
#                 present += 1
#         working_days = sheet.ncols - 2
#         absent = working_days-present
#         hall_no = HallCaretaker.objects.get(staff__id=user_id).hall
#         print(month,year)
#         new_report = WorkerReport.objects.create(worker_id=worker_id, hall=hall_no, worker_name=worker_name, month=month, year=year, absent=absent, total_day=working_days, remark="none")
#         new_report.save()    