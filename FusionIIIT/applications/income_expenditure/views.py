from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, request
from .models import (ExpenditureType, Expenditure, IncomeSource, Income, FixedAttributes, BalanceSheet)
import django. utils. timezone as timezone
from django.db.models import Sum
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from django.core.files import File

from django.db.models import Min,Max

fixed_attributes_list = ['Corpus Fund','Endowment Funds','Liabilities and Provisions','Fixed Assets','Tangible Assets','Intangible Assets','Capital Work-In-Progress','Investments','Loans and Deposits']

'''
    
            Parameters:
                    
					income_history (queryset) - queryset of income objects
					expenditure_history (queryset) - queryset of expenditure objects
					income_sources (queryset) - queryset of income_source objects
					expenditure_types (queryset) - queryset of expenditure type objects
					fixed_attributes (list) - list of fixed attributes
					inc_fin_years (list) - Contains years present in income table
                    exp_fin_years  (list) - Contains years present in expenditure table
                    mini_year  (int) - min_year of which data is present
                    maxi_year  (int) - max_year of which data is present
            
'''



def main_page(request):

	pres_date = timezone.now()
	fin_years = []
	inc_fin_years = []
	exp_fin_years = []
	
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
			year = str(fin_year-1)+'-'+str(fin_year)
			fin_years.append(year)

	if len(Income.objects.all()):
		
		min_date_in = Income.objects.all().aggregate(Min('date_added'))
		max_date_in = Income.objects.all().aggregate(Max('date_added'))
		mini_year = min_date_in['date_added__min'].year
		maxi_year = max_date_in['date_added__max'].year

		if min_date_in['date_added__min'].month < 4:
			mini_year-=1
		if max_date_in['date_added__max'].month < 4:
			maxi_year-=1

		for fin_year in range(maxi_year, mini_year-1, -1):
			inc_fin_years.append(fin_year)

	if len(Expenditure.objects.all()):
		
		min_date_exp = Expenditure.objects.all().aggregate(Min('date_added'))
		max_date_exp = Expenditure.objects.all().aggregate(Max('date_added'))
		mini_year = min_date_exp['date_added__min'].year
		maxi_year = max_date_exp['date_added__max'].year

		if min_date_exp['date_added__min'].month < 4:
			mini_year-=1
		if max_date_exp['date_added__max'].month < 4:
			maxi_year-=1

		for fin_year in range(maxi_year, mini_year-1, -1):
			exp_fin_years.append(fin_year)


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
    
	if(request.user.is_staff==True):
		return render(
				request,
				'../templates/incomeExpenditure/ie.html',
				{
					'income_sources':income_sources,
					'income_history':income_history,
					'expenditure_types':expenditure_types,
					'expenditure_history':expenditure_history,
					'fin_years':fin_years,
					'fixedDetails':fixed_attributes,
					'min_date':min_date,
					'max1_date':max_date,
					'inc_fin_years':inc_fin_years,
					'exp_fin_years':exp_fin_years,
				})
	else:
		return render(
				request,
				'../templates/incomeExpenditure/iesu.html',
				{
					'fin_years':fin_years,
					'min_date':min_date,
					'max1_date':max_date,
					'inc_fin_years':inc_fin_years,
					'exp_fin_years':exp_fin_years,
				})
	




'''
    to add new income
            Parameters:
                    source  (string) - From where the income is coming
                    amount (int) - contains amount received
                    date  (date) - date of income
                    receipt  (file) - contains receipt
                    remarks  (string) - remarks or detailed explanation.(if any)
            
'''




#view to add income
def add_income(request):
	if(request.method == 'POST' and request.user.is_staff==True):
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
		balanceSheet_table() 
	return redirect('main-page')




'''
    to add a new expense
            Parameters:
                    spent_on  (string) - Contains on whic the expenditure is made
                    amount (int) - Contains the amount spent
                    date  (date) - date of expense
                    receipt  (file) - contains receipt
                    remarks  (string) - Remarks or detailed explanation.
            
'''

def add_expenditure(request):
	if(request.method == 'POST' and request.user.is_staff==True):
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
		balanceSheet_table()
	return redirect('main-page')


'''
	used to maintain fixed list of income sources
            Parameters:
                    income_sources (list) - list of income sources
'''


def add_income_source():
	income_sources = ['Academic Reciepts','Grants / Subsidies','Income From Investment','Interest Earned','Other Income','Prior Period Income']
	if len(IncomeSource.objects.all()):
		return
	else:
		for i in income_sources:
			new_source = IncomeSource(income_source = i,)
			new_source.save()

'''
	used to maintain fixed list of expenditure types
        Parameters:
                    expenditure_types (list) - list of expenditure types
'''

def add_expenditure_type():
	expenditure_types = ['Staff Payments & Benefits','Establishment Expenses','Academic Expenses','Administrative and General Expenses','Transportation Expenses','Repairs & Maintainance','Other Expenses','Prior Perios Expenses']
	if len(ExpenditureType.objects.all()):
		return
	else:
		for i in expenditure_types:
			new_type = ExpenditureType(expenditure_type = i,)
			new_type.save()

def updateFixedValues(request):
	if(request.method == 'POST' and request.user.is_staff==True):
		for i in fixed_attributes_list:
			update_ob = FixedAttributes.objects.get(attribute=i)
			up_val = request.POST.get(i)
			update_ob.value = up_val
			update_ob.save()
			balanceSheet_table()

	return redirect('main-page')

'''
	delete's an expense
        Parameters:
			id : (int) - id of the expense to be deleted
'''


def del_expenditure(request):
	if(request.method == 'POST' and request.user.is_staff==True):
		ex_id = request.POST.get('id')
		Expenditure.objects.get(id=ex_id).delete()
		balanceSheet_table()

	return redirect('main-page')


