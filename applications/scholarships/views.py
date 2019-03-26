# from django.shortcuts import render

# Create your views here.
# from django.shortcuts import render

# Create your views here.
# from django.shortcuts import render

import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.shortcuts import render

from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)

from .models import (Award_and_scholarship, Constants, Director_gold,
                     Director_silver, Mcm, Notional_prize, Previous_winner,
                     Proficiency_dm, Release)

# Create your views here.


@login_required(login_url='/accounts/login')
def spacs(request):
    # context = {}
    convener = Designation.objects.get(name='spacsconvenor')
    assistant = Designation.objects.get(name='spacsassistant')
    hd = HoldsDesignation.objects.filter(user=request.user,designation=convener)
    hd1 = HoldsDesignation.objects.filter(user=request.user,designation=assistant)
    if request.user.extrainfo.user_type == 'student':
        return HttpResponseRedirect('/spacs/student_view')
    elif hd:
        return HttpResponseRedirect('/spacs/convener_view')
    elif hd1:
        return HttpResponseRedirect('/spacs/staff_view')


@login_required(login_url='/accounts/login')
def convener_view(request):
    if request.method == 'POST':
        if 'Submit' in request.POST:
            award = request.POST.get('type')
            from_date = request.POST.get('From')
            to_date = request.POST.get('To')
            remarks = request.POST.get('remarks')

            Release.objects.create(
                startdate=from_date,
                enddate=to_date,
                award=award,
                remarks=remarks
            )
            messages.success(request,award+' are invited successfully')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Email' in request.POST:
            year = request.POST.get('year')
            spi = request.POST.get('spi')
            cpi = request.POST.get('cpi')
            award = request.POST.get('award')
            a = Award_and_scholarship.objects.get(award_name=award).id
            award_id = Award_and_scholarship.objects.get(id=a)
            Notional_prize.objects.create(
                year=year,
                spi=spi,
                cpi=cpi,
                award_id=award_id
            )
            messages.success(request,award+' are invited successfully')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_mcm' in request.POST:
            pk = request.POST.get('id')
            award = Mcm.objects.get(id=pk).award_id
            student_id = Mcm.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Mcm.objects.filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Reject_mcm' in request.POST:
            pk = request.POST.get('id')
            student_id = Mcm.objects.get(id=pk).student
            Mcm.objects.filter(id=pk).update(status='Reject')
            messages.success(request,'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_gold' in request.POST:
            pk = request.POST.get('id')
            award = Director_gold.objects.get(id=pk).award_id
            student_id = Director_gold.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Director_gold.objects.filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Reject_gold' in request.POST:
            pk = request.POST.get('id')
            student_id = Director_gold.objects.get(id=pk).student
            Director_gold.objects.filter(id=pk).update(status='Reject')
            messages.success(request,'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_silver' in request.POST:
            pk = request.POST.get('id')
            award = Director_silver.objects.get(id=pk).award_id
            student_id = Director_silver.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Director_silver.objects.filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Reject_silver' in request.POST:
            pk = request.POST.get('id')
            student_id = Director_silver.objects.get(id=pk).student
            Director_silver.objects.filter(id=pk).update(status='Reject')
            messages.success(request,'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Accept_dm' in request.POST:
            pk = request.POST.get('id')
            award = Proficiency_dm.objects.get(id=pk).award_id
            student_id = Proficiency_dm.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Proficiency_dm.objects.filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Rejec_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='Reject')
            student_id = Proficiency_dm.objects.get(id=pk).student
            messages.success(request,'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')


    else:
        mcm = Mcm.objects.all()
        ch = Constants.batch
        source = Constants.father_occ_choice
        time = Constants.time
        release = Release.objects.all()
        winners = Previous_winner.objects.all()
        spi = Spi.objects.all()
        student = Student.objects.all()
        awards = Award_and_scholarship.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
        con = Designation.objects.get(name='spacsconvenor')
        assis = Designation.objects.get(name='spacsassistant')
        hd = HoldsDesignation.objects.get(designation=con)
        hd1 = HoldsDesignation.objects.get(designation=assis)
        context={'mcm': mcm, 'source': source, 'time': time, 'ch': ch, 'awards': awards,
                   'spi': spi, 'student': student, 'winners': winners, 'release': release,
                   'gold': gold, 'silver': silver, 'dandm': dandm, 'con': con, 'assis': assis,
                    'hd': hd, 'hd1': hd1
                   }

        return render(request, 'scholarshipsModule/scholarships_convener.html',context)


@login_required(login_url='/accounts/login')
def student_view(request):
    if request.method == 'POST':
        if 'Submit_mcm' in request.POST:
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
            a = Award_and_scholarship.objects.get(award_name="Mcm").id
            award_id = Award_and_scholarship.objects.get(id=a)
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
                college_name=college_name
            )
            messages.success(request,'Mcm scholarhsip is successfully applied')
            return HttpResponseRedirect('/spacs/student_view')

        elif 'Submit_gold' in request.POST:
            relevant_document = request.FILES.get('myfile')
            student_id = request.user.extrainfo.student
            a = Award_and_scholarship.objects.get(award_name="Director Gold Medal").id
            award_id = Award_and_scholarship.objects.get(id=a)
            academic_achievements = request.POST.get('academic_achievements')
            science_inside = request.POST.get('science_inside')
            science_outside = request.POST.get('science_outside')
            games_inside = request.POST.get('games_inside')
            games_outside = request.POST.get('games_outside')
            cultural_inside = request.POST.get('cultural_inside')
            cultural_outside = request.POST.get('cultural_outside')
            social = request.POST.get('social')
            coorporate = request.POST.get('coorporate')
            hall_activities = request.POST.get('hall_activities')
            gymkhana_activities = request.POST.get('gymkhana_activities')
            institute_activities = request.POST.get('institute_activities')
            counselling_activities = request.POST.get('counselling_activities')
            other_activites = request.POST.get('other_activites')
            justification = request.POST.get('justification')
            correspondence_address=request.POST.get('c_address')
            financial_assistance=request.POST.get('financial_assistance')
            grand_total=request.POST.get('grand_total')
            nearest_policestation=request.POST.get('nps')
            nearest_railwaystation=request.POST.get('nrs')

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
                coorporate=coorporate,
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
            messages.success(request,'Application is successfully submitted')
            return HttpResponseRedirect('/spacs/student_view')

        elif 'Submit_silver' in request.POST:
            relevant_document = request.FILES.get('myfile')
            award = request.POST.get('award')
            a = Award_and_scholarship.objects.get(award_name=award).id
            award_id = Award_and_scholarship.objects.get(id=a)
            student_id = request.user.extrainfo.student
            inside_achievements = request.POST.get('inside_achievements')
            outside_achievements = request.POST.get('outside_achievements')
            justification = request.POST.get('justification')
            correspondence_address=request.POST.get('c_address')
            financial_assistance=request.POST.get('financial_assistance')
            grand_total=request.POST.get('grand_total')
            nearest_policestation=request.POST.get('nps')
            nearest_railwaystation=request.POST.get('nrs')

            Director_silver.objects.create(
                student=student_id,
                award_id=award_id,
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

            messages.success(request,'Application is successfully submitted')
            return HttpResponseRedirect('/spacs/student_view')


        elif 'Submit_dandm' in request.POST:
            title_name = request.POST.get('title')
            no_of_students = request.POST.get('students')
            relevant_document = request.FILES.get('myfile')
            award = request.POST.get('award')
            a = Award_and_scholarship.objects.get(award_name=award).id
            award_id = Award_and_scholarship.objects.get(id=a)
            student_id = request.user.extrainfo.student
            try:
                roll_no1 = int(request.POST.get('roll_no1'))
            except:
                roll_no1=0

            try:
                roll_no2 = int(request.POST.get('roll_no2'))
            except:
                roll_no2=0

            try:
                roll_no3 = int(request.POST.get('roll_no3'))
            except:
                roll_no3=0

            try:
                roll_no4 = int(request.POST.get('roll_no4'))
            except:
                roll_no4=0

            try:
                roll_no5 = int(request.POST.get('roll_no5'))
            except:
                roll_no5=0

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
            correspondence_address=request.POST.get('c_address')
            financial_assistance=request.POST.get('financial_assistance')
            grand_total=request.POST.get('grand_total')
            nearest_policestation=request.POST.get('nps')
            nearest_railwaystation=request.POST.get('nrs')


            Proficiency_dm.objects.create(
                title_name=title_name,
                no_of_students=no_of_students,
                student=student_id,
                award_id=award_id,
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

            messages.success(request,'Application is successfully submitted')
            return HttpResponseRedirect('/spacs/student_view')


    else:
        mcm = Mcm.objects.all()
        ch = Constants.batch
        time = Constants.time
        mother_occ = Constants.MOTHER_OCC_CHOICES
        source = Constants.father_occ_choice
        release = Release.objects.all()
        winners = Previous_winner.objects.all()
        spi = Spi.objects.all()
        student = Student.objects.all()
        awards = Award_and_scholarship.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
        con = Designation.objects.get(name='spacsconvenor')
        assis = Designation.objects.get(name='spacsassistant')
        hd = HoldsDesignation.objects.get(designation=con)
        hd1 = HoldsDesignation.objects.get(designation=assis)
        return render(request, 'scholarshipsModule/scholarships_student.html',
                  {'mcm': mcm, 'time': time, 'ch': ch, 'awards': awards, 'spi': spi,
                   'student': student, 'winners': winners, 'release': release,
                   'gold': gold, 'silver': silver, 'dandm': dandm, 'source': source,
                  'mother_occ': mother_occ, 'con': con, 'assis': assis,'hd': hd, 'hd1': hd1})


@login_required(login_url='/accounts/login')
def staff_view(request):
    if request.method == 'POST':
        if 'Verify_mcm' in request.POST:
            pk = request.POST.get('id')
            Mcm.objects.filter(id=pk).update(status='COMPLETE')
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Reject_mcm' in request.POST:
            pk = request.POST.get('id')
            Mcm.objects.filter(student=pk).update(status='Reject')
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='COMPLETE')
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')
        elif 'Reject_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='Reject')
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='COMPLETE')
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')
        elif 'Reject_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='Reject')
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='COMPLETE')
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')
        elif 'Rejec_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='Reject')
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')
    else:
        mcm = Mcm.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
        student = Student.objects.all()
        awards = Award_and_scholarship.objects.all()
        winners = Previous_winner.objects.all()
        con = Designation.objects.get(name='spacsconvenor')
        assis = Designation.objects.get(name='spacsassistant')
        hd = HoldsDesignation.objects.get(designation=con)
        hd1 = HoldsDesignation.objects.get(designation=assis)

        return render(request, 'scholarshipsModule/scholarships_staff.html',
                  {'mcm': mcm, 'student': student,
                   'awards': awards, 'gold': gold,
                   'silver': silver, 'dandm': dandm, 'winners': winners,
                   'con': con, 'assis': assis,'hd': hd, 'hd1': hd1})


