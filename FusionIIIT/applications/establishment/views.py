from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation

from datetime import datetime
from .models import Cpda_application, Cpda_tracking, Cpda_bill, Establishment_variables, Constants
from .forms import Cpda_Form, Cpda_Bills_Form, Cpda_Assign_Form, Cpda_Review_Form

@login_required(login_url='/accounts/login')
def establishment(request):
    # Check if establishment variables exist, if not create some fields

    # If user is establishment admin, then give all access
    if request.user == Establishment_variables.objects.first().est_admin: 
        # handle POST requests

        if request.method == "POST":

            app_id = request.POST.get('app_id')
            status = request.POST.get('status')
            reviewer = request.POST.get('reviewer_id')
            designation = request.POST.get('reviewer_design')
            remarks = request.POST.get('remarks')
            if status == 'requested' or status == 'adjustments_pending':
                if reviewer and designation and app_id:
                    # assign the app to the reviewer
                    reviewer_id = User.objects.get(username=reviewer)
                    reviewer_design = Designation.objects.filter(name=designation)

                    # check if the reviewer holds the given designation, if not show error
                    if reviewer_design:
                        reviewer_design = reviewer_design[0]
                    # if reviewer_design != HoldsDesignation.objects.get(user=reviewer_id):
                    #     messages.error(request, 'Reviewer doesn\'t holds the designation you specified!')
                    # else:
                    application = Cpda_application.objects.get(id=app_id)
                    application.tracking_info.reviewer_id = reviewer_id
                    application.tracking_info.reviewer_design = reviewer_design
                    application.tracking_info.remarks = remarks
                    application.tracking_info.review_status = 'under_review'
                    application.tracking_info.save()
                    
                    # add notif
                    messages.success(request, 'Reviewer assigned successfully!')
                    # print (reviewer_design, ' ||| ', reviewer_id)

                else:
                    errors = "Please specify a reviewer and their designation."
                    messages.error(request, errors)

            elif app_id:
                # update the status of app
                # verify that app_id is not changed, ie untampered
                application = Cpda_application.objects.get(id=app_id)
                application.status = status;
                application.save()
                # print (application)

                # add notif
                messages.success(request, 'Status updated successfully!')
                


        # only requested and adjustment_pending
        unreviewed_apps = (Cpda_application.objects
                        .exclude(status='rejected')
                        .exclude(status='finished')
                        .exclude(status='approved')
                        .order_by('-request_timestamp'))
        pending_apps = []
        under_review_apps = []
        for app in unreviewed_apps:
            if app.tracking_info.review_status == 'under_review':
                under_review_apps.append(app)
            else:
                pending_apps.append(app)

        # combine assign_form object into pending_app object respectively
        for app in unreviewed_apps:
            # if status is requested:to_assign/reviewed
            if app.status == 'requested':
                temp = Cpda_Assign_Form(initial={'status': 'requested', 'app_id': app.id})
                temp.fields["status"]._choices = [
                    ('requested', 'Requested'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected')
                ]
            # if status is adjustments_pending:to_assign/reviewed
            else:
                temp = Cpda_Assign_Form(initial={'status': 'adjustments_pending', 'app_id': app.id})
                temp.fields["status"]._choices = [
                    ('adjustments_pending', 'Adjustments Pending'),
                    ('finished', 'Finished')
                ]
            app.assign_form = temp
            # print (app.assign_form.fields['status']._choices)
            
        # only approved
        approved_apps = (Cpda_application.objects
                        .filter(status='approved')
                        .order_by('-request_timestamp'))

        # only rejected and finished
        archived_apps = (Cpda_application.objects
                        .exclude(status='approved')
                        .exclude(status='requested')
                        .exclude(status='adjustments_pending')
                        .order_by('-request_timestamp'))

        response = render(request, 'establishment/establishment.html', {
            'admin': True,
            'pending_apps': pending_apps,
            'under_review_apps': under_review_apps,
            'approved_apps': approved_apps,
            'archived_apps': archived_apps
        })
        return response

    ############################################################################
    ############################################################################
    ############################################################################
    ############################################################################
    ############################################################################
    ############################################################################


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
                # next 3 lines are working magically, DON'T TOUCH THEM
                track = Cpda_tracking.objects.create(
                    application = application,
                    review_status = 'to_assign'
                )
                # print (application.tracking_info.application)

                # add notif here
                messages.success(request, 'Request sent successfully!')

            if 'adjust' in request.POST:
                # add multiple files
                # get application object here DONE
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

                # get tracking info of a particular application
                application.tracking_info.review_status = 'to_assign'
                application.tracking_info.save()
                # add notif here
                messages.success(request, 'Bills submitted successfully!')
                
            if 'review' in request.POST:
                print(" *** CPDA Review submit *** ")
                app_id = request.POST.get('app_id')
                # verify that app_id is not changed, ie untampered
                review_comment = request.POST.get('remarks')
                application = Cpda_application.objects.get(id=app_id)
                application.tracking_info.remarks = review_comment
                application.tracking_info.review_status = 'reviewed'
                application.tracking_info.save()
                # add notif here
                messages.success(request, 'Review submitted successfully!')


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
    to_review_apps = (Cpda_application.objects
                    .filter(tracking_info__reviewer_id=request.user)
                    .exclude(status='rejected')
                    .exclude(status='finished')
                    .exclude(status='approved')
                    .filter(tracking_info__review_status='under_review')
                    .order_by('-request_timestamp'))
    for app in to_review_apps:
        app.reviewform = Cpda_Review_Form(initial={'app_id': app.id})

    form = Cpda_Form()
    bill_forms = {}
    apps = Cpda_application.objects.filter(applicant=request.user).filter(status='approved')
    for app in apps:
        bill_forms[app.id] = Cpda_Bills_Form(initial={'app_id': app.id})
    response = render(request, 'establishment/establishment.html', {
        'form': form,
        'billforms': bill_forms,
        'active_apps': active_apps,
        'archive_apps': archive_apps,
        'to_review_apps': to_review_apps
    })
    return response
