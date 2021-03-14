from django.contrib import admin
from .models import CounsellingInfo,Issues,FAQ,CounsellingMeeting,CounsellingMinutes
# Register your models here.

admin.site.register(CounsellingInfo)
admin.site.register(Issues)
admin.site.register(FAQ)
admin.site.register(CounsellingMinutes)
admin.site.register(CounsellingMeeting)
