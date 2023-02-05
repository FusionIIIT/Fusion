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

import logging

logger = logging.getLogger(__name__)
def coordinator_club(request):
	"""
		coordinator_club:
			this function is used to return the details of the Club_info of the requested user 
			if the  user is either the coordinator or the cocoordinator of the club
	    @param:
			request - trivial 
	    @variables:
			details - contains the Club_info 
			co_ordinator - contains the details of the Club co_ordinator 
			co_coordinator - contains the details of the Club co_coordinator
	"""
	for details in Club_info.objects.select_related('co_ordinator','co_ordinator__id','co_ordinator__id__user','co_ordinator__id__department','co_coordinator','co_coordinator__id','co_coordinator__id__user','co_coordinator__id__department','faculty_incharge','faculty_incharge__id','faculty_incharge__id__user','faculty_incharge__id__department').all():
		co_ordinator= (str(details.co_ordinator)).split(" ")
		co_coordinator= (str(details.co_coordinator)).split(" ")
		if co_ordinator[0] == str(request.user) or co_coordinator[0] == str(request.user) :
			return(details)

@csrf_exempt
def delete_sessions(request):
	"""
		delete_sessions:
			This view deletes the session based on the request_id  in Session_info
			if it runs without exception then it deletes and return the result : success
			if not then it just returns the result : error 
		@param:
			request - trivial 
		@variables:
			selectedIds - contains the id of the request
			delSession - this contains the details of Session which needs to be deleted based on the SelectedIds from Session_info   
	
	"""
	selectedIds = request.POST['ids']
	selectedIds = json.loads(selectedIds)
	try:
		for ids in selectedIds:
			delSession = Session_info.objects.get(id=ids)
			delSession.delete()
		return HttpResponse("success")
	except Exception as e:
		logger.error("An error was encountered")
		return HttpResponse("error")


def editsession(request, session_id):
	"""
	    editsession:
			  	This function is used to edit  the club_sessions for clubs by their users.
				By using this the club user can edit the session.
				If the given date and time and venue clasheswith already booked session it doesn't edit the session.
				And it displays success if there is no exception and displays error if there is an exception.

		@param:
			request - trivial

		@variables:
			venue - the place/room at which the session is going to happen
			session_poster - it is a file that has to be uploaded which contains the poster for session
			date - the date at which session is going to happen
			start_time - the time at which session is going to start
			end_time - the time at which session is going to end
			desc - brief explanation about session if any
			club_name - requests the coordinator_club and it returns
			result - checks wheather the date,time,venue clashes with other session using conflict_algorithm_session view
			session - if result is success then the session books successfully
			 
	
	"""
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
			result = conflict_algorithm_session(date, start_time, end_time, venue)
			message = ""
			if (result == 'success'):
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
			result = "error"
			message = "Some error occurred"
			logger.info(message,e)

	##Get Request
	#  Session_info.objects(club=club_name,venue=venue,date=date,start_time=start_time,end_time=end_time,session_poster=session_poster, details=desc)
	venue = []
	event = Session_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(pk=session_id)

	for rooms in Constants.venue:
		for venues in rooms[1]:
			venue.append(venues[0])
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
	"""
		delete_events:
			This view deletes the event based on the request_id  in Event_info
			if it runs without exception then it deletes and return the result : success
			if not then it just returns the result : error 
		@param:
			request - trivial 
		@variables:
			selectedIds - contains the id of the request
			delEvent - this contains the details of Event which needs to be deleted based on the SelectedIds from Event_info   
	
	"""
	selectedIds = request.POST['ids']
	selectedIds = json.loads(selectedIds)
	message = ""
	try:
		for ids in selectedIds:
			delEvent = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(id=ids)
			delEvent.delete()
		return HttpResponse("success")
	except Exception as e:
		logger.error("An error was encountered")
		return HttpResponse("error")

