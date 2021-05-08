from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.db.models import Q
from bisect import bisect
from django.contrib import messages
from django.shortcuts import *
from applications.filetracking.models import  File, Tracking
from django.template.defaulttags import csrf_token
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core import serializers
from django.contrib.auth.models import User
from timeit import default_timer as time
from notification.views import gymkhana_voting, office_module_notif, gymkhana_session, gymkhana_event
from django.views.decorators.csrf import ensure_csrf_cookie
from applications.academic_information.models import Student
from applications.globals.models import *
from datetime import datetime
from django.core import serializers
import json
from .models import *
from django.views.decorators.csrf import csrf_exempt, csrf_protect

def coordinator_club(request):
	for i in Club_info.objects.select_related('co_ordinator','co_ordinator__id','co_ordinator__id__user','co_ordinator__id__department','co_coordinator','co_coordinator__id','co_coordinator__id__user','co_coordinator__id__department','faculty_incharge','faculty_incharge__id','faculty_incharge__id__user','faculty_incharge__id__department').all():
		co = (str(i.co_ordinator)).split(" ")
		co_co = (str(i.co_coordinator)).split(" ")
		if co[0] == str(request.user) or co_co[0] == str(request.user) :
			return(i)

@csrf_exempt
def delete_sessions(request):
	selectedIds = request.POST['ids']
	selectedIds = json.loads(selectedIds)
	try:
		for i in selectedIds:
			delSession = Session_info.objects.get(id=i)
			delSession.delete()
		return HttpResponse("success")
	except Exception as e:
		print("An error was encountered")
		return HttpResponse("error")


def editsession(request, session_id):
	
	if request.method == 'POST':
		try:
			body = request.POST
			venue = body.get('venue_type')
			session_poster = request.FILES.get('session_poster')
			date = body.get('date')
			start_time = body.get('start_time')
			end_time = body.get('end_time')
			desc = body.get('d_d')
			club_name = coordinator_club(request)
			res = conflict_algorithm_session(date, start_time, end_time, venue)
			message = ""
			if (res == 'success'):
				event = Session_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(id=session_id)
				event.club = club_name
				event.venue = venue
				event.date = date
				event.start_time = start_time
				event.end_time = end_time
				event.session_poster = session_poster
				event.details = desc
				event.save()
				# e = Session_info.objects.filter(id=session_id).update(club=club_name,venue=venue, date=date,start_time=start_time, end_time=end_time, session_poster=session_poster, details=desc)
				message += "Your form has been dispatched for further process"
				return redirect('/gymkhana/')
			else:
				message += "The selected time slot for the given date and venue conflicts with already booked session"
		except Exception as e:
			res = "error"
			message = "Some error occurred"
			print(message, e)

	##Get Request
	#  Session_info.objects(club=club_name,venue=venue,date=date,start_time=start_time,end_time=end_time,session_poster=session_poster, details=desc)
	venue = []
	event = Session_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(pk=session_id)

	for i in Constants.venue:
		for j in i[1]:
			venue.append(j[0])
	context = {
		'form': {
			"venue": event.venue,
			"session_poster": event.session_poster,
			"date": datetime.datetime.strftime(event.date, '%Y-%m-%d'),
			"start_time": event.start_time,
			"end_time": event.end_time,
			"desc": event.details,
			"club_name": event.club,
			"Venue": venue,
			"id": session_id
		}
	}
	# res = conflict_algorithm_event(date, start_time, end_time, venue)
	template = 'gymkhanaModule/editsession.html'

	return render(request, template, context)


@csrf_exempt
def delete_events(request):
	selectedIds = request.POST['ids']
	selectedIds = json.loads(selectedIds)
	message = ""
	try:
		for i in selectedIds:
			delEvent = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(id=i)
			delEvent.delete()
		return HttpResponse("success")
	except Exception as e:
		print("An error was encountered")
		return HttpResponse("error")

def edit_event(request,event_id):
	# event = Event_info.objects.get(pk=event_id)


	if request.method == 'POST':
		try:
			body = request.POST
			event_name = body.get('event_name')
			incharge=body.get('incharge')
			venue = body.get('venue_type')
			event_poster = request.FILES.get('event_poster')
			date = body.get('date')
			start_time = body.get('start_time')
			end_time = body.get('end_time')
			desc = body.get('d_d')
			club_name = coordinator_club(request)
			res = conflict_algorithm_event(date, start_time, end_time, venue)
			message = ""
			if(res == 'success'):
				event = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(id=event_id)
				event.club = club_name
				event.event_name = event_name
				event.incharge = incharge
				event.venue = venue
				event.date = date
				event.start_time = start_time
				event.end_time = end_time
				event.event_poster = event_poster
				event.details = desc
				event.save()
				# e = Event_info.objects.filter(id=event_id).update(club = club_name, event_name=event_name, incharge=incharge, venue = venue, date =date, start_time=start_time , end_time = end_time ,event_poster = event_poster , details = desc)
				message += "Your form has been dispatched for further process"
				return redirect('/gymkhana/')
			else:
				message += "The selected time slot for the given date and venue conflicts with already booked session"
		except Exception as e:
			res = "error"
			message = "Some error occurred"
			print(message,e)


	##Get Request
	#  Event_info(club = club_name, event_name=event_name, incharge=incharge, venue = venue, date =date, start_time=start_time , end_time = end_time ,event_poster = event_poster , details = desc)
	venue = []
	event = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(pk=event_id)

	for i in Constants.venue:
		for j in i[1]:
			venue.append(j[0])
	context = {
		'form':{
				"event_name":event.event_name,
				"incharge":event.incharge,
				"venue" : event.venue,
				"event_poster" : event.event_poster,
				"date":datetime.datetime.strftime(event.date,'%Y-%m-%d'),
				"start_time": event.start_time,
				"end_time" : event.end_time,
				"desc" : event.details,
				"club_name" : event.club,
				"Venue": venue,
				"id":event_id
			}
	}
	# res = conflict_algorithm_event(date, start_time, end_time, venue)
	template='gymkhanaModule/editevent.html'

	return render(request,template,context)

