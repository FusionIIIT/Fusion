from django.contrib import admin

from .models import (Club_budget, Club_info, Club_member, Club_report,
                     Core_team, Fest_budget, Other_report, Session_info)

# Register your models here.

admin.site.register(Club_info)
admin.site.register(Club_member)
admin.site.register(Core_team)
admin.site.register(Club_budget)
admin.site.register(Session_info)
admin.site.register(Club_report)
admin.site.register(Fest_budget)
admin.site.register(Other_report)
