from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import (ExpenditureType, Expenditure, IncomeSource, Income)

# Create your views here.

def main_page(request):
	income_history = Income.objects.all()
	income_sources = IncomeSource.objects.all()
	return render(
				request,
				'../templates/incomeExpenditure/ie.html',
				{
					'income_sources':income_sources,
					'income_history':income_history,
				})

	
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
	else:
	return redirect('main-page')