def delete_memberform(request):
	selectedIds = request.POST['ids']
	selectedIds = json.loads(selectedIds)
	try:
		for i in selectedIds:
			delMemberform = Club_member.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department','member','member__id','member__id__user','member__id__department').get(id=i)
			delMemberform.delete()
		return HttpResponse("success")
	except Exception as e:
		print("An error was encountered")
		return HttpResponse("error")

def facultyData(request):
	current_value = request.POST['current_value']
	try:
		# students =ExtraInfo.objects.all().filter(user_type = "student")
		faculty = ExtraInfo.objects.select_related('user','department').all().filter(user_type = "faculty")
		facultyNames = []
		for i in faculty:
			name = i.user.first_name + " " + i.user.last_name
			if current_value != "":
				Lowname = name.lower()
				Lowcurrent_value = current_value.lower()
				if Lowcurrent_value in Lowname:
					facultyNames.append(name)
			else:
				facultyNames.append(name)
		faculty = json.dumps(facultyNames)
		return HttpResponse(faculty)
	except Exception as e:
		return HttpResponse("error")


def studentsData(request):
	current_value = request.POST['current_value']
	try:
		# students = ExtraInfo.objects.all().filter(user_type="student").filter(id__startswith=current_value)
		students = ExtraInfo.objects.select_related('user','department').all().filter(user_type="student").filter(id__startswith=current_value)
		students = serializers.serialize('json', students)
		return HttpResponse(students)
	except Exception as e:
		return HttpResponse("error")


@login_required
def new_club(request):
	if request.method == 'POST':
		res = None
		message = None
		try:
			club_name = request.POST.get("club_name")
			category = request.POST.get("category")
			co = request.POST.get("co")
			coco = request.POST.get("coco")
			faculty = request.POST.get("faculty")
			# club_file = request.FILES.get("file")
			d_d = request.POST.get("d_d")

			res = "error"
			message = ""
			co = co.strip()
			coco = coco.strip()
			faculty = faculty.strip()
			#checking if the form data is authentic
			#checking for coordinator field
			students = ExtraInfo.objects.select_related('user','department').all().filter(user_type = "student")
			CO = None
			for i in students:
				if co == i.id:
					res = "success"
					CO = i
					break
			if (res == "error"):
				message = message + "The entered roll number of the co_ordinator does not exist"
				content = {
					'status' : res,
					'message' : message
				}
				content = json.dumps(content)
				return HttpResponse(content)

			#checking for co-coordinator field
			COCO = None
			res = "error"
			for i in students:
				if coco == i.id:
					res = "success"
					COCO = i
					break
			if(res == "error"):
				message = message + "The entered roll number of the co_coordinator does not exist"
				content = {
					'status' : res,
					'message' : message
				}
				content = json.dumps(content)
				return HttpResponse(content)

			#checking for faculty field
			FACUL = None
			faculties = ExtraInfo.objects.select_related('user','department').all().filter(user_type = "faculty")
			res = "error"
			for i in faculties:
				checkName = i.user.first_name + " " + i.user.last_name
				if faculty == checkName:
					res = "success"
					FACUL = i
					break
			if (res == "error"):
				message = message + "The entered faculty incharge does not exist"
				content = {
					'status' : res,
					'message' : message
				}
				content = json.dumps(content)
				return HttpResponse(content)
			#getting queryset class objects
			co_student = get_object_or_404(Student, id = CO)

			#getting queryset class objects
			coco_student = get_object_or_404(Student, id = COCO)

			#getting queryset class objects
			# faculty = faculty.split(" - ")
			# user_name = get_object_or_404(User, username = faculty[1])
			# faculty = get_object_or_404(ExtraInfo, id = faculty[0], user = user_name)
			faculty_inc = get_object_or_404(Faculty, id = FACUL)

			# club_file.name = club_name+"_club_file"

			club_info = Club_info(club_name = club_name, category = category, co_ordinator = co_student, co_coordinator = coco_student, faculty_incharge = faculty_inc, description = d_d)
			club_info.save()

			message = message + "The form has been successfully dispatched for further process"
		except Exception as e:
			res = "error"
			message = "Some error occurred"

		content = {
		'status' : res,
		'message' : message
				}
		content = json.dumps(content)
		HttpResponse(content)
		return redirect('/gymkhana/')


