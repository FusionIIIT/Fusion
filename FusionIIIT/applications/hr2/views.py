from django.shortcuts import render
from .models import *
from applications.globals.models import ExtraInfo
from django.db.models import Q
from django.http import Http404
from .forms import EditDetailsForm,EditConfidentialDetailsForm
from django.contrib import messages
# def hr2_index(request):
#         """ Views for HR2 main page"""
#         template='hr2Module/hr2_index.html'
#         temps = Employee.objects.all()


#         return render(request,template,{'temps':temps})



def edit_employee_details(request,id):
        """ Views for edit details"""
        template='hr2Module/editDetails.html'

        try:
               employee = ExtraInfo.objects.get(pk=id)
        except:
                raise Http404("Post does not exist")

        

        if request.method == "POST":
                form = EditDetailsForm(request.POST, request.FILES)
                conf_form = EditConfidentialDetailsForm(request.POST,request.FILES)

                
                if form.is_valid() and conf_form.is_valid():
                        form.save()
                        conf_form.save()
                        messages.success(request, "Employee details edited successfully")
                else:
                        print(form['extra_info'].value())
                        print(form['father_name'].value())
                        
                        print("___________ ",form.errors)
                        print("+=++++",conf_form.errors)
        

        form = EditDetailsForm(initial={'extra_info': employee.id})
        conf_form = EditConfidentialDetailsForm(initial={'extra_info': employee})
        context = {'form': form,'confForm':conf_form
               }

        return render(request,template, context)



def hr_admin(request):
        """ Views for HR2 Admin page """
        template='hr2Module/hradmin.html'

        # searched employee
        query = request.GET.get('search')
        
        if(request.method == "GET"):
                if(query!=None):
                        emp = ExtraInfo.objects.filter(
                                Q(user__first_name__icontains=query)|
                                Q(user__last_name__icontains=query)
                                

                        ).distinct()
                        emp  = emp.filter(user_type="faculty")
                else:
                        emp = ExtraInfo.objects.all()
                        emp  = emp.filter(user_type="faculty")
        else:
                emp = ExtraInfo.objects.all()
                emp  = emp.filter(user_type="faculty")

        context = {'emps':emp}
        return render(request,template,context)

def service_book(request):
        """
        Views for service book page
        """
        user = request.user
        extra_info = ExtraInfo.objects.select_related().get(user=user)
        lien_service_book = ForeignService.objects.filter(extra_info = extra_info).filter(service_type= "LIEN").order_by('-start_date')
        deputation_service_book = ForeignService.objects.filter(extra_info = extra_info).filter(service_type= "DEPUTATION").order_by('-start_date')
        other_service_book = ForeignService.objects.filter(extra_info = extra_info).filter(service_type= "OTHER").order_by('-start_date')
        appraisal_form = EmpAppraisalForm.objects.filter(extra_info = extra_info).order_by('-year')
        template = 'hr2Module/servicebook.html'
        context = {'lienServiceBooks':lien_service_book,'deputationServiceBooks':deputation_service_book,'otherServiceBooks':other_service_book,'appraisalForm':appraisal_form}
        return render(request,template,context)


def view_employee_details(request,id):
        """ Views for edit details"""
        extra_info = ExtraInfo.objects.get(pk=id)
        lien_service_book = ForeignService.objects.filter(extra_info = extra_info).filter(service_type= "LIEN").order_by('-start_date')
        deputation_service_book = ForeignService.objects.filter(extra_info = extra_info).filter(service_type= "DEPUTATION").order_by('-start_date')
        other_service_book = ForeignService.objects.filter(extra_info = extra_info).filter(service_type= "OTHER").order_by('-start_date')
        template = 'hr2Module/viewdetails.html'
        context = {'lienServiceBooks':lien_service_book,'deputationServiceBooks':deputation_service_book,'otherServiceBooks':other_service_book,'user':extra_info.user,'extrainfo':extra_info}
        return render(request,template,context)

