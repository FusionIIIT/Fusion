from django.contrib import admin
from .models import *

admin.site.register(Requisitions)
admin.site.register(Filemovement)
admin.site.register(stock)
admin.site.register(apply_for_purchase)
admin.site.register(quotations)
admin.site.register(Registrar_File)
admin.site.register(registrar_create_doc)
admin.site.register(registrar_general_section)
admin.site.register(registrar_purchase_sales_section)
admin.site.register(registrar_finance_section)
admin.site.register(registrar_establishment_section)
admin.site.register(registrar_director_section)
admin.site.register(Assistantship)

admin.site.register(LTC)
admin.site.register(CPDA)
admin.site.register(Auto_fair_claim)
admin.site.register(Teaching_credits1)
admin.site.register(Assigned_Teaching_credits)
admin.site.register(Lab1)
admin.site.register(TA_assign)
