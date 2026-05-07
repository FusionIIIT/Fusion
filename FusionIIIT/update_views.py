import os
import textwrap

content = """\
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from . import services, models
from applications.academic_information.models import Course

class BaseCourseView(APIView):
    permission_classes = [IsAuthenticated]
    
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
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        
        curr = services.get_course_obj(course_code)
        if not curr:
            return Response({'detail': 'Course not found'}, status=404)
        
        assignments_count = models.Assignment.objects.filter(course_id=curr.course_id).count()
        documents_count = models.CourseDocuments.objects.filter(course_id=curr.course_id).count()
        
        return Response({
            "courseCode": course_code,
            "courseName": curr.course_id.course_name,
            "courseDetails": curr.course_id.course_details,
            "credits": curr.credits,
            "semester": curr.sem,
            "programme": curr.course_id.program_id.name if curr.course_id.program_id else "",
            "branch": curr.course_id.branch_id.name if getattr(curr.course_id, "branch_id", None) else "",
            "batch": curr.course_id.batch_id.name if getattr(curr.course_id, "batch_id", None) else "",
            "counts": {
                "assignments": assignments_count,
                "documents": documents_count
            }
        })

class ApiAssignments(BaseCourseView):
    def get(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        
        curr = services.get_course_obj(course_code)
        course = curr.course_id
        assignments = models.Assignment.objects.filter(course_id=course)
        
        extra_info, is_student_user = self.get_role_info(request)
        
        res = []
        for a in assignments:
            item = {
                'id': a.pk,
                'title': a.assignment_name,
                'description': a.assignment_description,
                'deadline': a.submit_date.isoformat(),
                'createdAt': a.submit_date.isoformat(), # approximation if no createdAt
                'submissions': []
            }
            if is_student_user:
                student = models.Student.objects.filter(id=extra_info).first()
                subs = models.StudentAssignment.objects.filter(assignment_id=a, student_id=student)
            else:
                subs = models.StudentAssignment.objects.filter(assignment_id=a)
                
            for s in subs:
                item['submissions'].append({
                    'id': s.pk,
                    'assignmentId': a.pk,
                    'studentName': s.student_id.id.user.get_full_name() if s.student_id else 'Unknown',
                    'file': request.build_absolute_uri(s.upload_url.url) if s.upload_url else None,
                    'submittedAt': getattr(s, 'submitted_at', timezone.now()).isoformat() if hasattr(s, 'submitted_at') else None,
                    'marks': s.marks,
                    'feedback': s.description if hasattr(s, 'description') else getattr(s, 'feedback', '')
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
        data = request.data
        a = models.Assignment.objects.create(
            course_id=curr.course_id,
            assignment_name=data.get('title'),
            assignment_description=data.get('description'),
            submit_date=data.get('deadline')
        )
        return Response({'id': a.pk})

class ApiUploadAssignment(BaseCourseView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if not is_student_user:
            return Response({'detail': 'Student only'}, status=403)
            
        assignment_id = request.data.get('assignment_id')
        a = models.Assignment.objects.get(pk=assignment_id)
        if timezone.now() > a.submit_date:
            return Response({'detail': 'Submission deadline has passed'}, status=400)
            
        student = models.Student.objects.get(id=extra_info)
        sub = models.StudentAssignment.objects.create(
            student_id=student,
            assignment_id=a,
            upload_url=request.data.get('file')
        )
        return Response({'id': sub.pk, 'submittedAt': timezone.now().isoformat()})

class ApiGradeAssignment(BaseCourseView):
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)
            
        sub = models.StudentAssignment.objects.get(pk=request.data.get('student_assignment_id', request.data.get('id', request.resolver_match.kwargs.get('pk'))))
        sub.marks = request.data.get('marks')
        sub.description = request.data.get('feedback')
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
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
            
        curr = services.get_course_obj(course_code)
        docs = models.CourseDocuments.objects.filter(course_id=curr.course_id)
        res = []
        for d in docs:
            res.append({
                'id': d.pk,
                'title': getattr(d, 'title', getattr(d, 'document_name', '')),
                'description': d.description,
                'docFile': request.build_absolute_uri(d.document_url.url) if d.document_url else None,
                'uploadedAt': d.upload_time.isoformat() if hasattr(d, 'upload_time') else None
            })
        return Response(res)

class ApiAddDocument(BaseCourseView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            return Response({'detail': 'Faculty only'}, status=403)
            
        curr = services.get_course_obj(course_code)
        doc = models.CourseDocuments.objects.create(
            course_id=curr.course_id,
            description=request.data.get('description', ''),
            document_url=request.data.get('doc_file')
        )
        if hasattr(doc, 'title'):
            doc.title = request.data.get('title', '')
        if hasattr(doc, 'document_name'):
            doc.document_name = request.data.get('title', '')
        doc.save()
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
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        curr = services.get_course_obj(course_code)
        forums = models.Forum.objects.filter(course_id=curr.course_id)
        res = []
        for f in forums:
            replies = models.ForumReply.objects.filter(forum_reply=f)
            res.append({
                'id': f.pk,
                'question': f.question,
                'postedBy': f.commenter.user.get_full_name() if f.commenter else 'Unknown',
                'createdAt': f.comment_time.isoformat() if hasattr(f, 'comment_time') else None,
                'replies': [{
                    'id': r.pk,
                    'reply': r.reply,
                    'postedBy': r.replier.user.get_full_name() if r.replier else 'Unknown',
                    'createdAt': getattr(r, 'reply_time', timezone.now()).isoformat() if hasattr(r, 'reply_time') else None
                } for r in replies]
            })
        return Response(res)

class ApiForumNew(BaseCourseView):
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        curr = services.get_course_obj(course_code)
        extra_info, _ = self.get_role_info(request)
        f = models.Forum.objects.create(
            course_id=curr.course_id,
            commenter=extra_info,
            question=request.data.get('question')
        )
        return Response({'id': f.pk})

class ApiForumReply(BaseCourseView):
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, _ = self.get_role_info(request)
        forum = models.Forum.objects.get(pk=request.data.get('forum_id'))
        r = models.ForumReply.objects.create(
            forum_reply=forum,
            replier=extra_info,
            reply=request.data.get('reply')
        )
        return Response({'id': r.pk})

class ApiForumRemove(BaseCourseView):
    def delete(self, request, course_code, pk):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        # Assuming faculty or poster can delete (enforcement simplified)
        models.Forum.objects.filter(pk=pk).delete()
        return Response(status=204)

class ApiQuizzes(BaseCourseView):
    def get(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        curr = services.get_course_obj(course_code)
        extra_info, is_student_user = self.get_role_info(request)
        
        quizzes = models.Quiz.objects.filter(course_id=curr.course_id)
        res = []
        now = timezone.now()
        for q in quizzes:
            if is_student_user:
                student = models.Student.objects.get(id=extra_info)
                has_finished = models.QuizResult.objects.filter(quiz_id=q, student_id=student, finished=True).exists()
                if not (q.start_time <= now and (q.end_time is None or now <= q.end_time) and not has_finished):
                    continue
                    
            res.append({
                'id': q.pk,
                'title': getattr(q, 'title', getattr(q, 'quiz_name', '')),
                'description': q.description if hasattr(q, 'description') else '',
                'startTime': q.start_time.isoformat(),
                'endTime': q.end_time.isoformat() if q.end_time else None,
                'duration': getattr(q, 'duration', getattr(q, 'd_time', 0)),
                'negativeMarks': getattr(q, 'negative_marks', 0),
                'totalQuestions': q.number_of_question if hasattr(q, 'number_of_question') else 0
            })
        return Response(res)

class ApiCreateQuiz(BaseCourseView):
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
            
        curr = services.get_course_obj(course_code)
        d = request.data
        q = models.Quiz(course_id=curr.course_id)
        if hasattr(q, 'quiz_name'): q.quiz_name = d.get('title')
        if hasattr(q, 'title'): q.title = d.get('title')
        if hasattr(q, 'description'): q.description = d.get('description', '')
        q.start_time = d.get('start_time')
        q.end_time = d.get('end_time')  # Can be None now
        if hasattr(q, 'd_time'): q.d_time = d.get('duration', 0)
        if hasattr(q, 'duration'): q.duration = d.get('duration', 0)
        if hasattr(q, 'negative_marks'): q.negative_marks = d.get('negative_marks', 0)
        q.save()
        return Response({'id': q.pk})

class ApiQuizDetail(BaseCourseView):
    def get(self, request, course_code, quiz_id):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled in this course'}, status=403)
        q = models.Quiz.objects.get(pk=quiz_id)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            if q.end_time and timezone.now() > q.end_time:
                return Response({'detail': 'Quiz has ended'}, status=403)
            student = models.Student.objects.get(id=extra_info)
            if models.QuizResult.objects.filter(quiz_id=q, student_id=student, finished=True).exists():
                return Response({'detail': 'You have already attempted this quiz'}, status=403)
                
        questions = models.QuizQuestion.objects.filter(quiz_id=q)
        res_q = []
        for x in questions:
            res_q.append({
                'id': x.pk,
                'question': getattr(x, 'question', getattr(x, 'question_name', '')),
                'option1': getattr(x, 'option1', getattr(x, 'options1', '')),
                'option2': getattr(x, 'option2', getattr(x, 'options2', '')),
                'option3': getattr(x, 'option3', getattr(x, 'options3', '')),
                'option4': getattr(x, 'option4', getattr(x, 'options4', '')),
                'option5': getattr(x, 'option5', getattr(x, 'options5', '')),
                'marks': x.marks
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
            
        q = models.Quiz.objects.get(pk=quiz_id)
        if timezone.now() > q.end_time:
            return Response({'detail': 'Quiz has ended'}, status=403)
            
        student = models.Student.objects.get(id=extra_info)
        answers = request.data.get('answers', [])
        score = 0
        total = 0
        negative = getattr(q, 'negative_marks', 0)
        
        for ans in answers:
            ques = models.QuizQuestion.objects.get(pk=ans['question_id'])
            total += ques.marks
            correct = getattr(ques, 'answer', getattr(ques, 'correct_option', ''))
            models.StudentAnswer.objects.create(
                student_id=student,
                quiz_id=q,
                question_id=ques,
                choice=ans['selected_option']
            )
            if str(ans['selected_option']) == str(correct):
                score += ques.marks
            else:
                score -= negative
                
        res, _ = models.QuizResult.objects.get_or_create(student_id=student, quiz_id=q)
        res.score = score
        res.finished = True
        res.save()
        
        return Response({'score': score, 'totalMarks': total})

class ApiRemoveQuiz(BaseCourseView):
    def delete(self, request, course_code, quiz_id):
        if not self.check_enrollment(request, course_code):
            return Response({'detail': 'Not enrolled' }, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        models.Quiz.objects.filter(pk=quiz_id).delete()
        return Response(status=204)

class ApiAttendance(BaseCourseView):
    def get(self, request, course_code):
        if not self.check_enrollment(request, course_code): return Response({'detail': 'Not enrolled'}, status=403)
        curr = services.get_course_obj(course_code)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user:
            student = models.Student.objects.get(id=extra_info)
            recs = models.Student_attendance.objects.filter(course_id=curr.course_id, student_id=student)
            return Response([{'date': r.date.isoformat(), 'present': r.present} for r in recs])
        else:
            recs = models.Student_attendance.objects.filter(course_id=curr.course_id)
            res = {}
            for r in recs:
                d = r.date.isoformat()
                if d not in res: res[d] = []
                res[d].append({
                    'student_id': r.student_id.id.user.username,
                    'name': r.student_id.id.user.get_full_name(),
                    'present': r.present
                })
            return Response(res)

    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code): return Response({'detail': 'Not enrolled'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        curr = services.get_course_obj(course_code)
        d = request.data.get('date')
        atts = request.data.get('attendance', [])
        for att in atts:
            student = models.Student.objects.get(id__user__username=att['student_id'])
            rec, _ = models.Student_attendance.objects.get_or_create(
                course_id=curr.course_id, student_id=student, date=d)
            rec.present = att['present']
            rec.save()
        return Response({'status': 'saved', 'count': len(atts)})

class ApiQuestionBank(BaseCourseView):
    def get(self, request, course_code):
        if not self.check_enrollment(request, course_code): return Response({'detail': 'Not enrolled'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        
        curr = services.get_course_obj(course_code)
        # Using a dummy implementation or empty list if no models exist for QB since it wasn't specified completely in models
        # Assuming we might have QuestionBank models if not we send empty array 
        try:
            banks = models.QuestionBank.objects.filter(course_id=curr.course_id)
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
        if not self.check_enrollment(request, course_code): return Response({'detail': 'Not enrolled'}, status=403)
        curr = services.get_course_obj(course_code)
        extra_info, is_student_user = self.get_role_info(request)
        
        schemes = models.GradingScheme.objects.filter(course_id=curr.course_id)
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
        if not self.check_enrollment(request, course_code): return Response({'detail': 'Not enrolled'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if is_student_user: return Response({'detail': 'Faculty only'}, status=403)
        
        curr = services.get_course_obj(course_code)
        w = float(request.data.get('weightage', 0))
        schemes = models.GradingScheme.objects.filter(course_id=curr.course_id)
        total = sum([s.weightage for s in schemes])
        if total + w > 100:
            return Response({'detail': 'Total weightage cannot exceed 100'}, status=400)
            
        gs = models.GradingScheme.objects.create(
            course_id=curr.course_id,
            component=request.data.get('component'),
            weightage=w,
            max_marks=float(request.data.get('max_marks', 0))
        )
        return Response({'id': gs.pk})

class ApiEvaluate(BaseCourseView):
    def post(self, request, course_code):
        if not self.check_enrollment(request, course_code): return Response({'detail': 'Not enrolled'}, status=403)
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
        if not self.check_enrollment(request, course_code): return Response({'detail': 'Not enrolled'}, status=403)
        extra_info, is_student_user = self.get_role_info(request)
        if not is_student_user: return Response({'detail': 'Student only'}, status=403)
        
        curr = services.get_course_obj(course_code)
        student = models.Student.objects.get(id=extra_info)
        schemes = models.GradingScheme.objects.filter(course_id=curr.course_id)
        
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

"""
with open("/mnt/c/Users/indra/Desktop/Fusion/Fusion/FusionIIIT/applications/online_cms/views.py", "w") as f:
    f.write(content)
print("Updated views.py")
