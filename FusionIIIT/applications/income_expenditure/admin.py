from django.contrib import admin

<<<<<<< HEAD
from .models import (ExpenditureType, Expenditure, IncomeSource, Income)
=======
from .models import (ExpenditureType, Expenditure, IncomeSource, Income, FixedAttributes, BalanceSheet)
>>>>>>> 9b561901b48e4d2e343d71189149122b60d642b6

admin.site.register(ExpenditureType)
admin.site.register(Expenditure)
admin.site.register(IncomeSource)
admin.site.register(Income)
<<<<<<< HEAD
=======
admin.site.register(FixedAttributes)
admin.site.register(BalanceSheet)
>>>>>>> 9b561901b48e4d2e343d71189149122b60d642b6
