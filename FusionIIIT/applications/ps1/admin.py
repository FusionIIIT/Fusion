from django.contrib import admin


# Register your models here.
from applications.ps1.models import StockEntry,IndentFile
admin.site.register(StockEntry)
admin.site.register(IndentFile)