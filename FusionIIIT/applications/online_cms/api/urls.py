from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.ApiCourseList.as_view(), name='api_courses'),
    path('<str:course_code>/dashboard/', views.ApiCourseDashboard.as_view(), name='api_dashboard'),

    path('<str:course_code>/assignments/', views.ApiAssignments.as_view(), name='api_assignments'),
    path('<str:course_code>/assignments/add/', views.ApiAddAssignment.as_view(), name='api_add_assignment'),
    path('<str:course_code>/assignments/upload/', views.ApiUploadAssignment.as_view(), name='api_upload_assignment'),
    path('<str:course_code>/assignments/<int:pk>/grade/', views.ApiGradeAssignment.as_view(), name='api_grade_assignment'),
    path('<str:course_code>/assignments/<int:pk>/delete/', views.ApiDeleteAssignment.as_view(), name='api_delete_assignment'),

    path('<str:course_code>/documents/', views.ApiDocuments.as_view(), name='api_documents'),
    path('<str:course_code>/documents/add/', views.ApiAddDocument.as_view(), name='api_add_document'),
    path('<str:course_code>/documents/<int:pk>/delete/', views.ApiDeleteDocument.as_view(), name='api_delete_document'),

    path('<str:course_code>/forum/', views.ApiForum.as_view(), name='api_forum'),
    path('<str:course_code>/forum/new/', views.ApiForumNew.as_view(), name='api_forum_new'),
    path('<str:course_code>/forum/reply/', views.ApiForumReply.as_view(), name='api_forum_reply'),
    path('<str:course_code>/forum/<int:pk>/remove/', views.ApiForumRemove.as_view(), name='api_forum_remove'),

    path('<str:course_code>/quizzes/', views.ApiQuizzes.as_view(), name='api_quizzes'),
    path('<str:course_code>/quizzes/create/', views.ApiCreateQuiz.as_view(), name='api_create_quiz'),
    path('<str:course_code>/quizzes/<int:quiz_id>/', views.ApiQuizDetail.as_view(), name='api_quiz_detail'),
    path('<str:course_code>/quizzes/<int:quiz_id>/submit/', views.ApiQuizSubmit.as_view(), name='api_quiz_submit'),
    path('<str:course_code>/quizzes/<int:quiz_id>/remove/', views.ApiRemoveQuiz.as_view(), name='api_remove_quiz'),

    path('<str:course_code>/attendance/', views.ApiAttendance.as_view(), name='api_attendance'),
    path('<str:course_code>/attendance/roster/', views.ApiAttendanceRoster.as_view(), name='api_attendance_roster'),

    path('<str:course_code>/grading/', views.ApiGrading.as_view(), name='api_grading'),
    path('<str:course_code>/grading/create/', views.ApiCreateGradingScheme.as_view(), name='api_create_grading'),
    path('<str:course_code>/grading/evaluate/', views.ApiEvaluate.as_view(), name='api_evaluate'),
    path('<str:course_code>/grading/student-grades/', views.ApiStudentGrades.as_view(), name='api_student_grades'),
]