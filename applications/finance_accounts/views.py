import datetime

from django.http import (Http404, HttpResponse, HttpResponseNotFound,
                         HttpResponseRedirect)
from django.shortcuts import render, reverse

from applications.globals.models import HoldsDesignation

from .models import Bank, Company, Payments, Paymentscheme, Receipts


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
    print(request.user)
    k = HoldsDesignation.objects.filter(working = request.user)
    print(k)
    print("asdasd")
    flag = 0
    for z in k:
        print(str(z.designation))
        if(str(z.designation) == 'dealing assistant'):
            flag = 1
            b = Paymentscheme.objects.filter(view = True, senior_verify = False )
            context = {
                'b': b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModuleds.html", context)

        if (str(z.designation) == 'adminstrator'):
            flag = 1
            return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html", context)

        if (str(z.designation) == 'sr dealing assitant'):
            flag = 1
            b = Paymentscheme.objects.filter(senior_verify = True , view = True,ass_registrar_verify = False)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulesrda.html", context)

        if (str(z.designation) == 'asst.registrar fa'):
            flag = 1
            b = Paymentscheme.objects.filter(ass_registrar_verify = True , view = True , ass_registrar_aud_verify = False)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

        if (str(z.designation) == 'asst. registrar aud'):
            flag = 1
            b = Paymentscheme.objects.filter(ass_registrar_aud_verify = True , view = True , registrar_director_verify = False)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)

        if (str(z.designation) == 'Registrar'):
            flag = 1
            b = Paymentscheme.objects.filter(registrar_director_verify = True , view = True , )
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

        if (str(z.designation) == 'director'):
            flag = 1
            b = Paymentscheme.objects.filter(registrar_director_verify = True , view = True)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    if(flag == 0):
        return render(request, "financeAndAccountsModule/employee.html", context)


def previewing(request):
    """
    This function allows the dealing assistant to access the Payment Scheme model to view the payroll of the individual employees

    @param
    Payment scheme model form the model.py is previewed for the creation of the payroll

    @variables
    Basic details of the employee with all the salary components are previewed in this function
    """
    print(request.user)
    k = HoldsDesignation.objects.filter(working = request.user)
    print(k)
    print("asdasd")
    flag = 0
    for z in k:
        print(str(z.designation))
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

            a = Paymentscheme(month = month ,year = year , pf = pf ,name = name , designation = designation , pay = pay , gr_pay =  gr_pay ,da = da , ta = ta , hra = hra , fpa = fpa , special_allow = special_allow , nps = nps , gpf = gpf , income_tax = income_tax , p_tax = p_tax , gslis = gslis , gis = gis , license_fee = license_fee , electricity_charges = electricity_charges , others = others )
            a.save()
            context = {
            }
            return render(request ,"financeAndAccountsModule/financeAndAccountsModuleds.html",context)


        if (str(z.designation) == 'adminstrator'):
            flag = 1
            return render(request, "financeAndAccountsModule/financeAndAccountsModulead.html", context)

        if (str(z.designation) == 'sr dealing assitant'):
            flag = 1
            b = Paymentscheme.objects.filter(senior_verify = True , view = True,ass_registrar_verify = False)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulesrda.html", context)

        if (str(z.designation) == 'asst.registrar fa'):
            flag = 1
            b = Paymentscheme.objects.filter(ass_registrar_verify = True , view = True , ass_registrar_aud_verify = False)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)

        if (str(z.designation) == 'asst. registrar aud'):
            flag = 1
            b = Paymentscheme.objects.filter(ass_registrar_aud_verify = True , view = True , registrar_director_verify = False)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)

        if (str(z.designation) == 'Registrar'):
            flag = 1
            b = Paymentscheme.objects.filter(registrar_director_verify = True , view = True , )
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

        if (str(z.designation) == 'director'):
            flag = 1
            b = Paymentscheme.objects.filter(registrar_director_verify = True , view = True)
            context = {
                'b' : b
            }
            return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    if(flag == 0):
        return render(request, "financeAndAccountsModule/employee.html", context)





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
    k = HoldsDesignation.objects.filter(working = request.user)
    print(k)
    print("asdasd")
    flag = 0
    for z in k:
        if request.method == "POST" :
            if(str(z.designation) == 'dealing assistant'):
                a = request.POST.getlist('box')
                for i in range(len(a)) :
                    if "verify" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.senior_verify = True
                        p.save()


                    if "delete" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.senior_verify = False
                        p.delete()

            if(str(z.designation) == 'sr dealing assitant'):
                a = request.POST.getlist('box')
                for i in range(len(a)) :
                    if "verify" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.ass_registrar_verify = True
                        p.save()


                    if "delete" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.senior_verify = False
                        p.save()


            if(str(z.designation) == 'asst.registrar fa'):
                a = request.POST.getlist('box')
                for i in range(len(a)) :
                    if "verify" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.ass_registrar_aud_verify = True
                        p.save()


                    if "delete" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.ass_registrar_verify = False
                        p.save()

            if(str(z.designation) == 'asst. registrar aud'):
                a = request.POST.getlist('box')
                for i in range(len(a)) :
                    if "verify" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.registrar_director_verify = True
                        p.save()


                    if "delete" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.ass_registrar_aud_verify = False
                        p.save()

            if(str(z.designation) == 'Registrar'):
                a = request.POST.getlist('box')
                for i in range(len(a)) :
                    if "verify" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.runpayroll = True
                        p.view = False
                        p.save()


                    if "delete" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.registrar_director_verify = False
                        p.view = True
                        p.save()

            if(str(z.designation) == 'director'):
                a = request.POST.getlist('box')
                for i in range(len(a)) :
                    if "verify" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.runpayroll = True
                        p.view = False
                        p.save()


                    if "delete" in request.POST :
                        p = Paymentscheme.objects.get(id = a[i])
                        p.registrar_director_verify = False
                        p.view = True
                        p.save()

    return HttpResponseRedirect("/finance/finance/")



