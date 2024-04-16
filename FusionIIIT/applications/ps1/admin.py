from django.contrib import admin


# Register your models here.
from applications.ps1.models import StockEntry,IndentFile,StockItem,StockTransfer
admin.site.register(StockEntry)
admin.site.register(IndentFile)
admin.site.register(StockItem)
admin.site.register(StockTransfer)