from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import (ExpenditureType, Expenditure, IncomeSource, Income)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
# Create your views here.

def main_page(request):
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
	if(request.method == 'POST'):
		spent_on = request.POST.get('spent_on')
		spent_on = ExpenditureType.objects.filter(id=spent_on).first()

		amount = request.POST.get('amount')
		date = request.POST.get('date_spent')
		receipt = request.POST.get('expenditure_receipt')
		granted_to = request.POST.get('granted_to')

		new_e = Expenditure(
		 				spent_on = spent_on,
		 				amount = amount,
		 				date_added = date,
						granted_to = granted_to,
		 				expenditure_receipt = receipt,
		 				
		 				)
		new_e.save()
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

def balanceSheet(request):
	pdf = render_to_pdf('incomeExpenditure/balanceSheet_pdf.html')
	if pdf:
		response = HttpResponse(pdf,content_type='application/pdf')
		response['Content-Disposition'] = 'attachment; filename=BalanceSheet.pdf'
		return response
	return HttpResponse('PDF could not be generated')

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None