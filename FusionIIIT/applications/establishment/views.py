from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import datetime
from .models import Cpda_application, Cpda_tracking, Cpda_bill
from .forms import Cpda_Form, Cpda_Bills_Form
from django.template import RequestContext

@login_required(login_url='/accounts/login')
def establishment(request):
    if request.method == "POST":
        # try:
            if 'request' in request.POST:
                print(" *** CPDA request submit *** ")
                applicant = request.user
                pf_number = request.POST.get('pf_number')
                purpose = request.POST.get('purpose')
                advance = request.POST.get('requested_advance')
                status = 'requested'
                timestamp = datetime.now()
                print (pf_number, purpose, advance)
                application = Cpda_application.objects.create(
                    applicant=applicant,
                    pf_number=pf_number,
                    purpose=purpose,
                    requested_advance=advance,
                    request_timestamp=timestamp,
                    status=status
                )
                # print(" app id = ", application_id)

                # reviewer = request.POST.get('reviewer') 
                # reviewer_id = User.objects.get(username=reviewer)
                # designation = request.POST.get('designation')
                # reviewer_design = Designation.objects.filter(name=designation)[0]
                # remarks = request.POST.get('remarks')

                # CPDA_tracking.objects.create(
                #     application_id = application,
                #     reviewer_id = reviewer_id,
                #     reviewer_design = reviewer_design,
                #     remarks=remarks
                # )
                # add notif here
                # add message here

            if 'adjust' in request.POST:
                # add multiple files
                # get application object here
                # application_id = request.POST.get('application_id')
                app_id = request.POST.get('app_id')
                # verify that app_id is not changed, ie untampered
                application = Cpda_application.objects.get(id=app_id)
                upload_file = request.FILES.get('bills')
                adjustment_amount = request.POST.get('adjustment_amount')
                bills_amount = request.POST.get('total_bills_amount')

                Cpda_bill.objects.create(
                    application_id = app_id,
                    bill = upload_file
                )                           

                bills_attached = 1                
                timestamp = datetime.now()

                application.bills_attached = bills_attached
                application.total_bills_amount = bills_amount
                application.adjustment_amount = adjustment_amount
                application.adjustment_timestamp = timestamp
                application.status = 'adjustments_pending'
                application.save()

            #     # get tarcking info of a particular application
            #     track = CPDA_tracking.objects.get(application=application)
                


        # except:
        #     message = "An error has occured!"
        #     print(message)
            # return HttpResponse(message)
    active_apps = (Cpda_application.objects
                    .filter(applicant=request.user)
                    .exclude(status='rejected')
                    .exclude(status='finished')
                    .order_by('-request_timestamp'))

    archive_apps = (Cpda_application.objects
                    .filter(applicant=request.user)
                    .exclude(status='requested')
                    .exclude(status='approved')
                    .exclude(status='adjustments_pending')
                    .order_by('-request_timestamp'))

    form = Cpda_Form()
    bill_forms = {}
    apps = Cpda_application.objects.filter(applicant=request.user).filter(status='approved')
    for app in apps:
        bill_forms[app.id] = Cpda_Bills_Form(initial={'app_id': app.id})
    response = render(request, 'establishment/establishment.html', {
        'form': form,
        'billforms': bill_forms,
        'active_apps': active_apps,
        'archive_apps': archive_apps
    })
    return response
