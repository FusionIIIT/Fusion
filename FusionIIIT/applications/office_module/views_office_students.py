
from django.shortcuts import render , get_object_or_404
from django.http import HttpResponse , HttpResponseRedirect
from applications.academic_information.models import Meeting
from .models import Constants,hostel_allotment,Budget
from applications.gymkhana.models import Club_budget,Club_info
from applications.globals.models import *
import json
from django.contrib.auth.decorators import login_required

@login_required
def officeOfDeanStudents(request):
    budget_app= Club_budget.objects.all().filter(status='open');
    past_budget=Club_budget.objects.all().exclude(status='open');
    minutes=Meeting.objects.all().filter(minutes_file="");
    final_minutes=Meeting.objects.all().exclude(minutes_file="");
    hall_allotment=hostel_allotment.objects.all()
    clubNew= Club_info.objects.all().filter(status='open')
    club =Club_info.objects.all().exclude(status='open')
    budgets=Club_info.objects.all().filter(status='confirmed')
    approved_budgets=Club_budget.objects.all().filter(status='confirmed')
    budget_allotment= Club_info.objects.all().filter(status='confirmed', alloted_budget=0)
    budget_alloted = Club_info.objects.all().exclude(alloted_budget=0)
    designation = HoldsDesignation.objects.all().filter(working=request.user)
    desig = list(HoldsDesignation.objects.all().filter(working = request.user).values_list('designation'))
    b = [i for sub in desig for i in sub]
    roll_=[]
    for i in b :
        name_ = get_object_or_404(Designation, id = i)
        roll_.append(str(name_.name))

    all_designation=[]
    for i in designation:
        all_designation.append(str(i.designation))
    HALL_NO = (('HALL-1','hall-1'),('HALL-3','hall-3'),('HALL-4','hall-4'))
    hall=[]
    hostel_file= hostel_allotment.objects.all()
    for i in HALL_NO:
        if(str(i[1]) ):  #not in [j.hall_no for j in hostel_file]#
            hall.append(str(i[1]))
    print(roll_)
    context = {'meetingMinutes':minutes,
                'final_minutes':final_minutes,
                'hall': hall,
                'hall_allotment':hall_allotment,
                'budget_app':budget_app,
                'p_budget':past_budget,
                'clubNew':clubNew,
                'club':club,
                'budgets':budgets,
                'approved_budgets':approved_budgets,
                'budget_allotment':budget_allotment,
                'budget_alloted' : budget_alloted,
                'all_designation' : roll_,
                }
    return render(request, "officeModule/officeOfDeanStudents/officeOfDeanStudents.html", context)

"""
    View for the meeting being called by Dean_Student
    Inputs:- Agenda, Date, Time, Venue, Minutes_File
        (*) Minutes file is to be added by JuniorSuprintendent
    An object holdMeeting object is being created and accessed in the holding_form.html template. 
"""
@login_required
def holdingMeeting(request):
    """title= request.POST.get('title')"""
    Agenda = request.POST.get('agenda')
    date = request.POST.get('date')
    Time = request.POST.get('time')
    Venue = request.POST.get('venue')
    Minutes_File = request.POST.get('minutes_file')
    # print(Venue," ",date," ", Time," ",Agenda)

    """An object holdMeeting is created with all the inputs and pushed back"""
    holdMeeting_object=Meeting(venue=Venue,date=date,time=Time,agenda=Agenda,minutes_file= Minutes_File)

    holdMeeting_object.save()
    return HttpResponse('ll')


"""
    View for the minutes of the meeting initiated by the Junior Suprintendent
    Inputs:- file
        (*) Minutes file is to be added by JuniorSuprintendent
    An object meeting_object saves the file 
"""


@login_required
def meetingMinutes(request):
    file=request.FILES['minutes_file']
    id=request.POST.get('id')
    meeting_object=Meeting.objects.get(pk=id)
    meeting_object.minutes_file=file
    meeting_object.save()
    #return HttpResponseRedirect('/office/officeOfDeanStudents/first')
    return render(request, "officeModule/officeModule/officeOfDeanStudents/holdingMeetings.html", context)