def edit_event(request,event_id):
	# event = Event_info.objects.get(pk=event_id)
	"""
	edit_event:
			This function is used to edit  the club_event for clubs by their users.
			By using this the club user can edit the event.
			If the given date and time and venue clasheswith already booked session it doesn't edit the event.
			And it displays success if there is no exception and displays error if there is an exception.

	@param:
		request - trivial

	@variables:
		venue - the place/room at which the event is going to happen
		event_name - it has the name of the event 
		date - the date at which event is going to happen
		start_time - the time at which event is going to start
		end_time - the time at which event is going to end
		desc - brief explanation about event if any
		club_name - requests the coordinator_club and it returns
		result - checks wheather the date,time,venue clashes with other event using conflict_algorithm_session view
		event - if result is success then the event books successfully		 

	"""
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
			result = conflict_algorithm_event(date, start_time, end_time, venue)
			message = ""
			if(result == 'success'):
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
			result = "error"
			message = "Some error occurred"
			logger.info(message,e)


	##Get Request
	#  Event_info(club = club_name, event_name=event_name, incharge=incharge, venue = venue, date =date, start_time=start_time , end_time = end_time ,event_poster = event_poster , details = desc)
	venue = []
	event = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').get(pk=event_id)

	for rooms in Constants.venue:
		for venues in rooms[1]:
			venue.append(venues[0])
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
	"""
		delete_memberform:
			This view deletes the memberform based on the request_id  in Club_member
			if it runs without exception then it deletes and return the result : success
			if not then it just returns the result : error 
		@param:
			request - trivial 
		@variables:
			selectedIds - contains the id of the request
			delMemberform - this contains the details of member which needs to be deleted based on the SelectedIds from Club_member   
	
	"""
	selectedIds = request.POST['ids']
	selectedIds = json.loads(selectedIds)
	try:
		for ids in selectedIds:
			delMemberform = Club_member.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department','member','member__id','member__id__user','member__id__department').get(id=ids)
			delMemberform.delete()
		return HttpResponse("success")
	except Exception as e:
		logger.error("An error was encountered")
		return HttpResponse("error")

def facultyData(request):
	"""
		facultyData:
			this function is used to return the facultyNames from the ExtraInfo of the requested value which are not present in the current value 
	    @param:
			request - trivial 
	    @variables:
			faculty - contains the Extrainfo of the faculty
			facultyName - contains the list of faculties firstname and lastname
			name - contains the lecturers first name and the last name 
	"""
	current_value = request.POST['current_value']
	try:
		# students =ExtraInfo.objects.all().filter(user_type = "student")
		faculty = ExtraInfo.objects.select_related('user','department').all().filter(user_type = "faculty")
		facultyNames = []
		for lecturer in faculty:
			name = lecturer.user.first_name + " " +lecturer.user.last_name
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
	"""
		studentsData:
			this function is used to return the students data from the ExtraInfo of the requested value 
	    @param:
			request - trivial 
	    @variables:
			students- contains the Extrainfo of the faculty for the required current value
			
	"""
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
	"""
		new_club:
			this function is used to create a new club with the given data and to check whether 
			the given info of the co_ordinator , co-coordinator and faculty is true or not from the Student_info and Extra_info ,
			And if the data is true then dump the json content or else return the error that these data doesn't exit  
			
	    @param:
			request - trivial 
	    @variables:
			club_name - contains the club_name from the request 
			category - contains the category to which the club belongs
			co_ordinator - contains the id of the new_club's co_ordinator 
			co_coordinator - contains the id of the new_club's co_coordinator
			faculty - contains the details of the faculty for the new_club
			d_d = contains the descriptons of the  
	"""
	if request.method == 'POST':
		result = None
		message = None
		try:
			club_name = request.POST.get("club_name")
			category = request.POST.get("category")
			print(category)
			co_ordinator = request.POST.get("co")
			co_coordinator = request.POST.get("coco")
			faculty = request.POST.get("faculty")
			print("faculty",faculty)
			# club_file = request.FILES.get("file")
			d_d = request.POST.get("d_d")

			result = "error"
			message = ""
			co_ordinator = co_ordinator.strip()
			co_coordinator = co_coordinator.strip()
			faculty = faculty.strip()
			#checking if the form data is authentic
			#checking for coordinator field
			students = ExtraInfo.objects.select_related('user','department').all().filter(user_type = "student")
			CO = None
			for student_info in students:
				if co_ordinator == student_info.id:
					result = "success"
					CO = student_info
					break
			print("result",result)
			if (result == "error"):
				message = message + "The entered roll number of the co_ordinator does not exist"
				content = {
					'status' : result,
					'message' : message
				}
				content = json.dumps(content)
				return HttpResponse(content)

			#checking for co-coordinator field
			COCO = None
			result = "error"
			for student_info in students:
				if co_coordinator == student_info.id:
					result = "success"
					COCO = student_info
					break
			print("cocoordinator",result)
			if(result == "error"):
				message = message + "The entered roll number of the co_coordinator does not exist"
				content = {
					'status' : result,
					'message' : message
				}
				content = json.dumps(content)
				return HttpResponse(content)

			#checking for faculty field
			FACUL = None
			faculties = ExtraInfo.objects.select_related('user','department').all().filter(user_type = "faculty")
			result = "error"
			for lecturer in faculties:
				checkName = lecturer.user.first_name + " " + lecturer.user.last_name
				# print()
				if faculty == checkName:
					result = "success"
					FACUL = lecturer
					break
			print("faculty",result)
			print(CO,COCO)
			if (result == "error"):
				message = message + "The entered faculty incharge does not exist"
				content = {
					'status' : result,
					'message' : message
				}
				content = json.dumps(content)
				return HttpResponse(content)
			#getting queryset class objects
			co_student = get_object_or_404(Student, id = CO)
			print(co_student)
			#getting queryset class objects
			coco_student = get_object_or_404(Student, id = COCO)
			print(coco_student)
			#getting queryset class objects
			# faculty = faculty.split(" - ")
			# user_name = get_object_or_404(User, username = faculty[1])
			# faculty = get_object_or_404(ExtraInfo, id = faculty[0], user = user_name)
			faculty_inc = get_object_or_404(Faculty, id = FACUL)
			print(faculty_inc)
			# club_file.name = club_name+"_club_file"
			
			club_info = Club_info(club_name = club_name, category = category, co_ordinator = co_student, co_coordinator = coco_student, faculty_incharge = faculty_inc, description = d_d)
			print(club_info)
			club_info.save()
			print("saved successfully")
			message = message + "The form has been successfully dispatched for further process"
		except Exception as e:
			result = "error"
			message = "Some error occurred"

		content = {
		'status' : result,
		'message' : message
				}
		content = json.dumps(content)
		HttpResponse(content)
		return redirect('/gymkhana/')



