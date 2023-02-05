from django.contrib import admin


from .models import (
    CounsellingFAQ,
    CounsellingIssue,
    CounsellingIssueCategory,
    CounsellingMeeting,
    CounsellingMinutes,
    FacultyCounsellingTeam,
    StudentCounsellingInfo,
    StudentCounsellingTeam,
    StudentMeetingRequest
)



admin.site.register(CounsellingFAQ)
admin.site.register(CounsellingIssue)
admin.site.register(CounsellingIssueCategory)
admin.site.register(CounsellingMeeting)
admin.site.register(CounsellingMinutes)
admin.site.register(FacultyCounsellingTeam)
admin.site.register(StudentMeetingRequest)
admin.site.register(StudentCounsellingInfo)
admin.site.register(StudentCounsellingTeam)