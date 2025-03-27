
from django.http import (Http404, HttpResponse, HttpResponseNotFound,
                         HttpResponseRedirect)
from django.shortcuts import render, reverse

from django.contrib import messages

from applications.globals.models import HoldsDesignation, Designation

from .models import Bank, Company, Payments, Paymentscheme, Receipts

from django.views.generic import View

from .render import Render

from datetime import datetime

import calendar

from django.contrib.auth.decorators import login_required
from Fusion.settings.common import LOGIN_URL, LOGIN_REDIRECT_URL


# making login mandatory to access this view
@login_required(login_url=LOGIN_URL)
def financeModule(request):
    """
    This function verifies the designation of the employee whether he/she is in the accounts department or not and if yes on the basis of designation he/she
    is redirected to the corresponding page

    @param:
    request - designation of the logged in user

    @variables:
    context - is used for pasing the information from the login page to the corresponding designated html page
    b - object of the context
    """

    context = {
    }
    k = HoldsDesignation.objects.select_related().filter(working=request.user)
    flag = 0
    for z in k:
        if(str(z.designation) == 'dealing assistant'):
            flag = 1
            b = Paymentscheme.objects.filter(view=True, senior_verify=False)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModuleds.html", context)

        if (str(z.designation) == 'adminstrator'):
            flag = 1
            return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html", context)

        if (str(z.designation) == 'sr dealing assitant'):
            flag = 1
            b = Paymentscheme.objects.filter(
                senior_verify=True, view=True, ass_registrar_verify=False)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulesrda.html", context)

        if (str(z.designation) == 'asst. registrar fa'):
            flag = 1
            b = Paymentscheme.objects.filter(
                ass_registrar_verify=True, view=True, ass_registrar_aud_verify=False)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

        if (str(z.designation) == 'asst. registrar aud'):
            flag = 1
            b = Paymentscheme.objects.filter(
                ass_registrar_aud_verify=True, view=True, registrar_director_verify=False)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)

        if (str(z.designation) == 'Registrar'):
            flag = 1
            b = Paymentscheme.objects.filter(
                registrar_director_verify=True, view=True, )
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

        if (str(z.designation) == 'Director'):
            flag = 1
            b = Paymentscheme.objects.filter(
                registrar_director_verify=True, view=True)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    if(flag == 0):
        return render(request, "financeAndAccountsModule/employee.html", context)


# making login mandatory to access this view
@login_required(login_url=LOGIN_URL)
def previewing(request):
    """
    This function allows the dealing assistant to access the Payment Scheme model to view the payroll of the individual employees

    @param
    Payment scheme model form the model.py is previewed for the creation of the payroll

    @variables
    Basic details of the employee with all the salary components are previewed in this function
    """
    k = HoldsDesignation.objects.select_related().filter(working=request.user)

    flag = 0
    for z in k:
        if(str(z.designation) == 'dealing assistant'):
            flag = 1
            month = request.POST.get("month")
            year = request.POST.get("number1")
            pf = request.POST.get("number2")
            name = request.POST.get("name")
            designation = request.POST.get("designation")
            pay = request.POST.get("number3")
            gr_pay = request.POST.get("number4")
            da = request.POST.get("number5")
            ta = request.POST.get("number6")
            hra = request.POST.get("number7")
            fpa = request.POST.get("number8")
            special_allow = request.POST.get("number9")
            nps = request.POST.get("number10")
            gpf = request.POST.get("number11")
            income_tax = request.POST.get("number12")
            p_tax = request.POST.get("number13")
            gslis = request.POST.get("number14")
            gis = request.POST.get("number15")
            license_fee = request.POST.get("number16")
            electricity_charges = request.POST.get("number17")
            others = request.POST.get("number18")
            gr_reduction = int(nps) + int(gpf) + int(income_tax) + int(p_tax) + int(
                gslis) + int(gis) + int(license_fee) + int(electricity_charges) + int(others)
            income = int(pay) + int(gr_pay) + int(da) + int(ta) + \
                int(hra) + int(fpa) + int(special_allow)
            net_payment = (income - gr_reduction)

            a = Paymentscheme(month=month, year=year, pf=pf, name=name, designation=designation, pay=pay, gr_pay=gr_pay, da=da, ta=ta, hra=hra, fpa=fpa, special_allow=special_allow, nps=nps, gpf=gpf,
                              income_tax=income_tax, p_tax=p_tax, gslis=gslis, gis=gis, license_fee=license_fee, electricity_charges=electricity_charges, others=others, gr_reduction=gr_reduction, net_payment=net_payment)
            a.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModuleds.html", context)
        # if (str(z.designation) == 'adminstrator'):
        #     flag = 1
        #     return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html", context)

        if (str(z.designation) == 'sr dealing assitant'):
            flag = 1
            b = Paymentscheme.objects.filter(
                senior_verify=True, view=True, ass_registrar_verify=False)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulesrda.html", context)

        if (str(z.designation) == 'asst. registrar fa'):
            flag = 1
            b = Paymentscheme.objects.filter(
                ass_registrar_verify=True, view=True, ass_registrar_aud_verify=False)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

        if (str(z.designation) == 'asst. registrar aud'):
            flag = 1
            b = Paymentscheme.objects.filter(
                ass_registrar_aud_verify=True, view=True, registrar_director_verify=False)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)

        if (str(z.designation) == 'Registrar'):
            flag = 1
            b = Paymentscheme.objects.filter(
                registrar_director_verify=True, view=True)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

        if (str(z.designation) == 'director'):
            flag = 1
            b = Paymentscheme.objects.filter(
                registrar_director_verify=True, view=True)
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    # if(flag == 0):
    #     return render(request, "financeAndAccountsModule/employee.html", context)


