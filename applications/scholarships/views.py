import datetime
import json
from operator import or_
from functools import reduce

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)

from .models import (Award_and_scholarship, Constants, Director_gold,
                     Director_silver, Mcm, Notional_prize, Previous_winner,
                     Proficiency_dm, Release, Notification)

from notification.views import scholarship_portal_notif
from .validations import MCM_list, MCM_schema, gold_list, gold_schema, silver_list, silver_schema, proficiency_list,proficiency_schema
from jsonschema import validate
from jsonschema.exceptions import ValidationError
# Create your views here.


@login_required(login_url='/accounts/login')
def spacs(request):
    convener = Designation.objects.get(name='spacsconvenor')
    assistant = Designation.objects.get(name='spacsassistant')
    hd_convener = HoldsDesignation.objects.filter(
        user=request.user, designation=convener)
    hd_assistant = HoldsDesignation.objects.filter(
        user=request.user, designation=assistant)

    # Student either accepts or Declines the Award Notification
    if request.method == 'POST':
        if 'studentApproveSubmit' in request.POST:
            award = request.POST.get('studentApproveSubmit')
            if award == 'Merit-cum-Means Scholarship':
                request.session['last_clicked'] = 'studentApproveSubmit_MCM'
            else:
                request.session['last_clicked'] = 'studentApproveSubmit_Con'
        elif 'studentDeclineSubmit' in request.POST:
            award = request.POST.get('studentDeclineSubmit')
            release_id = request.POST.get('release_id')
            release = Release.objects.get(id=release_id)
            x = Notification.objects.select_related('student_id','release_id').get(
                student_id=request.user.extrainfo.id, release_id=release)
            if award == 'Merit-cum-Means Scholarship':
                request.session['last_clicked'] = 'studentApproveSubmit_MCM'
                x.notification_mcm_flag = False
            else:
                request.session['last_clicked'] = 'studentApproveSubmit_Con'
                x.notification_convocation_flag = False
            x.save()

    if request.user.extrainfo.user_type == 'student':
        return HttpResponseRedirect('/spacs/student_view')
    elif hd_convener:
        return HttpResponseRedirect('/spacs/convener_view')
    elif hd_assistant:
        return HttpResponseRedirect('/spacs/staff_view')
    else:
        # this view is for the other members of the college
        return HttpResponseRedirect('/spacs/stats')