def convener_catalogue(request):
    if request.method == 'POST':
        award_name=request.POST.get('award_name')
        catalog_content=request.POST.get('catalog_content')
        context = {}
        try:
            award=Award_and_scholarship.objects.get(award_name=award_name)
            award.catalog=catalog_content
            award.save()
            context['result']='Success'
        except:
            context['result']='Failure'
        return HttpResponse(json.dumps(context), content_type='convener_catalogue/json')

    else:
        award_name=request.GET.get('award_name')
        print(award_name)
        context = {}
        try:
            award = Award_and_scholarship.objects.get(award_name=award_name)
            context['catalog']=award.catalog
            context['result'] = 'Success'
        except:
            context['result'] = 'Failure'
        return HttpResponse(json.dumps(context), content_type='convener_catalogue/json')


def get_winners(request):
    award_name = request.GET.get('award_name')
    batch_year = int(request.GET.get('batch'))
    award=Award_and_scholarship.objects.get(award_name=award_name)
    print(award_name,award)
    print(batch_year)
    winners=Previous_winner.objects.filter(year=batch_year,award_id=award)
    context={}
    context['student_name']=[]
    context['student_program'] = []
    context['roll']=[]


    if winners:
        for winner in winners:

            extra_info = ExtraInfo.objects.get(id=winner.student_id)
            s_id = Student.objects.get(id=extra_info)
            s_name = extra_info.user.first_name
            s_roll = winner.student_id
            s_program=s_id.programme
            print(s_roll,type(s_roll))
            context['student_name'].append(s_name)
            context['roll'].append(s_roll)
            context['student_program'].append(s_program)

        context['result']='Success'

    else:
        context['result']='Failure'

    return HttpResponse(json.dumps(context), content_type='get_winners/json')


def get_content(request):
    print('data is coming through')
    award_name=request.GET.get('award_name')
    print(award_name)
    context={}
    try:
        award = Award_and_scholarship.objects.get(award_name=award_name)
        context['result']='Success'
        context['content']=award.catalog

    except:
        context['result']='Failure'

    return HttpResponse(json.dumps(context), content_type='get_content/json')
