from django.db import models
from django.utils import timezone
from datetime import datetime


class ExpenditureType(models.Model):
	expenditure_type = models.CharField(max_length=100)

	def __str__(self):
		return self.expenditure_type

class ExpenditureSubType(models.Model):
	expenditure_sub_type = models.CharField(max_length=100)
	expenditure_type = models.ForeignKey(ExpenditureType, related_name="expenditure_category", on_delete=models.PROTECT)

	def __str__(self):
		return self.expenditure_sub_type


class Expenditure(models.Model):
	spent_on = models.ForeignKey(ExpenditureType, related_name="expenditureType", on_delete=models.PROTECT)
	sub_type = models.ForeignKey(ExpenditureSubType, related_name="expenditureSubType", on_delete=models.PROTECT)
	amount = models.IntegerField()
	date_added = models.DateField()
	remarks = models.CharField(max_length=100)
	expenditure_receipt = models.FileField( upload_to = 'iemodule/expenditure_receipts')

	def __str__(self):
		return str(self.amount)



class IncomeSource(models.Model):
	income_source = models.CharField(max_length=100)

	def __str__(self):
		return self.income_source


class IncomeSubType(models.Model):
	income_sub_type = models.CharField(max_length=100)
	income_type = models.ForeignKey(IncomeSource, related_name="income_category", on_delete=models.PROTECT)

	def __str__(self):
		return self.income_sub_type


class Income(models.Model):
	source = models.ForeignKey(IncomeSource, related_name="incomeSource", on_delete=models.PROTECT)
	sub_type = models.ForeignKey(IncomeSubType, related_name="incomeSubType", on_delete=models.PROTECT)
	amount = models.IntegerField()
	date_added = models.DateField()
	remarks = models.CharField(max_length=100, blank=True)
	receipt = models.FileField(blank=True, upload_to = 'iemodule/income_receipts')

	def __str__(self):
		return str(self.amount)

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

