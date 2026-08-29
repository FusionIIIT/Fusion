from django.urls import path
from . import views


urlpatterns = [
    path('batches/', views.BatchListView.as_view(), name="batches"),
    path('semesters-filter/', views.SemesterFilterView.as_view(), name="semesters-filter"),
    path('student-courses-detail/', views.StudentCoursesDetail.as_view(), name="student-courses-detail"),
    path('students-grade-info/', views.StudentsGradeInfo.as_view(), name="students-grade-info"),
    path('course-student-count/', views.CourseStudentCountView.as_view(), name="course-student-count"),
    path('course-students/', views.CourseStudentsListView.as_view(), name="course-students"),
    path('unregistered-by-batch/', views.UnregisteredStudentsByBatchView.as_view(), name="unregistered-by-batch"),
]