@login_required()
def form_avail(request):
	"""
		form_avail:
			this function is used to fill the form if available and then save the data 
			if there is an exception return an error
			
	    @param:
			request - trivial 
	    @variables:
			form_name - it is used to send the data for the registration
			status - it is availablity of form  
	"""
	if request.method == 'POST':
		result = "success"
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
			logger.info(e)
			result = "error"
			message = "You've already filled the form."

		content = {
			'status': result,
			'message': message,
		}
		content = json.dumps(content)
		# messages.success(request, "Form available?")
		return HttpResponse(content)
		# redirect("/gymkhana/")

@login_required
def delete_requests(request):
	"""
		delete_requests:
		This view deletes all objects in Registration_form table
		if it runs without exception then it deletes and return the result : success
		if not then it just returns the result : error in json object 
		Only this can be when the method is POST
		@param:
			request : trivial
		@variables:
			register_objects : all objects of records in Registration_form
	"""
	if request.method == 'POST':
		result = "success"
		message = "Data is Deleted."
		try:
			register_objects = Registration_form.objects.all()
			register_objects.delete()

		except Exception as e:
			result = "error"
			message = "Some error occured."
		content = {
			'status': result,
			'message': message,
		}
		content = json.dumps(content)
		return HttpResponse(content)


@login_required()
def registration_form(request):
	"""
		registration_form
		This view recieves the data from Front-end side and saves into the Registration_form database
		if it runs without exception then it deletes and return the result : success
		if not then it just returns the result : error in json object 
		Only this can be when the method is POST
		@params:
			request : trivial
		@variables:
			user_name : name of the user
			roll      : Roll number of student
			cpi       : cpi of the student
			branch    : branch name of the student
			programme : Programme of the student
	"""
	if request.method == 'POST':
		result = "success"
		message = "The form has been dispatched for further process"
		try:
			#getting form data
			info = Student.objects.select_related('id','id__user','id__department').get(id__user=request.user).cpi
			user_name = request.POST.get("user_name")
			roll = request.POST.get("roll")
			cpi = request.POST.get("cpi")
			branch = request.POST.get("branch")
			programme = request.POST.get("programme")

			#saving data to the database
			register = Registration_form(user_name=user_name, branch=branch, roll=roll, cpi=cpi, programme=programme)
			register.save()
			# club_member = Club_member(member = student, club = club_name, description = pda)
			# club_member.save()
		except Exception as e:
			logger.info(f"{e}DSANKJDVBJBDAKSCBASKFBasjcbaskjvbaskvaslvbna")
			result = "error"
			message = "You've already filled the form."

		content = {
			'status':result,
			'message':message
		}
		content = json.dumps(content)
		return HttpResponse(content)
		# messages.success(request,"Successfully sent the application !!!")

	# return redirect('/gymkhana/')