# making login mandatory to access this view
@login_required(login_url=LOGIN_URL)
def verifying(request):
    """
    This function verification of the salary slips starting from the range of the dealing assistant to sr. dealing assistant to asst. registrar FA to
    asst. registrar aud to registrar/director

    @param
    request - trivial
officeOfRegistrar
    @variables
    a - object of the verifying method
    id - primary key of the payment scheme model
    """
    k = HoldsDesignation.objects.select_related().filter(working=request.user)

    for z in k:
        if request.method == "POST":
            if(str(z.designation) == 'dealing assistant'):
                a = request.POST.getlist('box')
                pay_scheme = []
                for i in range(len(a)):
                    if "verify" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.senior_verify = True
                        pay_scheme.append(p)

                    if "delete" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.senior_verify = False
                        pay_scheme.append(p)
                Paymentscheme.objects.bulk_update(
                    pay_scheme, ['senior_verify'])

            if(str(z.designation) == 'sr dealing assitant'):
                a = request.POST.getlist('box')
                sr_pay_scheme = []
                for i in range(len(a)):
                    if "verify" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.ass_registrar_verify = True
                        sr_pay_scheme.append(p)

                    if "delete" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.senior_verify = False
                        sr_pay_scheme.append(p)
                Paymentscheme.objects.bulk_update(
                    sr_pay_scheme, ['senior_verify', 'ass_registrar_verify'])

            if(str(z.designation) == 'asst. registrar fa'):
                a = request.POST.getlist('box')
                asst_pay_scheme = []
                for i in range(len(a)):
                    if "verify" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.ass_registrar_aud_verify = True
                        asst_pay_scheme.append(p)

                    if "delete" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.ass_registrar_verify = False
                        asst_pay_scheme.append(p)
                Paymentscheme.objects.bulk_update(
                    asst_pay_scheme, ['ass_registrar_verify', 'ass_registrar_aud_verify'])

            if(str(z.designation) == 'asst. registrar aud'):
                a = request.POST.getlist('box')
                aud_pay_scheme = []
                for i in range(len(a)):
                    if "verify" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.registrar_director_verify = True
                        aud_pay_scheme.append(p)

                    if "delete" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.ass_registrar_aud_verify = False
                        aud_pay_scheme.append(p)
                Paymentscheme.objects.bulk_update(
                    aud_pay_scheme, ['registrar_director_verify', 'ass_registrar_aud_verify'])

            if(str(z.designation) == 'Registrar'):
                a = request.POST.getlist('box')
                reg_pay_scheme = []
                for i in range(len(a)):
                    if "verify" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.runpayroll = True
                        p.view = False
                        reg_pay_scheme.append(p)

                    if "delete" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.registrar_director_verify = False
                        p.view = True
                        reg_pay_scheme.append(p)
                Paymentscheme.objects.bulk_update(
                    reg_pay_scheme, ['runpayroll', 'view', 'registrar_director_verify'])

            if(str(z.designation) == 'director'):
                a = request.POST.getlist('box')
                dir_pay_scheme = []
                for i in range(len(a)):
                    if "verify" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.runpayroll = True
                        p.view = False
                        dir_pay_scheme.append(p)

                    if "delete" in request.POST:
                        p = Paymentscheme.objects.get(id=a[i])
                        p.registrar_director_verify = False
                        p.view = True
                        dir_pay_scheme.append(p)
                Paymentscheme.objects.bulk_update(
                    dir_pay_scheme, ['view', 'runpayroll', 'registrar_director_verify'])

    return HttpResponseRedirect("/finance/finance/")


