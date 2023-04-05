from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from .models import StockEntry, StockAdmin
from ..globals.models import ExtraInfo, User

# Create your views here.
def ps2(request):
    current_user = get_object_or_404(User, username=request.user.username)
    extraInfo = ExtraInfo.objects.get(user=current_user)
    if(extraInfo.user_type=="student"):
        return HttpResponseRedirect('/')

    stock_admin = StockAdmin.objects.filter(user=current_user)
    if not stock_admin:
        return HttpResponseRedirect('/')

    stock_admin_department =  stock_admin.first().department

    stocks = StockEntry.objects.all().filter(head_of_asset=stock_admin_department)

    if current_user.username == 'acadadmin':
        stocks = StockEntry.objects.all()
    
    context = {
        'stocks': stocks,
    }

    return render(request, "ps2/ps2.html", context)

def addstock(request):
    current_user = get_object_or_404(User, username=request.user.username)
    extraInfo = ExtraInfo.objects.get(user=current_user)
    if(extraInfo.user_type=="student"):
        return HttpResponseRedirect('/')
    
    if request.method == "POST":
        name_of_particulars = request.POST.get('name_of_particulars')
        inventory_no = request.POST.get('inventory_no')
        rate = request.POST.get('rate')
        amount = request.POST.get('amount')
        quantity = request.POST.get('quantity')
        supplier_name = request.POST.get('supplier_name')
        bill_no = request.POST.get('bill_no')
        buy_date = request.POST.get('buy_date')
        head_of_asset = request.POST.get('head_of_asset')
        issued_date = request.POST.get('issued_date') 
        section = request.POST.get('section')
        floor = request.POST.get('floor')
        receiver_name = request.POST.get('receiver_name')

        stock_admin = StockAdmin.objects.filter(user=current_user)
        if not stock_admin:
            return HttpResponseRedirect('/')
        
        if not head_of_asset:
            head_of_asset = stock_admin.first().department

        for i in range(int(quantity)):
            stock = StockEntry(name_of_particulars=name_of_particulars, inventory_no=inventory_no, rate=rate, amount=amount, supplier_name=supplier_name, bill_no=bill_no, buy_date=buy_date, issued_date=issued_date, head_of_asset=head_of_asset, section=section, floor=floor, receiver_name=receiver_name)
            stock.save()

        return HttpResponseRedirect('/purchase-and-store2/')
    
    context = {
        'global_admin': False 
    }

    if current_user.username == 'acadadmin':
        context['global_admin'] = True

    return render(request, "ps2/addstock.html", context)