def retrun_content(request, roll, name, desig , club__ ):
	"""
	retrun_content
	This view returns all data regarding the parameters that sent through function
	The returned data contains all information regarding all clubs , polling system , status of clubs ,
	students info who are in the designation, which was sent through parameters of this function
	@param:
		request : trivial
		roll    : Roll number of the student
		name    : name of the user
		desig   : Designition of the user
		club__  : club name of the user
	@variables:
		student           : All info of the student passes through the function
		faculty           : All info of the faculty
		club_name         : All club names
		club_member       : All info of the Club_member
		fest_budget       : All info of the fest_budget
		club_budget       : All info of the Club_budget
		club_session      : All info of the Session_info
		club_event        : All info of the Event_info
		club_event_report : All info of the Club_report

	"""
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
			logger.info(f'{form_name} MKNCjncknisncs')
			status = Form_available.objects.get(roll=request.user.username).status
		except Exception as e:
			forms = Form_available.objects.all()
			for form in forms:
				form_name = form.form_name
				status = form.status
				break

	venue_type = []
	id =0
	venue = []


	for rooms in Constants.venue:
		for room in rooms[1]:
			venue.append(room[0])
	curr_club=[]
	if 'student' in desig:
		user_name = get_object_or_404(User, username = str(roll))
		extra = get_object_or_404(ExtraInfo, id = roll, user = user_name)
		student = get_object_or_404(Student, id = extra)
	else :
		curr_club = []

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
		'Curr_club' : curr_club,
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
	"""
		getVenue
		This view takes the venue type from Front-end and returns the list of venues which of type
		provided by User
		@param:
			request : trivial
		@variables:
			selected : Type of the venue selected by the user
	"""
	selected = request.POST.get('venueType')
	selected = selected.strip()
	venue_type = []
	venue_details = {}
	idd = 0
	for rooms in Constants.venue:
		for room in rooms:
			if(idd % 2 == 0):
				venue_type.append(room)
			else:
				venue_list = [venue[0] for venue in room]
				venue_details[venue_type[int(idd/2)]] = venue_list
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
	"""
		gymkhana
		This view gives us the complete information regarding various clubs and it
		contains the records of the coordinator and co-coordinator of all the clubs and users can join any
		club and cancel his/her membership from any club that he/she wishes to. And it also contains the
		details of the sessions and events conducted by various clubs and club heads can also conduct
		surveys by conducting polls and by taking the permission from the academic office students can
		also create the clubs for a purpose.
		@param:
			request : trivial
		@variables:
			roll 		 : Roll number of the User
			name 		 : full name of the user
			designations : List contains all info of the user logged in

	"""
	roll = request.user
	name = request.user.first_name +"_"+ request.user.last_name
	designations = list(HoldsDesignation.objects.select_related('user','working','designation').all().filter(working = request.user).values_list('designation'))
	designation_data = [element for designation in designations for element in designation]
	roll_ = []
	for designation in designation_data :
		name_ = get_object_or_404(Designation, id = designation)
		# #    #    print name_
		roll_.append(str(name_.name))
	for club_data in Club_info.objects.select_related('co_ordinator','co_ordinator__id','co_ordinator__id__user','co_ordinator__id__department','co_coordinator','co_coordinator__id','co_coordinator__id__user','co_coordinator__id__department','faculty_incharge','faculty_incharge__id','faculty_incharge__id__user','faculty_incharge__id__department').all():
		lines =str("")
		Types = lines.split(" ")
	club__ = coordinator_club(request)
	return render(request, "gymkhanaModule/gymkhana.html", retrun_content(request, roll, name, roll_ , club__ ))

@login_required
def club_membership(request):
	"""
		club_membership:
		This view takes the user_name, club name, achievements of that student and saves it to
		club_memder database. Finally displays success if there are no Exceptions and errors and if there
		is some Exception, then by using json.dump() which converts python objects to json string.
		@param:
			request : trivial
		@variables:
			user_name 	 : Name of the user
			club      	 : Name of the club
			achievements : Achievements of the user
	"""
	if request.method == 'POST':
		result = "success"
		message = "The form has been dispatched for further process"
		try:
			# getting form data
			user_name = request.POST.get("user_name")
			club = request.POST.get("club")
			achievements = request.POST.get("achievements")

			# getting queryset class objects
			#user_name = User.objects.get(username = user[-7:])
			USER = user_name.split(' - ')
			user_name = get_object_or_404(User, username=USER[1])
			extra = get_object_or_404(ExtraInfo, id=USER[0], user=user_name)
			student = get_object_or_404(Student, id=extra)
			#extra = ExtraInfo.objects.get(id = user[:-10], user = user_name)
			#student = Student.objects.get(id = extra)

			club_name = get_object_or_404(Club_info, club_name=club)

			# saving data to the database
			club_member = Club_member(
				member=student, club=club_name, description=achievements)
			club_member.save()
		except Exception as e:
			result = "error"
			message = "Some error occurred"

		content = {
			'status': result,
			'message': message
		}
		content = json.dumps(content)
		return HttpResponse(content)
		# messages.success(request,"Successfully sent the application !!!")

	# return redirect('/gymkhana/')


