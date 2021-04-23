from django.db import models
from django.utils import timezone
<<<<<<< HEAD
=======
from datetime import datetime
>>>>>>> 9b561901b48e4d2e343d71189149122b60d642b6


class ExpenditureType(models.Model):
	expenditure_type = models.CharField(max_length=100)
<<<<<<< HEAD
	
=======

>>>>>>> 9b561901b48e4d2e343d71189149122b60d642b6
	def __str__(self):
		return self.expenditure_type

class Expenditure(models.Model):
	spent_on = models.ForeignKey(ExpenditureType, related_name="expenditureType", on_delete=models.PROTECT)
	amount = models.IntegerField()
<<<<<<< HEAD
	date_added = models.DateTimeField(auto_now_add=True)
	granted_to = models.CharField(max_length=100)
=======
	date_added = models.DateField()
	remarks = models.CharField(max_length=100)
>>>>>>> 9b561901b48e4d2e343d71189149122b60d642b6
	expenditure_receipt = models.FileField( upload_to = 'iemodule/expenditure_receipts')

	def __str__(self):
		return str(self.amount)

class IncomeSource(models.Model):
	income_source = models.CharField(max_length=100)

	def __str__(self):
		return self.income_source

class Income(models.Model):
	source = models.ForeignKey(IncomeSource, related_name="incomeSource", on_delete=models.PROTECT)
	amount = models.IntegerField()
<<<<<<< HEAD
	source_account = models.CharField( max_length=100,null=True)
	date_added = models.DateTimeField(auto_now_add=True)
	granted_by = models.CharField(max_length=100, blank=True)
=======
	date_added = models.DateField()
	remarks = models.CharField(max_length=100, blank=True)
>>>>>>> 9b561901b48e4d2e343d71189149122b60d642b6
	receipt = models.FileField(blank=True, upload_to = 'iemodule/income_receipts')

	def __str__(self):
		return str(self.amount)
<<<<<<< HEAD
=======

class FixedAttributes(models.Model):
	attribute = models.CharField(max_length=100)
	value = models.IntegerField(default=0)

	def __str__(self):
		return str(self.value)

class BalanceSheet(models.Model):
	balanceSheet = models.FileField()
	date_added = models.CharField(max_length=10)

	def __str__(self):
		return str(self.date_added)

>>>>>>> 9b561901b48e4d2e343d71189149122b60d642b6
