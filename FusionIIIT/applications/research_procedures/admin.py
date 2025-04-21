from django.contrib import admin
from applications.research_procedures.models import *
from django.utils.html import format_html

# Adding a custom admin view for patent

class ResearchGroupAdmin(admin.ModelAdmin):
    list_display = ["name","description"]

# Register your models here.

admin.site.register(projects)
admin.site.register(staff)
admin.site.register(expenditure)
admin.site.register(project_access)
admin.site.register(budget)
# admin.site.register(requests)
# admin.site.register(category)
# admin.site.register(requests)
# admin.site.register(rspc_inventory)
# admin.site.register(project_staff_info)


# admin.site.register(ResearchGroup,ResearchGroupAdmin)