def previous(request) :
    """
        This method is used to view the already executed payroll run the registrar, and this method will take the input of the month and year which generates
        the entire payments of the employee of particular month and year

        @param
        request - trivial

        @variables
        a,b - these are taken as inout variables of month and year respectively for the display of the corresponding month's payments
    """
    k = HoldsDesignation.objects.filter(working = request.user)
    print(k)
    print("asdasd")
    flag = 0
    for z in k:
        if request.method == "POST" :
            if(str(z.designation) == 'dealing assistant'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                print (a)

                c = Paymentscheme.objects.filter(month = a , year = b , runpayroll = True)
                context = {
                    'c': c,

                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModuleds.html", context)

            if(str(z.designation) == 'sr dealing assitant'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                print (a)

                c = Paymentscheme.objects.filter(month = a , year = b , runpayroll = True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModulesrda.html", context)

            if(str(z.designation) == 'asst.registrar fa'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                print (a)

                c = Paymentscheme.objects.filter(month = a , year = b , runpayroll = True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModulearfa.html", context)


            if(str(z.designation) == 'asst. registrar aud'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                print (a)

                c = Paymentscheme.objects.filter(month = a , year = b , runpayroll = True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/finanaceAndAccountsModulearaud.html", context)


            if(str(z.designation) == 'Registrar'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                print (a)

                c = Paymentscheme.objects.filter(month = a , year = b , runpayroll = True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)

            if(str(z.designation) == 'director'):
                a = request.POST.get('selectmonth')
                b = request.POST.get('selectyear')
                print (a)

                c = Paymentscheme.objects.filter(month = a , year = b , runpayroll = True)
                context = {
                    'c': c
                }
                return render(request, "financeAndAccountsModule/financeAndAccountsModule.html", context)
    return HttpResponseRedirect("/finance/finance/")