@login_required
def core_team(request):
	"""
		core_team:
		This view takes the data of students. Data like, their name, fest name, team, pda and 
		year. And finally saving this data to the database of the core team.
		This will done only when the method is POST and at the end it will redirect to '/gymkhana/'
		@params:
			request : trivial
		@variables:
			user 		 : Name of the user
			fest 		 : Name of the fest
			team 		 : Name of the team
			achievements : Achievements of the user
			year		 : Acedamic year of the core team

	"""
	if request.method == 'POST':
		# getting form data
		user = request.POST.get("user_name")
		fest = request.POST.get("fest")
		team = request.POST.get("team")
		achievements = request.POST.get("pda")
		year = request.POST.get("year")

		# getting queryset class objects
		USER = user.split(' - ')
		user_name = get_object_or_404(User, username=USER[1])
		extra = get_object_or_404(ExtraInfo, id=USER[00], user=user_name)
		student = get_object_or_404(Student, id=extra)

		# saving data to the database
		core_team = Core_team(student_id=student,
							  fest_name=fest, team=team, pda=achievements, year=year)
		core_team.save()
		messages.success(request, "Successfully applied for the post !!!")

	return redirect('/gymkhana/')

@login_required
def event_report(request):
	"""
		event_report:
		This view takes mainly the event, date, time, report and description of that
		certain event. And then it appends that particular event`s report to other_report and 
		saves it to the database. Finally it redirects to the gymkhana homepage.
		@param:
			request : trivial
		@variables:
			user : Name of the user
			event : Name of the event
			description : Event`s description
			date : Date of the event
			time : Time of the event schedule
			report : This is a file of details of the event

	"""
	if request.method == 'POST':
		# getting form data
		user = request.POST.get("st_inc")
		event = request.POST.get("event")
		description = request.POST.get("d_d")
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
									date=date+" "+time, event_details=report, description=description)
		other_report.save()
		messages.success(request, "Successfully saved the report !!!")

	return redirect('/gymkhana/')


@login_required
def club_budget(request):
	"""
		club_budget:
		This view takes details of club name, reason for the event and the amount
		required for the event of the club.if the club name doesn't match with the clubs in database it
		shows errors,else it the uploads to database and a message displays successfully uploaded the
		budget.And then it redirects to gymkhana homepage.
		@param:
			request : trivial
		@variables:
			club : Name of the club
			budget_for : Reason for the budget
			budget_amount : Amount of the budget
			budget_file : File that contains the budget details
			description : Brief note of the whole budget view.


	"""
	if request.method == 'POST' and request.FILES['budget_file']:
		club = request.POST.get("club")
		budget_for = request.POST.get("budget_for")
		budget_amount = request.POST.get('amount')
		budget_file = request.FILES['budget_file']
		description = request.POST.get('d_d')
		budget_file.name = club+"_budget"
		club_name = get_object_or_404(Club_info, club_name=club)

		club_budget = Club_budget(club=club_name, budget_amt=budget_amount,
								  budget_file=budget_file, budget_for=budget_for, description=description)
		club_budget.save()
		messages.success(request, "Successfully requested for the budget !!!")

	return redirect('/gymkhana/')


@login_required
def act_calender(request):
	"""
		act_calender:
		This view gets the date from the club if there is any wrong info it shows the error
		otherwise it shows Successfully uploaded the calendar in the form of Json object 
		and adds to the calendar
		@params:
			request : trivial
		@variables:
			club : Name of the club
			act_calender : File that contains the active calender of the club
	"""
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
	"""
     This function is used to add the details of the club event along with a report.
	 It adds the club event details to the database.
	 And also uploads report file.

	 @param:
          request - trivial

	 @variable:
	        club - name of the club
			user - the id of user who adds this club event details
            event - name of the event
			d_d - description of the event
			date - date in which the event going to happen/happened
			time - time in which the event going to happen/happened
			report - the club_report file on the event uploads by the user who adds data
            
	"""
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
	"""
	This  used to change the heads of club.
	It gets the old co_ordinator and co_cordinator and replaces them with new co and co_co.
	And adds to the database.

	@param:
	      request - trivial

	@variables:

	       club - name of the club
		   co_ordinator - new co_ordinator of the club
		   co_coordinator - new co_cordinator of the club
		   date - date at which the heads of the clubs changes
           time - time at which the heads changes
		   desc - description on change of heads
		   old_co_ordinator - HoldsDesignation object and after deletes this co_ordinator
		   old_co_coordinator - HoldsDesignation object and after deletes this co_coordinator
		   new_co_ordinator - HoldsDesignation object and after saves this object as co_ordinator
		   new_co_coordinator - HoldsDesignation object and after saves this object as co_coordinator
	"""

	if request.method == "POST":
		club = request.POST.get("club")
		co_ordinator = request.POST.get('co')
		co_coordinator = request.POST.get('coco')
		date = request.POST.get("date")
		time = request.POST.get("time")
		desc = "co-ordinator and co co-ordinator changed on "+date+" at "+time
		message = ""

		# club_name = get_object_or_404(Club_info, club_name=club)

		co_ordinator_student = get_object_or_404(Student, id__user__username=co_ordinator)

		co_coordinator_student = get_object_or_404(Student, id__user__username=co_coordinator)

		club_info = get_object_or_404(Club_info, club_name=club)

		old_co_ordinator = club_info.co_ordinator
		old_co_coordinator = club_info.co_coordinator
		club_info.co_ordinator = co_ordinator_student
		club_info.co_coordinator = co_coordinator_student
		club_info.save()

		message += "Successfully changed !!!"
		
		new_co_ordinator = HoldsDesignation(user=User.objects.get(username=co_ordinator), working=User.objects.get(username=co_ordinator), designation=Designation.objects.get(name="co-ordinator"))
		new_co_ordinator.save()
		new_co_coordinator = HoldsDesignation(user=User.objects.get(username=co_coordinator), working=User.objects.get(username=co_coordinator), designation=Designation.objects.get(name="co co-ordinator"))
		new_co_coordinator.save()

		old_co_ordinator = HoldsDesignation.objects.select_related('user','working','designation').filter(user__username=old_co_ordinator, designation__name="co-ordinator")
		old_co_ordinator.delete()
		old_co_coordinator = HoldsDesignation.objects.select_related('user','working','designation').filter(user__username=old_co_coordinator, designation__name="co co-ordinator")
		old_co_coordinator.delete()

		content = {
				'status':"success",
				'message':message,
			}

		content = json.dumps(content)
		return HttpResponse(content)

		# return redirect('/gymkhana/')



