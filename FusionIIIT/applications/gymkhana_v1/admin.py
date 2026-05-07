from django.contrib import admin

from .models import Budget, Club, ClubMember, Event, GalleryItem, Poll, PollOption, PollVote


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "coordinator", "status", "alloted_budget", "spent_budget")
    list_filter = ("category", "status")
    search_fields = ("name", "coordinator__username", "co_coordinator__username")


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ("student", "club", "status", "applied_at")
    list_filter = ("status", "club")
    search_fields = ("student__username", "student__first_name", "student__last_name", "club__name")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "date", "venue", "status")
    list_filter = ("status", "club", "date")
    search_fields = ("name", "club__name", "incharge")


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("club", "budget_for", "amount", "status", "created_at")
    list_filter = ("status", "club", "budget_type")


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("title", "pub_date", "exp_date", "created_by")


admin.site.register(PollOption)
admin.site.register(PollVote)
admin.site.register(GalleryItem)