@login_required()
def form_avail(request):
	if request.method == 'POST':
		res = "success"
		message = "Form available?"
		try:
			#getting form data
			form_name = request.POST["registration"]
			status = request.POST["available"]

			if(status == "On"):
				status = True
			else:
				status = False
			roll = request.user.username
			rev = Form_available.objects.get(roll=roll).form_name
			if rev != form_name:
				delete_requests(request)
			#saving data to the database
			rob = Form_available.objects.get(roll=roll)
			rob.form_name = form_name
			rob.status = status
			rob.save()

		except Exception as e:
			print(e)
			res = "error"
			message = "You've already filled the form."

		content = {
			'status': res,
			'message': message,
		}
		content = json.dumps(content)
		# messages.success(request, "Form available?")
		return HttpResponse(content)
		# redirect("/gymkhana/")

@login_required
def delete_requests(request):
	if request.method == 'POST':
		res = "success"
		message = "Data is Deleted."
		try:
			rev = Registration_form.objects.all()
			rev.delete()

		except Exception as e:
			res = "error"
			message = "Some error occured."
		content = {
			'status': res,
			'message': message,
		}
		content = json.dumps(content)
		return HttpResponse(content)


@login_required()
def registration_form(request):
	if request.method == 'POST':
		res = "success"
		message = "The form has been dispatched for further process"
		try:
			#getting form data
			info = Student.objects.select_related('id','id__user','id__department').get(id__user=request.user).cpi
			user = request.POST.get("user_name")
			roll = request.POST.get("roll")
			cpi = request.POST.get("cpi")
			branch = request.POST.get("branch")
			programme = request.POST.get("programme")

			#saving data to the database
			reg = Registration_form(user_name=user, branch=branch, roll=roll, cpi=cpi, programme=programme)
			reg.save()
			# club_member = Club_member(member = student, club = club_name, description = pda)
			# club_member.save()
		except Exception as e:
			print(f"{e}DSANKJDVBJBDAKSCBASKFBasjcbaskjvbaskvaslvbna")
			res = "error"
			message = "You've already filled the form."

		content = {
			'status':res,
			'message':message
		}
		content = json.dumps(content)
		return HttpResponse(content)
		# messages.success(request,"Successfully sent the application !!!")

	# return redirect('/gymkhana/')

def retrun_content(request, roll, name, desig , club__ ):
	students =ExtraInfo.objects.select_related('user','department').filter(user_type = "student")
	faculty = ExtraInfo.objects.select_related('user','department').filter(user_type = "faculty")
	club_name = Club_info.objects.select_related('co_ordinator','co_ordinator__id','co_ordinator__id__user','co_ordinator__id__department','co_coordinator','co_coordinator__id','co_coordinator__id__user','co_coordinator__id__department','faculty_incharge','faculty_incharge__id','faculty_incharge__id__user','faculty_incharge__id__department').all()
	club_member = Club_member.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department','member','member__id','member__id__user','member__id__department').all()
	fest_budget = Fest_budget.objects.all()
	club_budget = Club_budget.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').all()
	club_session = Session_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').all()
	club_event = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').all()
	club_event_report = Club_report.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department','incharge','incharge__user','incharge__department').all()
	if 'student' in desig or 'Convenor' in desig:
		registration_form = Registration_form.objects.all()
		cpi = Student.objects.select_related('id','id__user','id__department').get(id__user=request.user).cpi
		programme = Student.objects.select_related('id','id__user','id__department').get(id__user=request.user).programme

		try:
			form_name = Form_available.objects.get(roll=request.user.username).form_name
			print(f'{form_name} MKNCjncknisncs')
			status = Form_available.objects.get(roll=request.user.username).status
		except Exception as e:
			stat = Form_available.objects.all()
			for i in stat:
				form_name = i.form_name
				status = i.status
				break

	venue_type = []
	id =0
	venue = []


	for i in Constants.venue:
		for j in i[1]:
			venue.append(j[0])
	b=[]
	if 'student' in desig:
		user_name = get_object_or_404(User, username = str(roll))
		extra = get_object_or_404(ExtraInfo, id = roll, user = user_name)
		student = get_object_or_404(Student, id = extra)
	else :
		b = []

	# creating the data for the active voting polls
	voting_polls = []
	for poll in Voting_polls.objects.all():
		event = {}
		choices = []
		event["id"] = poll.id
		event["title"] = poll.title
		event["desc"] = poll.description
		event['exp_date'] = (poll.exp_date- datetime.datetime.now()).days if (datetime.datetime.now() - poll.exp_date).days <= 0 else 'expire'
		event['pub_date'] = poll.exp_date.strftime("%d/%m/%Y")
		event["created_by"] = poll.created_by.split(":")
		for choice in poll.voting_choices_set.all():
			choices.append({'title':choice.title,'id':choice.id,'votes':choice.votes})

		event['choices'] = choices
		event['max'] = poll.voting_choices_set.latest()
		event['voters'] = poll.voting_voters_set.values_list('student_id', flat=True)
		event['groups'] = json.loads(poll.groups)

		voting_polls.append(event)

	content = {
		'Students' : students,
		'Club_name' : club_name,
		'Faculty' : faculty,
		'Club_member' : club_member,
		'Fest_budget' : fest_budget,
		'Club_budget' : club_budget,
		'Club_session': club_session,
		'Club_event' :   club_event,
		'Club_event_report' : club_event_report,
		'Curr_club' : b,
		'venue' : venue,
		'Curr_desig' : desig,
		'club_details':club__,
		'voting_polls': voting_polls,
		'roll' : str(roll),

	}
	if 'student' in desig or 'Convenor' in desig:
		content1 = {
			'registration_form': registration_form,
			'cpi': cpi,
			'programme': programme,
			'form_name': form_name,
			'status': status,
		}
		content.update(content1)
	return content

