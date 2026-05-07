from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.db import IntegrityError
from datetime import timedelta
import logging
from .. import services, models
from applications.academic_information.models import Student, Student_attendance

# Set up logging
logger = logging.getLogger(__name__)

class BaseCourseView(APIView):
    permission_classes = [IsAuthenticated]
    def get_course_or_error(self, request, course_code):
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        return curr

    
    def check_enrollment(self, request, course_code):
        return services.is_enrolled(request.user, course_code)
    
    def get_role_info(self, request):
        extra_info = services.get_extra_info(request.user)
        return extra_info, services.is_student(extra_info)

class ApiCourseList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        courses = services.get_courses_for_user(request.user)
        return Response(courses)

class ApiCourseDashboard(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        assignments_count = models.Assignment.objects.filter(course_id=course_obj).count()
        documents_count = models.CourseDocuments.objects.filter(course_id=course_obj).count()
        
        # Get course name from either old or new system
        course_name = getattr(course_obj, 'course_name', None) or getattr(course_obj, 'name', 'Unknown')
        course_details = getattr(course_obj, 'course_details', getattr(course_obj, 'syllabus', ''))
        
        return Response({
            "courseCode": course_code,
            "courseName": course_name,
            "courseDetails": course_details,
            "credits": curr.credits if hasattr(curr, 'credits') else course_obj.credit,
            "semester": curr.sem if hasattr(curr, 'sem') else 1,
            "programme": "",
            "branch": "",
            "batch": "",
            "counts": {
                "assignments": assignments_count,
                "documents": documents_count
            }
        })

class ApiAssignments(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        assignments = models.Assignment.objects.filter(course_id=course_obj).order_by('-upload_time')

        extra_info, is_student_user = self.get_role_info(request)
        student_obj = None
        if is_student_user:
            student_obj = Student.objects.filter(id=extra_info).first()

        res = []
        for a in assignments:
            item = {
                'id': a.pk,
                'title': a.assignment_name,
                'deadline': a.submit_date.isoformat() if a.submit_date else None,
                'createdAt': a.upload_time.isoformat() if hasattr(a, 'upload_time') else None,
                'submissions': [],
            }

            if is_student_user:
                subs = models.StudentAssignment.objects.filter(assignment_id=a, student_id=student_obj).order_by('-upload_time')
            else:
                subs = models.StudentAssignment.objects.filter(assignment_id=a).select_related(
                    'student_id', 'student_id__id', 'student_id__id__user'
                ).order_by('-upload_time')

            for s in subs:
                username = None
                full_name = 'Unknown'
                if s.student_id and getattr(s.student_id, 'id', None) and getattr(s.student_id.id, 'user', None):
                    username = s.student_id.id.user.username
                    full_name = s.student_id.id.user.get_full_name() or username

                item['submissions'].append({
                    'id': s.pk,
                    'assignmentId': a.pk,
                    'studentId': username,
                    'studentName': full_name,
                    'submissionLink': s.upload_url,
                    'submittedAt': s.upload_time.isoformat() if hasattr(s, 'upload_time') else None,
                    'score': s.score,
                    'feedback': s.feedback,
                })

            res.append(item)

        return Response(res)

class ApiAddAssignment(BaseCourseView):
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)
            
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        data = request.data

        deadline = data.get('deadline')
        deadline_dt = parse_datetime(deadline) if isinstance(deadline, str) else None
        if deadline_dt is None and isinstance(deadline, str):
            d = parse_date(deadline)
            if d is not None:
                deadline_dt = timezone.make_aware(timezone.datetime(d.year, d.month, d.day, 23, 59, 0))

        if not data.get('title'):
            return Response({'detail': 'title is required'}, status=400)
        if deadline_dt is None:
            return Response({'detail': 'deadline is required (ISO datetime or YYYY-MM-DD)'}, status=400)
        a = models.Assignment.objects.create(
            course_id=course_obj,
            assignment_name=data.get('title'),
            submit_date=deadline_dt,
        )
        return Response({'id': a.pk})

class ApiUploadAssignment(BaseCourseView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)

        extra_info, is_student_user = self.get_role_info(request)
        if not is_student_user:
            return Response({'detail': 'Student only'}, status=403)

        assignment_id = request.data.get('assignment_id')
        submission_link = request.data.get('submission_link') or request.data.get('upload_url') or request.data.get('link')

        if not submission_link:
            return Response({'detail': 'submission_link is required'}, status=400)

        a = models.Assignment.objects.get(pk=assignment_id)

        if timezone.now() > a.submit_date:
            return Response({'detail': 'Submission deadline has passed'}, status=400)

        student = Student.objects.get(id=extra_info)

        # 🔥 KEY CHANGE: update or create
        sub, created = models.StudentAssignment.objects.update_or_create(
            student_id=student,
            assignment_id=a,
            defaults={
                'upload_url': submission_link,
                'assign_name': a.assignment_name,
                'upload_time': timezone.now(),  # ensures updated timestamp
            }
        )

        return Response({
            'id': sub.pk,
            'submittedAt': sub.upload_time.isoformat(),
            'message': 'Created' if created else 'Updated'
        })
class ApiGradeAssignment(BaseCourseView):
    def post(self, request, course_code, pk=None):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)

        sub_pk = request.data.get('student_assignment_id') or request.data.get('id') or pk
        sub = models.StudentAssignment.objects.get(pk=sub_pk)
        sub.score = request.data.get('score')
        sub.feedback = request.data.get('feedback')
        sub.save()
        return Response({'status': 'graded'})

