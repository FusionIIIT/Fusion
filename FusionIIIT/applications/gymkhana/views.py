from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from applications.academic_information.models import Student
from applications.globals.models import *

from .models import *


def retrun_content(roll, name, desig):
	students = ExtraInfo.objects.all().filter(user_type = "student")
	faculty = ExtraInfo.objects.all().filter(user_type = "faculty")
	club_name = Club_info.objects.all()
	club_member = Club_member.objects.all()
	fest_budget = Fest_budget.objects.all()
	club_budget = Club_budget.objects.all()
	club_session = Session_info.objects.all()
	club_event = Club_report.objects.all()

	# user = name +" - "+ roll
	b=[]
	##    print (roll, name, desig)
	if 'student' in desig:
		user_name = get_object_or_404(User, username = str(roll))
		extra = get_object_or_404(ExtraInfo, id = roll, user = user_name)
		student = get_object_or_404(Student, id = extra)

		# curr_club = list(Club_member.objects.all().filter(member = student).values_list('club'))

		# b = [i for sub in curr_club for i in sub]
		##    print (b)
	else :
		b = []
	# #    print roll, name.lower()

	content = {
		'Students' : students,
		'Club_name' : club_name,
		'Faculty' : faculty,
		'Club_member' : club_member,
		'Fest_budget' : fest_budget,
		'Club_budget' : club_budget,
		'Club_session': club_session,
		'Club_event' : club_event,
		'Curr_club' : b,
		'Curr_desig' : desig
	}
	return content

@login_required
def gymkhana(request):
	roll = request.user
	name = request.user.first_name +"_"+ request.user.last_name
	desig = list(HoldsDesignation.objects.all().filter(working = request.user).values_list('designation'))
	b = [i for sub in desig for i in sub]
	roll_ = []
	for i in b :
		name_ = get_object_or_404(Designation, id = i)
		# #    #    print name_
		roll_.append(str(name_.name))

	return render(request, "gymkhanaModule/gymkhana.html", retrun_content(roll, name, roll_))

@login_required
def club_membership(request):
	if request.method == 'POST':
		#getting form data
		user = request.POST.get("user_name")
		club = request.POST.get("club")
		pda = request.POST.get("pda")

		#getting queryset class objects
		#user_name = User.objects.get(username = user[-7:])
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username = USER[1])
		extra = get_object_or_404(ExtraInfo, id = USER[0], user = user_name)
		student = get_object_or_404(Student, id = extra)
		#extra = ExtraInfo.objects.get(id = user[:-10], user = user_name)
		#student = Student.objects.get(id = extra)

		club_name = get_object_or_404(Club_info, club_name = club)

		#saving data to the database
		club_member = Club_member(member = student, club = club_name, description = pda)
		club_member.save()
		messages.success(request,"Successfully sent the application !!!")

	return redirect('/gymkhana/')

@login_required
def core_team(request):
	if request.method == 'POST':
		#getting form data
		user = request.POST.get("user_name")
		fest = request.POST.get("fest")
		team = request.POST.get("team")
		pda = request.POST.get("pda")
		year = request.POST.get("year")

		#getting queryset class objects
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username = USER[1])
		extra = get_object_or_404(ExtraInfo, id = USER[00], user = user_name)
		student = get_object_or_404(Student, id = extra)


		#saving data to the database
		core_team = Core_team(student_id = student, fest_name = fest, team = team, pda = pda, year = year)
		core_team.save()
		messages.success(request,"Successfully applied for the post !!!")

	return redirect('/gymkhana/')

@login_required
def new_club(request):
	if request.method == 'POST' and request.FILES["file"]:
		club_name = request.POST.get("club_name")
		category = request.POST.get("category")
		co = request.POST.get("co")
		coco = request.POST.get("coco")
		faculty = request.POST.get("faculty")
		club_file = request.FILES["file"]
		d_d = request.POST.get("d_d")

		#getting queryset class objects
		CO = co.split(' - ')
		user_name = get_object_or_404(User, username = CO[1])
		extra = get_object_or_404(ExtraInfo, id = CO[0], user = user_name)
		co_student = get_object_or_404(Student, id = extra)

		#getting queryset class objects
		COCO = coco.split(' - ')
		user_name = get_object_or_404(User, username = COCO[1])
		extra = get_object_or_404(ExtraInfo, id = COCO[0], user = user_name)
		coco_student = get_object_or_404(Student, id = extra)

		#    #    print "----------------------------------"
		#    #    print COCO[1]
		#    #    print COCO[0]
		#    print "----------------------------"
		#getting queryset class objects
		faculty = faculty.split(" - ")
		user_name = get_object_or_404(User, username = faculty[1])
		faculty = get_object_or_404(ExtraInfo, id = faculty[0], user = user_name)
		faculty_inc = get_object_or_404(Faculty, id = faculty)

		club_file.name = club_name+"_club_file"

		club_info = Club_info(club_name = club_name, category = category, co_ordinator = co_student, co_coordinator = coco_student, faculty_incharge = faculty_inc, club_file = club_file, description = d_d)
		club_info.save()

		messages.success(request,"Successfully sent the request !!!")

	return redirect('/gymkhana/')