# making login mandatory to access this view
@login_required(login_url=LOGIN_URL)
def previous(request):
    """
        This method is used to view the already executed payroll run the registrar, and this method will take the input of the month and year which generates
        the entire payments of the employee of particular month and year

        @param
        request - trivial

        @variables
        a,b - these are taken as inout variables of month and year respectively for the display of the corresponding month's payments
    """
    k = HoldsDesignation.objects.select_related().filter(working=request.user)

    for z in k:
        if request.method == "POST":
            if(str(z.designation) == 'dealing assistant'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')

                c = Paymentscheme.objects.filter(
                    month=a, year=b, runpayroll=True)
                context = {
                    'c': c,

                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModuleds.html", context)

            if(str(z.designation) == 'sr dealing assitant'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')

                c = Paymentscheme.objects.filter(
                    month=a, year=b, runpayroll=True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModulesrda.html", context)

            if(str(z.designation) == 'asst. registrar fa'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')

                c = Paymentscheme.objects.filter(
                    month=a, year=b, runpayroll=True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

            if(str(z.designation) == 'asst. registrar aud'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')

                c = Paymentscheme.objects.filter(
                    month=a, year=b, runpayroll=True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)

            if(str(z.designation) == 'Registrar'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')

                c = Paymentscheme.objects.filter(
                    month=a, year=b, runpayroll=True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

            if(str(z.designation) == 'director'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')

                c = Paymentscheme.objects.filter(
                    month=a, year=b, runpayroll=True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    return HttpResponseRedirect("/finance/finance/")

# making login mandatory to access this view


@login_required(login_url=LOGIN_URL)
def createPayments(request):
    """
        This method is used to create a new payement transaction by the Assistant Registrar(fa), Registrar, Assistant Registrar(aud).

        @param
        request - trivial

        @variables
        Basic details of a new payement transaction.
    """
    k = HoldsDesignation.objects.select_related().filter(working=request.user)

    for z in k:
        if(str(z.designation) == "asst. registrar fa"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Payments(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

        if(str(z.designation) == "asst. registrar aud"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Payments(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearaud.html", context)

        if(str(z.designation) == "Registrar"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Payments(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

        if(str(z.designation) == "director"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Payments(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

# Function to get month number
# making login mandatory to access this view


@login_required(login_url=LOGIN_URL)
def getMonth(i):
    month = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12
    }

    return month.get(i, -1)


# making login mandatory to access this view
@login_required(login_url=LOGIN_URL)
def previousPayments(request):
    """
        This method is used to view the already created payement transaction, and this method will take the input of the month and year which generates
        the entire payments of particular month and year, made by the concerned authorities.

        @param
        request - trivial

        @variables
        a,b - these are taken as inout variables of month and year respectively for the display of the corresponding month's payments.
    """
    k = HoldsDesignation.objects.select_related().filter(working=request.user)

    for z in k:
        if request.method == "POST":
            if(str(z.designation) == 'asst. registrar fa'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Payments.objects.filter(Date__month=month_no, Date__year=b)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

            if(str(z.designation) == 'asst. registrar aud'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Payments.objects.filter(Date__month=month_no, Date__year=b)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)

            if(str(z.designation) == 'Registrar'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Payments.objects.filter(Date__month=month_no, Date__year=b)

                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

            if(str(z.designation) == 'director'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Payments.objects.filter(Date__month=month_no, Date__year=b)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    return HttpResponseRedirect("/finance/finance/")

# making login mandatory to access this view


@login_required(login_url=LOGIN_URL)
def createReceipts(request):
    """
        This method is used to create a receipt of a new transaction by the Assistant Registrar(fa), Registrar, Assistant Registrar(aud).

        @param
        request - trivial

        @variables
        Basic details of a new payement transaction for generating receipts.
    """
    k = HoldsDesignation.objects.select_related().filter(working=request.user)

    for z in k:
        if(str(z.designation) == "asst. registrar fa"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Receipts(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

        if(str(z.designation) == "asst. registrar aud"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Receipts(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearaud.html", context)

        if(str(z.designation) == "Registrar"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Receipts(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

        if(str(z.designation) == "director"):
            t_id = request.POST.get("t_id")
            toWhom = request.POST.get("toWhom")
            fromWhom = request.POST.get("fromWhom")
            purpose = request.POST.get("purpose")
            date = request.POST.get("date")

            p = Receipts(TransactionId=t_id, ToWhom=toWhom,
                         FromWhom=fromWhom, Purpose=purpose, Date=date)
            p.save()
            context = {
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

# making login mandatory to access this view


@login_required(login_url=LOGIN_URL)
def previousReceipts(request):
    """
        This method is used to view Receipts of already created payement transaction, and this method will take the input of the month and year which generates
        the entire payments of particular month and year, made by the concerned authorities.

        @param
        request - trivial

        @variables
        a,b - these are taken as inout variables of month and year respectively for the display of the corresponding month's payment recei.
    """
    k = HoldsDesignation.objects.select_related().filter(working=request.user)

    for z in k:
        if request.method == "POST":
            if(str(z.designation) == 'asst. registrar fa'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Receipts.objects.filter(Date__month=month_no, Date__year=b)
                context = {
                    'x': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

            if(str(z.designation) == 'asst. registrar aud'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Receipts.objects.filter(Date__month=month_no, Date__year=b)
                context = {
                    'x': c
                }
                return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)

            if(str(z.designation) == 'Registrar'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Receipts.objects.filter(Date__month=month_no, Date__year=b)
                context = {
                    'x': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

            if(str(z.designation) == 'director'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                month_no = getMonth(a)

                c = Receipts.objects.filter(Date__month=month_no, Date__year=b)
                context = {
                    'x': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    return HttpResponseRedirect("/finance/finance/")

# making login mandatory to access this view


@login_required(login_url=LOGIN_URL)
def createBank(request):
    """
        This method is used to create a new Bank Branch by the Administrator.

        @param
        request - trivial

        @variables
        Basic details of a new bank Branch.
    """
    k = HoldsDesignation.objects.select_related().filter(
        working=request.user, designation=Designation.objects.get(name='adminstrator'))

    acc_no = request.POST.get("acc_no")
    bank_Name = request.POST.get("bank_name")
    IFSC_code = request.POST.get("IFSC_code")
    branch = request.POST.get("branch")

    p = Bank(Account_no=acc_no, Bank_Name=bank_Name,
             IFSC_Code=IFSC_code, Branch_Name=branch)
    p.save()
    context = {
    }
    return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html", context)

# making login mandatory to access this view


@login_required(login_url=LOGIN_URL)
def createCompany(request):
    """
        This method is used to create a new Company by the Administrator.

        @param
        request - trivial

        @variables
        Basic details of a new Company.
    """
    k = HoldsDesignation.objects.select_related().filter(
        working=request.user, designation=Designation.objects.get(name='adminstrator'))

    c_name = request.POST.get("c_name")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date") or None
    description = request.POST.get("description")
    status = request.POST.get("status")

    p = Company(Company_Name=c_name, Start_Date=start_date,
                End_Date=end_date, Description=description, Status=status)
    p.save()
    context = {
    }
    return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html", context)

# def alterBank(request):
#     """
#         This method is used to update the details of Bank Branch by the Administrator.

#         @param
#         request - trivial

#         @variables
#         Basic details of a new bank Branch.
#     """
#     k = HoldsDesignation.objects.filter(working = request.user, designation = Designation.objects.get(name = 'adminstrator'))

#     acc_no = request.POST.get("acc_no")
#     bank_Name = request.POST.get("bank_name")
#     IFSC_code = request.POST.get("IFSC_code")
#     branch = request.POST.get("branch")

#     if request.method == "POST" :
#         a = request.POST.getlist('box')
#         print(a)
#         for i in range(len(a)) :
#             if "update" in request.POST :
#                 p = Bank.objects.get(bank_id = a[i])
#                 if(p.Account_no == acc_no and p.Bank_Name == bank_Name):
#                     p.Account_no = acc_no
#                     p.Bank_Name = bank_Name
#                     p.IFSC_Code = IFSC_code
#                     p.Branch = branch
#                     p.save()
#                 else:
#                     messeges.success(request, "Please Add the curresponding bank first!")
#     context = {
#     }
#     return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html")

# def alterCompany(request):
#     """
#         This method is used to update the details of Bank Branch by the Administrator.

#         @param
#         request - trivial

#         @variables
#         Basic details of a new bank Branch.
#     """
#     k = HoldsDesignation.objects.filter(working = request.user, designation = Designation.objects.get(name = 'adminstrator'))

#     c_name = request.POST.get("c_name")
#     start_date = request.POST.get("start_date")
#     end_date = request.POST.get("end_date")
#     description = request.POST.get("description")
#     status = request.POST.get("status")

#     a = request.POST.getlist('box')
#     for i in range(len(a)) :
#         if "update" in request.POST :
#             p = Company.objects.get(id = a[i])
#             p.Company_Name = c_name
#             p.Start_Date = start_date
#             p.End_Date = end_date
#             p.Description = description
#             p.Status = status

#             p.save()

#     context = {
#     }
#     return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html")

# making login mandatory to access this view


@login_required(login_url=LOGIN_URL)
def printSalary(request):
    """
      This method is used to print the salary details of an employee by the Administrator.

      @param
      request - trivial

      @variables
      Basic details of an employee's salary including basic pay, ta, da, hra, nps etc.

    """

    k = HoldsDesignation.objects.select_related().filter(
        working=request.user, designation=Designation.objects.get(name='adminstrator'))

    month = request.POST.get("month")
    year = request.POST.get("year")

    c = Paymentscheme.objects.filter(month=month, year=year)
    context = {
        'c': c,
    }

    return Render.render('financeAndAccountsModule/payroll_content4.html', context)
