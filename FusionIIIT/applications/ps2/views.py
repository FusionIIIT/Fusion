from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
import datetime as dd

from .models import StockEntry, StockAdmin ,TransferEntry
from ..globals.models import ExtraInfo, User

# Create your views here.
def ps2(request):
    sel = request.GET.get("dep")
    
    current_user = get_object_or_404(User, username=request.user.username)
    extraInfo = ExtraInfo.objects.get(user=current_user)
    if(extraInfo.user_type=="student"):
        return HttpResponseRedirect('/')

    stock_admin = StockAdmin.objects.filter(user=current_user)
    if not stock_admin:
        return HttpResponseRedirect('/')

    stock_admin_department =[]
    stock_admin_department.append(stock_admin.first().department)

    stocks = StockEntry.objects.all().filter(head_of_asset=stock_admin_department)

    if current_user.username == 'acadadmin':
        if sel:
            if sel != 'Global': 
                stocks = StockEntry.objects.all().filter(head_of_asset=sel)
            else :
                stocks = StockEntry.objects.all()
        else :
            stocks = StockEntry.objects.all()


        stock_admin = StockAdmin.objects.all()
        stock_ad = set()
        for i in stock_admin:
            stock_ad.add(i.department)      
        
        context = {
            'stocks': stocks,
            'department': stock_ad,
        }            
        return render(request, "ps2/ps2.html", context)
    
    else :
        context = {
        'stocks': stocks,
        'department': stock_admin_department,    
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


def viewtransfers(request):
    current_user = get_object_or_404(User, username=request.user.username)
    extraInfo = ExtraInfo.objects.get(user=current_user)
    if(extraInfo.user_type=="student"):
        return HttpResponseRedirect('/')

    stock_admin = StockAdmin.objects.filter(user=current_user)
    if not stock_admin:
        return HttpResponseRedirect('/')

    stock_admin_department =[]
    stock_admin_department.append(stock_admin.first().department)

    stocks = TransferEntry.objects.all().filter(From_department=stock_admin_department,To_department=stock_admin_department)

    if current_user.username == 'acadadmin':
        stocks = TransferEntry.objects.all()
        stock_admin = set()   

        for i in stock_admin:
            stock_admin.add(i.department)      
        
        context = {
            'stocks': stocks,
            'department': stock_admin,
        }               
        return render(request, "ps2/viewtransfers.html", context)
    
    else :
        context = {
        'stocks': stocks,
        'department': stock_admin_department,    
        }
    return render(request, "ps2/viewtransfers.html", context)

def addtransfers(request):

    current_user = get_object_or_404(User, username=request.user.username)
    extraInfo = ExtraInfo.objects.get(user=current_user)
    if(extraInfo.user_type=="student"):
        return HttpResponseRedirect('/')
    
    if request.method == "POST":
        id = request.POST.get('id')
        to_department = request.POST.get('to_department')
        to_location = request.POST.get('to_location')
        Remark = request.POST.get('Remark')
        # if not stock_admin:
        #     return HttpResponseRedirect('/')

        item = StockEntry.objects.all().filter(id=id)

        stocks = TransferEntry(Item_id=id, From_department=item.first().head_of_asset, From_location=item.first().floor, To_department=to_department, To_location=to_location, Date=dd.date.today(), Remark=Remark)
        stocks.save()

        stock_admin = StockEntry.objects.get(id=id)
        stock_admin.head_of_asset = to_department
        stock_admin.floor = to_location
        stock_admin.save()


        return redirect('ps2:viewtransfers')

    context = {}
    return render(request, "ps2/addtransfers.html", context)