@login_required
def getVenue(request):
	selected = request.POST.get('venueType')
	selected = selected.strip()
	venue_type = []
	venue_details = {}
	idd = 0
	for i in Constants.venue:
		for j in i:
			if(idd % 2 == 0):
				venue_type.append(j)
			else:
				lt = [k[0] for k in j]
				venue_details[venue_type[int(idd/2)]] = lt
			idd = idd+1
	content = []
	for key, value in venue_details.items():
		if key == selected:
			for val in value:
				val = val.strip()
				content.append(val)
	content = json.dumps(content)
	return HttpResponse(content)

@login_required
def gymkhana(request):
	roll = request.user
	name = request.user.first_name +"_"+ request.user.last_name
	desig = list(HoldsDesignation.objects.select_related('user','working','designation').all().filter(working = request.user).values_list('designation'))
	b = [i for sub in desig for i in sub]
	roll_ = []
	for i in b :
		name_ = get_object_or_404(Designation, id = i)
		# #    #    print name_
		roll_.append(str(name_.name))
	for i in Club_info.objects.select_related('co_ordinator','co_ordinator__id','co_ordinator__id__user','co_ordinator__id__department','co_coordinator','co_coordinator__id','co_coordinator__id__user','co_coordinator__id__department','faculty_incharge','faculty_incharge__id','faculty_incharge__id__user','faculty_incharge__id__department').all():
		lines =str("")
		Types = lines.split(" ")
	club__ = coordinator_club(request)
	return render(request, "gymkhanaModule/gymkhana.html", retrun_content(request, roll, name, roll_ , club__ ))

@login_required
def club_membership(request):
	if request.method == 'POST':
		res = "success"
		message = "The form has been dispatched for further process"
		try:
			# getting form data
			user = request.POST.get("user_name")
			club = request.POST.get("club")
			pda = request.POST.get("achievements")

			# getting queryset class objects
			#user_name = User.objects.get(username = user[-7:])
			USER = user.split(' - ')
			user_name = get_object_or_404(User, username=USER[1])
			extra = get_object_or_404(ExtraInfo, id=USER[0], user=user_name)
			student = get_object_or_404(Student, id=extra)
			#extra = ExtraInfo.objects.get(id = user[:-10], user = user_name)
			#student = Student.objects.get(id = extra)

			club_name = get_object_or_404(Club_info, club_name=club)

			# saving data to the database
			club_member = Club_member(
				member=student, club=club_name, description=pda)
			club_member.save()
		except Exception as e:
			res = "error"
			message = "Some error occurred"

		content = {
			'status': res,
			'message': message
		}
		content = json.dumps(content)
		return HttpResponse(content)
		# messages.success(request,"Successfully sent the application !!!")

	# return redirect('/gymkhana/')


@login_required
def core_team(request):
	if request.method == 'POST':
		# getting form data
		user = request.POST.get("user_name")
		fest = request.POST.get("fest")
		team = request.POST.get("team")
		pda = request.POST.get("pda")
		year = request.POST.get("year")

		# getting queryset class objects
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username=USER[1])
		extra = get_object_or_404(ExtraInfo, id=USER[00], user=user_name)
		student = get_object_or_404(Student, id=extra)

		# saving data to the database
		core_team = Core_team(student_id=student,
							  fest_name=fest, team=team, pda=pda, year=year)
		core_team.save()
		messages.success(request, "Successfully applied for the post !!!")

	return redirect('/gymkhana/')

@login_required
def event_report(request):
	if request.method == 'POST':
		# getting form data
		user = request.POST.get("st_inc")
		event = request.POST.get("event")
		d_d = request.POST.get("d_d")
		date = request.POST.get("date")
		time = request.POST.get("time")
		report = request.FILES["report"]
		report.name = event+"_report"

		# getting queryset class objects
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username=USER[1])
		extra = get_object_or_404(ExtraInfo, id=USER[0], user=user_name)

		# saving data to the database
		other_report = Other_report(incharge=extra, event_name=event,
									date=date+" "+time, event_details=report, description=d_d)
		other_report.save()
		messages.success(request, "Successfully saved the report !!!")

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
		club_name = get_object_or_404(Club_info, club_name=club)

		club_budget = Club_budget(club=club_name, budget_amt=budget_amt,
								  budget_file=budget_file, budget_for=budget_for, description=desc)
		club_budget.save()
		messages.success(request, "Successfully requested for the budget !!!")

	return redirect('/gymkhana/')