@login_required
def new_session(request):
	"""
    This function is used to add/create new sessions for clubs by their users.
	By using this the club user can add new session.
	If the given date and time and venue clasheswith already booked session it doesn't add the session.
	And it displays success if there is no exception and displays error if there is an exception.
    
	@param:
	    request - trivial

	@variables:
		venue - the place/room at which the session is going to happen
		session_poster - it is a file that has to be uploaded which contains the poster for session
		date - the date at which session is going to happen
		start_time - the time at which session is going to start
		end_time - the time at which session is going to end
		desc - brief explanation about session if any
		club_name - requests the coordinator_club and it returns
		result - checks wheather the date,time,venue clashes with other session using conflict_algorithm_session view
		getstudents - extrainfo object
		session - if result is success then the session books successfully

	"""
	if request.method == "POST":
		club_name = None
		result =None
		message = None
		try:
			venue = request.POST.get("venue_type")
			session_poster = request.FILES.get("session_poster")
			date = request.POST.get("date")
			start_time = request.POST.get("start_time")
			end_time = request.POST.get("end_time")
			desc = request.POST.get("d_d")
			club_name = coordinator_club(request)
			result = conflict_algorithm_session(date, start_time, end_time, venue)
			message = ""
			getstudents = ExtraInfo.objects.select_related('user','department').filter(user_type = 'student')
			recipients = User.objects.filter(extrainfo__in=getstudents)
			if(result == "success"):
				session = Session_info(club = club_name, venue = venue, date =date, start_time=start_time , end_time = end_time , session_poster=session_poster, details = desc)
				session.save()
				message += "Session booked Successfully"
				gymkhana_session(request.user, recipients, 'new_session', club_name, desc, venue)

			else:
				message += "The selected time slot for the given date and venue conflicts with already booked session"
		except Exception as e:
			logger.info(e)
			result = "error"
			message = "Some error occurred"

		content = {
			'status':result,
			'message':message
		}
		
		content = json.dumps(content)
		return HttpResponse(content)

@login_required
def new_event(request):
	"""
    This function is used to add/create new event by clubs by their users.
	By using this the club user can add new event.
	If the given date and time and venue clasheswith already booked events/sessions it doesn't move to further process.
	And it displays your form has been moved for further process if there is no exception and displays error if there is an exception.
    
	@param:
	    request - trivial

	@variables:
        event_name - we have to give name of the event
		incharge - the faculty staff name who is going to incharge the event
		venue - the place/room at which the event is going to happen
		event_poster - it is a file that has to be uploaded which contains the poster for event
		date - the date at which event is going to happen
		start_time - the time at which event is going to start
		end_time - the time at which event is going to end
		desc - brief explanation about event
		club_name - requests the coordinator_club and it returns
		result - checks wheather the date,time,venue clashes with other event using conflict_algorithm_event view
		getstudents - Extrainfo object
		session - if result is success then the event has been saved

	"""
	if request.method == "POST":
		club_name = None
		result =None
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
			result = conflict_algorithm_event(date, start_time, end_time, venue)
			message = ""
			getstudents = ExtraInfo.objects.select_related('user','department').filter(user_type = 'student')
			recipients = User.objects.filter(extrainfo__in=getstudents)
			if(result == "success"):
				event = Event_info(club = club_name, event_name=event_name, incharge=incharge, venue = venue, date =date, start_time=start_time , end_time = end_time ,event_poster = event_poster , details = desc)
				event.save()
				message += "Your form has been dispatched for further process"
				gymkhana_event(request.user, recipients, 'new_event', club_name, event_name, desc, venue)
			else:
				message += "The selected time slot for the given date and venue conflicts with already booked session"
		except Exception as e:
			result = "error"
			message = "Some error occurred"

		content = {
			'status':result,
			'message':message
		}
		content = json.dumps(content)
		return HttpResponse(content)

