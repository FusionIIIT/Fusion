from django.contrib import admin
from .models import hidden_grades,authentication,grade

# Register your models here.

admin.site.register(hidden_grades)
admin.site.register(authentication)
admin.site.register(grade)