@login_required
def event_report(request):
	if request.method == 'POST':
		#getting form data
		##    print(request.POST, ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
		user = request.POST.get("st_inc")
		event = request.POST.get("event")
		d_d = request.POST.get("d_d")
		date = request.POST.get("date")
		time = request.POST.get("time")
		report = request.FILES["report"]
		report.name = event+"_report"

		#getting queryset class objects
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username = USER[1])
		extra = get_object_or_404(ExtraInfo, id = USER[0], user = user_name)

		#saving data to the database
		other_report = Other_report(incharge = extra, event_name = event, date = date+" "+time, event_details = report, description = d_d)
		other_report.save()
		messages.success(request,"Successfully saved the report !!!")

	return redirect('/gymkhana/')

@login_required
def club_budget(request):
	if request.method == 'POST' and request.FILES['budget_file']:
		club = request.POST.get("club")
		budget_for = request.POST.get("budget_for")
		budget_amt = request.POST.get('amount')
		budget_file = request.FILES['budget_file']
		desc = request.POST.get('d_d')
		budget_file.name = club+"_budget"
		club_name = get_object_or_404(Club_info, club_name = club)

		club_budget = Club_budget(club = club_name,budget_amt = budget_amt, budget_file = budget_file, budget_for = budget_for, description = desc)
		club_budget.save()
		messages.success(request,"Successfully requested for the budget !!!")

	return redirect('/gymkhana/')

@login_required
def act_calender(request):
	if request.method == "POST":
		#    print "-------------------"
		#    print request.FILES['act_file']
		club = request.POST.get("club")
		act_calender = request.FILES['act_file']
		act_calender.name = club+"_act_calender"

		#club_name = get_object_or_404(Club_info, club_name = club)

		club_info = get_object_or_404(Club_info, club_name = club)
		club_info.activity_calender = act_calender
		#    print "---------------"
		#    print club_info.activity_calender
		club_info.save()
		messages.success(request,"Successfully uploaded the calender !!!")

	return redirect('/gymkhana/')
	# return HttpResponse("success")

@login_required
def club_report(request):
	if request.method == 'POST' and request.FILES['report']:
		#getting form data
		##    print(request.POST, ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
		club = request.POST.get('club')
		user = request.POST.get("s_inc")
		event = request.POST.get("event")
		d_d = request.POST.get("d_d")
		date = request.POST.get("date")
		time = request.POST.get("time")
		report = request.FILES["report"]
		report.name = club+"_"+event+"_report"

		#getting queryset class objects
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username = USER[1])
		extra = get_object_or_404(ExtraInfo, id = USER[0], user = user_name)

		club_name = get_object_or_404(Club_info, club_name = club)

		#saving data to the database
		club_report = Club_report(club = club_name, incharge = extra, event_name = event, date = date+" "+time, event_details = report, description = d_d)
		club_report.save()
		messages.success(request,"Successfully updated the report !!!")

	return redirect('/gymkhana/')

