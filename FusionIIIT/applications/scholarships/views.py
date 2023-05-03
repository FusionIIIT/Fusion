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
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation

from .models import (
    Award_and_scholarship,
    Constants,
    Director_gold,
    Director_silver,
    IIITDM_Proficiency,
    Mcm,
    Notional_prize,
    Previous_winner,
    DM_Proficiency_gold,
    Release,
    Notification,
)

from notification.views import scholarship_portal_notif
from .validations import (
    Mcm_list,
    Mcm_schema,
    Director_gold_list,
    Director_gold_schema,
    Director_silver_list,
    Director_silver_schema,
    DM_Proficiency_Gold_list,
    DM_Proficiency_Gold_schema,
    IIITDM_Proficiency_list,
    IIITDM_Proficiency_schema,
)
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Create your views here.


@login_required(login_url="/accounts/login")
def spacs(request):
    convener = Designation.objects.get(name="spacsconvenor")
    assistant = Designation.objects.get(name="spacsassistant")
    hd_convener = HoldsDesignation.objects.filter(
        user=request.user, designation=convener
    )
    hd_assistant = HoldsDesignation.objects.filter(
        user=request.user, designation=assistant
    )

    # Student either accepts or Declines the Award Notification
    if request.method == "POST":
        if "studentApproveSubmit" in request.POST:
            award = request.POST.get("studentApproveSubmit")
            if award == "Merit-cum-Means Scholarship":
                request.session["last_clicked"] = "studentApproveSubmit_MCM"
            else:
                request.session["last_clicked"] = "studentApproveSubmit_Con"
        elif "studentDeclineSubmit" in request.POST:
            award = request.POST.get("studentDeclineSubmit")
            release_id = request.POST.get("release_id")
            release = Release.objects.get(id=release_id)
            x = Notification.objects.select_related("student_id", "release_id").get(
                student_id=request.user.extrainfo.id, release_id=release
            )
            if award == "Merit-cum-Means Scholarship":
                request.session["last_clicked"] = "studentApproveSubmit_MCM"
                x.notification_mcm_flag = False
            else:
                request.session["last_clicked"] = "studentApproveSubmit_Con"
                x.notification_convocation_flag = False
            x.save()

    if request.user.extrainfo.user_type == "student":
        return HttpResponseRedirect("/spacs/student_view")
    elif hd_convener:
        return HttpResponseRedirect("/spacs/convener_view")
    elif hd_assistant:
        return HttpResponseRedirect("/spacs/staff_view")
    else:
        # this view is for the other members of the college
        return HttpResponseRedirect("/spacs/stats")


