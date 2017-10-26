from django.contrib import admin

# Register your models here.
from .models import (Award_and_scholarship, Common_info, Director_gold,
                     Director_silver, Financial_assistance, Group_student, Mcm,
                     Previous_winner, Proficiency_dm, Release)

admin.site.register(Mcm),
admin.site.register(Award_and_scholarship),
admin.site.register(Previous_winner),
admin.site.register(Release),
admin.site.register(Financial_assistance),
admin.site.register(Common_info),
admin.site.register(Proficiency_dm),
admin.site.register(Group_student),
admin.site.register(Director_silver),
admin.site.register(Director_gold)