@login_required
def change_head(request):
	if request.method == "POST" :
		club = request.POST.get("club")
		co = request.POST.get('co')
		coco = request.POST.get('coco')
		date = request.POST.get("date")
		time = request.POST.get("time")
		desc = "co-ordinator and co co-ordinator changed on "+date+" at "+time

		club_name = get_object_or_404(Club_info, club_name = club)

		#getting queryset class objects
		CO = co.split(' - ')
		user_name = get_object_or_404(User, username = CO[1])
		extra = get_object_or_404(ExtraInfo, id = CO[0], user = user_name)
		co_student = get_object_or_404(Student, id = extra)

		#getting queryset class objects
		COCO = coco.split(' - ')
		user_name1 = get_object_or_404(User, username = COCO[1])
		extra1 = get_object_or_404(ExtraInfo, id = COCO[0], user = user_name1)
		coco_student = get_object_or_404(Student, id = extra1)

		club_info = get_object_or_404(Club_info, club_name = club_name)

		old_co = club_info.co_ordinator.id.user
		old_coco = club_info.co_coordinator.id.user
		#    print "--------111"
		#    print old_coco, old_co

		club_info.co_ordinator = co_student
		club_info.co_coordinator = coco_student
		club_info.save()

		designation = get_object_or_404(Designation, name = "co-ordinator")
		get_object_or_404(HoldsDesignation, user = old_co, designation = designation).delete()
		HoldsDesig = HoldsDesignation(user = user_name, working = user_name, designation = designation)
		HoldsDesig.save()

		designation = get_object_or_404(Designation, name = "co co-ordinator")
		get_object_or_404(HoldsDesignation, user = old_coco, designation = designation).delete()
		HoldsDesig = HoldsDesignation(user = user_name1, working = user_name1, designation = designation)
		HoldsDesig.save()

		messages.success(request,"Successfully changed the club heads !!!")

	return redirect('/gymkhana/')

@login_required
def new_session(request):
	if request.method == "POST":
		club = request.POST.get("club")
		date = request.POST.get("date")
		time = request.POST.get("time")
		venue = request.POST.get("venue")
		desc = request.POST.get("d_d")

		club_name = get_object_or_404(Club_info, club_name = club)

		session = Session_info(club = club_name, venue = venue, date = date+" "+time, details = desc)
		session.save()
		messages.success(request,"Successfully created the session !!!")

	return redirect('/gymkhana/')

@login_required
def fest_budget(request):
	if request.method == 'POST' and request.FILES['file']:
		fest = request.POST.get("fest")
		budget_amt = request.POST.get('amount')
		budget_file = request.FILES['file']
		desc = request.POST.get('d_d')
		year = request.POST.get('year')
		budget_file.name = fest+"_budget_"+year

		fest_budget = Fest_budget(fest = fest, budget_amt = budget_amt, budget_file = budget_file, description = desc, year = year)
		fest_budget.save()
		messages.success(request,"Successfully uploaded the budget !!!")

	return redirect('/gymkhana/')

@login_required
def approve(request):

	lis = list(request.POST.getlist('check'))

	for user in lis :
		#pos = lis.index(user)
		re = "remarks"+user
		remarks = request.POST.getlist(re)
		user = user.split(',')
		info = user[0].split(' - ')

		#getting queryset class objects
		user_name = get_object_or_404(User, username = info[1])
		extra1 = get_object_or_404(ExtraInfo, id = info[0], user = user_name)
		student = get_object_or_404(Student, id = extra1)

		club_member = get_object_or_404(Club_member, club = user[1], member = student)
		club_member.status = "confirmed"
		club_member.remarks = remarks[0]
		club_member.save()
		messages.success(request,"Successfully Approved !!!")

	return redirect ('/gymkhana/')

@login_required
def reject(request):

	lis = list(request.POST.getlist('check'))

	for user in lis :
		#pos = lis.index(user)
		re = "remarks"+user
		remarks = request.POST.getlist(re)
		user = user.split(',')
		info = user[0].split(' - ')

		#getting queryset class objects
		user_name = get_object_or_404(User, username = info[1])
		extra1 = get_object_or_404(ExtraInfo, id = info[0], user = user_name)
		student = get_object_or_404(Student, id = extra1)

		club_member = get_object_or_404(Club_member, club = user[1], member = student)
		club_member.status = "rejectd"
		club_member.remarks = remarks[0]
		club_member.save()
		messages.success(request,"Successfully rejected !!!")

	return redirect ('/gymkhana/')

@login_required
def cancel(request):

	lis = list(request.POST.getlist('check'))

	for user in lis :
		#pos = lis.index(user)
		user = user.split(',')
		info = user[0].split(' - ')

		#getting queryset class objects
		user_name = get_object_or_404(User, username = info[1])
		extra1 = get_object_or_404(ExtraInfo, id = info[0], user = user_name)
		student = get_object_or_404(Student, id = extra1)

		club_member = get_object_or_404(Club_member, club = user[1], member = student)

		club_member.delete()
		messages.success(request,"Successfully deleted !!!")

	return redirect ('/gymkhana/')
