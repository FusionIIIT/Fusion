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
admin.site.register(hostel_allotment)
admin.site.register(hostel_capacity)

# registering Dean RSPC project management models

admin.site.register(Project_Registration)
admin.site.register(Project_Extension)
admin.site.register(Project_Closure)
admin.site.register(Project_Reallocation)

admin.site.register(Member)
admin.site.register(Registrar)
admin.site.register(vendor)
admin.site.register(purchase_commitee)
admin.site.register(LTC)