@login_required
def act_calender(request):
	if request.method == "POST":
		message = ""
		club = request.POST.get("club")
		act_calender = request.FILES['act_file']
		act_calender.name = club+"_act_calender.pdf"

		#club_name = get_object_or_404(Club_info, club_name = club)

		club_info = get_object_or_404(Club_info, club_name=club)
		club_info.activity_calender = act_calender
		club_info.save()
		message += "Successfully uploaded the calender !!!"

		content = {
				'status':"success",
				'message':message,
			}
		content = json.dumps(content)
		return HttpResponse(content)



@login_required
def club_report(request):
	if request.method == 'POST' and request.FILES['report']:
		# getting form data
		club = request.POST.get('club')
		user = request.POST.get("s_inc")
		event = request.POST.get("event")
		d_d = request.POST.get("d_d")
		date = request.POST.get("date")
		time = request.POST.get("time")
		report = request.FILES["report"]
		report.name = club+"_"+event+"_report"

		# getting queryset class objects
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username=USER[1])
		extra = get_object_or_404(ExtraInfo, id=USER[0], user=user_name)

		club_name = get_object_or_404(Club_info, club_name=club)

		# saving data to the database
		club_report = Club_report(club=club_name, incharge=extra, event_name=event,
								  date=date+" "+time, event_details=report, description=d_d)
		club_report.save()
		messages.success(request, "Successfully updated the report !!!")

	return redirect('/gymkhana/')

@login_required
def change_head(request):
	if request.method == "POST":
		club = request.POST.get("club")
		co = request.POST.get('co')
		coco = request.POST.get('coco')
		date = request.POST.get("date")
		time = request.POST.get("time")
		desc = "co-ordinator and co co-ordinator changed on "+date+" at "+time
		message = ""

		# club_name = get_object_or_404(Club_info, club_name=club)

		co_student = get_object_or_404(Student, id__user__username=co)

		coco_student = get_object_or_404(Student, id__user__username=coco)

		club_info = get_object_or_404(Club_info, club_name=club)

		old_co = club_info.co_ordinator
		old_coco = club_info.co_coordinator
		club_info.co_ordinator = co_student
		club_info.co_coordinator = coco_student
		club_info.save()

		message += "Successfully changed !!!"
		
		new_co = HoldsDesignation(user=User.objects.get(username=co), working=User.objects.get(username=co), designation=Designation.objects.get(name="co-ordinator"))
		new_co.save()
		new_coco = HoldsDesignation(user=User.objects.get(username=coco), working=User.objects.get(username=coco), designation=Designation.objects.get(name="co co-ordinator"))
		new_coco.save()

		old_co = HoldsDesignation.objects.select_related('user','working','designation').filter(user__username=old_co, designation__name="co-ordinator")
		old_co.delete()
		old_coco = HoldsDesignation.objects.select_related('user','working','designation').filter(user__username=old_coco, designation__name="co co-ordinator")
		old_coco.delete()

		content = {
				'status':"success",
				'message':message,
			}

		content = json.dumps(content)
		return HttpResponse(content)

		# return redirect('/gymkhana/')



@login_required
def new_session(request):
	if request.method == "POST":
		club_name = None
		res =None
		message = None
		try:
			venue = request.POST.get("venue_type")
			session_poster = request.FILES.get("session_poster")
			date = request.POST.get("date")
			start_time = request.POST.get("start_time")
			end_time = request.POST.get("end_time")
			desc = request.POST.get("d_d")
			club_name = coordinator_club(request)
			res = conflict_algorithm_session(date, start_time, end_time, venue)
			message = ""
			getstudents = ExtraInfo.objects.select_related('user','department').filter(user_type = 'student')
			recipients = User.objects.filter(extrainfo__in=getstudents)
			if(res == "success"):
				session = Session_info(club = club_name, venue = venue, date =date, start_time=start_time , end_time = end_time , session_poster=session_poster, details = desc)
				session.save()
				message += "Session booked Successfully"
				gymkhana_session(request.user, recipients, 'new_session', club_name, desc, venue)

			else:
				message += "The selected time slot for the given date and venue conflicts with already booked session"
		except Exception as e:
			print(e)
			res = "error"
			message = "Some error occurred"

		content = {
			'status':res,
			'message':message
		}
		
		content = json.dumps(content)
		return HttpResponse(content)

