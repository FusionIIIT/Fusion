from django.shortcuts import render
from .models import *
from applications.globals.models import ExtraInfo
from django.db.models import Q
from django.http import Http404
from .forms import editDetailsForm,editConfidentialDetailsForm
# def hr2_index(request):
#         """ Views for HR2 main page"""
#         template='hr2Module/hr2_index.html'
#         temps = Employee.objects.all()


#         return render(request,template,{'temps':temps})



def editEmployeeDetails(request):
        """ Views for edit details"""
        template='hr2Module/editDetails.html'


        if request.method == "POST":
                form = editDetailsForm(request.POST, request.FILES)
                conf_form = editConfidentialDetailsForm(request.POST,request.FILES)

                if form.is_valid() and conf_form.is_valid():
                        form.save()
                        conf_form.save()
                        messages.success(request, "Employee details edited successfully")
        


        form = editDetailsForm()
        conf_form = editConfidentialDetailsForm()
        context = {'form': form,'confForm':conf_form
               }

        return render(request,template, context)



def hrAdmin(request):
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

def serviceBook(request):
        """
        Views for service book page
        """
        template = 'hr2Module/servicebook.html'
        return render(request,template)