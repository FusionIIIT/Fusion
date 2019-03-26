from django.contrib import admin

from .models import *


# Register your models here.
class emp_research_papersAdmin(admin.ModelAdmin):
    list_per_page = 900

admin.site.register(emp_research_projects)
admin.site.register(emp_visits)

admin.site.register(emp_research_papers, emp_research_papersAdmin)
admin.site.register(emp_published_books)

admin.site.register(emp_patents)
admin.site.register(emp_mtechphd_thesis)

admin.site.register(emp_keynote_address)
admin.site.register(emp_expert_lectures)

admin.site.register(emp_event_organized)
admin.site.register(emp_consultancy_projects)

admin.site.register(emp_confrence_organised)
admin.site.register(emp_session_chair)

admin.site.register(emp_techtransfer)
admin.site.register(emp_achievement)

admin.site.register(faculty_about)