@login_required
def hostelRoomAllotment(request):
    file=request.FILES['hostel_file']
    hall_no=request.POST.get('hall_no')
    hostel_allotment_object=hostel_allotment(allotment_file=file,hall_no=hall_no)
    hostel_allotment_object.save()
    return HttpResponseRedirect('/office/officeOfDeanStudents')

@login_required
def budgetApproval(request):
    id_r=request.POST.getlist('check')
    remark=request.POST.getlist('remark')
    for i in range(len(id_r)):
        Club_budget_object=Club_budget.objects.get(id=id_r[i]);
        Club_budget_object.status='confirmed'
        Club_budget_object.remarks=request.POST.get(id_r[i])
        budget= request.POST.get('amount '+ id_r[i])
        spentBudget=Club_budget_object.club.spent_budget
        availBudget= Club_budget_object.club.avail_budget
        Club_info_object=Club_info.objects.get(club_name = Club_budget_object.club.club_name )
        Club_info_object.spent_budget= (spentBudget+int(budget))
        Club_info_object.avail_budget= (availBudget- int(budget))
        Club_budget_object.save()
        Club_info_object.save()
    return HttpResponseRedirect('/office/officeOfDeanStudents')

@login_required
def budgetRejection(request):
    id_r=request.POST.getlist('check')
    remark=request.POST.getlist('remark')
    for i in range(len(id_r)):
        Club_budget_object=Club_budget.objects.get(id=id_r[i]);
        Club_budget_object.status='rejected'
        Club_budget_object.remarks=request.POST.get(id_r[i])
        Club_budget_object.save()
    return HttpResponseRedirect('/office/officeOfDeanStudents')


@login_required
def clubApproval(request):
    id_r=request.POST.getlist('check')
    for i in range(len(id_r)):
        Club_info_object=Club_info.objects.get(pk=id_r[i])
        co_ordinator= Club_info_object.co_ordinator.id.user
        co_co = Club_info_object.co_coordinator.id.user
        Club_info_object.status='confirmed'
        Club_info_object.save()
        designation = get_object_or_404(Designation, name="co-ordinator")
        designation1 = get_object_or_404(Designation, name="co co-ordinator")
        HoldsDesig= HoldsDesignation(user=co_ordinator,working=co_ordinator,designation=designation)
        HoldsDesig.save()
        HoldsDesig = HoldsDesignation( user= co_co, working= co_co, designation=designation1)
        HoldsDesig.save()
    return HttpResponseRedirect('/office/officeOfDeanStudents')
    return render(request, "officeModule/officeModule / officeOfDeanStudents / newClubApprovals.html", context)

@login_required
def clubRejection(request):
    id_r=request.POST.getlist('check')
    for i in range(len(id_r)):
        Club_info_object=Club_info.objects.get(pk=id_r[i]);
        Club_info_object.status='rejected'
        Club_info_object.save()
    return HttpResponseRedirect('/office/officeOfDeanStudents')

@login_required
def budgetAllot(request):
    id_r=request.POST.get('id')
    budget= request.POST.get('budget')
    Club_info_object= Club_info.objects.get(pk=id_r)
    Club_info_object.alloted_budget=int(budget)
    Club_info_object.avail_budget= int(budget)
    Club_info_object.save()
    return HttpResponseRedirect('/office/officeOfDeanStudents')


@login_required
def budgetAllotEdit(request):
    id_r=request.POST.get('id')
    budget= request.POST.get('budget')
    Club_info_object= Club_info.objects.get(pk=id_r)
    Club_info_object.alloted_budget=int(budget)
    Club_info_object.avail_budget= int(budget)
    Club_info_object.spent_budget= int(0)
    Club_info_object.save()
    return HttpResponseRedirect('/office/officeOfDeanStudents')