@login_required
def new_event(request):
	if request.method == "POST":
		club_name = None
		res =None
		message = None
		try:
			event_name=request.POST.get("event_name")
			incharge=request.POST.get("incharge")
			venue = request.POST.get("venue_type")
			event_poster = request.FILES.get("event_poster")
			date = request.POST.get("date")
			start_time = request.POST.get("start_time")
			end_time = request.POST.get("end_time")
			desc = request.POST.get("d_d")
			club_name = coordinator_club(request)
			res = conflict_algorithm_event(date, start_time, end_time, venue)
			message = ""
			getstudents = ExtraInfo.objects.select_related('user','department').filter(user_type = 'student')
			recipients = User.objects.filter(extrainfo__in=getstudents)
			if(res == "success"):
				event = Event_info(club = club_name, event_name=event_name, incharge=incharge, venue = venue, date =date, start_time=start_time , end_time = end_time ,event_poster = event_poster , details = desc)
				event.save()
				message += "Your form has been dispatched for further process"
				gymkhana_event(request.user, recipients, 'new_event', club_name, event_name, desc, venue)
			else:
				message += "The selected time slot for the given date and venue conflicts with already booked session"
		except Exception as e:
			res = "error"
			message = "Some error occurred"

		content = {
			'status':res,
			'message':message
		}
		content = json.dumps(content)
		return HttpResponse(content)

@login_required
def fest_budget(request):
	if request.method == 'POST' and request.FILES['file']:
		fest = request.POST.get("fest")
		budget_amt = request.POST.get('amount')
		budget_file = request.FILES['file']
		desc = request.POST.get('d_d')
		year = request.POST.get('year')
		budget_file.name = fest+"_budget_"+year

		fest_budget = Fest_budget(fest=fest, budget_amt=budget_amt,
								  budget_file=budget_file, description=desc, year=year)
		fest_budget.save()
		messages.success(request, "Successfully uploaded the budget !!!")

	return redirect('/gymkhana/')


@login_required
def approve(request):
	lis = list(request.POST.getlist('check'))
	for user in lis:
		# pos = lis.index(user)
		re = "remarks" + user
		remarks = request.POST.getlist(re)
		user = user.split(',')
		info = user[0].split(' - ')

		# getting queryset class objects
		user_name = get_object_or_404(User, username=info[1])
		extra1 = get_object_or_404(ExtraInfo, id=info[0], user=user_name)
		student = get_object_or_404(Student, id=extra1)

		club_member = get_object_or_404(Club_member, club=user[1], member=student)
		club_member.status = "confirmed"
		club_member.remarks = remarks[0]
		club_member.save()
		messages.success(request, "Successfully Approved !!!")

	return redirect('/gymkhana/')

@login_required
def club_approve(request):
	lisx = list(request.POST.getlist('check'))
	for club in lisx:
		club_name = get_object_or_404(Club_info, club_name=club)
		club_name.status = "confirmed"
		club_name.save()
		messages.success(request, "Successfully Approved !!!")

	return redirect('/gymkhana/')


@login_required
def club_reject(request):
	lisx = list(request.POST.getlist('check'))
	for club in lisx:
		club_name = get_object_or_404(Club_info, club_name=club)
		club_name.status = "rejected"
		club_name.save()
		messages.success(request, "Successfully Rejected !!!")

	return redirect('/gymkhana/')

@login_required
def reject(request):
	lis = list(request.POST.getlist('check'))

	for user in lis:
		# pos = lis.index(user)
		re = "remarks" + user
		remarks = request.POST.getlist(re)
		user = user.split(',')
		info = user[0].split(' - ')

		# getting queryset class objects
		user_name = get_object_or_404(User, username=info[1])
		extra1 = get_object_or_404(ExtraInfo, id=info[0], user=user_name)
		student = get_object_or_404(Student, id=extra1)

	club_member = get_object_or_404(Club_member, club=user[1], member=student)
	club_member.status = "rejected"
	club_member.remarks = remarks[0]
	club_member.save()
	messages.success(request, "Successfully Rejected !!!")

	return redirect('/gymkhana/')

	return redirect('/gymkhana/')

@login_required
def cancel(request):

	lis = list(request.POST.getlist('check'))

	for user in lis:
		#pos = lis.index(user)
		user = user.split(',')
		info = user[0].split(' - ')

		# getting queryset class objects
		user_name = get_object_or_404(User, username=info[1])
		extra1 = get_object_or_404(ExtraInfo, id=info[0], user=user_name)
		student = get_object_or_404(Student, id=extra1)

		club_member = get_object_or_404(
			Club_member, club=user[1], member=student)

		club_member.delete()
		messages.success(request, "Successfully deleted !!!")

	return redirect('/gymkhana/')


@login_required
@csrf_exempt
def date_sessions(request):
	if(request.is_ajax()):
		value = request.POST.get('date')
		get_sessions = Session_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').filter(date=value).order_by('start_time')
		dates = []
		for i in get_sessions:
			dates.append(i)
		dates = serializers.serialize('json', dates)
		return HttpResponse(dates)

@login_required
@csrf_exempt
def date_events(request):
	if(request.method=='POST'):
		value = request.POST.get('date')
		get_events = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').filter(date=value).order_by('start_time')
		dates = []
		for i in get_events:
			dates.append(i)
		dates = serializers.serialize('json', dates)
		return HttpResponse(dates)
	return Httpresponse("Hurray")

