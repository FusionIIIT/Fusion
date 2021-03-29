from django.contrib import admin

from .models import (ExpenditureType, Expenditure, IncomeSource, Income)

admin.site.register(ExpenditureType)
admin.site.register(Expenditure)
admin.site.register(IncomeSource)
admin.site.register(Income)
