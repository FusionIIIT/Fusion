from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import (ExpenditureType, Expenditure, IncomeSource, Income)

# Create your views here.

def main_page(request):
	income_history = Income.objects.all()
	income_sources = IncomeSource.objects.all()
	expenditure_types = ExpenditureType.objects.all()
	return render(
				request,
				'../templates/incomeExpenditure/ie.html',
				{
					'income_sources':income_sources,
					'income_history':income_history,
					'expenditure_types':expenditure_types,
				})


#view to add income
def add_income(request):
	if(request.method == 'POST'):
		source = request.POST.get('income_source')
		source = IncomeSource.objects.filter(id=source).first()

		amount = request.POST.get('amount')
		date = request.POST.get('date_recieved')
		receipt = request.POST.get('income_receipt')
		granted_by = request.POST.get('granted_by')

		new_i = Income(
						source = source,
						amount = amount,
						date_added = date,
						receipt = receipt,
						granted_by = granted_by
						)
		new_i.save()
<<<<<<< HEAD
	return redirect('main-page')
=======
	else:
		return redirect('main-page')
>>>>>>> 25e9c4f7960a3062fb02464c7b56af79ce9ac1b9

def add_income_source(request):
	if(request.method == 'POST'):
		source = request.POST.get('income_source')
		new_i = IncomeSource(
						income_source = source,
						)
		new_i.save()
	return redirect('main-page')

def add_expenditure_type(request):
	if(request.method == 'POST'):
		e_type = request.POST.get('expenditure_type')
		new_e = ExpenditureType(
						expenditure_type = e_type,
						)
		new_e.save()
	return redirect('main-page')

def add_expenditure(request):
	# if(request.method == 'POST'):
		# source = request.POST.get('income_source')
		# source = IncomeSource.objects.filter(id=source).first()

		# amount = request.POST.get('amount')
		# date = request.POST.get('date_recieved')
		# receipt = request.POST.get('income_receipt')
		# granted_by = request.POST.get('granted_by')

		# new_i = Income(
		# 				source = source,
		# 				amount = amount,
		# 				date_added = date,
		# 				receipt = receipt,
		# 				granted_by = granted_by
		# 				)
		# new_i.save()
	return redirect('main-page')