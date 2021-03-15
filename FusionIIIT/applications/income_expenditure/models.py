from django.db import models
from django.utils import timezone


class ExpenditureType(models.Model):
	expenditure_type = models.TextField(max_length=100, blank=False)

	def __str__(self):
        return self.expenditure_type

class Expenditure(models.Model):
	spent_on = models.ForeignKey(ExpenditureType, related_name="expenditureType", on_delete=models.PROTECT)
	amount = models.IntegerField(null=False)
	date_added = models.DateTimeField(auto_now_add=True)
	granted_to = models.CharField(max_length=100, blank=False)
	expenditure_receipt = models.ImageField(blank=False, upload_to = 'iemodule/expenditure_receipts')

	def __str__(self):
        return str(self.amount)

class IncomeSource(models.Model):
	income_source = models.TextField(max_length=100, blank=False)

	def __str__(self):
        return self.income_source

class Income(models.Model):
	source = models.ForeignKey(IncomeSource, related_name="incomeSource", on_delete=models.PROTECT)
	amount = models.IntegerField(null=False)
	source_account = models.BigIntegerField(null=False)
	date_added = models.DateTimeField(auto_now_add=True)
	granted_by = models.CharField(max_length=100, blank=False)
	receipt = models.ImageField(blank=False, upload_to = 'iemodule/income_receipts')

	def __str__(self):
        return str(self.amount)