'''
	delete's an income
        Parameters:
			id : (int) - id of the income to be deleted
'''


def del_income(request):
	if(request.method == 'POST' and request.user.is_staff==True):
		in_id = request.POST.get('id')
		Income.objects.get(id=in_id).delete()
		balanceSheet_table()

	return redirect('main-page')


'''
	download's balancesheet
        Parameters:
			fixed_attributes : (list) - contains list of fixed attributes
			income_dic : {dict} - contains the names and amount of each income source
			expenditure_dic : {dict} - contains the names and amount of each expenditure type
			incomeSum : {int} - total sum of income
			expenditureSum : {int} - total sum of expenses
			balance : {int} 
			filename : {string} - name of the balance sheet
'''



def balanceSheet_table():
	fixed_attributes = FixedAttributes.objects.all()


	income_type_ob = IncomeSource.objects.all()
	income_ob = Income.objects.all()
	result=(income_ob.values('source').annotate(amount=Sum('amount')).order_by('source'))
	income_dic={}
	for each in result:
		income_dic[IncomeSource.objects.get(id=each['source']).income_source]=each['amount']
	incomeSum = sum(income_dic.values())
	
	expenditure_type_ob = ExpenditureType.objects.all()
	expenditure_ob = Expenditure.objects.all()
	result=(expenditure_ob.values('spent_on').annotate(amount=Sum('amount')).order_by('spent_on'))
	expenditure_dic={}
	for each in result:
		expenditure_dic[ExpenditureType.objects.get(id=each['spent_on']).expenditure_type]=each['amount']
	expenditureSum=sum(expenditure_dic.values())


	balance = incomeSum - expenditureSum

    	


	 
	pdf = render_to_pdf('incomeExpenditure/balanceSheet_pdf.html',{'fixedDetails':fixed_attributes,'incomeDetails':income_dic,'incomeTypes':income_type_ob,'expenditureDetails':expenditure_dic,'expenditureTypes':expenditure_type_ob,'incomeSum':incomeSum,'expenditureSum':expenditureSum,'balance':balance,})
	
	curr_year = timezone.now().date().year
	fin_year = str(curr_year-1)+'-'+str(curr_year) if timezone.now().date().month < 4 else str(curr_year)+'-'+str(curr_year+1)
	filename = 'Balance_sheet{}.pdf'.format(fin_year)

	
	
	if len(BalanceSheet.objects.filter(date_added=fin_year)):
		update_balanceSheet = BalanceSheet.objects.get(date_added=fin_year)
		#update_balanceSheet.balanceSheet = File(BytesIO(pdf.content))
		#update_balanceSheet.save()
		update_balanceSheet.balanceSheet.save(filename,File(BytesIO(pdf.content)))

	else:  
		new = BalanceSheet(
			balanceSheet = File(BytesIO(pdf.content)),
			date_added=fin_year,

		)
		new.balanceSheet.save(filename,File(BytesIO(pdf.content)))
		#new.save()
	
	


def balanceSheet(request):
	



	if request.method =='POST' :
		fin_year = request.POST.get('fin_year')
		balance_sheet_ob = BalanceSheet.objects.get(date_added=fin_year)
		response = HttpResponse(balance_sheet_ob.balanceSheet,content_type='application/pdf')
		response['Content-Disposition'] = 'attachment; filename=BalanceSheet.pdf'
		return response


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

'''
	to view income stats
        Parameters:
			income_labels : (list) - contains the names of each income source
			income_data : {list} - stores the sum of each source 
			fin_year : {string} - contains financial year
			
'''


def view_income_stats(request):
	if(request.method == 'POST'):
		year = request.POST.get('year')

		start_date = year + "-04-01";
		end_date = str(int(year)+1) + "-03-31";

		fin_year = year + " - " + str(int(year)+1)
		temp = Income.objects.filter(date_added__range=[start_date, end_date])
		# temp = Income.objects.filter(date_added__year = 2021)
		result = (temp
			.values('source')
			.annotate(amount=Sum('amount'))
			.order_by('-amount')
			)
		income_labels = []
		income_data = []
		for each in result:
			each['source'] = IncomeSource.objects.get(id=each['source']).income_source
		for each in result:
			income_labels.append(each['source'])
			income_data.append(each['amount'])
		return render(
						request,
						'../templates/incomeExpenditure/viewIncomeStats.html',
						{
							'income_data':income_data,
							'income_labels':income_labels,
							'fin_year':fin_year,
						})

'''
	to view expenditure stats
        Parameters:
			expenditure_labels : (list) - contains the list of expenditure types
			expenditure_data : {list} - stores the sum of each type
			fin_year : {string} - contains the financial year
			
'''


def view_expenditure_stats(request):
	if(request.method == 'POST'):
		year = request.POST.get('year')

		start_date = year + "-04-01";
		end_date = str(int(year)+1) + "-03-31";

		fin_year = year + " - " + str(int(year)+1)
		temp = Expenditure.objects.filter(date_added__range=[start_date, end_date])
		# temp = Income.objects.filter(date_added__year = 2021)
		result = (temp
			.values('spent_on')
			.annotate(amount=Sum('amount'))
			.order_by('-amount')
			)
		expenditure_labels = []
		expenditure_data = []
		for each in result:
			each['spent_on'] = ExpenditureType.objects.get(id=each['spent_on']).expenditure_type
		for each in result:
			expenditure_labels.append(each['spent_on'])
			expenditure_data.append(each['amount'])
		return render(
						request,
						'../templates/incomeExpenditure/viewExpenditureStats.html',
						{
							'expenditure_data':expenditure_data,
							'expenditure_labels':expenditure_labels,
							'fin_year':fin_year,
						})
