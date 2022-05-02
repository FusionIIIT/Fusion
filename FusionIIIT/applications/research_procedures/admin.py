from django.contrib import admin
from applications.research_procedures.models import Patent, ResearchGroup,ResearchProject,ConsultancyProject,TechTransfer
from django.utils.html import format_html

# Adding a custom admin view for patent
class PatentAdmin(admin.ModelAdmin):

    list_filter = ('status',) 
    search_fields = ['title', 'application_id']

    def _status(self, obj):
        color = "orange"
        if obj.status == "Approved":
            color = "green"
        elif obj.status == "Disapproved":
            color = "red"
        return format_html('<span style="color: %s"><b>%s</b></span>' % (color, obj.status))

    list_display = ["faculty_id","title","_status"]


class ResearchGroupAdmin(admin.ModelAdmin):
    list_display = ["name","description"]

# Register your models here.
admin.site.register(Patent,PatentAdmin)
admin.site.register(ResearchProject)
admin.site.register(ConsultancyProject)
admin.site.register(TechTransfer)
# admin.site.register(ResearchGroup,ResearchGroupAdmin)