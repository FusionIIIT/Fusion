from django.contrib import admin
from .models import Paymentscheme
from .models import Receipts
from .models import Payments
from .models import Bank
from .models import Company

admin.site.register(Paymentscheme)
admin.site.register(Receipts)
admin.site.register(Payments)
admin.site.register(Bank)
admin.site.register(Company)




# Register your models here.
