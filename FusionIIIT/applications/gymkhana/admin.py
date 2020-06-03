from django.contrib import admin

from .models import (Club_budget, Club_info, Club_member, Club_report,
                     Core_team, Fest_budget, Other_report, Session_info,Event_info)


# Register your models here.

class ClubInfoAdmin(admin.ModelAdmin):
    raw_id_fields = ("co_ordinator", "co_coordinator")


class ClubMemberAdmin(admin.ModelAdmin):
    raw_id_fields = ("member",)


admin.site.register(Club_info, ClubInfoAdmin)
admin.site.register(Club_member, ClubMemberAdmin)
admin.site.register(Core_team)
admin.site.register(Club_budget)
admin.site.register(Session_info)
admin.site.register(Event_info)
admin.site.register(Club_report)
admin.site.register(Fest_budget)
admin.site.register(Other_report)