class ApiDeleteAssignment(BaseCourseView):
    def delete(self, request, course_code, pk):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)
            
        models.Assignment.objects.filter(pk=pk).delete()
        return Response(status=204)

class ApiDocuments(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        docs = models.CourseDocuments.objects.filter(course_id=course_obj)
        res = []
        for d in docs:
            raw_url = (d.document_url or '').strip() if hasattr(d, 'document_url') else ''
            if raw_url:
                if raw_url.startswith('http://') or raw_url.startswith('https://'):
                    full_url = raw_url
                elif raw_url.startswith('/'):
                    full_url = request.build_absolute_uri(raw_url)
                else:
                    full_url = request.build_absolute_uri('/' + raw_url)
            else:
                full_url = None

            res.append({
                'id': d.pk,
                'title': getattr(d, 'title', None) or getattr(d, 'document_name', ''),
                'description': d.description,
                'url': full_url,
                # Back-compat for any older UI expecting docFile.
                'docFile': full_url,
                'uploadedAt': d.upload_time.isoformat() if hasattr(d, 'upload_time') else None,
            })
        return Response(res)

class ApiAddDocument(BaseCourseView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)
            
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr

        title = (request.data.get('title') or request.data.get('document_name') or '').strip()
        description = (request.data.get('description') or '').strip()
        url = request.data.get('url') or request.data.get('document_url') or request.data.get('doc_file')

        if url is None:
            return Response({'detail': 'url is required'}, status=400)

        # If someone posts a file in multipart, this will be an UploadedFile.
        if hasattr(url, 'read'):
            return Response({'detail': 'Only link uploads are supported. Provide a URL.'}, status=400)

        url = str(url).strip()
        if not url:
            return Response({'detail': 'url is required'}, status=400)

        # Model constraints
        if hasattr(models.CourseDocuments, 'document_name'):
            title = title[:40]
        description = description[:100]

        doc = models.CourseDocuments.objects.create(
            course_id=course_obj,
            description=description,
            document_name=title or 'Material',
            document_url=url,
        )

        if hasattr(doc, 'title'):
            doc.title = title
            doc.save(update_fields=['title'])

        return Response({'id': doc.pk})

class ApiDeleteDocument(BaseCourseView):
    def delete(self, request, course_code, pk):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)
            
        models.CourseDocuments.objects.filter(pk=pk).delete()
        return Response(status=204)

