from django.db.models import Count, Q, F, Max
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from applications.academic_procedures.models import course_registration, SemesterMarks
from applications.academic_information.models import Student
from applications.programme_curriculum.models import Course, Semester, Batch, Programme
from applications.online_cms.models import Student_grades
from .serializers import CourseStudentCountSerializer, StudentCourseDetailSerializer
import logging
from datetime import datetime

logger = logging.getLogger(__name__)



VALID_PROGRAMME_TYPES = ['UG', 'PG', 'PHD']


class BatchListView(APIView):
    """
    GET: Retrieve all available batches.
    Returns: List of batch IDs and batch years
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            batches = Student.objects.values('batch').distinct().order_by('-batch')
            batch_list = [{'id': batch['batch'], 'batch_year': batch['batch']} for batch in batches]
            
            return Response({
                'success': True,
                'data': batch_list,
                'count': len(batch_list)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching batches: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Failed to fetch batches'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SemesterFilterView(APIView):
    """
    GET: Retrieve semesters for a specific batch.
    Query params:
        - batch_id (required): Batch year, e.g., '2021'
    Returns: List of semester numbers available for the batch
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        batch_id = request.query_params.get('batch_id')
        
        if not batch_id:
            return Response({
                'success': False,
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Validate batch exists
            batch_exists = Student.objects.filter(batch=batch_id).exists()
            if not batch_exists:
                return Response({
                    'success': False,
                    'error': 'Invalid batch year'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get semesters for the batch
            semesters = course_registration.objects.filter(
                student_id__batch=batch_id
            ).values('semester_id__semester_no', 'semester_id__id').distinct().order_by('semester_id__semester_no')
            
            semester_list = [
                {'id': sem['semester_id__id'], 'semester_no': sem['semester_id__semester_no']}
                for sem in semesters
            ]
            
            return Response({
                'success': True,
                'data': semester_list,
                'count': len(semester_list)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching semesters: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Failed to fetch semesters'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CourseStudentCountView(APIView):
    """
    GET: Return course-wise student counts for a given session, semester, and programme type.
    Query params: 
        - session (required): e.g., '2025-26'
        - semester_type (required): e.g., 'Odd Semester', 'Even Semester'
        - programme_type (optional): 'UG' or 'PG', defaults to 'UG'
        - course_code (optional): to filter by specific course
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get and validate query parameters
        session = request.GET.get('session')
        semester_type = request.GET.get('semester_type')
        programme_type = request.GET.get('programme_type', 'UG').upper()
        course_code = request.GET.get('course_code')

        # Validate required parameters
        if not session:
            return Response({'error': 'session parameter is required'}, status=400)
        
        if not semester_type:
            return Response({'error': 'semester_type parameter is required'}, status=400)

        # Validate semester_type
        valid_semester_types = ['Odd Semester', 'Even Semester', 'Summer Semester']
        if semester_type not in valid_semester_types:
            return Response({
                'error': f'Invalid semester_type. Must be one of: {", ".join(valid_semester_types)}'
            }, status=400)

        # Validate programme_type
        if programme_type not in VALID_PROGRAMME_TYPES:
            return Response({
                'error': f'Invalid programme_type. Must be one of: {", ".join(VALID_PROGRAMME_TYPES)}'
            }, status=400)

        try:
            # Build category filter dynamically using programme category from database
            category_filter = Q(student_id__batch_id__curriculum__programme__category=programme_type)

           
            queryset = course_registration.objects.filter(
                category_filter,
                session=session,
                semester_type=semester_type,
            ).select_related('course_id', 'student_id')

            # Filter by course code if provided
            if course_code:
                queryset = queryset.filter(course_id__code=course_code)

        
            course_counts = queryset.values(
                'session',
                'semester_type',
                'course_id__code',
                'course_id__name',
                'course_id__credit'
            ).annotate(
                student_count=Count('student_id', distinct=True)
            ).order_by('course_id__code')

          
            data = [
                {
                    'academic_year': item['session'],
                    'semester_type': item['semester_type'],
                    'code': item['course_id__code'],
                    'name': item['course_id__name'],
                    'credit': item['course_id__credit'],
                    'student_count': item['student_count']
                }
                for item in course_counts
            ]

       
            serializer = CourseStudentCountSerializer(data=data, many=True)
            if serializer.is_valid():
                return Response({
                    'courses': serializer.data,
                    'count': len(serializer.data),
                    'programme_type': programme_type,
                }, status=200)
            else:
                logger.error(f"Serialization error: {serializer.errors}")
                return Response({'error': 'Data serialization failed'}, status=500)

        except Exception as e:
            logger.error(f"Error in CourseStudentCountView: {str(e)}", exc_info=True)
            return Response({'error': f'An error occurred while fetching data: {str(e)}'}, status=500)


class CourseStudentsListView(APIView):
    """
    GET: Return student list for a specific course in a given session.
    Query params:
        - session (required): e.g., '2025-26'
        - semester_type (required): e.g., 'Odd Semester'
        - course_code (required): specific course code
        - programme_type (optional): 'UG' or 'PG', defaults to 'UG'
    Returns: list of students with roll_no, discipline, course_code, course_name, credit
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = request.GET.get('session')
        semester_type = request.GET.get('semester_type')
        course_code = request.GET.get('course_code')
        programme_type = request.GET.get('programme_type', 'UG').upper()

        if not session:
            return Response({'error': 'session parameter is required'}, status=400)
        if not semester_type:
            return Response({'error': 'semester_type parameter is required'}, status=400)
        if not course_code:
            return Response({'error': 'course_code parameter is required'}, status=400)

        valid_semester_types = ['Odd Semester', 'Even Semester', 'Summer Semester']
        if semester_type not in valid_semester_types:
            return Response({'error': f'Invalid semester_type. Must be one of: {", ".join(valid_semester_types)}'}, status=400)

        if programme_type not in VALID_PROGRAMME_TYPES:
            return Response({'error': f'Invalid programme_type. Must be one of: {", ".join(VALID_PROGRAMME_TYPES)}'}, status=400)

        try:
            # Build category filter dynamically using programme category from database
            category_filter = Q(student_id__batch_id__curriculum__programme__category=programme_type)

            queryset = course_registration.objects.filter(
                category_filter,
                session=session,
                semester_type=semester_type,
                course_id__code=course_code,
            ).values(
                'student_id__id__user__username',
                'student_id__batch_id__discipline__acronym',
                'course_id__code',
                'course_id__name',
                'course_id__credit',
            ).distinct().order_by('student_id__id__user__username')

            data = [
                {
                    'roll_no': item['student_id__id__user__username'],
                    'discipline': item['student_id__batch_id__discipline__acronym'] or 'N/A',
                    'course_code': item['course_id__code'],
                    'course_name': item['course_id__name'],
                    'credit': item['course_id__credit'],
                }
                for item in queryset
            ]

            return Response({'students': data, 'count': len(data)}, status=200)

        except Exception as e:
            logger.error(f"Error in CourseStudentsListView: {str(e)}", exc_info=True)
            return Response({'error': f'An error occurred: {str(e)}'}, status=500)


class StudentCoursesDetail(APIView):
    """
    GET: Return all student courses for a given batch in flat format (one row per student-course).
    Retrieves all course registrations for the batch across all semesters dynamically.
    Query params:
        - batch_id (required): Batch year, e.g., '2021'
    Returns: 
        Flat list of student-course records sorted by roll number, semester number, then course code.
        Each record contains: roll_no, semester, semester_no, course_code, course_name,
        credit, registration_type, semester_type (Odd Semester, Even Semester, Summer Semester)
    Frontend creates unique keys from: semester_no + semester_type (e.g., "2_Summer Semester")
    Frontend applies filters: By semester, By course, By roll number
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get and validate query parameters
        batch_id = request.query_params.get('batch_id')

        # Validate required parameters
        if not batch_id:
            return Response({
                'success': False, 
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate batch_id is a valid year
        try:
            batch_year = int(batch_id)
            if batch_year < 2000 or batch_year > 2100:
                return Response({
                    'success': False, 
                    'error': 'Invalid batch year'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({
                'success': False, 
                'error': 'batch_id must be a valid year'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:

            current_year = datetime.now().year
            years_since_batch = current_year - batch_year
            # Calculate maximum expected semester (2 semesters per year + 1 for buffer)
            max_expected_semester = (years_since_batch * 2) + 1
            
       
            queryset = course_registration.objects.filter(
                student_id__batch=batch_year
            ).select_related(
                'student_id',
                'student_id__id',
                'student_id__id__user',
                'course_id',
                'semester_id'
            ).values(
                'student_id__id__user__username',
                'student_id__batch_id__discipline__acronym',
                'course_id__code',
                'course_id__name',
                'course_id__credit',
                'registration_type',
                'semester_id__semester_no',
                'semester_type'
            ).order_by(
                'student_id__id__user__username',
                'semester_id__semester_no',
                'course_id__code'
            )
            
            if not queryset.exists():
                return Response({
                    'success': True,
                    'data': [],
                    'count': 0,
                    'batch_id': batch_id,
                    'available_courses': [],
                    'message': 'No course registrations found for this batch'
                }, status=status.HTTP_200_OK)
            
           
            all_data = []
            available_courses = set()
            
            for item in queryset:
                available_courses.add(item['course_id__code'])
                all_data.append({
                    'roll_no': item['student_id__id__user__username'],
                    'discipline': item['student_id__batch_id__discipline__acronym'] or 'N/A',
                    'semester': item['semester_id__semester_no'],
                    'course_code': item['course_id__code'],
                    'course_name': item['course_id__name'],
                    'credit': item['course_id__credit'],
                    'registration_type': item['registration_type'],
                    'semester_no': item['semester_id__semester_no'],
                    'semester_type': item['semester_type']
                })
            
            
            sorted_data = sorted(all_data, key=lambda x: (x['roll_no'], x['semester_no'], x['course_code']))

            return Response({
                'success': True,
                'data': sorted_data,
                'count': len(sorted_data),
                'batch_id': batch_id,
                'available_courses': sorted(list(available_courses))
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in StudentCoursesDetail: {str(e)}", exc_info=True)
            return Response({
                'success': False, 
                'error': f'An error occurred while fetching data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentsGradeInfo(APIView):
    """
    GET: Return all student courses with grades for a given batch in flat format (one row per student-course).
    Similar to StudentCoursesDetail but includes grade information from Student_grades (online_cms).
    
    PERFORMANCE OPTIMIZATIONS:
    - Uses select_related() to reduce database queries for foreign keys
    - Fetches all grades in a single query (instead of N+1 queries)
    - Uses dictionary lookup for O(1) grade retrieval
    - Server-side filtering for efficient search across entire dataset
    - Returns statistics calculated from filtered dataset
    
    RECOMMENDED DATABASE INDEXES:
    - CREATE INDEX idx_course_reg_batch ON course_registration(student_id_id);
    - CREATE INDEX idx_student_batch ON academic_information_student(batch);
    - CREATE INDEX idx_student_grades_batch ON online_cms_student_grades(batch, roll_no, course_id_id);
    
    Query params:
        - batch_id (required): Batch year, e.g., '2021'
        - limit (optional): Limit number of records returned (for preview), default: 10000
        - export (optional): If 'true', returns all records (ignores limit)
        - filter_roll_no (optional): Filter by roll number (case-insensitive substring match)
    Returns: 
        Flat list of student-course records sorted by roll number, semester number, then course code.
        Each record contains: roll_no, semester_no, course_code, course_name, credit, grade, 
        registration_type
        Statistics reflect the FILTERED dataset: total_students, total_courses, total_credits
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
      
        batch_id = request.query_params.get('batch_id')
        limit = request.query_params.get('limit', '10000')
        is_export = request.query_params.get('export', 'false').lower() == 'true'
        filter_roll_no = request.query_params.get('filter_roll_no', '').strip()

  
        if not batch_id:
            return Response({
                'success': False, 
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)


        try:
            batch_year = int(batch_id)
            if batch_year < 2000 or batch_year > 2100:
                return Response({
                    'success': False, 
                    'error': 'Invalid batch year'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({
                'success': False, 
                'error': 'batch_id must be a valid year'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
        
            queryset = course_registration.objects.filter(
                student_id__batch=batch_year
            ).select_related(
                'student_id',
                'student_id__id',
                'student_id__id__user',
                'student_id__batch_id',
                'student_id__batch_id__discipline',
                'course_id',
                'semester_id'
            )

            if not queryset.exists():
                return Response({
                    'success': True,
                    'data': [],
                    'count': 0,
                    'batch_id': batch_id,
                    'available_courses': [],
                    'message': 'No course registrations found for this batch'
                }, status=status.HTTP_200_OK)
            
            total_count = queryset.count()
            
            # OPTIMIZATION: Fetch all grades for this batch in one query
            # LEFT JOIN logic: match on (roll_no, course_id_id, semester_no)
            # Build a dictionary for O(1) lookup: {(roll_no, course_id_id, semester_no): grade}
            grades_dict = {}
            try:
                
                all_grades = Student_grades.objects.filter(
                    batch=batch_year
                ).values('roll_no', 'course_id_id', 'semester', 'grade')
                
                for grade_record in all_grades:
                 
                    key = (grade_record['roll_no'], grade_record['course_id_id'], grade_record['semester'])
                
                    grades_dict[key] = grade_record['grade']
            except Exception as grades_error:
                logger.warning(f"Could not fetch grades in bulk: {str(grades_error)}")
            
        
            all_data = []
            available_courses = set()
            
            for registration in queryset:
                available_courses.add(registration.course_id.code)
                
               
                roll_no = registration.student_id.id.user.username
                semester_no = registration.semester_id.semester_no
                

                key = (roll_no, registration.course_id_id, semester_no)
                grade_value = grades_dict.get(key) 

                if grade_value is None or str(grade_value).strip() == '':
                    grade = 'Not Submitted'
                else:
                    grade = str(grade_value).strip()
                
                all_data.append({
                    'roll_no': roll_no,
                    'discipline': registration.student_id.batch_id.discipline.acronym if (
                        registration.student_id.batch_id and
                        registration.student_id.batch_id.discipline
                    ) else 'N/A',
                    'semester_no': semester_no,
                    'course_code': registration.course_id.code,
                    'course_name': registration.course_id.name,
                    'credit': registration.course_id.credit,
                    'grade': grade,
                    'registration_type': registration.registration_type
                })
            

            sorted_data = sorted(all_data, key=lambda x: (x['roll_no'], x['semester_no'], x['course_code']))
            
           
            if filter_roll_no:
                sorted_data = [item for item in sorted_data if filter_roll_no.lower() in item['roll_no'].lower()]
            

            unique_students = set()
            unique_courses = set()
            total_credits = 0
            backlog_improvement_count = 0
            registration_type_counts = {
                'regular': 0,
                'backlog': 0,
                'improvement': 0
            }
            
            for item in sorted_data:
                unique_students.add(item['roll_no'])
                unique_courses.add(item['course_code'])
                # Only sum credits for courses with valid (submitted) grades
                # Exclude "Not Submitted" and "CD" (no credit or incomplete)
                if item['credit'] and item['grade'] not in ['Not Submitted', 'CD']:
                    total_credits += item['credit']
            
                if item['registration_type'] in ['Backlog', 'Improvement']:
                    backlog_improvement_count += 1
        
                reg_type = item['registration_type'].lower()
                if reg_type == 'backlog':
                    registration_type_counts['backlog'] += 1
                elif reg_type == 'improvement':
                    registration_type_counts['improvement'] += 1
                else:
                    registration_type_counts['regular'] += 1
            
            total_students = len(unique_students)
            total_courses = len(unique_courses)
            
          
            filtered_count = len(sorted_data)
            
          
            if not is_export:
                try:
                    limit_value = int(limit)
                    if limit_value > 0:
                        sorted_data = sorted_data[:limit_value]
                except ValueError:
                    pass 

            return Response({
                'success': True,
                'data': sorted_data,
                'count': len(sorted_data),
                'total_count': total_count,
                'filtered_count': filtered_count,
                'is_limited': not is_export and len(sorted_data) < filtered_count,
                'batch_id': batch_id,
                'available_courses': sorted(list(available_courses)),
                'statistics': {
                    'total_students': total_students,
                    'total_courses': total_courses,
                    'total_credits': total_credits,
                    'backlog_improvement_count': backlog_improvement_count,
                    'registration_type_counts': registration_type_counts
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in StudentsGradeInfo: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'An error occurred while fetching data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnregisteredStudentsByBatchView(APIView):
    """
    GET: Retrieve students who haven't registered for any course in semesters
    1 to their current semester, grouped by semester.

    Query params:
        - batch_id (required): Batch year, e.g., '2022'

    Response format:
        {
            'success': True,
            'data': [
                {'roll_no': '201234001', 'student_name': 'John Doe', 'semester_no': 7,
                 'batch': '2022', 'current_semester': 8},
                ...
            ],
            'count': 45,
            'batch_id': '2022',
            'semester_range': [1, 2, 3, 4, 5, 6, 7, 8]
        }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        batch_id = request.query_params.get('batch_id')

        
        if not batch_id:
            return Response({
                'success': False,
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

   
        if not self._is_valid_batch_year(batch_id):
            return Response({
                'success': False,
                'error': 'Invalid batch_id. Must be a year between 2000 and 2100'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            batch_exists = Student.objects.filter(batch=batch_id).exists()
            if not batch_exists:
                return Response({
                    'success': False,
                    'error': f'No students found for batch {batch_id}'
                }, status=status.HTTP_400_BAD_REQUEST)

           
            students = Student.objects.filter(batch=batch_id).select_related(
                'id', 'id__user'
            ).values(
                'id_id', 'curr_semester_no', 'id__user__first_name', 'id__user__last_name'
            )

            # Find max semester in batch to determine range
            max_semester_result = students.aggregate(Max('curr_semester_no'))
            max_semester = max_semester_result.get('curr_semester_no__max') or 1
            semesters = list(range(1, max_semester + 1))

            
            result = []

            
            for semester in semesters:
                # Get set of students registered in this semester
                registered_students = set(
                    course_registration.objects.filter(
                        student_id__batch=batch_id,
                        semester_id__semester_no=semester
                    ).values_list('student_id_id', flat=True)
                )

                # Add unregistered students for this semester
                for student in students:
                    student_roll_no = student['id_id']

                    # Only add if student hasn't registered for this semester
                    if student_roll_no not in registered_students:
                        result.append({
                            'roll_no': student_roll_no,
                            'student_name': f"{student['id__user__first_name']} {student['id__user__last_name']}",
                            'semester_no': semester,
                            'batch': batch_id,
                            'current_semester': student['curr_semester_no']
                        })

           
            result.sort(key=lambda x: (x['semester_no'], x['roll_no']))

            return Response({
                'success': True,
                'data': result,
                'count': len(result),
                'batch_id': batch_id,
                'semester_range': semesters
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in UnregisteredStudentsByBatch: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'An error occurred while fetching unregistered students: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _is_valid_batch_year(self, batch_id):
        """Validate that batch_id is a valid year"""
        try:
            year = int(batch_id)
            return 2000 <= year <= 2100
        except (ValueError, TypeError):
            return False