@login_required
def fest_budget(request):
	"""
	 This view uploads the budget details for the fest to the database.
	 Then the academic management can check the budget and accordingly allot the budget.
    
	 @param:
	       fest - takes the name of the fest
		   budget_amt - the amount that is needed for the club
		   budget_file - have to upload the file that contails all details about the budget for fest
		   descrition - anything that we want write about fest
		   year - year fest is happening
		   fest_budget - the given details saved to the database

	"""
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
	"""
	This view is used by the clubs to approve the students who wants to join the club and changes status of student to  confirmed.
	It gets a list of students who has to be approved and checks them and approves accordingly.
	 
	@variables:
	          approve_list - list of students who has to be checked and approved.
			  remarks - gets remarks list if any remarks present
              club_member - gets the object(club and student) and the confirms the status of student in the club.
	"""
	approve_list = list(request.POST.getlist('check'))
	for user in approve_list:
		# pos = lis.index(user)
		remark = "remarks" + user
		remarks = request.POST.getlist(remark)
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
	"""
    This view is used by the administration to approve the clubs.
	It gets a list of clubs and then approves if they want to.

	@variables:
	          club_approve_list - list of clubs which has to be approved
			  club_name - gets the object and then confirms the club

	"""
	club_approve_list = list(request.POST.getlist('check'))
	for club in club_approve_list:
		club_name = get_object_or_404(Club_info, club_name=club)
		club_name.status = "confirmed"
		club_name.save()
		messages.success(request, "Successfully Approved !!!")

	return redirect('/gymkhana/')


@login_required
def club_reject(request):
	"""
    This view is used by the administration to reject the clubs.
	It gets a list of clubs and then rejects if they want to.
    
	@variables:
	          club_reject_list - list of clubs which has to be checked and rejected
			  club_name - gets the object and then rejects the club

	"""
	club_reject_list = list(request.POST.getlist('check'))
	for club in club_reject_list:
		club_name = get_object_or_404(Club_info, club_name=club)
		club_name.status = "rejected"
		club_name.save()
		messages.success(request, "Successfully Rejected !!!")

	return redirect('/gymkhana/')

@login_required
def reject(request):
	"""
	This view is used by the clubs to approve the students who wants to join the club.
	It gets a list of students who has to be approved and checks them and approves accordingly.
	 
	@variables:
	          approve_list - list of students who has to be checked and approved.
			  remarks - gets remarks list if any remarks present

	"""
	reject_list = list(request.POST.getlist('check'))

	for user in reject_list:
		# pos = lis.index(user)
		remark = "remarks" + user
		remarks = request.POST.getlist(remark)
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
	"""
    This function is used to cancel/remove the member from a club.
    It gets the list of student and checks in their club and the deletes the student from that club.
	Finally gets the message successfully deleted.

	@variables:
	          cancel_list - list of students who are to be removed/delted from club.
			  club_member - checks the object and then deletes the member from club.
	"""

	cancel_list = list(request.POST.getlist('check'))

	for user in cancel_list:
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
	"""
		date_sessions:
			this function is used to return the details of the Session_info for the requested date 
			and sends the serialized data
	    @param:
			request - trivial 
	    @variables:
			value - contains the requested date 
			get_sessions - contains the details of the Club's from the Session_info which are having sessions on the requested date  
			dates - it's a list which contains the data present in the get_sessions 
	
	"""
	if(request.is_ajax()):
		value = request.POST.get('date')
		get_sessions = Session_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').filter(date=value).order_by('start_time')
		dates = []
		for session_info in get_sessions:
			dates.append(session_info)
		dates = serializers.serialize('json', dates)
		return HttpResponse(dates)

