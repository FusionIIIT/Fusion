from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import (ExpenditureType, Expenditure, IncomeSource, Income)
import django. utils. timezone as timezone
from django.db.models import Sum

# Create your views here.

def main_page(request):
	pres_year = timezone.now().year
	fin_years = []
	for fin_year in range(pres_year,2016,-1):
		fin_years.append(fin_year)

	# income_labels = []
	# income_data = []

	# income_details = {}

	# for year in fin_years:
	temp = Income.objects.filter(date_added__year = 2021)
	result = (temp
		.values('source')
		.annotate(amount=Sum('amount'))
		.order_by('-amount')
		)
	for each in result:
		each['source'] = IncomeSource.objects.get(id=each['source']).income_source
		# income_details[year] = result


	# income = Income.objects.order_by('-amount')[:5]
	# for each in income:
	#     income_labels.append(each.source.income_source)
	#     income_data.append(each.amount)


	income_history = Income.objects.all()
	income_sources = IncomeSource.objects.all()
	expenditure_types = ExpenditureType.objects.all()
	expenditure_history = Expenditure.objects.all()
	return render(
				request,
				'../templates/incomeExpenditure/ie.html',
				{
					'income_sources':income_sources,
					'income_history':income_history,
					'expenditure_types':expenditure_types,
					'expenditure_history':expenditure_history,
					'fin_years':fin_years,
					'income_details':result,
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
	return redirect('main-page')

def add_expenditure(request):
	if(request.method == 'POST'):
		spent_on = request.POST.get('spend_on')
		spent_on = ExpenditureType.objects.filter(id=spent_on).first()

		amount = request.POST.get('amount')
		date = request.POST.get('date_spent')
		receipt = request.POST.get('expenditure_receipt')
		granted_to = request.POST.get('granted_to')

		new_e = Expenditure(
						spent_on = spent_on,
						amount = amount,
						date_added = date,
						expenditure_receipt = receipt,
						granted_to = granted_to,
						)
		new_e.save()
	return redirect('main-page')

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

# def income_pie_chart(request):
#     income_labels = []
#     income_data = []

#     income = Income.objects.order_by('-amount')[:5]
#     for each in income:
#         income_labels.append(each.income_source)
#         income_data.append(each.amount)

#     return render(request, 'pie_chart.html', {
#         'income_labels': income_labels,
#         'income_data': income_data,
#     })