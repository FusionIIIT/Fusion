from django.contrib import admin
from .models import StockAdmin, StockEntry
# Register your models here.
admin.site.register(StockAdmin)
admin.site.register(StockEntry)
