"""The student's course registration receipt (courses, credits and previous CPI) for the React app.

Moved unchanged from academic_procedures/views.py (the old server-rendered pages).
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from applications.programme_curriculum.models import Semester

from ..models import course_registration


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_course_registration_receipt(request):
    try:
        current_user = request.user
        current_user = ExtraInfo.objects.all().filter(user=current_user).first()
        current_user = Student.objects.all().filter(id = current_user.id).first()

        batch = current_user.batch_id
        curr_id = batch.curriculum
        curr_sem_id = Semester.objects.get(curriculum = curr_id, semester_no = current_user.curr_semester_no)
        courses = course_registration.objects.filter(student_id = current_user, semester_id = curr_sem_id)

        course_list = []
        for course in courses:
            course_list.append({
                'course_code': course.course_id.code,
                'course_name': course.course_id.name,
                'credits': course.course_id.credit
            })
        
        # CPI as of the last completed term, summer terms included.
        from applications.examination.api.views import previous_term_cpi
        prev_sem = (current_user.curr_semester_no or 0) - 1
        prev_sem_cpi = previous_term_cpi(current_user, current_user.curr_semester_no)

        context = {
            'current_courseregistrations': course_list,
            'semester_no': current_user.curr_semester_no,
            'name': request.user.first_name + request.user.last_name,
            'roll_no' : current_user.id_id,
            'batch': batch.name+' '+str(batch.year),
            'branch': curr_id.name.split(' ')[0],
            'prev_semester_no': prev_sem if prev_sem >= 1 else None,
            'prev_sem_cpi': prev_sem_cpi,
        }
        return JsonResponse(context)
    
    except Exception as e:
        return JsonResponse({'error': 'Unable to retrieve data', 'details': str(e)})
