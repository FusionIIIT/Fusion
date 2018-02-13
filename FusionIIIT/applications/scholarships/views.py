# from django.shortcuts import render

# Create your views here.
# from django.shortcuts import render

# Create your views here.
# from django.shortcuts import render

import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.shortcuts import render

from applications.academic_information.models import Spi, Student
from applications.globals.models import Designation, HoldsDesignation

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
            award_id = Award_and_scholarship.objects.get(id=award)
            from_date = request.POST.get('From')
            to_date = request.POST.get('To')
            batch = request.POST.get('batch')
            time = request.POST.get('time')
            venue = request.POST.get('venue')

            Release.objects.create(
                startdate=from_date,
                enddate=to_date,
                time=time,
                venue=venue,
                batch=batch,
                award_id=award_id,
            )
            return HttpResponse('completed invite')

        elif 'Email' in request.POST:
            year = request.POST.get('year')
            spi = request.POST.get('spi')
            cpi = request.POST.get('cpi')

            Notional_prize.objects.create(
                year=year,
                spi=spi,
                cpi=cpi
            )
            return HttpResponse('completed notionalprize')

        elif 'a1' in request.POST:
            award = request.POST['award']
            Award_and_scholarship.objects.filter(award_name="Mcm").update(catalog=award)
            return HttpResponse('')

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
            return HttpResponse('updated sucessfully')
        elif 'Reject_mcm' in request.POST:
            pk = request.POST.get('id')
            Mcm.objects.filter(id=pk).update(status='Reject')
            return HttpResponse('updated Successfully')

        elif 'Accept_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='Accept')
            award = Director_gold.objects.get(id=pk).award_id
            student_id = Director_gold.objects.get(id=pk).student
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            return HttpResponse('updated sucessfully')
        elif 'Reject_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='Reject')
            return HttpResponse('updated Successfully')

        elif 'Accept_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='Accept')
            award = Director_silver.objects.get(id=pk).award_id
            student_id = Director_silver.objects.get(id=pk).student
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            return HttpResponse('updated sucessfully')
        elif 'Reject_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='Reject')
            return HttpResponse('updated Successfully')

        elif 'Accept_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='Accept')
            award = Proficiency_dm.objects.get(id=pk).award_id
            student_id = Proficiency_dm.objects.get(id=pk).student
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            return HttpResponse('updated sucessfully')
        elif 'Rejec_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='Reject')
            return HttpResponse('updated Successfully')


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
        context={'mcm': mcm, 'source': source, 'time': time, 'ch': ch, 'awards': awards,
                   'spi': spi, 'student': student, 'winners': winners, 'release': release,
                   'gold': gold, 'silver': silver, 'dandm': dandm}

    return render(request, 'scholarshipsModule/scholarships_convener.html',context)


@login_required(login_url='/accounts/login')
def student_view(request):
    if request.method == 'POST':
        if 'Submit_mcm' in request.POST:
            father_occ = request.POST.get('father_occ')
            mother_occ = request.POST.get('mother_occ')
            brother_name = request.POST.get('brother_name')
            sister_name = request.POST.get('sister_name')
            income_father = int(request.POST.get('father_income'))
            income_mother = int(request.POST.get('mother_income'))
            income_other = int(request.POST.get('other_income'))
            brother_occupation = request.POST.get('brother_occupation')
            sister_occupation = request.POST.get('sister_occupation')
            relevant_document = request.FILES.get('myfile')
            student = request.user.extrainfo.student
            annual_income = income_father + income_mother + income_other
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
                relevant_document=relevant_document
            )
            return HttpResponse('Submitted_mcm form')

        elif 'Submit_gold' in request.POST:
            c_address = request.POST.get('c_address')
            relevant_document = request.FILES.get('myfile')
            nps = request.POST.get('nps')
            nrs = request.POST.get('nrs')
            student_id = request.user.extrainfo.student
            Director_gold.objects.create(
                correspondence_address=c_address,
                nearest_policestation=nps,
                student=student_id,
                relevant_document=relevant_document,
                nearest_railwaystation=nrs
            )

            return HttpResponse('gold medal submitted')

        elif 'Submit_silver' in request.POST:
            c_address = request.POST.get('c_address')
            relevant_document = request.FILES.get('myfile')
            nps = request.POST.get('nps')
            nrs = request.POST.get('nrs')
            award = request.POST.get('type')
            award_id = Award_and_scholarship.objects.get(id=award)
            student_id = request.user.extrainfo.student
            Director_silver.objects.create(
                correspondence_address=c_address,
                nearest_policestation=nps,
                student=student_id,
                award_id=award_id,
                relevant_document=relevant_document,
                nearest_railwaystation=nrs
            )

            return HttpResponse('silver medal submitted')

        elif 'Submit_dandm' in request.POST:
            title_name = request.POST.get('title')
            no_of_students = request.POST.get('students')
            c_address = request.POST.get('c_address')
            relevant_document = request.FILES.get('myfile')
            nps = request.POST.get('nps')
            nrs = request.POST.get('nrs')
            award = request.POST.get('type')
            award_id = Award_and_scholarship.objects.get(id=award)
            student_id = request.user.extrainfo.student
            Proficiency_dm.objects.create(
                correspondence_address=c_address,
                title_name=title_name,
                no_of_students=no_of_students,
                nearest_policestation=nps,
                student=student_id,
                award_id=award_id,
                relevant_document=relevant_document,
                nearest_railwaystation=nrs
            )

            return HttpResponse('proficiency medal submitted')

    else:
        mcm = Mcm.objects.all()
        ch = Constants.batch
        time = Constants.time
        release = Release.objects.all()
        winners = Previous_winner.objects.all()
        spi = Spi.objects.all()
        student = Student.objects.all()
        awards = Award_and_scholarship.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
    return render(request, 'scholarshipsModule/scholarships_student.html',
                  {'mcm': mcm, 'time': time, 'ch': ch, 'awards': awards, 'spi': spi,
                   'student': student, 'winners': winners, 'release': release,
                   'gold': gold, 'silver': silver, 'dandm': dandm})


@login_required(login_url='/accounts/login')
def staff_view(request):
    if request.method == 'POST':
        if 'Verify_mcm' in request.POST:
            pk = request.POST.get('id')
            Mcm.objects.filter(id=pk).update(status='COMPLETE')
            return HttpResponse('updated sucessfully')
        elif 'Reject_mcm' in request.POST:
            pk = request.POST.get('id')
            Mcm.objects.filter(student=pk).update(status='Reject')
            return HttpResponse('updated Successfully')

        elif 'Verify_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='COMPLETE')
            return HttpResponse('updated sucessfully')
        elif 'Reject_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='Reject')
            return HttpResponse('updated Successfully')

        elif 'Verify_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='COMPLETE')
            return HttpResponse('updated sucessfully')
        elif 'Reject_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='Reject')
            return HttpResponse('updated Successfully')

        elif 'Verify_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='COMPLETE')
            return HttpResponse('updated sucessfully')
        elif 'Rejec_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='Reject')
            return HttpResponse('updated Successfully')
    else:
        mcm = Mcm.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
        student = Student.objects.all()
        awards = Award_and_scholarship.objects.all()
        winners = Previous_winner.objects.all()

    return render(request, 'scholarshipsModule/scholarships_staff.html',
                  {'mcm': mcm, 'student': student,
                   'awards': awards, 'gold': gold,
                   'silver': silver, 'dandm': dandm, 'winners': winners})
