from django.contrib import admin

from .models import Bank, Company, Payments, Paymentscheme, Receipts

admin.site.register(Paymentscheme)
admin.site.register(Receipts)
admin.site.register(Payments)
admin.site.register(Bank)
admin.site.register(Company)




# Register your models here.