@login_required(login_url='/accounts/login')
def convener_view(request):
    try:
        convener = Designation.objects.get(name='spacsconvenor')
        hd = HoldsDesignation.objects.get(
            user=request.user, designation=convener)
    except:
        return HttpResponseRedirect('/logout')
    if request.method == 'POST':
        if 'Submit' in request.POST:
            award = request.POST.get('type')
            programme = request.POST.get('programme')
            batch = request.POST.get('batch')
            from_date = request.POST.get('From')
            to_date = request.POST.get('To')
            remarks = request.POST.get('remarks')
            request.session['last_clicked'] = 'Submit'
            d_time = datetime.datetime.now()
            Release.objects.create(
                date_time=d_time,
                programme=programme,
                startdate=from_date,
                enddate=to_date,
                award=award,
                remarks=remarks,
                batch=batch,
                notif_visible=1,
            )
            
            # It updates the student Notification table on the spacs head sending the mcm invitation
            if batch == 'all':
                active_batches = range(datetime.datetime.now().year - 4 , datetime.datetime.now().year + 1)
                query = reduce(or_, (Q(id__id__startswith=batch) for batch in active_batches))
                recipient = Student.objects.filter(programme=programme).filter(query)
            else:
                recipient = Student.objects.filter(programme=programme, id__id__startswith=batch)
            
            # Notification starts
            convenor = request.user
            for student in recipient:
                scholarship_portal_notif(convenor, student.id.user, 'award_' + award)  # Notification
            if award == 'Merit-cum-Means Scholarship':
                rel = Release.objects.get(date_time=d_time)
                Notification.objects.select_related('student_id','release_id').bulk_create([Notification(
                    release_id=rel,
                    student_id=student,
                    notification_mcm_flag=True,
                    invite_mcm_accept_flag=False) for student in recipient])
            else:
                rel = Release.objects.get(date_time=d_time)
                Notification.objects.select_related('student_id','release_id').bulk_create([Notification(
                    release_id=rel,
                    student_id=student,
                    notification_convocation_flag=True,
                    invite_convocation_accept_flag=False) for student in recipient])
            # Notification ends
            
            messages.success(request, 
                    award + ' applications are invited successfully for ' + batch + ' batch(es)')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Email' in request.POST:
            year = request.POST.get('year')
            spi = request.POST.get('spi')
            cpi = request.POST.get('cpi')
            award, award_id = getAwardId(request)
            Notional_prize.objects.create(
                year=year, spi=spi, cpi=cpi, award_id=award_id)
            messages.success(request, award+' are invited successfully')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_MCM' in request.POST:
            pk = request.POST.get('id')
            award = Mcm.objects.select_related('award_id','student').get(id=pk).award_id
            student_id = Mcm.objects.select_related('award_id','student').get(id=pk).student
            year = datetime.datetime.now().year
            Mcm.objects.select_related('award_id','student').filter(id=pk).update(status='Accept')
            request.session['last_clicked'] = 'Accept_MCM'
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award)
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, 'Accept_MCM')
            messages.success(request, 'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Reject_MCM' in request.POST:
            pk = request.POST.get('id')
            student_id = Mcm.objects.select_related('award_id','student').get(id=pk).student
            Mcm.objects.select_related('award_id','student').filter(id=pk).update(status='Reject')
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, 'Reject_MCM')
            messages.success(request, 'Application is rejected')
            request.session['last_clicked'] = 'Reject_MCM'
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_Gold' in request.POST:
            pk = request.POST.get('id')
            award = Director_gold.objects.select_related('student','award_id').get(id=pk).award_id
            student_id = Director_gold.objects.select_related('student','award_id').get(id=pk).student
            year = datetime.datetime.now().year
            Director_gold.objects.select_related('student','award_id').filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award)
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(
                convenor, recipient.id.user, 'Accept_Gold')
            request.session['last_clicked'] = 'Accept_Gold'
            messages.success(request, 'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Reject_Gold' in request.POST:
            pk = request.POST.get('id')
            student_id = Director_gold.objects.select_related('student','award_id').get(id=pk).student
            Director_gold.objects.select_related('student','award_id').filter(id=pk).update(status='Reject')
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(
                convenor, recipient.id.user, 'Reject_Gold')
            request.session['last_clicked'] = 'Reject_Gold'
            messages.success(request, 'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_Silver' in request.POST:
            pk = request.POST.get('id')
            award = Director_silver.objects.get(id=pk).award_id
            student_id = Director_silver.objects.select_related('student','award_id').get(id=pk).student
            year = datetime.datetime.now().year
            Director_silver.objects.select_related('student','award_id').filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award)
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(
                convenor, recipient.id.user, 'Accept_Silver')
            request.session['last_clicked'] = 'Accept_Silver'
            messages.success(request, 'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Reject_Silver' in request.POST:
            pk = request.POST.get('id')
            student_id = Director_silver.objects.select_related('student','award_id').get(id=pk).student
            Director_silver.objects.select_related('student','award_id').filter(id=pk).update(status='Reject')
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(
                convenor, recipient.id.user, 'Reject_Silver')
            request.session['last_clicked'] = 'Reject_Silver'
            messages.success(request, 'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_DM' in request.POST:
            pk = request.POST.get('id')
            award = Proficiency_dm.objects.select_related('student','award_id').get(id=pk).award_id
            student_id = Proficiency_dm.objects.select_related('student','award_id').get(id=pk).student
            year = datetime.datetime.now().year
            Proficiency_dm.objects.select_related('student','award_id').filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award)
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, 'Accept_DM')
            request.session['last_clicked'] = 'Accept_DM'
            messages.success(request, 'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Reject_DM' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.select_related('student','award_id').filter(id=pk).update(status='Reject')
            student_id = Proficiency_dm.objects.select_related('student','award_id').get(id=pk).student
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, 'Reject_DM')
            request.session['last_clicked'] = 'Reject_DM'
            messages.success(request, 'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')

        elif "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendConvenerRenderRequest(request, { 'winners_list':winners_list })

    else:
        return sendConvenerRenderRequest(request)


@login_required(login_url='/accounts/login')
def student_view(request):
    if request.method == 'POST':
        if 'Submit_MCM' in request.POST:
            return submitMCM(request)

        elif 'Submit_Gold' in request.POST:
            return submitGold(request)
            
        elif 'Submit_Silver' in request.POST:
            return submitSilver(request)

        elif 'Submit_DM' in request.POST:
            return submitDM(request)

        elif "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendStudentRenderRequest(request, {'winners_list':winners_list})
    else:
        return sendStudentRenderRequest(request)

@login_required(login_url='/accounts/login')
def staff_view(request):
    try:
        assistant = Designation.objects.get(
            name='spacsassistant'
        )
    except:
        return HttpResponseRedirect('/logout')

    if request.method == 'POST':

        if 'Verify_MCM' in request.POST:
            scholarship_key = request.POST.get('id')
            Mcm.objects.select_related('award_id','student').filter(id=scholarship_key).update(status='COMPLETE')
            request.session['last_clicked'] = 'Verify_MCM'
            messages.success(request, 'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Reject_MCM' in request.POST:
            scholarship_key = request.POST.get('id')
            Mcm.objects.select_related('award_id','student').filter(id=scholarship_key).update(status='Reject')
            request.session['last_clicked'] = 'Reject_MCM'
            messages.success(request, 'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_Gold' in request.POST:
            scholarship_key = request.POST.get('id')
            Director_gold.objects.select_related('student','award_id').filter(id=scholarship_key).update(status='COMPLETE')
            request.session['last_clicked'] = 'Verify_Gold'
            messages.success(request, 'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Reject_Gold' in request.POST:
            scholarship_key = request.POST.get('id')
            Director_gold.objects.select_related('student','award_id').filter(id=scholarship_key).update(status='Reject')
            request.session['last_clicked'] = 'Reject_Gold'
            messages.success(request, 'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_Silver' in request.POST:
            scholarship_key = request.POST.get('id')
            Director_silver.objects.select_related('student','award_id').filter(id=scholarship_key).update(status='COMPLETE')
            request.session['last_clicked'] = 'Verify_Silver'
            messages.success(request, 'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Reject_Silver' in request.POST:
            scholarship_key = request.POST.get('id')
            Director_silver.objects.select_related('student','award_id').filter(id=scholarship_key).update(status='Reject')
            request.session['last_clicked'] = 'Reject_Silver'
            messages.success(request, 'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_DM' in request.POST:
            scholarship_key = request.POST.get('id')
            Proficiency_dm.objects.select_related('student','award_id').filter(id=scholarship_key).update(status='COMPLETE')
            request.session['last_clicked'] = 'Verify_DM'
            messages.success(request, 'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Reject_DM' in request.POST:
            scholarship_key = request.POST.get('id')
            Proficiency_dm.objects.select_related('student','award_id').filter(id=scholarship_key).update(status='Reject')
            request.session['last_clicked'] = 'Reject_DM'
            messages.success(request, 'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendStaffRenderRequest(request, {'winners_list':winners_list})

    else:
        return sendStaffRenderRequest(request)

def stats(request): #  This view is created for the rest of audience excluding students, spacs convenor and spacs assistant
    if request.method == 'POST':
        if "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendStatsRenderRequest(request, {'winners_list':winners_list})
    else:
        return sendStatsRenderRequest(request)

def convenerCatalogue(request):
    if request.method == 'POST':
        award_name = request.POST.get('award_name')
        catalog_content = request.POST.get('catalog_content')
        context = {}
        try:
            award = Award_and_scholarship.objects.get(award_name=award_name)
            award.catalog = catalog_content
            award.save()
            context['result'] = 'Success'
        except:
            context['result'] = 'Failure'
        return HttpResponse(json.dumps(context), content_type='convenerCatalogue/json')
    else:
        award_name = request.GET.get('award_name')
        context = {}
        try:
            award = Award_and_scholarship.objects.get(award_name=award_name)
            context['catalog'] = award.catalog
            context['result'] = 'Success'
        except:
            context['result'] = 'Failure'
        return HttpResponse(json.dumps(context), content_type='convenerCatalogue/json')

def getWinners(request):
    award_name = request.GET.get('award_name')
    batch_year = int(request.GET.get('batch'))
    programme_name = request.GET.get('programme')
    award = Award_and_scholarship.objects.get(award_name=award_name)
    winners = Previous_winner.objects.select_related('student','award_id').filter(
        year=batch_year, award_id=award, programme=programme_name)
    context = {}
    context['student_name'] = []
    context['student_program'] = []
    context['roll'] = []

#  If-Else Condition for previous winner if there is or no data in the winner table
    if winners:
        for winner in winners:

            extra_info = ExtraInfo.objects.get(id=winner.student_id)
            student_id = Student.objects.get(id=extra_info)
            student_name = extra_info.user.first_name
            student_roll = winner.student_id
            student_program = student_id.programme
            context['student_name'].append(student_name)
            context['roll'].append(student_roll)
            context['student_program'].append(student_program)

        context['result'] = 'Success'

    else:
        context['result'] = 'Failure'

    return HttpResponse(json.dumps(context), content_type='getWinners/json')

def get_MCM_Flag(request):  # Here we are extracting mcm_flag
    x = Notification.objects.select_related('student_id','release_id').filter(student_id=request.user.extrainfo.id)
    for i in x:
        i.invite_mcm_accept_flag = True
        i.save()
        # i.notification_mcm_flag=False
    request.session['last_clicked'] = 'get_MCM_Flag'
    context = {}
    context['show_mcm_flag'] = True
    if x:
        context['result'] = 'Success'
    else:
        context['result'] = 'Failure'
    return HttpResponse(json.dumps(context), content_type='get_MCM_Flag/json')
    # return HttpResponseRedirect('/spacs/student_view')

def getConvocationFlag(request):  # Here we are extracting convocation_flag
    x = Notification.objects.filter(student_id=request.user.extrainfo.id)
    for i in x:
        i.invite_convocation_accept_flag = True
        i.save()
        # i.notification_convocation_flag=False
    request.session['last_clicked'] = 'getConvocationFlag'
    context = {}
    context['show_convocation_flag'] = True
    if x:
        context['result'] = 'Success'
    else:
        context['result'] = 'Failure'
    return HttpResponse(json.dumps(context), content_type='getConvocationFlag/json')

def getContent(request):
    award_name = request.GET.get('award_name')
    context = {}
    try:
        award = Award_and_scholarship.objects.get(award_name=award_name)
        context['result'] = 'Success'
        context['content'] = award.catalog
        print(type(award.catalog))
        # context['content'] = 'Hi'

    except:
        context['result'] = 'Failure'
    return HttpResponse(json.dumps(context), content_type='getContent/json')

def checkDate(start_date, end_date):
    current_date = datetime.date.today()
    if start_date < end_date:
        if current_date <= end_date:
            return True
        else:
            return False
    else:
        return False

def updateEndDate(request):
    id = request.GET.get('up_id')
    end_date = request.GET.get('up_d')
    is_released = Release.objects.filter(pk=id).update(enddate=end_date)
    request.session['last_clicked'] = "Enddate_updated"
    context = {}
    if is_released:
        context['result'] = 'Success'
    else:
        context['result'] = 'Failure'
    return HttpResponse(json.dumps(context), content_type='updateEndDate/json')

def getAwardId(request):
    award = request.POST.get('award')
    a = Award_and_scholarship.objects.get(award_name=award).id
    award_id = Award_and_scholarship.objects.get(id=a)
    return award, award_id

def submitMCM(request):
    i = Notification.objects.select_related('student_id','release_id').filter(student_id=request.user.extrainfo.id)
    for x in i:
        x.invite_mcm_accept_flag = False
        x.save()
    father_occ = request.POST.get('father_occ')
    mother_occ = request.POST.get('mother_occ')
    brother_name = request.POST.get('brother_name')
    sister_name = request.POST.get('sister_name')
    brother_occupation = request.POST.get('brother_occupation')
    sister_occupation = request.POST.get('sister_occupation')
    income_father = int(request.POST.get('father_income'))
    income_mother = int(request.POST.get('mother_income'))
    income_other = int(request.POST.get('other_income'))
    father_occ_desc = request.POST.get('father_occ_desc')
    mother_occ_desc = request.POST.get('mother_occ_desc')
    four_wheeler = request.POST.get('four_wheeler')
    four_wheeler_desc = request.POST.get('four_wheeler_desc')
    two_wheeler_desc = request.POST.get('two_wheeler_desc')
    two_wheeler = request.POST.get('two_wheeler')
    house = request.POST.get('house')
    plot_area = request.POST.get('plot_area')
    constructed_area = request.POST.get('constructed_area')
    school_fee = request.POST.get('school_fee')
    school_name = request.POST.get('school_name')
    college_fee = request.POST.get('college_fee')
    college_name = request.POST.get('college_name')
    loan_amount = request.POST.get('loan_amount')
    bank_name = request.POST.get('bank_name')
    income_certificate = request.FILES.get('income_certificate')
    student = request.user.extrainfo.student
    annual_income = income_father + income_mother + income_other
    award, award_id = getAwardId(request)
    data_insert = {
        "brother_name": brother_name,
        "brother_occupation": brother_occupation,
        "sister_name": sister_name,
        "sister_occupation": sister_occupation,
        "income_father": income_father,
        "income_mother": income_mother,
        "income_other": income_other,
        "father_occ": father_occ,
        "mother_occ": mother_occ,
        "father_occ_desc": father_occ_desc,
        "mother_occ_desc": mother_occ_desc,
        "four_wheeler": four_wheeler,
        "four_wheeler_desc": four_wheeler_desc,
        "two_wheeler": two_wheeler,
        "two_wheeler_desc": two_wheeler_desc,
        "house": house,
        "plot_area": plot_area,
        "constructed_area": constructed_area,
        "school_fee": school_fee,
        "school_name": school_name,
        "bank_name": bank_name,
        "loan_amount": loan_amount,
        "college_fee": college_fee,
        "college_name": college_name,
        "annual_income": annual_income,
    }
    try:
        for column in MCM_list:
            validate(instance=data_insert[column], schema=MCM_schema[column])

        releases = Release.objects.filter(
            Q(
                startdate__lte=datetime.datetime.today().strftime("%Y-%m-%d"),
                enddate__gte=datetime.datetime.today().strftime("%Y-%m-%d"),
            )
        ).filter(award="Merit-cum-Means Scholarship")
        for release in releases:
            if Mcm.objects.select_related('award_id','student').filter(
                Q(date__gte=release.startdate, date__lte=release.enddate)
            ).filter(student=request.user.extrainfo.student):
                # if len(Mcm.objects.filter(student = request.user.extrainfo.student)) > 0:
                Mcm.objects.select_related('award_id','student').filter(
                    Q(
                        date__gte=release.startdate,
                        date__lte=release.enddate,
                    )
                ).filter(student=request.user.extrainfo.student).update(
                    father_occ=father_occ,
                    mother_occ=mother_occ,
                    brother_name=brother_name,
                    sister_name=sister_name,
                    income_father=income_father,
                    income_mother=income_mother,
                    income_other=income_other,
                    brother_occupation=brother_occupation,
                    sister_occupation=sister_occupation,
                    student=student,
                    annual_income=annual_income,
                    income_certificate=income_certificate,
                    award_id=award_id,
                    father_occ_desc=father_occ_desc,
                    mother_occ_desc=mother_occ_desc,
                    four_wheeler=four_wheeler,
                    four_wheeler_desc=four_wheeler_desc,
                    two_wheeler_desc=two_wheeler_desc,
                    two_wheeler=two_wheeler,
                    house=house,
                    plot_area=plot_area,
                    constructed_area=constructed_area,
                    school_fee=school_fee,
                    school_name=school_name,
                    bank_name=bank_name,
                    loan_amount=loan_amount,
                    college_fee=college_fee,
                    college_name=college_name,
                    status="INCOMPLETE",
                )
                messages.success(
                    request, award + ' Application is successfully submitted'
                )
                break
            else:
                Mcm.objects.create(
                    father_occ=father_occ,
                    mother_occ=mother_occ,
                    brother_name=brother_name,
                    sister_name=sister_name,
                    income_father=income_father,
                    income_mother=income_mother,
                    income_other=income_other,
                    brother_occupation=brother_occupation,
                    sister_occupation=sister_occupation,
                    student=student,
                    annual_income=annual_income,
                    income_certificate=income_certificate,
                    award_id=award_id,
                    father_occ_desc=father_occ_desc,
                    mother_occ_desc=mother_occ_desc,
                    four_wheeler=four_wheeler,
                    four_wheeler_desc=four_wheeler_desc,
                    two_wheeler_desc=two_wheeler_desc,
                    two_wheeler=two_wheeler,
                    house=house,
                    plot_area=plot_area,
                    constructed_area=constructed_area,
                    school_fee=school_fee,
                    school_name=school_name,
                    bank_name=bank_name,
                    loan_amount=loan_amount,
                    college_fee=college_fee,
                    college_name=college_name,
                )
                messages.success(
                    request, award + ' Application is successfully submitted'
                )
                break
        request.session["last_clicked"] = "Submit_mcm"
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session['last_clicked'] = 'Submit_MCM'
    return HttpResponseRedirect('/spacs/student_view')

def submitGold(request):
    i = Notification.objects.select_related('student_id','release_id').filter(
                student_id=request.user.extrainfo.id)
    for x in i:
        x.invite_convocation_accept_flag = False
        x.save()
    relevant_document = request.FILES.get('myfile')
    student_id = request.user.extrainfo.student
    award, award_id = getAwardId(request)
    academic_achievements = request.POST.get('academic_achievements')
    science_inside = request.POST.get('science_inside')
    science_outside = request.POST.get('science_outside')
    games_inside = request.POST.get('games_inside')
    games_outside = request.POST.get('games_outside')
    cultural_inside = request.POST.get('cultural_inside')
    cultural_outside = request.POST.get('cultural_outside')
    social = request.POST.get('social')
    corporate = request.POST.get('corporate')
    hall_activities = request.POST.get('hall_activities')
    gymkhana_activities = request.POST.get('gymkhana_activities')
    institute_activities = request.POST.get('institute_activities')
    counselling_activities = request.POST.get('counselling_activities')
    other_activities = request.POST.get('other_activities')
    justification = request.POST.get('justification')
    correspondence_address = request.POST.get('c_address')
    financial_assistance = request.POST.get('financial_assistance')
    grand_total = request.POST.get('grand_total')
    nearest_policestation = request.POST.get('nps')
    nearest_railwaystation = request.POST.get('nrs')
    data_insert={
        "academic_achievements":academic_achievements,
        "science_inside":science_inside,
        "science_outside":science_outside,
        "games_inside":games_inside,
        "games_outside":games_outside,
        "cultural_inside":cultural_inside,
        "cultural_outside":cultural_outside,
        "social":social,
        "corporate":corporate,
        "hall_activities":hall_activities,
        "gymkhana_activities":gymkhana_activities,
        "institute_activities":institute_activities,
        "counselling_activities":counselling_activities,
        "other_activities":other_activities,
        "justification":justification,
        "correspondence_address":correspondence_address,
        "financial_assistance":financial_assistance,
        "grand_total":grand_total,
        "nearest_policestation":nearest_policestation,
        "nearest_railwaystation":nearest_railwaystation
    }
    try:
        for column in gold_list:
            validate(instance=data_insert[column], schema=gold_schema[column])
        releases = Release.objects.filter(Q(startdate__lte=datetime.datetime.today().strftime(
            '%Y-%m-%d'), enddate__gte=datetime.datetime.today().strftime('%Y-%m-%d'))).filter(award="Convocation Medals")
        for release in releases:
            existingRelease = Director_gold.objects.select_related('student','award_id').filter(Q(date__gte=release.startdate, date__lte=release.enddate)).filter(student=request.user.extrainfo.student)
            if existingRelease:
                existingRelease.update(
                    student=student_id,
                    relevant_document=relevant_document,
                    award_id=award_id,
                    academic_achievements=academic_achievements,
                    science_inside=science_inside,
                    science_outside=science_outside,
                    games_inside=games_inside,
                    games_outside=games_outside,
                    cultural_inside=cultural_inside,
                    cultural_outside=cultural_outside,
                    social=social,
                    corporate=corporate,
                    hall_activities=hall_activities,
                    gymkhana_activities=gymkhana_activities,
                    institute_activities=institute_activities,
                    counselling_activities=counselling_activities,
                    correspondence_address=correspondence_address,
                    financial_assistance=financial_assistance,
                    grand_total=grand_total,
                    nearest_policestation=nearest_policestation,
                    nearest_railwaystation=nearest_railwaystation,
                    justification=justification,
                    status='INCOMPLETE'
                )
                messages.success(request, award + ' Application is successfully updated')
                break
            else:
                Director_gold.objects.create(
                    student=student_id,
                    relevant_document=relevant_document,
                    award_id=award_id,
                    academic_achievements=academic_achievements,
                    science_inside=science_inside,
                    science_outside=science_outside,
                    games_inside=games_inside,
                    games_outside=games_outside,
                    cultural_inside=cultural_inside,
                    cultural_outside=cultural_outside,
                    social=social,
                    corporate=corporate,
                    hall_activities=hall_activities,
                    gymkhana_activities=gymkhana_activities,
                    institute_activities=institute_activities,
                    counselling_activities=counselling_activities,
                    correspondence_address=correspondence_address,
                    financial_assistance=financial_assistance,
                    grand_total=grand_total,
                    nearest_policestation=nearest_policestation,
                    nearest_railwaystation=nearest_railwaystation,
                    justification=justification
                )
                messages.success(request, award + ' Application is successfully submitted')
                break
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session['last_clicked'] = 'Submit_Gold'
    return HttpResponseRedirect('/spacs/student_view')

def submitSilver(request):
    i = Notification.objects.select_related('student_id','release_id').filter(
                student_id=request.user.extrainfo.id)
    for x in i:
        x.invite_convocation_accept_flag = False
        x.save()
    relevant_document = request.FILES.get('myfile')
    award, award_id = getAwardId(request)
    award_type = request.POST.get('award-type')
    student_id = request.user.extrainfo.student
    inside_achievements = request.POST.get('inside_achievements')
    outside_achievements = request.POST.get('outside_achievements')
    justification = request.POST.get('justification')
    correspondence_address = request.POST.get('c_address')
    financial_assistance = request.POST.get('financial_assistance')
    grand_total = request.POST.get('grand_total')
    nearest_policestation = request.POST.get('nps')
    nearest_railwaystation = request.POST.get('nrs')
    data_insert={
        "nearest_policestation":nearest_policestation,
        "nearest_railwaystation":nearest_railwaystation,
        "correspondence_address":correspondence_address,
        "financial_assistance":financial_assistance,
        "grand_total":grand_total,
        "inside_achievements":inside_achievements,
        "justification":justification,
        "outside_achievements":outside_achievements
    }
    try:
        for column in silver_list:
            validate(instance=data_insert[column], schema=silver_schema[column])
        releases = Release.objects.filter(Q(startdate__lte=datetime.datetime.today().strftime(
            '%Y-%m-%d'), enddate__gte=datetime.datetime.today().strftime('%Y-%m-%d'))).filter(award="Convocation Medals")
        for release in releases:
            existingRelease = Director_silver.objects.select_related('student','award_id').filter(Q(date__gte=release.startdate, date__lte=release.enddate)).filter(student=request.user.extrainfo.student)
            if existingRelease:
                existingRelease.update(
                    student=student_id,
                    award_id=award_id,
                    award_type=award_type,
                    relevant_document=relevant_document,
                    inside_achievements=inside_achievements,
                    justification=justification,
                    correspondence_address=correspondence_address,
                    financial_assistance=financial_assistance,
                    grand_total=grand_total,
                    nearest_policestation=nearest_policestation,
                    nearest_railwaystation=nearest_railwaystation,
                    outside_achievements=outside_achievements,
                    status='INCOMPLETE'
                )
                messages.success(request, award + ' Application is successfully updated')
                break
            else:
                Director_silver.objects.create(
                    student=student_id,
                    award_id=award_id,
                    award_type=award_type,
                    relevant_document=relevant_document,
                    inside_achievements=inside_achievements,
                    justification=justification,
                    correspondence_address=correspondence_address,
                    financial_assistance=financial_assistance,
                    grand_total=grand_total,
                    nearest_policestation=nearest_policestation,
                    nearest_railwaystation=nearest_railwaystation,
                    outside_achievements=outside_achievements
                )
                messages.success(request, award + ' Application is successfully submitted')
                break
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session['last_clicked'] = 'Submit_Silver'
    return HttpResponseRedirect('/spacs/student_view')

def submitDM(request):
    i = Notification.objects.select_related('student_id','release_id').filter(student_id=request.user.extrainfo.id)
    for x in i:
        x.invite_convocation_accept_flag = False
        x.save()
    title_name = request.POST.get('title')
    no_of_students = request.POST.get('students')
    relevant_document = request.FILES.get('myfile')
    award, award_id = getAwardId(request)
    award_type = request.POST.get('award-type')
    student_id = request.user.extrainfo.student
    try:
        roll_no1 = int(request.POST.get('roll_no1'))
    except:
        roll_no1 = 0
    try:
        roll_no2 = int(request.POST.get('roll_no2'))
    except:
        roll_no2 = 0
    try:
        roll_no3 = int(request.POST.get('roll_no3'))
    except:
        roll_no3 = 0
    try:
        roll_no4 = int(request.POST.get('roll_no4'))
    except:
        roll_no4 = 0
    try:
        roll_no5 = int(request.POST.get('roll_no5'))
    except:
        roll_no5 = 0
    ece_topic = request.POST.get('ece_topic')
    cse_topic = request.POST.get('cse_topic')
    mech_topic = request.POST.get('mech_topic')
    design_topic = request.POST.get('design_topic')
    ece_percentage = int(request.POST.get('ece_percentage'))
    cse_percentage = int(request.POST.get('cse_percentage'))
    mech_percentage = int(request.POST.get('mech_percentage'))
    design_percentage = int(request.POST.get('design_percentage'))
    brief_description = request.POST.get('brief_description')
    justification = request.POST.get('justification')
    correspondence_address = request.POST.get('c_address')
    financial_assistance = request.POST.get('financial_assistance')
    grand_total = request.POST.get('grand_total')
    nearest_policestation = request.POST.get('nps')
    nearest_railwaystation = request.POST.get('nrs')
    data_insert={
        "title_name":title_name,
        "award_type":award_type,
        "nearest_policestation":nearest_policestation,
        "nearest_railwaystation":nearest_railwaystation,
        "correspondence_address":correspondence_address,
        "financial_assistance":financial_assistance,
        "brief_description":brief_description,
        "justification":justification,
        "grand_total":grand_total,
        "ece_topic":ece_topic,
        "cse_topic":cse_topic,
        "mech_topic":mech_topic,
        "design_topic":design_topic,
        "ece_percentage":ece_percentage,
        "cse_percentage":cse_percentage,
        "mech_percentage":mech_percentage,
        "design_percentage":design_percentage,
        "correspondence_address":correspondence_address,
        "financial_assistance":financial_assistance,
        "grand_total":grand_total,
        "nearest_policestation":nearest_policestation,
        "nearest_railwaystation":nearest_railwaystation
    }
    try:
        for column in proficiency_list:
            validate(instance=data_insert[column], schema=proficiency_schema[column])
        releases = Release.objects.filter(Q(startdate__lte=datetime.datetime.today().strftime(
            '%Y-%m-%d'), enddate__gte=datetime.datetime.today().strftime('%Y-%m-%d'))).filter(award="Convocation Medals")
        for release in releases:
            existingRelease = Proficiency_dm.objects.select_related('student','award_id').filter(Q(date__gte=release.startdate, date__lte=release.enddate)).filter(student=request.user.extrainfo.student)
            if existingRelease:
                existingRelease.update(
                    title_name=title_name,
                    no_of_students=no_of_students,
                    student=student_id,
                    award_id=award_id,
                    award_type=award_type,
                    relevant_document=relevant_document,
                    roll_no1=roll_no1,
                    roll_no2=roll_no2,
                    roll_no3=roll_no3,
                    roll_no4=roll_no4,
                    roll_no5=roll_no5,
                    ece_topic=ece_topic,
                    cse_topic=cse_topic,
                    mech_topic=mech_topic,
                    design_topic=design_topic,
                    ece_percentage=ece_percentage,
                    cse_percentage=cse_percentage,
                    mech_percentage=mech_percentage,
                    design_percentage=design_percentage,
                    brief_description=brief_description,
                    correspondence_address=correspondence_address,
                    financial_assistance=financial_assistance,
                    grand_total=grand_total,
                    nearest_policestation=nearest_policestation,
                    nearest_railwaystation=nearest_railwaystation,
                    justification=justification,
                    status='INCOMPLETE'
                )
                messages.success(
                    request, award + ' Application is successfully updated')
                break
            else:
                Proficiency_dm.objects.create(
                    title_name=title_name,
                    no_of_students=no_of_students,
                    student=student_id,
                    award_id=award_id,
                    award_type=award_type,
                    relevant_document=relevant_document,
                    roll_no1=roll_no1,
                    roll_no2=roll_no2,
                    roll_no3=roll_no3,
                    roll_no4=roll_no4,
                    roll_no5=roll_no5,
                    ece_topic=ece_topic,
                    cse_topic=cse_topic,
                    mech_topic=mech_topic,
                    design_topic=design_topic,
                    ece_percentage=ece_percentage,
                    cse_percentage=cse_percentage,
                    mech_percentage=mech_percentage,
                    design_percentage=design_percentage,
                    brief_description=brief_description,
                    correspondence_address=correspondence_address,
                    financial_assistance=financial_assistance,
                    grand_total=grand_total,
                    nearest_policestation=nearest_policestation,
                    nearest_railwaystation=nearest_railwaystation,
                    justification=justification
                )
                messages.success(
                    request, award + ' Application is successfully submitted')
                break
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session['last_clicked'] = 'Submit_dm'
    return HttpResponseRedirect('/spacs/student_view')

def submitPreviousWinner(request):
    request.session["last_clicked"] = "SubmitPreviousWinner"
    PreviousWinnerAward = request.POST.get("PreviousWinnerAward")
    PreviousWinnerAcadYear = request.POST.get("PreviousWinnerAcadYear")
    PreviousWinnerProgramme = request.POST.get("PreviousWinnerProgramme")
    request.session["PreviousWinnerAward"] = PreviousWinnerAward
    request.session["PreviousWinnerAcadYear"] = PreviousWinnerAcadYear
    request.session["PreviousWinnerProgramme"] = PreviousWinnerProgramme

    award = Award_and_scholarship.objects.get(award_name=PreviousWinnerAward)
    winners = Previous_winner.objects.select_related('student','award_id').filter(year=PreviousWinnerAcadYear, award_id=award, programme=PreviousWinnerProgramme)

    paginator = Paginator(winners, 10)
    page = 1
    try:
        winners_list = paginator.page(page)
    except PageNotAnInteger:
        winners_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        winners_list = paginator.page(paginator.num_pages)
    return winners_list

def sendConvenerRenderRequest(request, additionalParams={}):
    context = getCommonParams(request)
    ch = Constants.BATCH
    source = Constants.FATHER_OCC_CHOICE
    time = Constants.TIME
    release = Release.objects.all()
    notification = Notification.objects.select_related('student_id','release_id').all()
    spi = Spi.objects.all()
    context.update({ 'source': source, 'time': time, 'ch': ch, 'spi': spi, 'release': release})
    context.update(additionalParams)
    return render(request, 'scholarshipsModule/scholarships_convener.html', context)

def sendStudentRenderRequest(request, additionalParams={}):
    context = getCommonParams(request)
    ch = Constants.BATCH
    time = Constants.TIME
    mother_occ = Constants.MOTHER_OCC_CHOICES
    source = Constants.FATHER_OCC_CHOICE
    release = Release.objects.all()
    release_count = release.count()
    spi = Spi.objects.all()
    no_of_mcm_filled = len(Mcm.objects.select_related('award_id','student').filter(
        student=request.user.extrainfo.student))
    no_of_con_filled = len(Director_silver.objects.select_related('student','award_id').filter(student=request.user.extrainfo.student)) + len(Director_gold.objects.select_related('student','award_id').filter(
        student=request.user.extrainfo.student)) + len(Proficiency_dm.objects.select_related('student','award_id').filter(student=request.user.extrainfo.student))
    #  Here we are fetching the flags from the Notification table of student
    # end of database queries

    # notification flags
    update_mcm_flag = False
    update_con_flag = False
    x_notif_mcm_flag = False
    x_notif_con_flag = False
    for dates in release:
        if checkDate(dates.startdate, dates.enddate):
            if dates.award == 'Merit-cum-Means Scholarship' and dates.batch == str(request.user.extrainfo.student)[0:4] and dates.programme == request.user.extrainfo.student.programme:
                x_notif_mcm_flag = True
                if no_of_mcm_filled > 0:
                    update_mcm_flag = True
            elif dates.award == 'Convocation Medals' and dates.batch == str(request.user.extrainfo.student)[0:4] and dates.programme == request.user.extrainfo.student.programme:
                x_notif_con_flag = True
                if no_of_con_filled > 0:
                    update_con_flag = True
        else:
            if dates.award == "Merit-cum-Means Scholarship" and dates.batch == str(request.user.extrainfo.student)[0:4]:
                try:
                    x = Notification.objects.select_related('student_id','release_id').get(
                        student_id=request.user.extrainfo.id, release_id=dates.id).delete()
                except:
                    pass
            elif dates.award == 'Convocation Medals' and dates.batch == str(request.user.extrainfo.student)[0:4]:
                try:
                    x = Notification.objects.select_related('student_id','release_id').get(
                        student_id=request.user.extrainfo.id, release_id=dates.id).delete()
                except:
                    pass

    x = Notification.objects.select_related('student_id','release_id').filter(student_id=request.user.extrainfo.id).order_by('-release_id__date_time')
    show_mcm_flag = False
    show_convocation_flag = False
    for i in x:
        if i.invite_mcm_accept_flag == True:
            show_mcm_flag = True
            break
    for i in x:
        if i.invite_convocation_accept_flag == True:
            show_convocation_flag = True
            break
    context.update({'time': time, 'ch': ch, 'spi': spi, 'release': release,
                    'release_count': release_count, 'x_notif_mcm_flag': x_notif_mcm_flag, 'x_notif_con_flag': x_notif_con_flag,
                    'source': source, 'show_mcm_flag': show_mcm_flag, 'show_convocation_flag': show_convocation_flag,
                    'update_mcm_flag': update_mcm_flag, 'update_con_flag': update_con_flag, 'mother_occ': mother_occ,'x': x})
    context.update(additionalParams)
    return render(request, 'scholarshipsModule/scholarships_student.html',context)

def sendStaffRenderRequest(request, additionalParams={}):
    context = getCommonParams(request)
    context.update(additionalParams)
    return render(request, 'scholarshipsModule/scholarships_staff.html', context)

def sendStatsRenderRequest(request, additionalParams={}):
    context = getCommonParams(request)
    context.update(additionalParams)
    return render(request, 'scholarshipsModule/stats.html', context)

def getCommonParams(request):
    student = Student.objects.all()
    mcm = Mcm.objects.select_related('award_id','student').all()
    gold = Director_gold.objects.select_related('student','award_id').all()
    silver = Director_silver.objects.select_related('student','award_id').all()
    dandm = Proficiency_dm.objects.select_related('student','award_id').all()
    awards = Award_and_scholarship.objects.all()
    con = Designation.objects.get(name='spacsconvenor')
    assis = Designation.objects.get(name='spacsassistant')
    hd = HoldsDesignation.objects.get(designation=con)
    hd1 = HoldsDesignation.objects.get(designation=assis)
    year_range = range(2013, datetime.datetime.now().year + 1)
    active_batches = range(datetime.datetime.now().year - 4 , datetime.datetime.now().year + 1)
    last_clicked = ''
    try:
        last_clicked = request.session['last_clicked']
    except:
        print('last_clicked not found')
    context = {'mcm': mcm, 'awards': awards, 'student': student, 'gold': gold, 'silver': silver, 
                'dandm': dandm, 'con': con, 'assis': assis, 'hd': hd, 'hd1': hd1, 
                'last_clicked': last_clicked, 'year_range': year_range, 'active_batches': active_batches}
    return context
