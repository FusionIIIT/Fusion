from applications.academic_information.models import Curriculum, Curriculum_Instructor, Student, Course, Student_attendance
from applications.academic_procedures.models import Register, course_registration
from applications.programme_curriculum.models import CourseInstructor
from applications.globals.models import ExtraInfo
from .models import (Assignment, StudentAssignment, CourseDocuments,
                     Forum, ForumReply, Quiz, QuizQuestion, StudentAnswer,
                     QuizResult, GradingScheme, StudentEvaluation)
import datetime

def get_extra_info(user):
    return ExtraInfo.objects.filter(user=user).first()

def is_student(extra_info):
    return Student.objects.filter(id=extra_info).exists()

def get_courses_for_user(user):
    extra_info = get_extra_info(user)
    if not extra_info:
        return []
    student = Student.objects.filter(id=extra_info).first()
    seen = set()
    result = []
    if student:
        # Check both old and new enrollment systems
        # Old system: Register table
        registers = Register.objects.filter(student_id=student).select_related(
            'curr_id', 'curr_id__course_id').order_by('curr_id__course_code')
        curriculums = [r.curr_id for r in registers]

        # New system: course_registration table
        course_regs = course_registration.objects.filter(
            student_id=student
        ).select_related('course_id').order_by('course_id__code')

        for reg in course_regs:
            course_code = reg.course_id.code
            if course_code not in seen:
                seen.add(course_code)
                result.append({
                    'courseCode': course_code,
                    'courseName': reg.course_id.name,
                    'semester': reg.semester_id.semester_type if reg.semester_id else '1',
                    'credits': reg.course_id.credit,
                })
    else:
        # For instructors, check both old and new systems
        # Old system: Curriculum_Instructor table
        instructor_links = Curriculum_Instructor.objects.filter(
            instructor_id=extra_info).select_related(
            'curriculum_id', 'curriculum_id__course_id').order_by(
            'curriculum_id__course_code')
        curriculums = [link.curriculum_id for link in instructor_links]

        # New system: CourseInstructor table
        course_instructors = CourseInstructor.objects.filter(
            instructor_id=extra_info
        ).select_related('course_id').order_by('course_id__code')

        for ci in course_instructors:
            course_code = ci.course_id.code
            if course_code not in seen:
                seen.add(course_code)
                result.append({
                    'courseCode': course_code,
                    'courseName': ci.course_id.name,
                    'semester': ci.semester_id.semester_type if hasattr(ci, 'semester_id') and ci.semester_id else '1' '1',
                    'credits': ci.course_id.credit,
                })

    # Add courses from old curriculum system (avoiding duplicates)
    for curr in curriculums:
        if not curr or curr.course_code in seen:
            continue
        seen.add(curr.course_code)
        result.append({
            'courseCode': curr.course_code,
            'courseName': curr.course_id.course_name,
            'semester': curr.sem,
            'credits': curr.credits,
        })
    return result

def get_course_obj(course_code):
    # First try the old Curriculum system
    curr = Curriculum.objects.select_related('course_id').filter(
        course_code=course_code).first()
    if curr:
        return curr

    # If not found in Curriculum, try the new programme_curriculum Course system
    from applications.programme_curriculum.models import Course as ProgrammeCourse
    try:
        programme_course = ProgrammeCourse.objects.get(code=course_code)
        # Create a mock curriculum object for compatibility
        class MockCurriculum:
            def __init__(self, course):
                self.course_id = course
                self.course_code = course.code
                self.credits = course.credit
                self.sem = 1  # Default semester
        return MockCurriculum(programme_course)
    except ProgrammeCourse.DoesNotExist:
        return None

def is_enrolled(user, course_code):
    extra_info = get_extra_info(user)
    if not extra_info:
        return False
    student = Student.objects.filter(id=extra_info).first()
    if student:
        # Check both old and new enrollment systems
        # Old system: Register table
        if Register.objects.filter(
            student_id=student,
            curr_id__course_code=course_code).exists():
            return True

        # New system: course_registration table
        from applications.programme_curriculum.models import Course
        try:
            course = Course.objects.get(code=course_code)
            return course_registration.objects.filter(
                student_id=student,
                course_id=course).exists()
        except Course.DoesNotExist:
            pass

        return False

    # For instructors, check both systems
    # Old system: Curriculum_Instructor table
    if Curriculum_Instructor.objects.filter(
        instructor_id=extra_info,
        curriculum_id__course_code=course_code).exists():
        return True

    # New system: CourseInstructor table
    from applications.programme_curriculum.models import Course
    try:
        course = Course.objects.get(code=course_code)
        return CourseInstructor.objects.filter(
            instructor_id=extra_info,
            course_id=course).exists()
    except Course.DoesNotExist:
        pass

    return False


def get_course_roster(course_code):
    """Return enrolled students for a curriculum/course_code.

    Output items:
      { "student_id": "23BCS001", "name": "Full Name" }
    """
    res = []
    seen = set()
    
    # Check old enrollment system (Register table)
    regs = Register.objects.filter(curr_id__course_code=course_code).select_related(
        'student_id', 'student_id__id', 'student_id__id__user'
    )
    for r in regs:
        s = r.student_id
        if not s or not getattr(s, 'id', None) or not getattr(s.id, 'user', None):
            continue
        username = s.id.user.username
        if username not in seen:
            seen.add(username)
            res.append({
                'student_id': username,
                'name': s.id.user.get_full_name() or username,
            })
    
    # Check new enrollment system (course_registration table)
    from applications.programme_curriculum.models import Course
    try:
        course = Course.objects.get(code=course_code)
        course_regs = course_registration.objects.filter(
            course_id=course
        ).select_related('student_id', 'student_id__id', 'student_id__id__user')
        
        for cr in course_regs:
            s = cr.student_id
            if not s or not getattr(s, 'id', None) or not getattr(s.id, 'user', None):
                continue
            username = s.id.user.username
            if username not in seen:
                seen.add(username)
                res.append({
                    'student_id': username,
                    'name': s.id.user.get_full_name() or username,
                })
    except Course.DoesNotExist:
        pass
    
    return res


def get_instructor_link(extra_info, course_code):
    """Return instructor link for this faculty+course_code (or None).
    
    Checks both old Curriculum_Instructor table and new CourseInstructor table.
    """
    # Check old system first
    old_link = Curriculum_Instructor.objects.filter(
        instructor_id=extra_info,
        curriculum_id__course_code=course_code,
    ).select_related('curriculum_id').first()
    if old_link:
        return old_link
    
    # Check new system
    from applications.programme_curriculum.models import Course
    try:
        course = Course.objects.get(code=course_code)
        new_link = CourseInstructor.objects.filter(
            instructor_id=extra_info,
            course_id=course
        ).select_related('course_id').first()
        if new_link:
            # Create a mock object for compatibility with old system
            class MockInstructorLink:
                def __init__(self, course_instructor):
                    self.instructor_id = course_instructor.instructor_id
                    self.curriculum_id = MockCurriculum(course_instructor.course_id)
            
            class MockCurriculum:
                def __init__(self, course):
                    self.course_id = course
                    self.course_code = course.code
                    self.credits = course.credit
                    self.sem = 1  # Default semester
            
            return MockInstructorLink(new_link)
    except Course.DoesNotExist:
        pass
    
    return None
