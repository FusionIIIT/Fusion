from django.contrib import admin


# Register your models here.
from applications.ps1.models import StockEntry,IndentFile,IndentFile2,Item
admin.site.register(StockEntry)
admin.site.register(IndentFile)
admin.site.register(IndentFile2)
admin.site.register(Item)