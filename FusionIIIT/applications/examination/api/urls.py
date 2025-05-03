
from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^exam_view/', views.exam_view, name='exam_view'),
    url(r'^download_template/', views.download_template, name='download_template'),
    url(r'^submitGrades/', views.SubmitGradesView.as_view(), name='submitGrades'),
    url(r'^upload_grades/', views.UploadGradesAPI.as_view(), name='upload_grades'),
    url(r'^update_grades/', views.UpdateGradesAPI.as_view(), name='update_grades'),
    url(r'^update_enter_grades/', views.UpdateEnterGradesAPI.as_view(), name='update_enter_grades'),
    url(r'^moderate_student_grades/', views.ModerateStudentGradesAPI.as_view(), name='moderate_student_grades'),
    url(r'^generate_transcript/', views.GenerateTranscript.as_view(), name='generate_transcript'),
    url(r'^generate_transcript_form/', views.GenerateTranscriptForm.as_view(), name='generate_transcript_form'),
    url(r'^generate_result/', views.GenerateResultAPI.as_view(), name='generate_result'),
    url(r'^submit/', views.SubmitAPI.as_view(), name='submit'),
    url(r'^download_excel/', views.DownloadExcelAPI.as_view(), name='download_excel'),
    url(r'^submitGradesProf/', views.SubmitGradesProfAPI.as_view(), name='submitGradesProf'),
    url(r'^upload_grades_prof/', views.UploadGradesProfAPI.as_view(), name='upload_grades_prof'),
    url(r'^generate_pdf/', views.GeneratePDFAPI.as_view(), name='generate_pdf'),
    url(r'^downloadGrades/', views.DownloadGradesAPI.as_view(), name='downloadGrades'),
    url(r'verify_grades_dean/',views.VerifyGradesDeanView.as_view(),name='verify_grades_dean'),
    url(r'update_enter_grades_dean/',views.UpdateEnterGradesDeanView.as_view(),name='update_enter_grades_dean'),
    url(r'validate_dean/',views.ValidateDeanView.as_view(),name='validate_dean'),
    url(r'validate_dean_submit/',views.ValidateDeanSubmitView.as_view(),name='validate_dean_submit'),
    url(r'check_result/',views.CheckResultView.as_view(),name='check_result'),
    url(r'preview_grades/',views.PreviewGradesAPI.as_view(),name='preview_grades'),
    url(r'result-announcements/', views.ResultAnnouncementListAPI.as_view(), name="result-announcements"),
    url(r'update-announcement/', views.UpdateAnnouncementAPI.as_view(), name="update-announcement"),
    url(r'create-announcement/', views.CreateAnnouncementAPI.as_view(), name="create-announcement"),
    url(r'unique-course-reg-years/', views.UniqueRegistrationYearsView.as_view(), name="unique-course-reg-years"),
    url(r'unique-stu-grades-years/', views.UniqueStudentGradeYearsView.as_view(), name="unique-stu-grades-years")
]