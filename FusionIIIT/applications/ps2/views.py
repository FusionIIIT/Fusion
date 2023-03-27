from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from .models import StockEntry
from ..globals.models import ExtraInfo, User, HoldsDesignation

# Create your views here.
def ps2(request):
    current_user = get_object_or_404(User, username=request.user.username)
    extraInfo = ExtraInfo.objects.get(user=current_user)
    if(extraInfo.user_type=="student"):
        return HttpResponseRedirect('/')

    user_department = extraInfo.department.name

    stocks = StockEntry.objects.all().filter(head_of_asset=user_department)

    if request.user.username == 'acadadmin':
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
        stock_no = request.POST.get('stock_no')
        name_of_particulars = request.POST.get('name_of_particulars')
        inventory_no = request.POST.get('inventory_no')
        quantity = request.POST.get('quantity')
        rate = request.POST.get('rate')
        amount = request.POST.get('amount')
        supplier_name = request.POST.get('supplier_name')
        bill_no = request.POST.get('bill_no')
        buy_date = request.POST.get('buy_date')
        issued_date = request.POST.get('issued_date')
        head_of_asset = request.POST.get('head_of_asset')
        section = request.POST.get('section')
        floor = request.POST.get('floor')
        receiver_name = request.POST.get('receiver_name')
        
        StockEntry.objects.create(
            stock_no=stock_no,
            name_of_particulars=name_of_particulars,
            inventory_no=inventory_no,
            quantity=quantity,
            rate=rate,
            amount=amount,
            supplier_name=supplier_name,
            bill_no=bill_no,
            buy_date=buy_date,
            issued_date=issued_date,
            head_of_asset=head_of_asset,
            section=section,
            floor=floor,
            receiver_name=receiver_name,
        )
        return HttpResponseRedirect('/purchase-and-store2/')

    return render(request, "ps2/addstock.html")