@login_required
@csrf_exempt
def date_events(request):
	"""
		date_sessions:
			this function is used to return the details of the Event_info for the requested date and sends the serialized data
	    @param:
			request - trivial 
	    @variables:
			value - contains the requested date 
			get_events - contains the details of the Club's from the Event_info which are having events on the requested date  
			dates - it's a list which contains the data present in the get_events 
	
	"""
	if(request.method=='POST'):
		value = request.POST.get('date')
		get_events = Event_info.objects.select_related('club','club__co_ordinator','club__co_ordinator__id','club__co_ordinator__id__user','club__co_ordinator__id__department','club__co_coordinator','club__co_coordinator__id','club__co_coordinator__id__user','club__co_coordinator__id__department','club__faculty_incharge','club__faculty_incharge__id','club__faculty_incharge__id__user','club__faculty_incharge__id__department').filter(date=value).order_by('start_time')
		dates = []
		for event_info in get_events:
			dates.append(event_info)
		dates = serializers.serialize('json', dates)
		return HttpResponse(dates)
	return HttpResponse("Hurray")

#this algorithm checks if the passed slot time coflicts with any of already booked sessions
def conflict_algorithm_session(date, start_time, end_time, venue):
	#converting string to datetime type variable
	"""
		conflict_algorithm_session:
			this algorithm is used to find if there any avaiable slot for the given date , stat_time ,end_time and venue 
			from the session_info to book the slot else it returns error.
	    @param:
		    date - date of the slot 
			start_time - starting time for the slot 
			end_time - ending time for the slot
			venue - venue for the slot
	    @variables:
			
			booked_session - contains the session_info of all previously alloted slots
	"""
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
	"""
		get_target_user:
		This function helps to fetch the passed list to Dictionary of Key unique batches(years) and
		values of braches and remove the redundancy and returns the "dic" through Json string
		@param:
		groups : This takes the info of which brach and batch can access(voting) this poll
	"""
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
	"""
		voting_poll:
		This view creates new voting poll by taking the values from Front-end and add this poll details
		to "Voting_polls" database and also it create and add object of "Voting_choices" contains
		poll_event and title>. Finally it calls gymkhana_voting as per the data given to "groups"
		@param:
			request : trivial
		@variables:
			title : Title of the voting poll
			description : It describes that what this poll is for
			choices     : Choices of the voting poll
			exp_data    : Expire date of the voting poll
			groups      : This takes the info of which brach and batch can access(voting) this poll
	"""
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
			logger.info(e)
			content = {
				'status':res,
				'message':message
			}
			content = json.dumps(content)
			return HttpResponse(content)

	return redirect('/gymkhana/')

@login_required
def vote(request,poll_id):
	"""
		vote:
		This view will update(increase) votes by 1 for particular 'submitted_choice' then it adds the
		voter(student)ID and poll_event for which he/she votes. Finally it saves to the database
		redirect to '/gymkhana/'. In case of any exception it return "error"
		@param:
			poll_id : ID of the poll
			request : trivial
		@variables:
			submitted_choice : Choice of the user selected for poll_event
			choice           : It is a object contains all data of "submitted_choice" from Voting_choices
			new_voter        : creating object of Voting_voter to save the voter info
	"""
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
			logger.info(e)
			return HttpResponse('error')
	data = serializers.serialize('json',Voting_choices.objects.select_related('poll_event').all())
	return redirect('/gymkhana/')

@login_required
def delete_poll(request, poll_id):
	"""
		delete_poll:
		This view delete the particular voting poll which is passed through function and redirect
		to "/gymkhana/" if there is an exception then it return the HttpResponse of "error" 
		@param:
			request : trivial
			poll_id : id of the poll in Voting_polls
		@variables:
			poll : It is an object stores the all data of poll_id  from Voting_poll
	"""
	try:
		poll = Voting_polls.objects.filter(pk=poll_id)
		poll.delete()
		return redirect('/gymkhana/')
	except Exception as e:
			logger.info(e)
			return HttpResponse('error')

	return redirect('/gymkhana/')

#this algorithm checks if the passed slot time coflicts with any of already booked events

def conflict_algorithm_event(date, start_time, end_time, venue):
	"""
		conflict_algorithm_event:
		This view takes the date, start_time , end_time , Venue which is passed by function and
		checks with data in database then it returns "success" if there is no time slot is clashng
		with passed data and returns "error" if there is some time slot is clashing with passed
		data
		@param:
			date       : date of the event
			start_time : Event's starting time
			end_time   : Event's ending time
			venue      : Venue of the event	
		@variables:
			booked_Events : This is an object contains all data of Event_info for which date 
			                and venue is equal to passed date and venue
	"""
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
				logger.info(uploader)
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
				logger.info(uploader)
				#ref_id = request.POST.get('fileid')
				subject = request.POST.get('title')
				description = request.POST.get('desc')
				design = request.POST.get('design')
				logger.info("designation is ", design)
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
				logger.info("Receiver_id = ")
				logger.info(receiver_id)
				receive = request.POST.get('recieve')
				logger.info("recieve = ")
				logger.info(receive)
				receive_designation = Designation.objects.filter(name=receive)
				logger.info("receive_designation = ")
				logger.info(receive_designation)
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


	
