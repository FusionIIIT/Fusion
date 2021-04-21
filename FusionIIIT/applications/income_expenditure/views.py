from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import (ExpenditureType, Expenditure, IncomeSource, Income, FixedAttributes, BalanceSheet)
import django. utils. timezone as timezone
from django.db.models import Sum

from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from django.core.files import File

from django.http import HttpResponse

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import io
import urllib, base64
from django.db.models import Min

fixed_attributes_list = ['Corpus Fund','Endowment Funds','Liabilities and Provisions','Fixed Assets','Tangible Assets','Intangible Assets','Capital Work-In-Progress','Investments','Loans and Deposits']


def main_page(request):
	
	plt.plot(range(10))
	fig = plt.gcf()
	buf = io.BytesIO()
	fig.savefig(buf,format='png')
	buf.seek(0)
	string = base64.b64encode(buf.read())
	uri = urllib.parse.quote(string)



	pres_date = timezone.now()
	fin_years = []
	if len(Income.objects.all()):
		min_date_ob = Income.objects.all().aggregate(Min('date_added'))
	

		pres_year,min_year = None,None
		if min_date_ob['date_added__min'].year == pres_date.year and min_date_ob['date_added__min'].month < 4 :
			pres_year = pres_date.year + 1
			min_year  = pres_date.year - 1
		elif min_date_ob['date_added__min'].year == pres_date.year and min_date_ob['date_added__min'].month >= 4:
			pres_year = pres_date.year + 1
			min_year = pres_date.year
		else:
			pres_year = pres_date.year + 1
			if min_date_ob['date_added__min'].month < 4 :
				min_year = min_date_ob['date_added__min'].year - 1
			else:
				min_year = min_date_ob['date_added__min'].year




		for fin_year in range(pres_year,min_year,-1):
			year = str(fin_year)+'-'+str(fin_year-1)
			fin_years.append(year)


	  

	temp = Income.objects.filter(date_added__year = 2021)
	result = (temp
		.values('source')
		.annotate(amount=Sum('amount'))
		.order_by('-amount')
		)
	for each in result:
		each['source'] = IncomeSource.objects.get(id=each['source']).income_source
	


	income_history = Income.objects.all()
	income_history = income_history[::-1]

	expenditure_history = Expenditure.objects.all()
	expenditure_history = expenditure_history[::-1]

	fixed_attributes = FixedAttributes.objects.all()

	add_income_source()
	add_expenditure_type()


	income_sources = IncomeSource.objects.all()
	expenditure_types = ExpenditureType.objects.all()
	
	
	current_financial_year_ob = timezone.now()
	month = str(current_financial_year_ob.month)
	month = '0' + month if len(month) == 1 else month
	day = str(current_financial_year_ob.day)
	day = '0' + month if len(day) == 1 else day 
	if current_financial_year_ob.month < 4 :
		 
		max_date = str(current_financial_year_ob.year)+'-'+month+'-'+day
		min_date = str(current_financial_year_ob.year - 1)+'-04-01'
	else:
		max_date = str(current_financial_year_ob.year)+'-'+month+'-'+day
		min_date = str(current_financial_year_ob.year)+'-04-01'


	if len(fixed_attributes) == 0:
		for i in fixed_attributes_list:
			entry = FixedAttributes(attribute=i)
			entry.save()
		fixed_attributes = FixedAttributes.objects.all()


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
					'data':uri,
					'fixedDetails':fixed_attributes,
					'min_date':min_date,
					'max1_date':max_date,

				})


#view to add income
def add_income(request):
	if(request.method == 'POST'):
		source = request.POST.get('income_source')
		source = IncomeSource.objects.filter(id=source).first()

		amount = request.POST.get('amount')
		date = request.POST.get('date_recieved')
		receipt = request.POST.get('income_receipt')
		remarks = request.POST.get('remarks')

		new_i = Income(
						source = source,
						amount = amount,
						date_added = date,
						receipt = receipt,
						remarks = remarks
						)
		new_i.save()
	return redirect('main-page')

def add_expenditure(request):
	if(request.method == 'POST'):
		spent_on = request.POST.get('spent_on')
		spent_on = ExpenditureType.objects.filter(id=spent_on).first()

		amount = request.POST.get('amount')
		date = request.POST.get('date_spent')
		receipt = request.POST.get('expenditure_receipt')
		remarks = request.POST.get('remarks')

		new_e = Expenditure(
						spent_on = spent_on,
						amount = amount,
						date_added = date,
						expenditure_receipt = receipt,
						remarks = remarks,
						)
		new_e.save()
	return redirect('main-page')




def add_income_source():
	income_sources = ['Academic Reciepts','Grants / Subsidies','Income From Investment','Interest Earned','Other Income','Prior Period Income']
	if len(IncomeSource.objects.all()):
		return
	else:
		for i in income_sources:
			new_source = IncomeSource(income_source = i,)
			new_source.save()

def add_expenditure_type():
	expenditure_types = ['Staff Payments & Benefits','Establishment Expenses','Academic Expenses','Administrative and General Expenses','Transportation Expenses','Repairs & Maintainance','Other Expenses','Prior Perios Expenses']
	if len(ExpenditureType.objects.all()):
		return
	else:
		for i in expenditure_types:
			new_type = ExpenditureType(expenditure_type = i,)
			new_type.save()

def updateFixedValues(request):
	if(request.method == 'POST'):
		for i in fixed_attributes_list:
			update_ob = FixedAttributes.objects.get(attribute=i)
			up_val = request.POST.get(i)
			update_ob.value = up_val
			update_ob.save()

	return redirect('main-page') 



def del_expenditure(request):
	if(request.method == 'POST'):
		ex_id = request.POST.get('id')
		Expenditure.objects.get(id=ex_id).delete()

	return redirect('main-page')

def del_income(request):
	if(request.method == 'POST'):
		in_id = request.POST.get('id')
		Income.objects.get(id=in_id).delete()

	return redirect('main-page')

def balanceSheet_table():
	fixed_attributes = FixedAttributes.objects.all()
	 
	pdf = render_to_pdf('incomeExpenditure/balanceSheet_pdf.html',{'fixedDetails':fixed_attributes,})
	curr_year = timezone.now().date().year
	fin_year = str(curr_year-1)+'-'+str(curr_year) if timezone.now().date().month < 4 else str(curr_year)+'-'+str(curr_year+1)
	
	if len(BalanceSheet.objects.filter(date_added=fin_year)):
		update_balanceSheet = BalanceSheet.objects.get(date_added=fin_year)
		update_balanceSheet.balanceSheet = File(BytesIO(pdf.content))
		update_balanceSheet.save()

	else:  
		new = BalanceSheet(
			balanceSheet = File(BytesIO(pdf.content)),
			date_added=fin_year,

		)
		new.save()
	
	


def balanceSheet(request):
	#fixed_attributes = FixedAttributes.objects.all()
	
	#pdf = render_to_pdf('incomeExpenditure/balanceSheet_pdf.html',{'fixedDetails':fixed_attributes,})
	#curr_year = timezone.now().date().year
	
	 
	
	#if pdf:
	#	response = HttpResponse(pdf,content_type='application/pdf')
	#	response['Content-Disposition'] = 'attachment; filename=BalanceSheet.pdf'
		
	#	return response
	#return HttpResponse('PDF could not be generated')

	if request.method =='POST' :
		fin_year = request.POST.get('fin_year')
		balance_sheet_ob = BalanceSheet.objects.filter(date_added=fin_year)
		response = HttpResponse(pdf,content_type='application/pdf')


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None