class ApiForum(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr

        # Forum rows are messages. ForumReply is an edge table: parent (forum_ques) -> child (forum_reply).
        messages = models.Forum.objects.filter(course_id=course_obj).select_related('commenter_id', 'commenter_id__user').order_by('comment_time')
        edges = models.ForumReply.objects.filter(
            forum_ques__course_id=course_obj,
            forum_reply__course_id=course_obj,
        ).select_related('forum_ques', 'forum_reply')

        by_id = {}
        children = {}
        is_child = set()

        for m in messages:
            posted_by = 'Unknown'
            posted_by_id = None
            if m.commenter_id and getattr(m.commenter_id, 'user', None):
                posted_by = m.commenter_id.user.get_full_name() or m.commenter_id.user.username
                posted_by_id = m.commenter_id.user.username

            by_id[m.pk] = {
                'id': m.pk,
                'message': m.comment,
                'postedBy': posted_by,
                'postedById': posted_by_id,
                'createdAt': m.comment_time.isoformat() if hasattr(m, 'comment_time') else None,
                'replies': [],
            }
            children[m.pk] = []

        for e in edges:
            parent_id = e.forum_ques_id
            child_id = e.forum_reply_id
            if parent_id in children and child_id in by_id:
                children[parent_id].append(child_id)
                is_child.add(child_id)

        # Build a nested tree (depth-first). Guard against cycles.
        def build_node(node_id, seen):
            if node_id in seen:
                return None
            seen.add(node_id)
            node = dict(by_id[node_id])
            node['replies'] = []
            for cid in children.get(node_id, []):
                child_node = build_node(cid, seen)
                if child_node:
                    node['replies'].append(child_node)
            return node

        roots = [mid for mid in by_id.keys() if mid not in is_child]
        res = []
        for rid in roots:
            n = build_node(rid, set())
            if n:
                res.append(n)
        return Response(res)

class ApiForumNew(BaseCourseView):
    def post(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        extra_info, _ = self.get_role_info(request)

        msg = (request.data.get('message') or request.data.get('question') or request.data.get('comment') or '').strip()
        if not msg:
            return Response({'detail': 'message is required'}, status=400)

        f = models.Forum.objects.create(
            course_id=course_obj,
            commenter_id=extra_info,
            comment=msg,
        )
        return Response({'id': f.pk})

class ApiForumReply(BaseCourseView):
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, _ = self.get_role_info(request)

        parent_id = request.data.get('parent_id') or request.data.get('forum_id')
        msg = (request.data.get('message') or request.data.get('reply') or '').strip()
        if not parent_id:
            return Response({'detail': 'parent_id is required'}, status=400)
        if not msg:
            return Response({'detail': 'message is required'}, status=400)

        parent = models.Forum.objects.get(pk=parent_id)
        child = models.Forum.objects.create(
            course_id=parent.course_id,
            commenter_id=extra_info,
            comment=msg,
        )
        edge = models.ForumReply.objects.create(
            forum_ques=parent,
            forum_reply=child,
        )
        return Response({'id': edge.pk, 'message_id': child.pk})

class ApiForumRemove(BaseCourseView):
    def delete(self, request, course_code, pk):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        target = models.Forum.objects.filter(pk=pk).select_related('commenter_id', 'commenter_id__user').first()
        if not target:
            return Response(status=204)

        is_owner = bool(target.commenter_id_id == getattr(extra_info, 'id', None))
        if is_student_user and not is_owner:
            return Response({'detail': 'Not allowed'}, status=403)

        # Delete subtree: collect all descendants via ForumReply edges.
        to_delete = set([target.pk])
        frontier = [target.pk]
        while frontier:
            parent_ids = frontier
            frontier = []
            child_ids = list(models.ForumReply.objects.filter(forum_ques_id__in=parent_ids).values_list('forum_reply_id', flat=True))
            for cid in child_ids:
                if cid not in to_delete:
                    to_delete.add(cid)
                    frontier.append(cid)
        models.Forum.objects.filter(pk__in=list(to_delete)).delete()
        return Response(status=204)

class ApiQuizzes(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        extra_info, is_student_user = self.get_role_info(request)
        
        quizzes = models.Quiz.objects.filter(course_id=course_obj)
        res = []
        for q in quizzes:
            if is_student_user:
                # For students: show all quizzes except those already completed
                student = models.Student.objects.get(id=extra_info)
                has_finished = models.QuizResult.objects.filter(quiz_id=q, student_id=student, finished=True).exists()
                if has_finished:
                    continue  # Skip this quiz, student has already completed it
                    
            duration_minutes = 0
            if q.start_time and q.end_time:
                delta = q.end_time - q.start_time
                duration_minutes = int(delta.total_seconds() // 60)
            elif hasattr(q, 'd_day') and hasattr(q, 'd_hour') and hasattr(q, 'd_minute'):
                try:
                    duration_minutes = (
                        int(q.d_day or 0) * 1440 + int(q.d_hour or 0) * 60 + int(q.d_minute or 0)
                    )
                except (ValueError, TypeError):
                    duration_minutes = 0

            res.append({
                'id': q.pk,
                'title': getattr(q, 'title', getattr(q, 'quiz_name', '')),
                'description': q.description if hasattr(q, 'description') else '',
                'startTime': q.start_time.isoformat(),
                'endTime': q.end_time.isoformat() if q.end_time else None,
                'duration': duration_minutes,
                'negativeMarks': getattr(q, 'negative_marks', 0),
                'totalQuestions': q.number_of_question if hasattr(q, 'number_of_question') else 0
            })
        return Response(res)

class ApiCreateQuiz(BaseCourseView):
    def post(self, request, course_code):
        try:
            if not self.check_enrollment(request, course_code):
                return Response({'detail': 'Not enrolled in this course'}, status=403)
            extra_info, is_student_user = self.get_role_info(request)
            if is_student_user:
                return Response({'detail': 'Faculty only'}, status=403)
            
            curr = services.get_course_obj(course_code)
            if not curr:
                return Response({'detail': 'Course not found'}, status=404)
            
            # Get the actual Course object
            course_obj = curr.course_id if hasattr(curr, 'course_id') else curr
            
            d = request.data

            title = (d.get('title') or '').strip()
            if not title:
                return Response({'detail': 'title is required'}, status=400)

            start_raw = d.get('start_time')
            duration_raw = d.get('duration')
            end_raw = d.get('end_time')
            start_dt = parse_datetime(start_raw) if isinstance(start_raw, str) else None
            end_dt = None

            if start_dt is None:
                return Response({'detail': 'start_time must be an ISO datetime'}, status=400)

            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt)

            if duration_raw is not None:
                try:
                    duration_val = int(duration_raw)
                except (ValueError, TypeError):
                    return Response({'detail': 'duration must be an integer (minutes)'}, status=400)

                if duration_val <= 0:
                    return Response({'detail': 'duration must be a positive number'}, status=400)

                end_dt = start_dt + timedelta(minutes=duration_val)
            elif isinstance(end_raw, str):
                end_dt = parse_datetime(end_raw)
                if end_dt is None:
                    return Response({'detail': 'end_time must be an ISO datetime when provided'}, status=400)
                if timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt)
            else:
                return Response({'detail': 'Either duration or end_time must be provided'}, status=400)

            if end_dt <= start_dt:
                return Response({'detail': 'end_time must be after start_time'}, status=400)

            delta = end_dt - start_dt
            total_minutes = int(delta.total_seconds() // 60)
            days = total_minutes // (60 * 24)
            hours = (total_minutes % (60 * 24)) // 60
            minutes = total_minutes % 60

            q = models.Quiz.objects.create(
                course_id=course_obj,
                quiz_name=title[:20],
                start_time=start_dt,
                end_time=end_dt,
                d_day=str(days).zfill(2),
                d_hour=str(hours).zfill(2),
                d_minute=str(minutes).zfill(2),
                negative_marks=float(d.get('negative_marks') or 0),
                description=(d.get('description') or '').strip(),
                rules=(d.get('rules') or '').strip(),
            )
            return Response({
                'id': q.pk,
                'title': q.quiz_name,
                'description': q.description,
                'startTime': q.start_time.isoformat(),
                'endTime': q.end_time.isoformat(),
                'negativeMarks': q.negative_marks,
            })
        except IntegrityError as e:
            logger.error(f"Database integrity error creating quiz: {e}")
            return Response({'detail': 'Database error occurred'}, status=500)
        except Exception as e:
            logger.error(f"Error creating quiz: {e}")
            return Response({'detail': 'An error occurred while creating the quiz'}, status=500)

class ApiQuizDetail(BaseCourseView):
    def get(self, request, course_code, quiz_id):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        q = models.Quiz.objects.get(pk=quiz_id)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            if timezone.now() > q.end_time:
                return Response({'detail': 'Quiz has ended'}, status=403)
            student = models.Student.objects.get(id=extra_info)
            if models.QuizResult.objects.filter(quiz_id=q, student_id=student, finished=True).exists():
                return Response({'detail': 'You have already attempted this quiz'}, status=403)
                
        questions = models.QuizQuestion.objects.filter(quiz_id=q).select_related('question')
        res_q = []
        for x in questions:
            ques = x.question
            res_q.append({
                'id': x.pk,
                'question': ques.question,
                'option1': ques.options1,
                'option2': ques.options2,
                'option3': ques.options3,
                'option4': ques.options4,
                'option5': ques.options5,
                'marks': ques.marks,
            })
        return Response({
            'id': q.pk,
            'title': getattr(q, 'title', getattr(q, 'quiz_name', '')),
            'questions': res_q
        })

class ApiQuizSubmit(BaseCourseView):
    def post(self, request, course_code, quiz_id):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if not is_student_user: return Response({'detail': 'Student only'}, status=403)
            
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        q = models.Quiz.objects.get(pk=quiz_id)
        if timezone.now() > q.end_time:
            return Response({'detail': 'Quiz has ended'}, status=403)
            
        student = models.Student.objects.get(id=extra_info)
        answers = request.data.get('answers', [])
        score = 0
        total = 0
        negative = getattr(q, 'negative_marks', 0)
        
        for ans in answers:
            qq = models.QuizQuestion.objects.select_related('question').get(pk=ans['question_id'])
            ques = qq.question
            total += ques.marks
            correct = ques.answer
            models.StudentAnswer.objects.create(
                student_id=student,
                quiz_id=q,
                question_id=qq,
                choice=ans['selected_option']
            )
            if int(ans['selected_option']) == int(correct):
                score += ques.marks
            else:
                score -= negative
                
        # QuizResult.score is non-null in this schema; don't use get_or_create()
        # because the implicit create would attempt score=NULL and fail.
        models.QuizResult.objects.update_or_create(
            student_id=student,
            quiz_id=q,
            defaults={'score': score, 'finished': True},
        )
        
        return Response({'score': score, 'totalMarks': total})

class ApiRemoveQuiz(BaseCourseView):
    def delete(self, request, course_code, quiz_id):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        models.Quiz.objects.filter(pk=quiz_id).delete()
        return Response(status=204)

class ApiAttendance(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr

        extra_info, is_student_user = self.get_role_info(request)

        if is_student_user:
            # For students, try both new and old system attendance records
            from applications.academic_information.models import CourseAttendance
            
            student_username = extra_info.user.username if hasattr(extra_info, 'user') else str(extra_info)
            logger.info(f"[Student Attendance] User: {request.user.username}, Course: {course_code}, StudentUsername: {student_username}")
            
            # Try new system first
            recs_new = CourseAttendance.objects.filter(
                course_code=course_code,
                student_id=student_username
            ).order_by('date')
            logger.info(f"[Student Attendance] New system records found: {recs_new.count()}")
            
            if recs_new.exists():
                # Found in new system
                res = {}
                for r in recs_new:
                    d = r.date.isoformat()
                    if d not in res:
                        res[d] = []
                    res[d].append({
                        'present': r.present,
                    })
                return Response(res)
            else:
                # Try old system
                try:
                    student = Student.objects.get(id=extra_info)
                    recs_old = Student_attendance.objects.filter(
                        instructor_id__curriculum_id__course_code=course_code,
                        student_id=student,
                    ).order_by('date')
                    logger.info(f"[Student Attendance] Old system records found: {recs_old.count()}")
                    return Response([{'date': r.date.isoformat(), 'present': r.present} for r in recs_old])
                except Student.DoesNotExist:
                    logger.warning(f"[Student Attendance] Student not found for {request.user.username}")
                    return Response([])

        # faculty
        link = services.get_instructor_link(extra_info, course_code)
        if not link:
            return Response({'detail': 'Not an instructor for this course'}, status=403)

        # Check if this is a MockInstructorLink (from new system)
        if hasattr(link, '__class__') and 'MockInstructorLink' in str(link.__class__):
            # New system - use CourseAttendance model
            from applications.academic_information.models import CourseAttendance
            
            # Get instructor user ID
            instructor_user_id = extra_info if isinstance(extra_info, int) else extra_info.user.id if hasattr(extra_info, 'user') else extra_info
            
            recs = CourseAttendance.objects.filter(
                course_code=course_code,
                instructor_id=instructor_user_id
            ).order_by('date')
            res = {}
            for r in recs:
                d = r.date.isoformat()
                if d not in res:
                    res[d] = []
                res[d].append({
                    'student_id': r.student_id,
                    'name': r.student_id,
                    'present': r.present,
                })
            return Response(res)

        # Old system
        recs = Student_attendance.objects.filter(instructor_id=link).select_related(
            'student_id', 'student_id__id', 'student_id__id__user'
        ).order_by('date')
        res = {}
        for r in recs:
            d = r.date.isoformat()
            if d not in res:
                res[d] = []
            username = r.student_id.id.user.username
            res[d].append({
                'student_id': username,
                'name': r.student_id.id.user.get_full_name() or username,
                'present': r.present,
            })
        return Response(res)

    def post(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)

        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr

        link = services.get_instructor_link(extra_info, course_code)
        if not link:
            return Response({'detail': 'Not an instructor for this course'}, status=403)

        date_str = request.data.get('date')
        dt = parse_date(date_str) if isinstance(date_str, str) else None
        if dt is None:
            return Response({'detail': 'date is required (YYYY-MM-DD)'}, status=400)

        atts = request.data.get('attendance', [])
        if not isinstance(atts, list):
            return Response({'detail': 'attendance must be a list'}, status=400)

        # Check if this is a MockInstructorLink (from new system)
        is_new_system = hasattr(link, '__class__') and 'MockInstructorLink' in str(link.__class__)

        # Get instructor user ID
        if is_new_system:
            instructor_user_id = extra_info if isinstance(extra_info, int) else extra_info.user.id if hasattr(extra_info, 'user') else extra_info

        count = 0
        for att in atts:
            sid = att.get('student_id')
            present = bool(att.get('present'))
            if not sid:
                continue
            
            if is_new_system:
                # New system - use CourseAttendance model
                from applications.academic_information.models import CourseAttendance
                rec, _ = CourseAttendance.objects.get_or_create(
                    student_id=sid,
                    course_code=course_code,
                    instructor_id=instructor_user_id,
                    date=dt,
                )
                rec.present = present
                rec.save()
                count += 1
            else:
                # Old system
                student = Student.objects.filter(id__user__username=sid).first()
                if not student:
                    continue
                rec, _ = Student_attendance.objects.get_or_create(
                    instructor_id=link,
                    student_id=student,
                    date=dt,
                )
                rec.present = present
                rec.save()
                count += 1

        return Response({'status': 'saved', 'count': count})


class ApiAttendanceRoster(BaseCourseView):
    def get(self, request, course_code):
        try:
            if not self.check_enrollment(request, course_code):
                return Response({'detail': 'Not enrolled'}, status=403)
            extra_info, is_student_user = self.get_role_info(request)
            if is_student_user:
                return Response({'detail': 'Faculty only'}, status=403)
            curr = services.get_course_obj(course_code)
            if not curr:
                return Response({'detail': 'Course not found'}, status=404)
            
            # Get the actual Course object - handle both old and new systems consistently
            if hasattr(curr, 'course_id'):
                # This is from the old curriculum system or MockCurriculum
                course_obj = curr.course_id
            else:
                # This is a direct Course object from new system
                course_obj = curr

            link = services.get_instructor_link(extra_info, course_code)
            if not link:
                return Response({'detail': 'Not an instructor for this course'}, status=403)

            roster = services.get_course_roster(course_code)
            if not roster:
                logger.warning(f"Empty roster for course {course_code}, instructor {extra_info}")
                return Response([], safe=True)
            return Response(roster)
        except Exception as e:
            logger.error(f"Error getting attendance roster for course {course_code}: {e}")
            return Response({'detail': 'An error occurred while fetching the roster'}, status=500)

class ApiQuestionBank(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        # Using a dummy implementation or empty list if no models exist for QB since it wasn't specified completely in models
        # Assuming we might have QuestionBank models if not we send empty array 
        try:
            banks = models.QuestionBank.objects.filter(course_id=course_obj)
            return Response([{'id': b.pk, 'title': b.name} for b in banks])
        except:
            return Response([])

class ApiCreateBank(BaseCourseView):
    def post(self, request, course_code):
        return Response({})

class ApiAddTopic(BaseCourseView):
    def post(self, request, course_code, bank_id):
        return Response({})

class ApiAddQuestion(BaseCourseView):
    def post(self, request, course_code, bank_id, topic_id):
        return Response({})

class ApiGrading(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        extra_info, is_student_user = self.get_role_info(request)
        
        schemes = models.GradingScheme.objects.filter(course_id=course_obj)
        if is_student_user:
            student = models.Student.objects.get(id=extra_info)
            evals = models.StudentEvaluation.objects.filter(student=student, scheme__in=schemes)
            sch_res = [{'id': s.pk, 'component': s.component, 'weightage': s.weightage, 'max_marks': s.max_marks} for s in schemes]
            ev_res = [{'id': e.pk, 'scheme_id': e.scheme.pk, 'marks_obtained': e.marks_obtained} for e in evals]
            return Response({'schemes': sch_res, 'evaluations': ev_res})
        else:
            evals = models.StudentEvaluation.objects.filter(scheme__in=schemes)
            sch_res = [{'id': s.pk, 'component': s.component, 'weightage': s.weightage, 'max_marks': s.max_marks} for s in schemes]
            ev_res = [{'id': e.pk, 'scheme_id': e.scheme.pk, 'student_id': e.student.id.user.username, 'student_name': e.student.id.user.get_full_name(), 'marks_obtained': e.marks_obtained} for e in evals]
            return Response({'schemes': sch_res, 'evaluations': ev_res})

class ApiCreateGradingScheme(BaseCourseView):
    def post(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        w = float(request.data.get('weightage', 0))
        schemes = models.GradingScheme.objects.filter(course_id=course_obj)
        total = sum([s.weightage for s in schemes])
        if total + w > 100:
            return Response({'detail': 'Total weightage cannot exceed 100'}, status=400)
            
        gs = models.GradingScheme.objects.create(
            course_id=course_obj,
            component=request.data.get('component'),
            weightage=w,
            max_marks=float(request.data.get('max_marks', 0))
        )
        return Response({'id': gs.pk})

class ApiEvaluate(BaseCourseView):
    def post(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        
        s_id = request.data.get('student_id')
        sc_id = request.data.get('scheme_id')
        m = float(request.data.get('marks_obtained', 0))
        
        student = models.Student.objects.get(id__user__username=s_id)
        scheme = models.GradingScheme.objects.get(pk=sc_id)
        ev, _ = models.StudentEvaluation.objects.get_or_create(scheme=scheme, student=student)
        ev.marks_obtained = m
        ev.save()
        return Response({'id': ev.pk})

class ApiStudentGrades(BaseCourseView):
    def get(self, request, course_code):
        curr = self.get_course_or_error(request, course_code)
        if isinstance(curr, Response):
            return curr
        extra_info, is_student_user = self.get_role_info(request)
        if not is_student_user: return Response({'detail': 'Student only'}, status=403)
        
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        # Get the actual Course object - handle both old and new systems consistently
        if hasattr(curr, 'course_id'):
            # This is from the old curriculum system or MockCurriculum
            course_obj = curr.course_id
        else:
            # This is a direct Course object from new system
            course_obj = curr
        
        student = models.Student.objects.get(id=extra_info)
        schemes = models.GradingScheme.objects.filter(course_id=course_obj)
        
        res = []
        total_w = 0
        for s in schemes:
            ev = models.StudentEvaluation.objects.filter(scheme=s, student=student).first()
            m = ev.marks_obtained if ev else 0
            w_score = (m / s.max_marks * s.weightage) if s.max_marks > 0 else 0
            res.append({
                'component': s.component,
                'weightage': s.weightage,
                'maxMarks': s.max_marks,
                'marksObtained': m,
                'weightedScore': w_score
            })
            total_w += w_score
            
        return Response({
            'grades': res,
            'totalWeightedScore': total_w
        })