#this algorithm checks if the passed slot time coflicts with any of already booked sessions
def conflict_algorithm_session(date, start_time, end_time, venue):
	#converting string to datetime type variable
	start_time = datetime.datetime.strptime(start_time, '%H:%M').time()
	end_time = datetime.datetime.strptime(end_time, '%H:%M').time()
	booked_Sessions = Session_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').filter(date=date, venue=venue)

	#placing start time and end time in tuple fashion inside this list
	slots = [(start_time, end_time)]
	for value in booked_Sessions:
		slots.append((value.start_time, value.end_time))
	slots.sort()
	#if there isn't any slot present for the selected day just book the session
	if (len(slots) == 1):
		return "success"
	else:
		#this whole logic checks if the end time of any slot is less than the start time of next slot
		counter = slots[0][1]
		flag = 0
		i=1
		while i < len(slots):
			if (slots[i][0] < counter):
				flag = 1
				break
			counter = slots[i][1]
			i = i + 1
		if (flag == 0):
			return "success"
		else:
			return "error"

##helper function to get the target user for the voting poll
def get_target_user(groups):
	dic = {}
	for i in range(len(groups)):
		value = groups[i].split(":")
		batch = value[0]
		branch = value[1]
		if dic.get(batch):
			if dic[batch][0] != 'All':
				dic[batch].append(branch)
		else:
			dic[batch] = [branch]
	return json.dumps(dic)

## Voting Polls
@login_required
def voting_poll(request):
	if request.POST:
		try:
			body = request.POST
			title = body.get('title')
			description = body.get('desc')
			choices = body.getlist('choices')
			exp_date = body.get('expire_date')
			groups = body.getlist('groups')
			target_groups = get_target_user(groups)
			name = request.user.first_name + " " + request.user.last_name
			roll = request.user
			created_by = str(name) +":"+ str(roll)
			new_poll = Voting_polls(title=title, description=description, exp_date=exp_date, created_by = str(created_by),groups=target_groups)
			new_poll.save()
			for choice in choices:
				new_choice = Voting_choices(poll_event=new_poll,title=choice)
				new_choice.save()
			for i in range(len(groups)):
				value = groups[i].split(":")
				batch = value[0]
				branch = value[1]
				allbatch = User.objects.filter(username__contains = batch)
				selbranch = ExtraInfo.objects.select_related('user','department').filter(department__name = branch)
				batchbranch = User.objects.filter(username__contains = batch, extrainfo__in=selbranch)
				if branch == 'All':
					gymkhana_voting(request.user, allbatch, 'voting_open', title, description)
				else:
					gymkhana_voting(request.user, batchbranch, 'voting_open', title, description)
			return redirect('/gymkhana/')
		except Exception as e:
			res = "error"
			message = "Some error occurred"
			print(e)
			content = {
				'status':res,
				'message':message
			}
			content = json.dumps(content)
			return HttpResponse(content)

	return redirect('/gymkhana/')

@login_required
def vote(request,poll_id):
	poll = Voting_polls.objects.get(pk=poll_id)
	if request.POST:
		try:
			body = request.POST
			submitted_choice = body.get('choice')
			choice = Voting_choices.objects.select_related('poll_event').get(pk=submitted_choice)
			choice.votes += 1
			choice.save()
			new_voter = Voting_voters(poll_event=poll, student_id=str(request.user))
			new_voter.save()
			return redirect('/gymkhana/')
		except Exception as e:
			print(e)
			return HttpResponse('error')
	data = serializers.serialize('json',Voting_choices.objects.select_related('poll_event').all())
	return redirect('/gymkhana/')

@login_required
def delete_poll(request, poll_id):
	try:
		poll = Voting_polls.objects.filter(pk=poll_id)
		poll.delete()
		return redirect('/gymkhana/')
	except Exception as e:
			print(e)
			return HttpResponse('error')

	return redirect('/gymkhana/')

#this algorithm checks if the passed slot time coflicts with any of already booked events

def conflict_algorithm_event(date, start_time, end_time, venue):
	#converting string to datetime type variable
	start_time = datetime.datetime.strptime(start_time, '%H:%M').time()
	end_time = datetime.datetime.strptime(end_time, '%H:%M').time()
	booked_Events = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').filter(date=date, venue=venue)

	#placing start time and end time in tuple fashion inside this list
	slots = [(start_time, end_time)]
	for value in booked_Events:
		slots.append((value.start_time, value.end_time))
	slots.sort()
	#if there isn't any slot present for the selected day just book the event
	if (len(slots) == 1):
		return "success"
	else:
		#this whole logic checks if the end time of any slot is less than the start time of next slot
		counter = slots[0][1]
		flag = 0
		i=1
		while i < len(slots):
			if (slots[i][0] < counter):
				flag = 1
				break
			counter = slots[i][1]
			i = i + 1
		if (flag == 0):
			return "success"
		else:
			return "error"

