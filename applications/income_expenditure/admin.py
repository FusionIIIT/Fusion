from django.contrib import admin



from .models import (ExpenditureType, Expenditure, IncomeSource, Income, FixedAttributes, BalanceSheet,otherExpense)

admin.site.register(ExpenditureType)
admin.site.register(Expenditure)
admin.site.register(IncomeSource)
admin.site.register(Income)
admin.site.register(FixedAttributes)
admin.site.register(BalanceSheet)
admin.site.register(otherExpense)
