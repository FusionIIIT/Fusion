from django.contrib import admin
from .models import StockAdmin, StockEntry, TransferEntry
# Register your models here.
admin.site.register(StockAdmin)
admin.site.register(StockEntry)
admin.site.register(TransferEntry)
