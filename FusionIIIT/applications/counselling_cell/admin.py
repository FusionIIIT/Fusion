from django.contrib import admin
from .models import CounsellingInfo,Issues,FAQ,Counselling_meeting,Counselling_minutes
# Register your models here.

admin.site.register(CounsellingInfo)
admin.site.register(Issues)
admin.site.register(FAQ)
admin.site.register(Counselling_minutes)
admin.site.register(Counselling_meeting)