@login_required(login_url="/accounts/login")
def convener_view(request):
    try:
        convener = Designation.objects.get(name="spacsconvenor")
        hd = HoldsDesignation.objects.get(user=request.user, designation=convener)
    except:
        return HttpResponseRedirect("/logout")
    if request.method == "POST":
        if "Submit" in request.POST:
            award = request.POST.get("type")
            programme = request.POST.get("programme")
            batch = request.POST.get("batch")
            from_date = request.POST.get("From")
            to_date = request.POST.get("To")
            remarks = request.POST.get("remarks")
            request.session["last_clicked"] = "Submit"
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
            if batch.lower() == "all":
                active_batches = range(
                    datetime.datetime.now().year - 4, datetime.datetime.now().year + 1
                )
                recipient = Student.objects.filter(programme=programme).filter(
                    batch__in=active_batches
                )
            else:
                recipient = Student.objects.filter(programme=programme, batch=batch)
            # Notification starts
            convenor = request.user
            for student in recipient:
                scholarship_portal_notif(
                    convenor, student.id.user, "award_" + award
                )  # Notification
            if award == "Merit-cum-Means Scholarship":
                rel = Release.objects.get(date_time=d_time)
                Notification.objects.select_related(
                    "student_id", "release_id"
                ).bulk_create(
                    [
                        Notification(
                            release_id=rel,
                            student_id=student,
                            notification_mcm_flag=True,
                            invite_mcm_accept_flag=False,
                        )
                        for student in recipient
                    ]
                )
            else:
                rel = Release.objects.get(date_time=d_time)
                Notification.objects.select_related(
                    "student_id", "release_id"
                ).bulk_create(
                    [
                        Notification(
                            release_id=rel,
                            student_id=student,
                            notification_convocation_flag=True,
                            invite_convocation_accept_flag=False,
                        )
                        for student in recipient
                    ]
                )
            # Notification ends

            messages.success(
                request,
                award
                + " applications are invited successfully for "
                + batch
                + " batch(es)",
            )
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Email" in request.POST:
            year = request.POST.get("year")
            spi = request.POST.get("spi")
            cpi = request.POST.get("cpi")
            award, award_id = getAwardId(request)
            Notional_prize.objects.create(
                year=year, spi=spi, cpi=cpi, award_id=award_id
            )
            messages.success(request, award + " are invited successfully")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Accept_MCM" in request.POST:
            pk = request.POST.get("id")
            award = (
                Mcm.objects.select_related("award_id", "student").get(id=pk).award_id
            )
            student_id = (
                Mcm.objects.select_related("award_id", "student").get(id=pk).student
            )
            year = datetime.datetime.now().year
            Mcm.objects.select_related("award_id", "student").filter(id=pk).update(
                status="Accept"
            )
            request.session["last_clicked"] = "Accept_MCM"
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Accept_MCM")
            messages.success(request, "Application is accepted")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Reject_MCM" in request.POST:
            pk = request.POST.get("id")
            student_id = (
                Mcm.objects.select_related("award_id", "student").get(id=pk).student
            )
            Mcm.objects.select_related("award_id", "student").filter(id=pk).update(
                status="Reject"
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Reject_MCM")
            messages.success(request, "Application is rejected")
            request.session["last_clicked"] = "Reject_MCM"
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Accept_Gold" in request.POST:
            pk = request.POST.get("id")
            award = (
                Director_gold.objects.select_related("student", "award_id")
                .get(id=pk)
                .award_id
            )
            student_id = (
                Director_gold.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            year = datetime.datetime.now().year
            Director_gold.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Accept")
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Accept_Gold")
            request.session["last_clicked"] = "Accept_Gold"
            messages.success(request, "Application is accepted")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Reject_Gold" in request.POST:
            pk = request.POST.get("id")
            student_id = (
                Director_gold.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            Director_gold.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Reject")
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Reject_Gold")
            request.session["last_clicked"] = "Reject_Gold"
            messages.success(request, "Application is rejected")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Accept_Silver" in request.POST:
            pk = request.POST.get("id")
            award = Director_silver.objects.get(id=pk).award_id
            student_id = (
                Director_silver.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            year = datetime.datetime.now().year
            Director_silver.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Accept")
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Accept_Silver")
            request.session["last_clicked"] = "Accept_Silver"
            messages.success(request, "Application is accepted")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Reject_Silver" in request.POST:
            pk = request.POST.get("id")
            student_id = (
                Director_silver.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            Director_silver.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Reject")
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Reject_Silver")
            request.session["last_clicked"] = "Reject_Silver"
            messages.success(request, "Application is rejected")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Accept_DM" in request.POST:
            pk = request.POST.get("id")
            award = (
                DM_Proficiency_gold.objects.select_related("student", "award_id")
                .get(id=pk)
                .award_id
            )
            student_id = (
                DM_Proficiency_gold.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            year = datetime.datetime.now().year
            DM_Proficiency_gold.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Accept")
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Accept_DM")
            request.session["last_clicked"] = "Accept_DM"
            messages.success(request, "Application is accepted")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Reject_DM" in request.POST:
            pk = request.POST.get("id")
            DM_Proficiency_gold.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Reject")
            student_id = (
                DM_Proficiency_gold.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Reject_DM")
            request.session["last_clicked"] = "Reject_DM"
            messages.success(request, "Application is rejected")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Accept_Proficiency" in request.POST:
            pk = request.POST.get("id")
            award = (
                IIITDM_Proficiency.objects.select_related("student", "award_id")
                .get(id=pk)
                .award_id
            )
            student_id = (
                IIITDM_Proficiency.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            year = datetime.datetime.now().year
            IIITDM_Proficiency.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Accept")
            Previous_winner.objects.create(
                student=student_id, year=year, award_id=award
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Accept_Proficiency")
            request.session["last_clicked"] = "Accept_Proficiency"
            messages.success(request, "Application is accepted")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "Reject_Proficiency" in request.POST:
            pk = request.POST.get("id")
            IIITDM_Proficiency.objects.select_related("student", "award_id").filter(
                id=pk
            ).update(status="Reject")
            student_id = (
                IIITDM_Proficiency.objects.select_related("student", "award_id")
                .get(id=pk)
                .student
            )
            convenor = request.user
            recipient = student_id
            scholarship_portal_notif(convenor, recipient.id.user, "Reject_Proficiency")
            request.session["last_clicked"] = "Reject_Proficiency"
            messages.success(request, "Application is rejected")
            return HttpResponseRedirect("/spacs/convener_view")

        elif "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendConvenerRenderRequest(request, {"winners_list": winners_list})

    else:
        return sendConvenerRenderRequest(request)


@login_required(login_url="/accounts/login")
def student_view(request):
    if request.method == "POST":
        # print(request.POST, request.POST.get("event_member_team") or None)
        # print(request.FILES, request.FILES.get("dhsfh") or None)
        print("Submit_Silver" in request.POST, request.POST)
        if "Submit_MCM" in request.POST:
            return submitMCM(request)

        elif "Submit_Gold" in request.POST:
            return submitGold(request)

        elif "Submit_Silver" in request.POST:
            return submitSilver(request)

        elif "Submit_DM" in request.POST:
            return submitDM(request)

        elif "Submit_Proficiency" in request.POST:
            return submitProficiency(request)

        elif "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendStudentRenderRequest(request, {"winners_list": winners_list})
    else:
        return sendStudentRenderRequest(request)


@login_required(login_url="/accounts/login")
def staff_view(request):
    try:
        assistant = Designation.objects.get(name="spacsassistant")
    except:
        return HttpResponseRedirect("/logout")

    if request.method == "POST":
        if "Verify_MCM" in request.POST:
            scholarship_key = request.POST.get("id")
            Mcm.objects.select_related("award_id", "student").filter(
                id=scholarship_key
            ).update(status="COMPLETE")
            request.session["last_clicked"] = "Verify_MCM"
            messages.success(request, "Verified successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Reject_MCM" in request.POST:
            scholarship_key = request.POST.get("id")
            Mcm.objects.select_related("award_id", "student").filter(
                id=scholarship_key
            ).update(status="Reject")
            request.session["last_clicked"] = "Reject_MCM"
            messages.success(request, "Rejected successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Verify_Gold" in request.POST:
            scholarship_key = request.POST.get("id")
            Director_gold.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="COMPLETE")
            request.session["last_clicked"] = "Verify_Gold"
            messages.success(request, "Verified successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Reject_Gold" in request.POST:
            scholarship_key = request.POST.get("id")
            Director_gold.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="Reject")
            request.session["last_clicked"] = "Reject_Gold"
            messages.success(request, "Rejected successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Verify_Silver" in request.POST:
            scholarship_key = request.POST.get("id")
            Director_silver.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="COMPLETE")
            request.session["last_clicked"] = "Verify_Silver"
            messages.success(request, "Verified successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Reject_Silver" in request.POST:
            scholarship_key = request.POST.get("id")
            Director_silver.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="Reject")
            request.session["last_clicked"] = "Reject_Silver"
            messages.success(request, "Rejected successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Verify_DM" in request.POST:
            scholarship_key = request.POST.get("id")
            DM_Proficiency_gold.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="COMPLETE")
            request.session["last_clicked"] = "Verify_DM"
            messages.success(request, "Verified successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Reject_DM" in request.POST:
            scholarship_key = request.POST.get("id")
            DM_Proficiency_gold.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="Reject")
            request.session["last_clicked"] = "Reject_DM"
            messages.success(request, "Rejected successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Verify_Proficiency" in request.POST:
            scholarship_key = request.POST.get("id")
            IIITDM_Proficiency.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="COMPLETE")
            request.session["last_clicked"] = "Verify_Proficiency"
            messages.success(request, "Verified successfully")
            return HttpResponseRedirect("/spacs/staff_view")

        elif "Reject_Proficiency" in request.POST:
            scholarship_key = request.POST.get("id")
            IIITDM_Proficiency.objects.select_related("student", "award_id").filter(
                id=scholarship_key
            ).update(status="Reject")
            request.session["last_clicked"] = "Reject_Proficiency"
            messages.success(request, "Rejected successfully")
            return HttpResponseRedirect("/spacs/staff_view")


        elif "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendStaffRenderRequest(request, {"winners_list": winners_list})

    else:
        return sendStaffRenderRequest(request)


def stats(
    request,
):  #  This view is created for the rest of audience excluding students, spacs convenor and spacs assistant
    if request.method == "POST":
        if "SubmitPreviousWinner" in request.POST:
            winners_list = submitPreviousWinner(request)
            return sendStatsRenderRequest(request, {"winners_list": winners_list})
    else:
        return sendStatsRenderRequest(request)


def convenerCatalogue(request):
    if request.method == "POST":
        award_name = request.POST.get("award_name")
        catalog_content = request.POST.get("catalog_content")
        context = {}
        try:
            award = Award_and_scholarship.objects.get(award_name=award_name)
            award.catalog = catalog_content
            award.save()
            context["result"] = "Success"
        except:
            context["result"] = "Failure"
        return HttpResponse(json.dumps(context), content_type="convenerCatalogue/json")
    else:
        award_name = request.GET.get("award_name")
        context = {}
        try:
            award = Award_and_scholarship.objects.get(award_name=award_name)
            context["catalog"] = award.catalog
            context["result"] = "Success"
        except:
            context["result"] = "Failure"
        return HttpResponse(json.dumps(context), content_type="convenerCatalogue/json")


def getWinners(request):
    award_name = request.GET.get("award_name")
    batch_year = int(request.GET.get("batch"))
    programme_name = request.GET.get("programme")
    award = Award_and_scholarship.objects.get(award_name=award_name)
    winners = Previous_winner.objects.select_related("student", "award_id").filter(
        year=batch_year, award_id=award, programme=programme_name
    )
    context = {}
    context["student_name"] = []
    context["student_program"] = []
    context["roll"] = []

    #  If-Else Condition for previous winner if there is or no data in the winner table
    if winners:
        for winner in winners:
            extra_info = ExtraInfo.objects.get(id=winner.student_id)
            student_id = Student.objects.get(id=extra_info)
            student_name = extra_info.user.first_name
            student_roll = winner.student_id
            student_program = student_id.programme
            context["student_name"].append(student_name)
            context["roll"].append(student_roll)
            context["student_program"].append(student_program)

        context["result"] = "Success"

    else:
        context["result"] = "Failure"

    return HttpResponse(json.dumps(context), content_type="getWinners/json")


def get_MCM_Flag(request):  # Here we are extracting mcm_flag
    x = Notification.objects.select_related("student_id", "release_id").filter(
        student_id=request.user.extrainfo.id
    )
    for i in x:
        i.invite_mcm_accept_flag = True
        i.save()
        # i.notification_mcm_flag=False
    request.session["last_clicked"] = "get_MCM_Flag"
    context = {}
    context["show_mcm_flag"] = True
    if x:
        context["result"] = "Success"
    else:
        context["result"] = "Failure"
    return HttpResponse(json.dumps(context), content_type="get_MCM_Flag/json")


# return HttpResponseRedirect('/spacs/student_view')


def getConvocationFlag(request):  # Here we are extracting convocation_flag
    x = Notification.objects.filter(student_id=request.user.extrainfo.id)
    for i in x:
        i.invite_convocation_accept_flag = True
        i.save()
        # i.notification_convocation_flag=False
    request.session["last_clicked"] = "getConvocationFlag"
    context = {}
    context["show_convocation_flag"] = True
    if x:
        context["result"] = "Success"
    else:
        context["result"] = "Failure"
    return HttpResponse(json.dumps(context), content_type="getConvocationFlag/json")


def getContent(request):
    award_name = request.GET.get("award_name")
    context = {}
    try:
        award = Award_and_scholarship.objects.get(award_name=award_name)
        context["result"] = "Success"
        context["content"] = award.catalog
        print(type(award.catalog))
        # context['content'] = 'Hi'

    except:
        context["result"] = "Failure"
    return HttpResponse(json.dumps(context), content_type="getContent/json")


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
    id = request.GET.get("up_id")
    end_date = request.GET.get("up_d")
    is_released = Release.objects.filter(pk=id).update(enddate=end_date)
    request.session["last_clicked"] = "Enddate_updated"
    context = {}
    if is_released:
        context["result"] = "Success"
    else:
        context["result"] = "Failure"
    return HttpResponse(json.dumps(context), content_type="updateEndDate/json")


def getAwardId(request):
    award = request.POST.get("award")
    a = Award_and_scholarship.objects.get(award_name=award).id
    award_id = Award_and_scholarship.objects.get(id=a)
    return award, award_id


def submitMCM(request):
    i = Notification.objects.select_related("student_id", "release_id").filter(
        student_id=request.user.extrainfo.id
    )
    for x in i:
        x.invite_mcm_accept_flag = False
        x.save()
    father_occ = request.POST.get("father_occ")
    mother_occ = request.POST.get("mother_occ")
    brother_name = request.POST.get("brother_name")
    sister_name = request.POST.get("sister_name")
    brother_occupation = request.POST.get("brother_occupation")
    sister_occupation = request.POST.get("sister_occupation")
    income_father = int(request.POST.get("father_income"))
    income_mother = int(request.POST.get("mother_income"))
    income_other = int(request.POST.get("other_income"))
    father_occ_desc = request.POST.get("father_occ_desc")
    mother_occ_desc = request.POST.get("mother_occ_desc")
    four_wheeler = request.POST.get("four_wheeler")
    four_wheeler_desc = request.POST.get("four_wheeler_desc")
    two_wheeler_desc = request.POST.get("two_wheeler_desc")
    two_wheeler = request.POST.get("two_wheeler")
    house = request.POST.get("house")
    plot_area = request.POST.get("plot_area")
    constructed_area = request.POST.get("constructed_area")
    school_fee = request.POST.get("school_fee")
    school_name = request.POST.get("school_name")
    college_fee = request.POST.get("college_fee")
    college_name = request.POST.get("college_name")
    loan_amount = request.POST.get("loan_amount")
    bank_name = request.POST.get("bank_name")
    income_certificate = request.FILES.get("income_certificate")
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
        for column in Mcm_list:
            validate(instance=data_insert[column], schema=Mcm_schema[column])

        releases = Release.objects.filter(
            Q(
                startdate__lte=datetime.datetime.today().strftime("%Y-%m-%d"),
                enddate__gte=datetime.datetime.today().strftime("%Y-%m-%d"),
            )
        ).filter(award="Merit-cum-Means Scholarship")
        for release in releases:
            if (
                Mcm.objects.select_related("award_id", "student")
                .filter(Q(date__gte=release.startdate, date__lte=release.enddate))
                .filter(student=request.user.extrainfo.student)
            ):
                # if len(Mcm.objects.filter(student = request.user.extrainfo.student)) > 0:
                Mcm.objects.select_related("award_id", "student").filter(
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
                    request, award + " Application is successfully submitted"
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
                    request, award + " Application is successfully submitted"
                )
                break
        request.session["last_clicked"] = "Submit_mcm"
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session["last_clicked"] = "Submit_MCM"
    return HttpResponseRedirect("/spacs/student_view")


def submitGold(request):
    i = Notification.objects.select_related("student_id", "release_id").filter(
        student_id=request.user.extrainfo.id
    )
    for x in i:
        x.invite_convocation_accept_flag = False
        x.save()

    student_id = request.user.extrainfo.student
    award, award_id = getAwardId(request)
    financial_assistance = request.POST.get("scholarship_detail")
    academic = request.POST.get("academic_detail")
    science = request.POST.get("science_detail")
    games = request.POST.get("sports_detail")
    cultural = request.POST.get("cultural_detail")
    social = request.POST.get("social_detail")
    corporate = request.POST.get("corporate_detail")
    hall_activities = request.POST.get("hall_detail")
    gymkhana_activities = request.POST.get("gymkhana_detail")
    institute_activities = request.POST.get("institute_detail")
    counselling_activities = request.POST.get("counselling_detail")
    sci = request.POST.get("sci")
    scie = request.POST.get("scie")
    ij = request.POST.get("ij")
    ic = request.POST.get("ic")
    nc = request.POST.get("nc")
    workshop = request.POST.get("workshop")
    novelty = request.POST.get("novelty")
    disciplinary_action = request.POST.get("disciplinary_details")

    academic_doc = request.FILES.get("academic_detail_doc") or None
    financial_assistance_doc = request.FILES.get("scholarship_detail_doc") or None
    science_doc = request.FILES.get("science_detail_doc") or None
    games_doc = request.FILES.get("sports_detail_doc") or None
    cultural_doc = request.FILES.get("cultural_detail_doc") or None
    social_doc = request.FILES.get("social_detail_doc") or None
    corporate_doc = request.FILES.get("corporate_detail_doc") or None
    hall_activities_doc = request.FILES.get("hall_detail_doc") or None
    gymkhana_activities_doc = request.FILES.get("gymkhana_detail_doc") or None
    institute_activities_doc = request.FILES.get("institute_detail_doc") or None
    counselling_activities_doc = request.FILES.get("counselling_detail_doc") or None
    sci_doc = request.FILES.get("sci_doc") or None
    scie_doc = request.FILES.get("scie_doc") or None
    ij_doc = request.FILES.get("ij_doc") or None
    ic_doc = request.FILES.get("ic_doc") or None
    nc_doc = request.FILES.get("nc_doc") or None
    workshop_doc = request.FILES.get("workshop_doc") or None
    warning_letter = request.FILES.get("warning_letter") or None
    jagriti = request.FILES.get("jagriti_doc") or None
    blood_donation = request.FILES.get("blood_donation_doc") or None
    other_extra_curricular_activities = (
        request.FILES.get("extra_curricular_others_doc") or None
    )

    data_insert = {
        "award_id": award_id,
        "financial_assistance": financial_assistance,
        "academic": academic,
        "science": science,
        "games": games,
        "cultural": cultural,
        "social": social,
        "corporate": corporate,
        "hall_activities": hall_activities,
        "gymkhana_activities": gymkhana_activities,
        "institute_activities": institute_activities,
        "counselling_activities": counselling_activities,
        "other_extra_curricular_activities": other_extra_curricular_activities,
        "sci": sci,
        "scie": scie,
        "ij": ij,
        "ic": ic,
        "nc": nc,
        "workshop": workshop,
        "novelty": novelty,
        "disciplinary_action": disciplinary_action,
    }
    try:
        for column in Director_gold_list:
            validate(instance=data_insert[column], schema=Director_gold_schema[column])
        releases = Release.objects.filter(
            Q(
                startdate__lte=datetime.datetime.today().strftime("%Y-%m-%d"),
                enddate__gte=datetime.datetime.today().strftime("%Y-%m-%d"),
            )
        ).filter(award="Convocation Medals")
        for release in releases:
            existingRelease = (
                Director_gold.objects.select_related("student", "award_id")
                .filter(Q(date__gte=release.startdate, date__lte=release.enddate))
                .filter(student=request.user.extrainfo.student)
            )
            if existingRelease:
                existingRelease.update(
                    student=student_id,
                    award_id=award_id,
                    financial_assistance=financial_assistance,
                    academic=academic,
                    science=science,
                    games=games,
                    cultural=cultural,
                    social=social,
                    corporate=corporate,
                    hall_activities=hall_activities,
                    gymkhana_activities=gymkhana_activities,
                    institute_activities=institute_activities,
                    counselling_activities=counselling_activities,
                    sci=sci,
                    scie=scie,
                    ij=ij,
                    ic=ic,
                    nc=nc,
                    workshop=workshop,
                    novelty=novelty,
                    disciplinary_action=disciplinary_action,
                    academic_doc=academic_doc,
                    financial_assistance_doc=financial_assistance_doc,
                    science_doc=science_doc,
                    games_doc=games_doc,
                    cultural_doc=cultural_doc,
                    social_doc=social_doc,
                    corporate_doc=corporate_doc,
                    hall_activities_doc=hall_activities_doc,
                    gymkhana_activities_doc=gymkhana_activities_doc,
                    institute_activities_doc=institute_activities_doc,
                    counselling_activities_doc=counselling_activities_doc,
                    sci_doc=sci_doc,
                    scie_doc=scie_doc,
                    ij_doc=ij_doc,
                    ic_doc=ic_doc,
                    nc_doc=nc_doc,
                    workshop_doc=workshop_doc,
                    warning_letter=warning_letter,
                    jagriti=jagriti,
                    blood_donation=blood_donation,
                    other_extra_curricular_activities=other_extra_curricular_activities,
                    status="INCOMPLETE",
                )
                messages.success(
                    request, award + " Application is successfully updated"
                )
                break
            else:
                Director_gold.objects.create(
                    student=student_id,
                    award_id=award_id,
                    academic=academic,
                    science=science,
                    games=games,
                    cultural=cultural,
                    social=social,
                    corporate=corporate,
                    hall_activities=hall_activities,
                    gymkhana_activities=gymkhana_activities,
                    institute_activities=institute_activities,
                    counselling_activities=counselling_activities,
                    sci=sci,
                    scie=scie,
                    ij=ij,
                    ic=ic,
                    nc=nc,
                    workshop=workshop,
                    novelty=novelty,
                    disciplinary_action=disciplinary_action,
                    academic_doc=academic_doc,
                    financial_assistance_doc=financial_assistance_doc,
                    science_doc=science_doc,
                    games_doc=games_doc,
                    cultural_doc=cultural_doc,
                    social_doc=social_doc,
                    corporate_doc=corporate_doc,
                    hall_activities_doc=hall_activities_doc,
                    gymkhana_activities_doc=gymkhana_activities_doc,
                    institute_activities_doc=institute_activities_doc,
                    counselling_activities_doc=counselling_activities_doc,
                    sci_doc=sci_doc,
                    scie_doc=scie_doc,
                    ij_doc=ij_doc,
                    ic_doc=ic_doc,
                    nc_doc=nc_doc,
                    workshop_doc=workshop_doc,
                    warning_letter=warning_letter,
                    jagriti=jagriti,
                    blood_donation=blood_donation,
                    other_extra_curricular_activities=other_extra_curricular_activities,
                )
                messages.success(
                    request, award + " Application is successfully submitted"
                )
                break
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session["last_clicked"] = "Submit_Gold"
    return HttpResponseRedirect("/spacs/student_view")


def submitSilver(request):
    i = Notification.objects.select_related("student_id", "release_id").filter(
        student_id=request.user.extrainfo.id
    )
    for x in i:
        x.invite_convocation_accept_flag = False
        x.save()
    award, award_id = getAwardId(request)
    student_id = request.user.extrainfo.student
    cultural_intercollege_certificates_no = int(
        request.POST.get("cultural_inter_college_certificate") or 0
    )
    cultural_intercollege_team_event = request.POST.get(
        "cultural_inter_college_team_event"
    )
    cultural_intercollege_team_certificates_no = int(
        request.POST.get("cultural_inter_college_team_certificate") or 0
    )
    culturalfest_certificates_no = int(request.POST.get("cultural_fest_certificate") or 0)
    cultural_club_coordinator = request.POST.get("cultural_club_coordinator")
    cultural_club_co_coordinator = request.POST.get("cultural_club_co_coordinator")
    cultural_event_member = request.POST.get("cultural_event_member_team")
    cultural_interIIIT_certificates_no = int(
        request.POST.get("cultural_inter_iiit_individual") or 0
    )
    cultural_interIIIT_team_certificates_no = int(
        request.POST.get("cultural_inter_iiit_team") or 0
    )
    sports_club_coordinator = request.POST.get("sports_club_coordinator")
    sports_club_co_coordinator = request.POST.get("sports_club_co_coordinator")
    sports_event_member = request.POST.get("sports_event_member_team")
    sports_other_accomplishment = request.POST.get("sports_accomplishments")
    cultural_intercollege_certificate = (
        request.FILES.get("cultural_inter_college_certificate_doc") or None
    )
    cultural_intercollege_team_certificate = (
        request.FILES.get("cultural_inter_college_team_certificate_doc") or None
    )
    culturalfest_certificate = (
        request.FILES.get("cultural_fest_certificate_doc") or None
    )
    cultural_club_coordinator_certificate = (
        request.FILES.get("cultural_club_coordinator_doc") or None
    )
    cultural_club_co_coordinator_certificate = (
        request.FILES.get("cultural_club_co_coordinator_doc") or None
    )
    cultural_event_member_certificate = (
        request.FILES.get("cultural_event_member_team_doc") or None
    )
    cultural_interIIIT_team_certificate = (
        request.FILES.get("cultural_inter_iiit_team_doc") or None
    )
    cultural_interIIIT_certificate = (
        request.FILES.get("cultural_inter_iiit_individual_doc") or None
    )
    sports_intercollege_certificate = (
        request.FILES.get("sports_inter_college_individual") or None
    )
    sports_intercollege_team_certificate = (
        request.FILES.get("sports_inter_college_team") or None
    )
    sportsfest_certificate = request.FILES.get("gusto_individual") or None
    sportsfest_team_certificate = request.FILES.get("gusto_team") or None
    sports_club_coordinator_certificate = (
        request.FILES.get("sports_club_coordinator_doc") or None
    )
    sports_club_co_coordinator_certificate = (
        request.FILES.get("sports_club_co_coordinator_doc") or None
    )
    sports_event_member_certificate = (
        request.FILES.get("sports_event_member_team_doc") or None
    )
    sports_interIIIT_team_certificate = (
        request.FILES.get("sports_inter_iiit_team") or None
    )
    sports_interIIIT_certificate = (
        request.FILES.get("sports_inter_iiit_individual") or None
    )
    sports_other_accomplishment_doc = (
        request.FILES.get("sports_accomplishments_doc") or None
    )

    data_insert = {
        "award_id": award_id,
        "cultural_intercollege_certificates_no": cultural_intercollege_certificates_no,
        "cultural_intercollege_team_event": cultural_intercollege_team_event,
        "cultural_intercollege_team_certificates_no": cultural_intercollege_team_certificates_no,
        "culturalfest_certificates_no": culturalfest_certificates_no,
        "cultural_club_coordinator": cultural_club_coordinator,
        "cultural_club_co_coordinator": cultural_club_co_coordinator,
        "cultural_event_member": cultural_event_member,
        "cultural_interIIIT_certificates_no": cultural_interIIIT_certificates_no,
        "cultural_interIIIT_team_certificates_no": cultural_interIIIT_team_certificates_no,
        "sports_club_coordinator": sports_club_coordinator,
        "sports_club_co_coordinator": sports_club_co_coordinator,
        "sports_event_member": sports_event_member,
        "sports_other_accomplishment": sports_other_accomplishment,
    }
    try:
        for column in Director_silver_list:
            validate(
                instance=data_insert[column], schema=Director_silver_schema[column]
            )
        releases = Release.objects.filter(
            Q(
                startdate__lte=datetime.datetime.today().strftime("%Y-%m-%d"),
                enddate__gte=datetime.datetime.today().strftime("%Y-%m-%d"),
            )
        ).filter(award="Convocation Medals")
        print(releases)
        for release in releases:
            existingRelease = (
                Director_silver.objects.select_related("student", "award_id")
                .filter(Q(date__gte=release.startdate, date__lte=release.enddate))
                .filter(student=request.user.extrainfo.student)
            )
            if existingRelease:
                existingRelease.update(
                    student=student_id,
                    award_id=award_id,
                    cultural_intercollege_certificates_no=cultural_intercollege_certificates_no,
                    cultural_intercollege_team_event=cultural_intercollege_team_event,
                    cultural_intercollege_team_certificates_no=cultural_intercollege_team_certificates_no,
                    culturalfest_certificates_no=culturalfest_certificates_no,
                    cultural_club_coordinator=cultural_club_coordinator,
                    cultural_club_co_coordinator=cultural_club_co_coordinator,
                    cultural_event_member=cultural_event_member,
                    cultural_interIIIT_certificates_no=cultural_interIIIT_certificates_no,
                    cultural_interIIIT_team_certificates_no=cultural_interIIIT_team_certificates_no,
                    sports_club_coordinator=sports_club_coordinator,
                    sports_club_co_coordinator=sports_club_co_coordinator,
                    sports_event_member=sports_event_member,
                    sports_other_accomplishment=sports_other_accomplishment,
                    cultural_intercollege_certificate=cultural_intercollege_certificate,
                    cultural_intercollege_team_certificate=cultural_intercollege_team_certificate,
                    culturalfest_certificate=culturalfest_certificate,
                    cultural_club_coordinator_certificate=cultural_club_coordinator_certificate,
                    cultural_club_co_coordinator_certificate=cultural_club_co_coordinator_certificate,
                    cultural_event_member_certificate=cultural_event_member_certificate,
                    cultural_interIIIT_team_certificate=cultural_interIIIT_team_certificate,
                    cultural_interIIIT_certificate=cultural_interIIIT_certificate,
                    sports_intercollege_certificate=sports_intercollege_certificate,
                    sports_intercollege_team_certificate=sports_intercollege_team_certificate,
                    sportsfest_certificate=sportsfest_certificate,
                    sportsfest_team_certificate=sportsfest_team_certificate,
                    sports_club_coordinator_certificate=sports_club_coordinator_certificate,
                    sports_club_co_coordinator_certificate=sports_club_co_coordinator_certificate,
                    sports_event_member_certificate=sports_event_member_certificate,
                    sports_interIIIT_team_certificate=sports_interIIIT_team_certificate,
                    sports_interIIIT_certificate=sports_interIIIT_certificate,
                    sports_other_accomplishment_doc=sports_other_accomplishment_doc,
                    status="INCOMPLETE",
                )
                messages.success(
                    request, award + " Application is successfully updated"
                )
                break
            else:
                Director_silver.objects.create(
                    student=student_id,
                    award_id=award_id,
                    cultural_intercollege_certificates_no=cultural_intercollege_certificates_no,
                    cultural_intercollege_team_event=cultural_intercollege_team_event,
                    cultural_intercollege_team_certificates_no=cultural_intercollege_team_certificates_no,
                    culturalfest_certificates_no=culturalfest_certificates_no,
                    cultural_club_coordinator=cultural_club_coordinator,
                    cultural_club_co_coordinator=cultural_club_co_coordinator,
                    cultural_event_member=cultural_event_member,
                    cultural_interIIIT_certificates_no=cultural_interIIIT_certificates_no,
                    cultural_interIIIT_team_certificates_no=cultural_interIIIT_team_certificates_no,
                    sports_club_coordinator=sports_club_coordinator,
                    sports_club_co_coordinator=sports_club_co_coordinator,
                    sports_event_member=sports_event_member,
                    sports_other_accomplishment=sports_other_accomplishment,
                    cultural_intercollege_certificate=cultural_intercollege_certificate,
                    cultural_intercollege_team_certificate=cultural_intercollege_team_certificate,
                    culturalfest_certificate=culturalfest_certificate,
                    cultural_club_coordinator_certificate=cultural_club_coordinator_certificate,
                    cultural_club_co_coordinator_certificate=cultural_club_co_coordinator_certificate,
                    cultural_event_member_certificate=cultural_event_member_certificate,
                    cultural_interIIIT_team_certificate=cultural_interIIIT_team_certificate,
                    cultural_interIIIT_certificate=cultural_interIIIT_certificate,
                    sports_intercollege_certificate=sports_intercollege_certificate,
                    sports_intercollege_team_certificate=sports_intercollege_team_certificate,
                    sportsfest_certificate=sportsfest_certificate,
                    sportsfest_team_certificate=sportsfest_team_certificate,
                    sports_club_coordinator_certificate=sports_club_coordinator_certificate,
                    sports_club_co_coordinator_certificate=sports_club_co_coordinator_certificate,
                    sports_event_member_certificate=sports_event_member_certificate,
                    sports_interIIIT_team_certificate=sports_interIIIT_team_certificate,
                    sports_interIIIT_certificate=sports_interIIIT_certificate,
                    sports_other_accomplishment_doc=sports_other_accomplishment_doc,
                )
                messages.success(
                    request, award + " Application is successfully submitted"
                )
                break
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session["last_clicked"] = "Submit_Silver"
    return HttpResponseRedirect("/spacs/student_view")


def submitDM(request):
    i = Notification.objects.select_related("student_id", "release_id").filter(
        student_id=request.user.extrainfo.id
    )
    for x in i:
        x.invite_convocation_accept_flag = False
        x.save()
    award, award_id = getAwardId(request)
    student_id = request.user.extrainfo.student
    brief_description_project = request.POST.get("brief_description_project")
    project_grade = request.POST.get("project_grades")
    cross_disciplinary = request.POST.get("cross_disciplinary_content")
    project_cross_disciplinary = request.POST.get("project_cross_disciplinary")
    project_publication = request.POST.get("project_publication")
    project_type = request.POST.get("project_type")
    patent_ipr_project = request.POST.get("project_patent_ipr")
    prototype_available = request.POST.get("prototype")
    team_members_name = request.POST.get("members_name")
    team_members_cpi = request.POST.get("members_cpi")
    project_evaluation_prototype = request.POST.get("project_prototype")
    project_utility = request.POST.get("project_utility")
    sports_cultural = request.POST.get("project_sports")
    sci = request.POST.get("sci")
    esci = request.POST.get("esci")
    scie = request.POST.get("scie")
    ij = request.POST.get("ij")
    ic = request.POST.get("ic")
    nc = request.POST.get("nc")
    workshop = request.POST.get("workshop")

    project_evaluation_prototype_doc = (
        request.FILES.get("project_prototype_doc") or None
    )
    project_utility_doc = request.FILES.get("project_utility_doc") or None
    sports_cultural_doc = request.FILES.get("project_sports_doc") or None
    project_cross_disciplinary_doc = (
        request.FILES.get("project_cross_disciplinary_doc") or None
    )
    sci_doc = request.FILES.get("sci_doc") or None
    esci_doc = request.FILES.get("esci_doc") or None
    scie_doc = request.FILES.get("scie_doc") or None
    ij_doc = request.FILES.get("ij_doc") or None
    ic_doc = request.FILES.get("ic_doc") or None
    nc_doc = request.FILES.get("nc_doc") or None
    workshop_doc = request.FILES.get("workshop_doc") or None

    data_insert = {
        "award_id": award_id,
        "brief_description_project": brief_description_project,
        "project_grade": project_grade,
        "cross_disciplinary": cross_disciplinary,
        "project_publication": project_publication,
        "project_type": project_type,
        "patent_ipr_project": patent_ipr_project,
        "prototype_available": prototype_available,
        "team_members_name": team_members_name,
        "team_members_cpi": team_members_cpi,
        "project_evaluation_prototype": project_evaluation_prototype,
        "project_utility": project_utility,
        "sports_cultural": sports_cultural,
        "sci": sci,
        "esci": esci,
        "scie": scie,
        "ij": ij,
        "ic": ic,
        "nc": nc,
        "workshop": workshop,
    }
    try:
        for column in DM_Proficiency_Gold_list:
            validate(
                instance=data_insert[column], schema=DM_Proficiency_Gold_schema[column]
            )
        releases = Release.objects.filter(
            Q(
                startdate__lte=datetime.datetime.today().strftime("%Y-%m-%d"),
                enddate__gte=datetime.datetime.today().strftime("%Y-%m-%d"),
            )
        ).filter(award="Convocation Medals")
        for release in releases:
            existingRelease = (
                DM_Proficiency_gold.objects.select_related("student", "award_id")
                .filter(Q(date__gte=release.startdate, date__lte=release.enddate))
                .filter(student=request.user.extrainfo.student)
            )
            if existingRelease:
                existingRelease.update(
                    student=student_id,
                    award_id=award_id,
                    brief_description_project=brief_description_project,
                    project_grade=project_grade,
                    cross_disciplinary=cross_disciplinary,
                    project_cross_disciplinary=project_cross_disciplinary,
                    project_publication=project_publication,
                    project_type=project_type,
                    patent_ipr_project=patent_ipr_project,
                    prototype_available=prototype_available,
                    team_members_name=team_members_name,
                    team_members_cpi=team_members_cpi,
                    project_evaluation_prototype=project_evaluation_prototype,
                    project_utility=project_utility,
                    sports_cultural=sports_cultural,
                    sci=sci,
                    esci=esci,
                    scie=scie,
                    ij=ij,
                    ic=ic,
                    nc=nc,
                    workshop=workshop,
                    project_evaluation_prototype_doc=project_evaluation_prototype_doc,
                    project_utility_doc=project_utility_doc,
                    sports_cultural_doc=sports_cultural_doc,
                    project_cross_disciplinary_doc=project_cross_disciplinary_doc,
                    sci_doc=sci_doc,
                    esci_doc=esci_doc,
                    scie_doc=scie_doc,
                    ij_doc=ij_doc,
                    ic_doc=ic_doc,
                    nc_doc=nc_doc,
                    workshop_doc=workshop_doc,
                    status="INCOMPLETE",
                )
                messages.success(
                    request, award + " Application is successfully updated"
                )
                break
            else:
                DM_Proficiency_gold.objects.create(
                    student=student_id,
                    award_id=award_id,
                    brief_description_project=brief_description_project,
                    project_grade=project_grade,
                    cross_disciplinary=cross_disciplinary,
                    project_cross_disciplinary=project_cross_disciplinary,
                    project_publication=project_publication,
                    project_type=project_type,
                    patent_ipr_project=patent_ipr_project,
                    prototype_available=prototype_available,
                    team_members_name=team_members_name,
                    team_members_cpi=team_members_cpi,
                    project_evaluation_prototype=project_evaluation_prototype,
                    project_utility=project_utility,
                    sports_cultural=sports_cultural,
                    sci=sci,
                    esci=esci,
                    scie=scie,
                    ij=ij,
                    ic=ic,
                    nc=nc,
                    workshop=workshop,
                    project_evaluation_prototype_doc=project_evaluation_prototype_doc,
                    project_utility_doc=project_utility_doc,
                    sports_cultural_doc=sports_cultural_doc,
                    project_cross_disciplinary_doc=project_cross_disciplinary_doc,
                    sci_doc=sci_doc,
                    esci_doc=esci_doc,
                    scie_doc=scie_doc,
                    ij_doc=ij_doc,
                    ic_doc=ic_doc,
                    nc_doc=nc_doc,
                    workshop_doc=workshop_doc,
                )
                messages.success(
                    request, award + " Application is successfully submitted"
                )
                break
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session["last_clicked"] = "Submit_dm"
    return HttpResponseRedirect("/spacs/student_view")


def submitProficiency(request):
    i = Notification.objects.select_related("student_id", "release_id").filter(
        student_id=request.user.extrainfo.id
    )
    for x in i:
        x.invite_convocation_accept_flag = False
        x.save()
    award, award_id = getAwardId(request)
    student_id = request.user.extrainfo.student
    project_objectives = request.POST.get("project_objectives")
    project_mentor = request.POST.get("project_mentor")
    project_outcome = request.POST.get("project_outcome")
    project_publications = request.POST.get("project_publication")
    research_Or_Patent_Detail = request.POST.get("project_ipr")
    project_Beneficial = request.POST.get("project_benefits")
    improvement_Done = request.POST.get("project_justification")
    project_title = request.POST.get("project_title")
    project_abstract = request.POST.get("project_brief")
    sci = request.POST.get("sci")
    esci = request.POST.get("esci")
    scie = request.POST.get("scie")
    ij = request.POST.get("ij")
    ic = request.POST.get("ic")
    nc = request.POST.get("nc")
    indian_national_Conference = request.POST.get("ic_nc")
    international_Conference = request.POST.get("international_conference")
    project_grade = request.POST.get("project_grade")
    patent_Status = request.POST.get("patent_status")
    interdisciplinary_Criteria = request.POST.get("interdisciplinary_criteria")
    awards_Recieved_Workshop = request.POST.get("awards_recieved")
    placement_Status = request.POST.get("placement_status")
    workshop = request.POST.get("workshop")
    prototype = request.POST.get("thesis_prototype")
    utility = request.POST.get("thesis_utility")
    core_Area = request.POST.get("thesis_core_area")
    technology_Transfer = request.POST.get("work_details")
    project_write_up = request.POST.get("project_write_up")

    project_report = request.FILES.get("project_report") or None
    sci_doc = request.FILES.get("sci_doc") or None
    esci_doc = request.FILES.get("esci_doc") or None
    scie_doc = request.FILES.get("scie_doc") or None
    ij_doc = request.FILES.get("ij_doc") or None
    ic_doc = request.FILES.get("ic_doc") or None
    nc_doc = request.FILES.get("nc_doc") or None
    indian_national_Conference_doc = request.FILES.get("ic_nc_doc") or None
    international_Conference_doc = (
        request.FILES.get("internation_conference_doc") or None
    )
    workshop_doc = request.FILES.get("workshop_doc") or None
    prototype_doc = request.FILES.get("thesis_prototype_doc") or None
    utility_doc = request.FILES.get("thesis_utility_doc") or None
    core_Area_doc = request.FILES.get("thesis_core_area_doc") or None
    technology_Transfer_doc = request.FILES.get("work_details_doc") or None

    data_insert = {
        "project_objectives": project_objectives,
        "project_mentor": project_mentor,
        "project_outcome": project_outcome,
        "research_Or_Patent_Detail": research_Or_Patent_Detail,
        "project_Beneficial": project_Beneficial,
        "improvement_Done": improvement_Done,
        "sci": sci,
        "esci": esci,
        "scie": scie,
        "ij": ij,
        "ic": ic,
        "nc": nc,
        "indian_national_Conference": indian_national_Conference,
        "international_Conference": international_Conference,
        "patent_Status": patent_Status,
        "interdisciplinary_Criteria": interdisciplinary_Criteria,
        "awards_Recieved_Workshop": awards_Recieved_Workshop,
        "placement_Status": placement_Status,
        "workshop": workshop,
        "prototype": prototype,
        "utility": utility,
        "core_Area": core_Area,
        "technology_Transfer": technology_Transfer,
    }
    try:
        for column in IIITDM_Proficiency_list:
            validate(
                instance=data_insert[column], schema=IIITDM_Proficiency_schema[column]
            )
        releases = Release.objects.filter(
            Q(
                startdate__lte=datetime.datetime.today().strftime("%Y-%m-%d"),
                enddate__gte=datetime.datetime.today().strftime("%Y-%m-%d"),
            )
        ).filter(award="Convocation Medals")
        for release in releases:
            existingRelease = (
                IIITDM_Proficiency.objects.select_related("student", "award_id")
                .filter(Q(date__gte=release.startdate, date__lte=release.enddate))
                .filter(student=request.user.extrainfo.student)
            )
            if existingRelease:
                existingRelease.update(
                    student=student_id,
                    award_id=award_id,
                    project_objectives=project_objectives,
                    project_mentor=project_mentor,
                    project_outcome=project_outcome,
                    project_publications=project_publications,
                    research_Or_Patent_Detail=research_Or_Patent_Detail,
                    project_Beneficial=project_Beneficial,
                    improvement_Done=improvement_Done,
                    project_title=project_title,
                    project_abstract=project_abstract,
                    sci=sci,
                    esci=esci,
                    scie=scie,
                    ij=ij,
                    ic=ic,
                    nc=nc,
                    indian_national_Conference=indian_national_Conference,
                    international_Conference=international_Conference,
                    project_grade=project_grade,
                    patent_Status=patent_Status,
                    interdisciplinary_Criteria=interdisciplinary_Criteria,
                    awards_Recieved_Workshop=awards_Recieved_Workshop,
                    placement_Status=placement_Status,
                    workshop=workshop,
                    prototype=prototype,
                    utility=utility,
                    core_Area=core_Area,
                    technology_Transfer=technology_Transfer,
                    project_write_up=project_write_up,
                    project_report=project_report,
                    sci_doc=sci_doc,
                    esci_doc=esci_doc,
                    scie_doc=scie_doc,
                    ij_doc=ij_doc,
                    ic_doc=ic_doc,
                    nc_doc=nc_doc,
                    indian_national_Conference_doc=indian_national_Conference_doc,
                    international_Conference_doc=international_Conference_doc,
                    workshop_doc=workshop_doc,
                    prototype_doc=prototype_doc,
                    utility_doc=utility_doc,
                    core_Area_doc=core_Area_doc,
                    technology_Transfer_doc=technology_Transfer_doc,
                    status="INCOMPLETE",
                )
                messages.success(
                    request, award + " Application is successfully updated"
                )
                break
            else:
                IIITDM_Proficiency.objects.create(
                    student=student_id,
                    award_id=award_id,
                    project_objectives=project_objectives,
                    project_mentor=project_mentor,
                    project_outcome=project_outcome,
                    project_publications=project_publications,
                    research_Or_Patent_Detail=research_Or_Patent_Detail,
                    project_Beneficial=project_Beneficial,
                    improvement_Done=improvement_Done,
                    project_title=project_title,
                    project_abstract=project_abstract,
                    sci=sci,
                    esci=esci,
                    scie=scie,
                    ij=ij,
                    ic=ic,
                    nc=nc,
                    indian_national_Conference=indian_national_Conference,
                    international_Conference=international_Conference,
                    project_grade=project_grade,
                    patent_Status=patent_Status,
                    interdisciplinary_Criteria=interdisciplinary_Criteria,
                    awards_Recieved_Workshop=awards_Recieved_Workshop,
                    placement_Status=placement_Status,
                    workshop=workshop,
                    prototype=prototype,
                    utility=utility,
                    core_Area=core_Area,
                    technology_Transfer=technology_Transfer,
                    project_write_up=project_write_up,
                    project_report=project_report,
                    sci_doc=sci_doc,
                    esci_doc=esci_doc,
                    scie_doc=scie_doc,
                    ij_doc=ij_doc,
                    ic_doc=ic_doc,
                    nc_doc=nc_doc,
                    indian_national_Conference_doc=indian_national_Conference_doc,
                    international_Conference_doc=international_Conference_doc,
                    workshop_doc=workshop_doc,
                    prototype_doc=prototype_doc,
                    utility_doc=utility_doc,
                    core_Area_doc=core_Area_doc,
                    technology_Transfer_doc=technology_Transfer_doc,
                )
                messages.success(
                    request, award + " Application is successfully submitted"
                )
                break
    except ValidationError as exc:
        messages.error(column + " : " + str(exc))
    request.session["last_clicked"] = "Submit_dm"
    return HttpResponseRedirect("/spacs/student_view")


def submitPreviousWinner(request):
    request.session["last_clicked"] = "SubmitPreviousWinner"
    PreviousWinnerAward = request.POST.get("PreviousWinnerAward")
    PreviousWinnerAcadYear = request.POST.get("PreviousWinnerAcadYear")
    PreviousWinnerProgramme = request.POST.get("PreviousWinnerProgramme")
    request.session["PreviousWinnerAward"] = PreviousWinnerAward
    request.session["PreviousWinnerAcadYear"] = PreviousWinnerAcadYear
    request.session["PreviousWinnerProgramme"] = PreviousWinnerProgramme

    award = Award_and_scholarship.objects.get(award_name=PreviousWinnerAward)
    winners = Previous_winner.objects.select_related("student", "award_id").filter(
        year=PreviousWinnerAcadYear, award_id=award, programme=PreviousWinnerProgramme
    )

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
    spi = Spi.objects.all()
    context.update(
        {"source": source, "time": time, "ch": ch, "spi": spi, "release": release}
    )
    context.update(additionalParams)
    return render(request, "scholarshipsModule/scholarships_convener.html", context)


def sendStudentRenderRequest(request, additionalParams={}):
    context = getCommonParams(request)
    ch = Constants.BATCH
    time = Constants.TIME
    mother_occ = Constants.MOTHER_OCC_CHOICES
    source = Constants.FATHER_OCC_CHOICE
    release = Release.objects.all()
    release_count = release.count()
    spi = Spi.objects.all()
    no_of_mcm_filled = len(
        Mcm.objects.select_related("award_id", "student").filter(
            student=request.user.extrainfo.student
        )
    )
    no_of_con_filled = 0
    len(
        Director_silver.objects.select_related("student", "award_id").filter(
            student=request.user.extrainfo.student
        )
    ) + len(
        Director_gold.objects.select_related("student", "award_id").filter(
            student=request.user.extrainfo.student
        )
    )
    +len(
        DM_Proficiency_gold.objects.select_related("student", "award_id").filter(
            student=request.user.extrainfo.student
        )
    )
    +len(
        IIITDM_Proficiency.objects.select_related("student", "award_id").filter(
            student=request.user.extrainfo.student
        )
    )
    #  Here we are fetching the flags from the Notification table of student
    # end of database queries

    # notification flags
    update_mcm_flag = False
    update_con_flag = False
    x_notif_mcm_flag = False
    x_notif_con_flag = False
    student_batch = str(request.user.extrainfo.student.batch)
    for dates in release:
        if checkDate(dates.startdate, dates.enddate):
            if (
                dates.award == "Merit-cum-Means Scholarship"
                and dates.batch == student_batch
                and dates.programme == request.user.extrainfo.student.programme
            ):
                x_notif_mcm_flag = True
                if no_of_mcm_filled > 0:
                    update_mcm_flag = True
            elif (
                dates.award == "Convocation Medals"
                and dates.batch == student_batch
                and dates.programme == request.user.extrainfo.student.programme
            ):
                x_notif_con_flag = True
                if no_of_con_filled > 0:
                    update_con_flag = True
        else:
            if (
                dates.award == "Merit-cum-Means Scholarship"
                and dates.batch == student_batch
            ):
                try:
                    x = (
                        Notification.objects.select_related("student_id", "release_id")
                        .get(student_id=request.user.extrainfo.id, release_id=dates.id)
                        .delete()
                    )
                except:
                    pass
            elif dates.award == "Convocation Medals" and dates.batch == student_batch:
                try:
                    x = (
                        Notification.objects.select_related("student_id", "release_id")
                        .get(student_id=request.user.extrainfo.id, release_id=dates.id)
                        .delete()
                    )
                except:
                    pass

    x = (
        Notification.objects.select_related("student_id", "release_id")
        .filter(student_id=request.user.extrainfo.id)
        .order_by("-release_id__date_time")
    )
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
    context.update(
        {
            "time": time,
            "ch": ch,
            "spi": spi,
            "release": release,
            "release_count": release_count,
            "x_notif_mcm_flag": x_notif_mcm_flag,
            "x_notif_con_flag": x_notif_con_flag,
            "source": source,
            "show_mcm_flag": show_mcm_flag,
            "show_convocation_flag": show_convocation_flag,
            "update_mcm_flag": update_mcm_flag,
            "update_con_flag": update_con_flag,
            "mother_occ": mother_occ,
            "x": x,
        }
    )
    context.update(additionalParams)
    return render(request, "scholarshipsModule/scholarships_student.html", context)


def sendStaffRenderRequest(request, additionalParams={}):
    context = getCommonParams(request)
    context.update(additionalParams)
    return render(request, "scholarshipsModule/scholarships_staff.html", context)


def sendStatsRenderRequest(request, additionalParams={}):
    context = getCommonParams(request)
    context.update(additionalParams)
    return render(request, "scholarshipsModule/stats.html", context)


def getCommonParams(request):
    student = Student.objects.all()
    mcm = Mcm.objects.select_related("award_id", "student").all().values()
    gold = Director_gold.objects.select_related("student", "award_id").all()
    silver = Director_silver.objects.select_related("student", "award_id").all()
    dandm = DM_Proficiency_gold.objects.select_related("student", "award_id").all()
    proficiency = IIITDM_Proficiency.objects.select_related("student", "award_id").all()
    awards = Award_and_scholarship.objects.all()
    con = Designation.objects.get(name="spacsconvenor")
    assis = Designation.objects.get(name="spacsassistant")
    hd = None
    hd1 = None
    try:
        hd = HoldsDesignation.objects.get(designation=con)
        hd1 = HoldsDesignation.objects.get(designation=assis)
    except:
        print("spcacsconvenor or spcacsassistant")
    year_range = range(2013, datetime.datetime.now().year + 1)
    active_batches = range(
        datetime.datetime.now().year - 4, datetime.datetime.now().year + 1
    )
    last_clicked = ""
    try:
        last_clicked = request.session["last_clicked"]
    except:
        print("last_clicked not found")
    context = {
        "mcm": mcm,
        "awards": awards,
        "student": student,
        "gold": gold,
        "silver": silver,
        "dandm": dandm,
        "proficiency": proficiency,
        "con": con,
        "assis": assis,
        "hd": hd,
        "hd1": hd1,
        "last_clicked": last_clicked,
        "year_range": year_range,
        "active_batches": active_batches,
    }
    return context