@login_required(login_url = "/accounts/login/")
def filetracking(request):
	"""
		The function is used to create files by current user(employee).
		It adds the employee(uploader) and file datails to a file(table) of filetracking(model)
		if he intends to create file.

		@param:
				request - trivial.

		@variables:


				uploader - Employee who creates file.
				subject - Title of the file.
				description - Description of the file.
				upload_file - Attachment uploaded while creating file.
				file - The file object.
				exations - The HoldsDesignation object.
				context - Hotrainfo - The Extrainfo object.
				holdsdesignlds data needed to make necessary changes in the template.
	"""
	if request.method =="POST":
		try:
			if 'save' in request.POST:
				uploader = request.user.extrainfo
				print(uploader)
				#ref_id = request.POST.get('fileid')
				subject = request.POST.get('title')
				description = request.POST.get('desc')
				design = request.POST.get('design')
				designation = Designation.objects.get(id=design)
				upload_file = request.FILES.get('myfile')

				File.objects.create(
					uploader=uploader,
					#ref_id=ref_id,
					description=description,
					subject=subject,
					 designation=designation,
					upload_file=upload_file
				)

			if 'send' in request.POST:


				uploader = request.user.extrainfo
				print(uploader)
				#ref_id = request.POST.get('fileid')
				subject = request.POST.get('title')
				description = request.POST.get('desc')
				design = request.POST.get('design')
				print("designation is ", design)
				designation = Designation.objects.get(id = HoldsDesignation.objects.select_related('user','working','designation').get(id = design).designation_id)

				upload_file = request.FILES.get('myfile')

				file = File.objects.create(
					uploader=uploader,
					#ref_id=ref_id,
					description=description,
					subject=subject,
					designation=designation,
					upload_file=upload_file
				)


				current_id = request.user.extrainfo
				remarks = request.POST.get('remarks')

				sender = request.POST.get('design')
				current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

				receiver = request.POST.get('receiver')
				receiver_id = User.objects.get(username=receiver)
				print("Receiver_id = ")
				print(receiver_id)
				receive = request.POST.get('recieve')
				print("recieve = ")
				print(receive)
				receive_designation = Designation.objects.filter(name=receive)
				print("receive_designation = ")
				print(receive_designation)
				receive_design = receive_designation[0]
				upload_file = request.FILES.get('myfile')
				return HttpResponse ("success")
				Tracking.objects.create(
					file_id=file,
					current_id=current_id,
					current_design=current_design,
					receive_design=receive_design,
					receiver_id=receiver_id,
					remarks=remarks,
					upload_file=upload_file,
				)
				office_module_notif(request.user, receiver_id)
				messages.success(request,'File sent successfully')

		except IntegrityError:
			message = "FileID Already Taken.!!"
			return HttpResponse(message)



	file = File.objects.select_related('uploader','uploader__user','uploader__department','designation').all()
	extrainfo = ExtraInfo.objects.select_related('user','department').all()
	holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
	designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user = request.user)

	context = {
		'file': file,
		'extrainfo': extrainfo,
		'holdsdesignations': holdsdesignations,
		'designations': designations,
	}
	return render(request, 'filetracking/composefile.html', context)

@login_required(login_url = "/accounts/login")
def forward(request, id):
	"""
			The function is used to forward files received by user(employee) from other
			employees which are filtered from Tracking(table) objects by current user
			i.e. receiver_id to other employees.
			It also gets track of file created by uploader through all users involved in file
			along with their remarks and attachments
			It displays details file of a File(table) and remarks and attachments of user involved
			in file of Tracking(table) of filetracking(model) in the template.

			@param:
					request - trivial.
					id - id of the file object which the user intends to forward to other employee.

			@variables:
					file - The File object.
					track - The Tracking object.
					remarks = Remarks posted by user.
					receiver = Receiver to be selected by user for forwarding file.
					receiver_id = Receiver_id who has been selected for forwarding file.
					upload_file = File attached by user.
					extrainfo = ExtraInfo object.
					holdsdesignations = HoldsDesignation objects.
					context - Holds data needed to make necessary changes in the template.
	"""
	# start = timer()
	file = get_object_or_404(File, id=id)
	# end = timer()

	# start = timer()
	track = Tracking.objects.select_related('file_id','file_id__uploader','file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id','current_id__user','current_id__department','current_design','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=file)
	# end = timer()

	if request.method == "POST":
			if 'finish' in request.POST:
				file.complete_flag = True
				file.save()

			if 'send' in request.POST:
				current_id = request.user.extrainfo
				remarks = request.POST.get('remarks')

				sender = request.POST.get('sender')
				current_design = HoldsDesignation.objects.select_related('user','working','designation').get(id=sender)

				receiver = request.POST.get('receiver')
				receiver_id = User.objects.get(username=receiver)
				receive = request.POST.get('recieve')
				receive_designation = Designation.objects.filter(name=receive)
				receive_design = receive_designation[0]
				upload_file = request.FILES.get('myfile')
				# return HttpResponse ("success")
				Tracking.objects.create(
					file_id=file,
					current_id=current_id,
					current_design=current_design,
					receive_design=receive_design,
					receiver_id=receiver_id,
					remarks=remarks,
					upload_file=upload_file,
				)
	# start = timer()

	extrainfo = ExtraInfo.objects.select_related('user','department').all()
	holdsdesignations = HoldsDesignation.objects.select_related('user','working','designation').all()
	designations = HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)

	context = {
		# 'extrainfo': extrainfo,
		# 'holdsdesignations': holdsdesignations,
		'designations':designations,
		'file': file,
		'track': track,
	}

	return render(request, 'filetracking/forward.html', context)


	