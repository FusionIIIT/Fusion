import datetime
from datetime import date, datetime, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.db import IntegrityError

from applications.academic_procedures.models import Thesis
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, User)
from applications.scholarships.models import Mcm
from applications.filetracking.models import (File, Tracking)
from applications.eis.models import emp_research_projects, emp_patents, emp_consultancy_projects

from notification.views import office_dean_PnD_notif,office_module_DeanRSPC_notif

from .forms import *
from .models import *
from .models import (Project_Closure, Project_Extension, Project_Reallocation,
                     Project_Registration)
from .views_office_students import *

from django.template.defaulttags import register


def officeOfDeanRSPC(request):
    '''
    This function is called when the office of dean RSPC is called.
    It returns the list of all the projects and the project extensions, project closures and project reallocations.

    @param request: 
        request from the page
    @return: 
        renders the page with all the projects and the project extensions, project closures and project reallocations.
    '''

    project=Project_Registration.objects.select_related('PI_id__user','PI_id__department').all()
    project1=Project_Extension.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').all()
    project2=Project_Closure.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').all()
    project3=Project_Reallocation.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').all()

    design = HoldsDesignation.objects.select_related('user','designation').filter(working=request.user)
    print(design)
    desig=[]
    for i in design:
        desig.append(str(i.designation))

    context = {'project':project, 'project1':project1, 'project2':project2, 'project3':project3, 'desig':desig}

    return render(request, "officeModule/officeOfDeanRSPC/officeOfDeanRSPC.html", context)

def _list_find(lists, predicate):
    """
    Find the first element in a list that satisfies the given predicate
    Arguments:
        - lst: List to search through
        - predicate: Predicate that determines what to return
    Returns:
        The first element that satisfies the predicate otherwise None
    """
    for list in lists:
        if predicate(list):
            return list
    return None

def _req_history(req):
    """
    Return requisition history: All tracking rows that are associated with the passet requisition
    """
    return Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=req.assign_file)

_pnd_deslist={
            'Civil_JE': 'Junior Engg. (Civil)',
            'Civil_AE':'Assistant Engg. (Civil)',
            'Electrical_JE': 'Junior Engg. (Electrical)',
            'Electrical_AE':'Assistant Engg. (Electrical)',
            'EE': 'Executive Engg.',
            'DeanPnD': 'Dean (P&D)',
            'Director': 'Director',
            'None':'Closed'
}

@register.filter
def pndReadableDesignation(key):
    # Map designations to readable titles.
    d = str(key)
    return _pnd_deslist.get(d, d) 

@login_required
def officeOfDeanPnD(request):
    """
        Main view for the office of dean (p&d) module.
        Generates four tabs:
            * Dashboard: Shows overview of requisitions and assignments
            * Create Requisition: Form to create new requisitions
            * View Requisitions: Lists all open requisitions and allows Junior Engg.
                to create work assignment from them.
            * View Assignments: Lists all assignments, incoming assignments and
                outgoing assignments. Allows performing actions on incoming assignments.
    
    This function is called when the office of dean (p&d) is called.
    It returns the list of all the requisitions, incoming requisitions, outgoing requisitions and
    the history of all the requisitions.

    @param request: 
        request from the page
    @return: 
        renders the page with all the requisitions, incoming requisitions, outgoing requisitions and
        the history of all the requisitions.
    """
    user = request.user
    extrainfo = ExtraInfo.objects.select_related('user','department').get(user=user)


    
    holds=HoldsDesignation.objects.filter(working=user)
    designations=[d.designation for d in HoldsDesignation.objects.select_related('user','designation','working').filter(working=user)]

    # handle createassignment POST request
    if 'createassign' in request.POST:
        print("createassign", request)
        req_id=request.POST.get('req_id')
        requisition=Requisitions.objects.select_related('userid__user','userid__department','assign_file__uploader__user','assign_file__uploader__department','assign_file__designation').get(pk=req_id)
        description=request.POST.get('description')
        upload_file=request.FILES.get('estimate')
        sender_design=None
        for hold in holds:
            # only allow respective Civil/Electrical JE to create assignment.
            if str(hold.designation.name) == "Civil_JE":
                if requisition.department != "civil":
                    return HttpResponse('Unauthorized', status=401)
                sender_design=hold
                receive=HoldsDesignation.objects.select_related('user','designation','working').get(designation__name="Civil_AE")
                #fdate = datetime.dat
            elif str(hold.designation.name)=="Electrical_JE":
                if requisition.department != "electrical":
                    return HttpResponse('Unauthorized', status=401)
                sender_design=hold
                receive=HoldsDesignation.objects.select_related('user','designation','working').get(designation__name="Electrical_AE")
                #fdate = datetime.datetime.now().date()
        if not sender_design:
            return HttpResponse('Unauthorized', status=401)

        # Create file in the File table from filetracking module
        requisition.assign_file = File.objects.create(
                uploader=extrainfo,
                #ref_id=ref_id,
                description=requisition.description,
                subject=requisition.title,
                designation=sender_design.designation,
            )
        requisition.save()

        # Send notifications to all concerned users
        office_dean_PnD_notif(request.user, requisition.userid.user, 'request_accepted')
        office_dean_PnD_notif(request.user, request.user, 'assignment_created')
        office_dean_PnD_notif(request.user, receive.working, 'assignment_received')

        # Create tracking row to send the file to Assistant Engg.
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=sender_design,
                receive_design=receive.designation,
                receiver_id=receive.working,
                remarks=description,
                upload_file=upload_file,
            )
    # Handle delete requisition post request
    # Requisitions are "deleted" by hiding them from requisition lists, but are
    # kept in the database for record-keeping reasons.
    elif 'delete_requisition' in request.POST:
        print('delete requisition')
        hold = HoldsDesignation.objects.select_related('user','designation','working').get(working=user,designation__name__in=_pnd_deslist)
        if hold:
            req_id=request.POST.get('req_id')
            try:
                req = Requisitions.objects.select_related('userid__user','userid__department','assign_file__uploader__user','assign_file__uploader__department','assign_file__designation').get(pk=req_id)
                office_dean_PnD_notif(request.user, req.userid.user, 'request_rejected')
                req.tag = 1 # tag = 1 implies the requisition has been deleted
                req.save()
            except Requisitions.DoesNotExist:
                print('ERROR NOT FOUND 409404040', req_id)
        else:
            return HttpResponse('Unauthorized', status=401)

    # Requisitions that *don't* have as assignment
    req=Requisitions.objects.select_related('userid__user','userid__department','assign_file__uploader__user','assign_file__uploader__department','assign_file__designation').filter(assign_file__isnull=True, tag=0)
    # all requisitions
    all_req=Requisitions.objects.select_related('userid__user','userid__department','assign_file__uploader__user','assign_file__uploader__department','assign_file__designation').filter(tag=0)
    # list of all requisitions that have an assignment
    assigned_req=list(Requisitions.objects.select_related('userid__user','userid__department','assign_file__uploader__user','assign_file__uploader__department','assign_file__designation').filter(assign_file__isnull=False).select_related())
    # use list comprehension to create a list of pairs of (tracking file, corresponding requisition)
    # for incoming tracking files
    incoming_files=[(f, _list_find(assigned_req, lambda r: r.assign_file==f.file_id))
            for f in Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(receiver_id=user).filter(is_read=False)]
    # use list comprehension to create a list of pairs of (tracking file, corresponding requisition)
    # for outgoing tracking files
    outgoing_files=[(f, _list_find(assigned_req, lambda r: r.assign_file==f.file_id))
            for f in Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(current_id__user=user)]
    # history of assignment, list of pair of (requisition, history list)
    assign_history=[(r, _req_history(r)) for r in assigned_req]


    allfiles=None
    sentfiles=None
    files=''
    req_history = []
    # generate a list of requisitions history to render dashboard
    for r in all_req:
        # in case the requisition has an assignment file
        if r.assign_file:
            # Passed has a list of designations through which req. has passed
            # First element is the sender + each tracking's receieve
            # this way all history is generated
            passed = [r.assign_file.designation] + [t.receive_design for t in Tracking.objects.filter(file_id=r.assign_file)]
            # the last date the requisition was sent
            last_date = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=r.assign_file).last().receive_date
            # map with readable titles from deslist
            passed = [pndReadableDesignation(d) for d in passed]
            req_history.append((r, passed, last_date))
        # in case there is no assignment, that means the history only contains the junior engg. 
        else:
            je = 'Civil_JE' if r.department == 'civil' else 'Electrical_JE'
            passed = [pndReadableDesignation(je)]
            req_history.append((r, passed, r.req_date))
    # sort based on last update, which is the element 2 in the 3-tuple
    req_history.sort(key=lambda t: t[2], reverse=True)
    # list of allowed actions filtered by designation
    allowed_actions = []
    for des in designations:
        if des.name == "DeanPnD" or des.name == "Director" or des.name == "EE":
            allowed_actions = ["Approve", "Reject"]
    """
    for des in designations:
        if des.name == "DeanPnD":
            allowed_actions = ["Forward", "Revert", "Approve", "Reject"]
        elif des.name == "Director":
            allowed_actions = ["Revert", "Approve", "Reject"]
        elif des.name == "Electrical_JE" or des.name == "Civil_JE":
            allowed_actions = ["Forward", "Reject"]
        else:
            allowed_actions = ["Forward", "Revert", "Reject"]
    """

    # Create context to render template
    context = {
            'files':files,
            'req':req,
            'incoming_files': incoming_files,
            'outgoing_files': outgoing_files,
            'assigned_req':assign_history,
            'desig':[d.name for d in designations],
            'req_history': req_history,
            'allowed_actions': allowed_actions,
            'deslist': _pnd_deslist,
    }
    return render(request, "officeModule/officeOfDeanPnD/officeOfDeanPnD.html", context)


@login_required
def submitRequest(request):
    """
        Endpoint used to create requisition
    This function is used to create a new requisition.
    It takes in the following parameters:
    1. request - the request from the user
    2. user - the user who has sent the request
    3. extrainfo - the extraInfo object of the user
    4. fdate - the current date
    5. dept - the department of the requisition
    6. building - the building of the requisition
    7. title - the title of the requisition
    8. description - the description of the requisition
    9. tag - the tag of the requisition
    10. file - the file of the requisition
    11. req_date - the date of the requisition
    12. assign_file - the assignment file of the requisition
    13. assign_date - the date of the assignment
    14. assign_desig - the designation of the assignment
    15. assign_user - the user of the assignment
    @param request: the request from the user
    @param user: the user who has sent the request
    @variable extrainfo: the extraInfo object of the user
    @variable fdate: the current date
    @variable dept: the department of the requisition
    @variable building: the building of the requisition
    @variable title: the title of the requisition
    @variable description: the description of the requisition
    @variable tag: the tag of the requisition
    """
    user = request.user
    extrainfo = ExtraInfo.objects.select_related('user','department').get(user=user)
    fdate = datetime.datetime.now().date()
    dept=request.POST.get('department')
    building = request.POST.get('building')
    title = request.POST.get('title')
    description = request.POST.get('description')

    request_obj = Requisitions(userid=extrainfo, req_date=fdate,
                               description=description, department=dept, title=title, building=building)
    request_obj.save()
    office_dean_PnD_notif(request.user, request.user, 'requisition_filed')

    # the cake is a lie
    context={}
    return HttpResponseRedirect("/office/officeOfDeanPnD#requisitions")


@login_required
def action(request):
    """
    Endpoint handling actions on assignment.
    This function is used to handle the actions of the office of the Dean (P&D)
    The actions are:
    1. Send: Send the file to the next authority.
    2. Reject: Reject the file and remove it from the system.
    3. Approve: Approve the file and send it to the next authority.
    4. Revert: Revert the file back to the previous authority.
    5. Return: Return the file to the user.
    The function also takes care of the notifications.
    The function is called when the user clicks on the action button on the files.
    The function is called on the files that have been sent to the user.
    
    """
    # deslist=['Civil_JE','Civil_AE','EE','DeanPnD','Electrical_JE','Electrical_AE']
    user = request.user
    extrainfo = ExtraInfo.objects.select_related('user','department').get(user=user)
    req_id=request.POST.get('req_id')
    requisition = Requisitions.objects.select_related('userid__user','userid__department','assign_file__uploader__user','assign_file__uploader__department','assign_file__designation').get(pk=req_id)
    description=request.POST.get('description')
    upload_file=request.FILES.get('estimate')
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(file_id=requisition.assign_file).filter(receiver_id=user).get(is_read=False)
    
    # current, previous and next Designation and HoldsDesignation found out
    current_design = track.receive_design
    current_hold_design = HoldsDesignation.objects.select_related('user','designation','working').filter(user=user).get(designation=current_design)
    # prev_design = track.current_design.designation
    # prev_hold_design = track.current_design
    
    """
    # This entire thing decides who is the next designation
    if current_design.name == "Civil_JE":
        next_hold_design = HoldsDesignation.objects.get(designation__name="Civil_AE")
    elif current_design.name == "Electrical_JE":
        next_hold_design = HoldsDesignation.objects.get(designation__name="Electrical_AE")
    elif current_design.name == "Civil_AE" or current_design.name == "Electrical_AE":
        next_hold_design = HoldsDesignation.objects.get(designation__name="EE")
    elif current_design.name == "EE":
        if requisition.building == "hostel":
            next_hold_design = HoldsDesignation.objects.get(designation__name="Dean_s")
        else:
            next_hold_design = HoldsDesignation.objects.get(designation__name="DeanPnD")
    elif current_design.name == "Dean_s":
        next_hold_design = HoldsDesignation.objects.get(designation__name="DeanPnD")
    # if estimate greater than 10 lacs, left to discretion of Dean PnD to forward when required
    elif "DeanPnD" in current_design.name: 
        next_hold_design = HoldsDesignation.objects.get(designation__name="Director")
    """

    if 'Send' in request.POST:
        sent_design=request.POST.get('sent_design')
        sent_design = Designation.objects.get(name=sent_design)
        sent_hold_design = HoldsDesignation.objects.select_related('user','designation','working').get(designation=sent_design)
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=current_hold_design,
                receive_design=sent_design,
                receiver_id=sent_hold_design.working,
                remarks=description,
                upload_file=upload_file,
            )
        print("in forward, old track")
        print(vars(track))
        track.is_read = True
        track.save()
        office_dean_PnD_notif(request.user,sent_hold_design.working, 'assignment_received')
        """
        elif 'Revert' in request.POST:
            Tracking.objects.create(
                    file_id=requisition.assign_file,
                    current_id=extrainfo,
                    current_design=current_hold_design,
                    receive_design=prev_design,
                    receiver_id=prev_hold_design.working,
                    remarks=description,
                    upload_file=upload_file,
                )
            print("in revert, old track")
            print(vars(track))
            track.is_read = True
            track.save()
            office_dean_PnD_notif(request.user,prev_hold_design.working, 'assignment_reverted')
        """
    elif 'Reject' in request.POST:
        description = description + " This assignment has been rejected. No further changes to this assignment are possible. Please create new requisition if needed."
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=current_hold_design,
                receive_design=None,
                receiver_id=None,
                remarks=description,
                upload_file=upload_file,
                is_read = True,
            )
        track.is_read = True
        track.save()
        office_dean_PnD_notif(request.user,request.user, 'assignment_rejected')

    elif 'Approve' in request.POST:
        description = description + " This assignment has been approved. No further changes to this assignment are possible. Please create new requisition if needed."
        Tracking.objects.create(
                file_id=requisition.assign_file,
                current_id=extrainfo,
                current_design=current_hold_design,
                receive_design=None,
                receiver_id=None,
                remarks=description,
                upload_file=upload_file,
                is_read = True,
            )
        track.is_read = True
        track.save()
        office_dean_PnD_notif(request.user,request.user, 'assignment_approved')

    return HttpResponseRedirect("/office/officeOfDeanPnD/")


@login_required
def frequest(request):
    '''
    This function is used to display the form for viewing the requisitions.
    @param request:request from the page
    @var form:the form to be displayed
    @return:returns the path to the form page

    '''
    if request.method=='POST':
        form=Requisitionform(request.POST)
        print("hi")
    else:
        form=Requisitionform()

    return render(request,"officeModule/officeOfDeanPnD/viewRequisitions_content2.html",{'form':form})



def eisModulenew(request):
    '''
    This function is used to display the profile of the user.
    It takes request from the user and checks the designation of the user.
    If the designation is of type "supervisor" or "hod" it will display the profile of the user.
    If the designation is of type "employee" it will display the profile of the employee.
    If the designation is of type "admin" it will display the profile of the admin.
    It returns the profile of the user.
    @param request:request from the page
    @var form:the form to be displayed
    @return:returns the path to the form page
    '''
    project=Project_Registration.objects.select_related('PI_id__user','PI_id__department').all()
    project1=Project_Extension.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').all()
    project2=Project_Closure.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').all()
    project3=Project_Reallocation.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').all()

    design = HoldsDesignation.objects.select_related('user','designation','working').filter(working=request.user)
    print(design)
    desig=[]
    for i in design:
        desig.append(str(i.designation))

    context = {'project':project, 'project1':project1, 'project2':project2, 'project3':project3, 'desig':desig}

    return render(request, "eisModulenew/profile.html", context)



def officeOfPurchaseOfficr(request):
    '''
   This function is used to render the office of the purchase officer.
    @param request: request from the page
    @var context: the context variable to be passed to the template.
    @return: renders the office of the purchase officer page.
    '''
    return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html", {})

def admin_reject(request):
    '''
    This function is used to reject the selected applications.

    Parameters:
    request (HttpRequest): The request sent to the server by the client.

    Returns:
    HttpResponse: A response sent to the client.
    '''
    if request.method == "POST":
        marked = request.POST.getlist("selected")

        return HttpResponse("Done!")

def officeOfRegistrar(request):

    """
    Dashboard for the registrar to view files from different departments and navigate to a specific department
    This function is called when the office of the registrar is visited.
    It returns the template for the office of the registrar with the required context variables.
    The variables are:
        1. archive_view: A dictionary of all the files that are archived.
        2. director_track: A list of all the files that are currently being handled by the director.
        3. director_view: A dictionary of all the files that are currently being handled by the director, but have not been responded to by the director yet.
        4. view3: A list of all the files that are currently being handled by the establishment department.
        5. view4: A list of all the files that are currently being handled by the purchasing department.
        6. view5: A list of all the files that are currently being handled by the general administration department.
        7. current_date: The current date and time.
        8. general: A list of all the files that are currently being handled by the general administration department
        ."""

    archive_view = {}
    archive_track = Registrar_response.objects.all()
    for atrack in archive_track:
        archive_view[atrack] = atrack.track_id.file_id

    director_track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').filter(receive_design__name = "Registrar", current_design__designation__name = "Director")
    director_view = {}
    for track in director_track:
        if not Registrar_response.objects.filter(track_id = track):
            director_view[track.id] = track.file_id 

    estab_view = []
    purch_view1 = []
    purch_view2 = [] 
    genadmin_view = []
    current_date = datetime.datetime.now()

    context = { 
                #"archive_track":archive_track,
                "archive_view":archive_view,
                "director_track":director_track,
                "director_view":director_view,
                "view3":estab_view,
                "view4":purch_view1,
                "view5":purch_view2,
                "current_date":current_date,
                "general":genadmin_view
    }

    return render(request, "officeModule/officeOfRegistrar/officeOfRegistrar.html", context)

def officeOfRegistrar_ajax_submit(request):

    """
    AJAX handler to handle request for approve/reject/forwarding of a file
    This function handles the request for approve/reject/forwarding of a file.
    It takes the request from the user and returns the response.
    It takes the request in the form of ajax and returns the response in the form of ajax.
    The variables are:
        1. file_id: The id of the file to be approved/rejected/forwarded.
        2. action: The action to be performed on the file.
        3. comment: The comment to be added to the file.
        4. user_id: The id of the user who is performing the action.
        5. user_name: The name of the user who is performing the action.
        6. user_department: The department of the user who is performing the action.
        7. user_designation: The designation of the user who is performing the action.
        8. user_email: The email of the user who is performing the action.
        9. user_phone: The phone number of the user who is performing the action.
        10. user_address: The address of the user who is performing the action.
        11. user_type: The type of the user who is performing the action.
    @param request: request from the page
    @var context: the context variable to be passed to the template.
    @return: renders the office of the registrar page.
    """

    #print("ajax")
    if request.method == "POST":
        values = request.POST.getlist('values[]')
        #print(values)
        track = Tracking(pk = int(values[0]))
        rr = Registrar_response(track_id = track, remark = values[1], status = values[2])
        rr.save()
        #print(rr.id) 
        return HttpResponse("Done", content_type='text/html')
    else:
        return HttpResponse("Error", content_type='text/html')

def officeOfRegistrar_forward(request, id):

    """form to set receiver and designation of forwarded file """

    context = {"track_id": id}
    return render(request, "officeModule/officeOfRegistrar/forwardingForm.html", context)

def officeOfRegistrar_forward_submit(request):

    """
    Submit handler for the above form
    This function is used to forward the file to the given receiver.
    It takes the track_id of the file as input and then checks if the file is present in the database or not.
    If the file is present, it checks if the receiver is present in the database or not.
    If the receiver is present, it creates a new entry in the Tracking table with the current_id as the receiver and the receiver_id as the receiver.
    If the receiver is not present, it returns an error message.
    If the file is not present, it returns an error message.
    It also creates a new entry in the Registrar_response table with the status as "forwarded" and the remark as "forwarded to <receiver>".
    It returns a success message if the file is forwarded successfully.
    @param request: request from the page
    @var context: the context variable to be passed to the template.
    @return: renders the office of the registrar page.
    """
    
    if request.method == "POST":
        try:
            track_id = int(request.POST.get("track_id"))
            receiver = request.POST.get("receiver")
            receiver_design_text = request.POST.get("designation")

            receiver_id = User.objects.get(username=receiver)
            if not User.objects.get(username=receiver):
                return HttpResponse("Cannot find user")
            receiver_design = Designation.objects.filter(name=receiver_design_text)[0]
            current_id = request.user.extrainfo
            current_design = HoldsDesignation.objects.select_related('user','designation','working').filter(user = request.user)[0]
            t_id = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').get(id = track_id)
            up_file = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').get(id = track_id)
            remarks = ""

            Tracking.objects.create(
                        file_id=t_id.file_id,
                        current_id=current_id,
                        current_design=current_design,
                        receive_design=receiver_design,
                        receiver_id=receiver_id,
                        remarks=remarks,
                    )
            rr = Registrar_response(track_id = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').get(id=track_id), remark = "forwarded to"+receiver, status = "forward")
            rr.save()
            messages.success(request,'File sent successfully')
            return HttpResponse('File sent successfully')
        except IntegrityError:
            message = "FileID Already Taken.!!"
            return HttpResponse(message)
    else:
        return HttpResponse('Error sending file')

def officeOfRegistrar_view_file(request, id):
    """
        This is the view to handle registrar's request to view the details of a file, The file whoose id is passed is accessed through
    This is the view to handle registrar's request to view the details of a file, The file whoose id is passed is accessed through
    and the details of the file are displayed.
    The file is accessed through the Tracking model and the file is accessed through the File model.
    The file is then displayed.
    The context passed in the form of a dictionary consists of the file, the track of the file and the designations of the user.
    The template used is view_file.html which is present in the officeModule/officeOfRegistrar/templates folder.
    @param request: request from the page
    @var context: the context variable to be passed to the template.
    @return: renders the office of the registrar page.
    """
    #file = get_object_or_404(File, id=id)
    
    track = Tracking.objects.select_related('file_id__uploader__user','file_id__uploader__department','file_id__designation','current_id__user','current_id__department','current_design__user','current_design__working','current_design__designation','receiver_id','receive_design').get(id=id)
    file = track.file_id
    extrainfo = ExtraInfo.objects.select_related('user','department').all()
    holdsdesignations = HoldsDesignation.objects.select_related('user','designation','working').all()
    designations = HoldsDesignation.objects.select_related('user','designation','working').filter(user=request.user)

    context = {
        'designations':designations,
        'file': file,
        'track': [track],
    }
    print("view called")
    return render(request, 'officeModule/officeOfRegistrar/view_file.html', context)

def upload(request):
    '''
    This function is used to upload the file in the server.
    It takes request as the parameter.
    It returns the HttpResponse.
    It also saves the file in the database.
    @param request: request from the page
    @return: HttpResponse
    '''
    print("asdasdasdasd")
    docname = request.POST.get("docname")
    purpose = request.POST.get("purpose")
    description = request.POST.get("description")
    file = request.FILES['upload']
    print(file)
    request = registrar_create_doc(file_name=docname, purpose=purpose, Description=description, file=file)
    request.save()
    print(request)
    return HttpResponseRedirect("/office/officeOfRegistrar/")


@login_required(login_url='/accounts/login')
def officeOfHOD(request):
    '''
    This function is used to render the office of HOD page.
    It returns the office of HOD page with all the teaching credits not assigned and all the assigned teaching credits.
    @param request: request from the page
    @return: renders the office of HOD page.
    '''
    pro = Teaching_credits1.objects.filter(tag=0)
    pro1 = Assigned_Teaching_credits.objects.all()

    context = {'pro':pro,'pro1':pro1}
    return render(request, "officeModule/officeOfHOD/officeOfHOD.html", context)


# DEAN RSPC MODULE STARTS............................................................................................

# Project Registration Starts.................................................................................
@login_required
def project_register(request):
    """
    called from officeOfDeanRSPC/submit in office_module/urls.py
    usage: To fill details in the database when faculty registers the project from project management form
    model used: Project_Registration
    """

    """Project Fields added"""
    current = datetime.datetime.now()
    currentDate=current.strftime("%Y-%m-%d")
    user = request.user
    extrainfo = ExtraInfo.objects.select_related('user','department').get(user=user)
    project_title = request.POST.get('project_title')
    sponsored_agency = ""
    sponsored_agency = request.POST.get('sponsored_agency')
    CO_PI = request.POST.get('copi_name')
    try:
        start_date = request.POST.get('start_date')
    except:
        messages.error(request, ' Date not entered')
        return HttpResponseRedirect('/profile')

    duration = request.POST.get('duration')
    agreement = request.POST.get('agreement')
    amount_sanctioned = request.POST.get('amount_sanctioned')
    project_type = request.POST.get('project_type')
    project_operated = request.POST.get('project_operated')
    fund_recieved_date = None

    try:
        fund_recieved_date = request.POST.get('fund_recieved_date')
    except:
        messages.error(request, 'Date not entered')
        return HttpResponseRedirect('/profile')

    file = request.FILES.get('p_register')
    description = request.POST.get('remarks')
    applied_date = datetime.date.today()
    project_operated = request.POST.get('project_operated')
    mou = request.POST.get('agreement')

    """Validations for project Registration MOU and Co PI name"""
    if len(sponsored_agency) is 0 and amount_sanctioned > '0':
        messages.error(request, 'Error in Project Registration form: Amount cannot be sanctioned without Agency')
        return HttpResponseRedirect('/profile/')

    if project_operated == "PI and Co_pi" and CO_PI == "":
        messages.error(request, 'Error in Project Registration form: Enter CO_PI name')
        return HttpResponseRedirect('/profile/')

    if project_operated == "Only By PI" and len(CO_PI) > 0:
        messages.error(request, 'Error in Project Registration form: Select PI and Co_PI in option')
        return HttpResponseRedirect('/profile/')

    if mou == "Yes" and not file:
        messages.error(request, 'Error in Project Registration form: Attach the MOU')
        return HttpResponseRedirect('/profile/')

    if len(sponsored_agency) is 0 and file:
        messages.error(request, 'Error in Project Registration form: Enter agency name mentioned on MOU')
        return HttpResponseRedirect('/profile/')

    if fund_recieved_date is not None and start_date < fund_recieved_date:
        messages.error(request, 'Error in Project Registration form: Project cannot be started before receiving fund')
        return HttpResponseRedirect('/profile/')
   
    if currentDate > start_date :
        messages.error(request, 'Error in Project Registration form: You cannot start project without applying')
        return HttpResponseRedirect('/profile/')
    

    """Save the Details to Project_Registration Table"""
    request_obj = Project_Registration(PI_id=extrainfo, project_title=project_title,
                                       sponsored_agency=sponsored_agency, CO_PI=CO_PI, agreement=agreement,
                                       amount_sanctioned=amount_sanctioned, project_type=project_type,
                                       duration=duration, fund_recieved_date=fund_recieved_date, start_date=start_date,
                                       file=file, description=description, applied_date=applied_date)
    request_obj.save()

    context = {}
    messages.success(request, 'Application Sent.')
    return render(request, "eisModulenew/profile.html", context)


# Project Registration Table End.................................................................................


def project_registration_permission(request):
    """
    called from officeOfDeanRSPC/action {name: registration} in office_module /urls.py
    usage: Save details of Dean RSPC response. He can either approve reject or forward the registration application.
    model used: Project_Registration, emp_research_projects
    """

    """on approving project should be displayed in projects tab of Dean RSPC Dashboard"""
    if 'approve' in request.POST or (request.method == 'GET' and request.GET['a'] == "approve"):
        """id list works if multiple projects are selected at a time"""
        id_list = []
        id_list = request.POST.getlist('id[]')
        if len(id_list) == 0:
            id_list.append(int(request.GET['pk']))
        for id in id_list:
            # obj = Project_Registration.objects.get(pk=id)
            obj = get_object_or_404(Project_Registration, pk=id)
            if "Pending" in obj.DRSPC_response or "Disapprove" in obj.DRSPC_response:

                # approved project should be registered in project displayed to Dean RSPC

                pf_no = obj.PI_id.id
                pi = obj.PI_id.user.first_name + " " + obj.PI_id.user.last_name
                co_pi = obj.CO_PI
                title = obj.project_title
                funding_agency = obj.sponsored_agency
                start_date = obj.start_date
                days = obj.duration * 7
                finish_date = start_date + timedelta(days=days)
                financial_outlay = obj.amount_sanctioned
                ptype = obj.project_type
                print(ptype)
                date_entry = obj.applied_date
                status = "Ongoing"

                """On approving project by Dean, it should be saved in emp_research_projects model"""
                if ptype == "sponsoered research":
                    emp_projects = emp_research_projects(pi=pi, co_pi=co_pi, title=title, funding_agency=funding_agency,
                                                         start_date=start_date, finish_date=finish_date,
                                                         date_entry=date_entry,
                                                         financial_outlay=financial_outlay, status=status, pf_no=pf_no,
                                                         ptype=ptype)
                    emp_projects.save()
                elif ptype == "consultancy":
                    emp_projects = emp_consultancy_projects(consultants=pi, title=title, client=funding_agency,
                                                            start_date=start_date, end_date=finish_date,
                                                            duration=str(obj.duration) + " " + "weeks",
                                                            financial_outlay=financial_outlay,
                                                            pf_no=pf_no, date_entry=date_entry)
                    emp_projects.save()
                obj.DRSPC_response = "Approve"
                obj.save()
                # notification for dean RSPC
                office_module_DeanRSPC_notif(request.user, obj.PI_id.user,obj.DRSPC_response)

    elif "forward" in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Registration, pk=id)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = "Forward"
                obj.save()
    elif "reject" in request.POST or request.GET['a'] == "reject":
        id_list = request.POST.getlist('id[]')
        if len(id_list) == 0:
            id_list.append(int(request.GET['pk']))
        for id in id_list:
            obj = get_object_or_404(Project_Registration, pk=id)
            # print(obj.DRSPC_response)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = "Disapprove"
                obj.save()
                # notification for dean RSPC
                office_module_DeanRSPC_notif(request.user, obj.PI_id.user,obj.DRSPC_response)
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')


# PROJECT EXTENSION TABLE START .....................................................................................

def project_extension(request):
    """
    called from officeOfDeanRSPC/extention {name:p_extension} from office_module/urls.py
    usage: To fill details in the database when faculty wants to extend date of the project from project management form
    model used: Project_Registration, Project_Extension
    """
    print("entered1")

    """Project extension details added"""
    project_id = request.POST.get('project_id')
    # ob = get_object_or_404(Project_Registration, pk=project_id)
    try:
        ob = Project_Registration.objects.select_related('PI_id__user','PI_id__department').get(pk=project_id)
    except:
        messages.error(request, 'Project ID not found! Try again')
        return HttpResponseRedirect('/profile')

    user = request.user
    extrainfo = ExtraInfo.objects.select_related('user','department').get(user=user)
    """Validating the user in each form, if not then generating error message"""
    if extrainfo.id == ob.PI_id.id:
        # date = ob.start_date
        date = datetime.date.today()
        sponser = ob.sponsored_agency
        extended_duration = request.POST.get('extended_duration')
        extension_detail = request.POST.get('extension_details')

        if ob.DRSPC_response == 'Approve':
            file = request.FILES.get('extension_file')
            request_obj2 = Project_Extension(project_id=ob, date=date, extended_duration=extended_duration,
                                             extension_details=extension_detail, file=file)
            request_obj2.save()
            messages.success(request, 'Application Sent')
        else:
            messages.error(request, 'Project is not accepted by Dean RSPC')

    else:
        messages.error(request, 'Invalid User for entered Project ID')
    context = {}
    return render(request, "eisModulenew/profile.html", context)


# PROJECT EXTENSION TABLE END .......................................................................................


def project_extension_permission(request):
    """
    called from officeOfDeanRSPC/extension {name: extension} in office_module /urls.py
    usage: Save details of Dean RSPC response. He can either approve reject or forward the extended application.
    model used: Project_Extension, emp_research_projects
    """

    """Project extension conditions added"""
    if 'approve' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Extension, pk=id)
            if "Pending" in obj.DRSPC_response or "Disapprove" in obj.DRSPC_response:
                ob = get_object_or_404(Project_Registration, pk=obj.project_id.id)
                pf = int(ob.PI_id.id)
                title = ob.project_title
                ptype = ob.project_type

                if ptype == "sponsoered research":
                    pr = emp_research_projects.objects.get(pf_no=pf, title=title)
                    days = obj.extended_duration * 7
                    pr.finish_date = pr.finish_date + timedelta(days=days)
                    pr.save()

                elif ptype == "consultancy":
                    pr = emp_consultancy_projects.objects.get(pf_no=pf, title=title)
                    days = obj.extended_duration * 7
                    pr.end_date = pr.end_date + timedelta(days=days)
                    pr.save()

                obj.DRSPC_response = 'Approve'
                obj.save()
    elif 'forward' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Extension, pk=id)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = 'Forward'
                obj.save()
    elif 'reject' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Extension, pk=id)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = 'Disapprove'
                obj.save()
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')


# PROJECT CLOSURE TABLE START .......................................................................................

def project_closure(request):
    """
    called from officeOfDeanRSPC/close {name:p_close} in office_module/urls.py
    usage: To fill details in the database when faculty wants to close the project from project management form
    model used: Project_Registration, Project_Closure
    """
    print("entered2")
    """Project closure conditions added"""
    project_id = request.POST.get('project_id')
    try:
        extrainfo1 = Project_Registration.objects.select_related('PI_id__user','PI_id__department').get(pk=project_id)
    except:
        messages.error(request, 'Project ID not found! Try again')
        return HttpResponseRedirect('/profile')

    user = request.user
    extrainfo = ExtraInfo.objects.select_related('user','department').get(user=user)
    """Validating the user in each form, if not then generating error message"""
    if extrainfo.id == extrainfo1.PI_id.id:
        completion_date = request.POST.get('date')
        # extended_duration = ob.duration
        date = datetime.date.today()
        expenses_dues = request.POST.get('committed')
        expenses_dues_description = request.POST.get('remark1')
        payment_dues = request.POST.get('payment')
        payment_dues_description = request.POST.get('remark2')
        salary_dues = request.POST.get('salary')
        salary_dues_description = request.POST.get('remark3')
        advances_dues = request.POST.get('advance')
        advances_description = request.POST.get('remark4')
        others_dues = request.POST.get('other')
        other_dues_description = request.POST.get('remark5')
        overhead_deducted = request.POST.get('overhead')
        overhead_description = request.POST.get('remark6')

        if extrainfo1.DRSPC_response == 'Approve':
            request_obj1 = Project_Closure(project_id=extrainfo1, completion_date=completion_date,
                                           expenses_dues=expenses_dues,
                                           expenses_dues_description=expenses_dues_description,
                                           payment_dues=payment_dues, payment_dues_description=payment_dues_description,
                                           salary_dues=salary_dues,
                                           salary_dues_description=salary_dues_description, advances_dues=advances_dues,
                                           advances_description=advances_description,
                                           others_dues=others_dues, other_dues_description=other_dues_description,
                                           overhead_deducted=overhead_deducted, date=date,
                                           overhead_description=overhead_description)
            request_obj1.save()

            messages.success(request, 'Application Sent')
        else:
            messages.error(request, 'Project is not accepted by Dean RSPC')
    else:
        messages.error(request, 'Invalid User for entered Project ID')
    context = {}
    return render(request, "eisModulenew/profile.html", context)


# PROJECT CLOSURE TABLE END HERE ....................................................................................


def project_closure_permission(request):
    """
    called from officeOfDeanRSPC/closure {name: closure} in office_module /urls.py
    usage: Save details of Dean RSPC response. He can either approve reject or forward the closure application.
    model used: Project_Closure, emp_research_projects
    """

    """Project closure conditions added"""
    if 'approve' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Closure, pk=id)
            if obj.DRSPC_response == 'Pending':
                print("bb")
                obj.DRSPC_response = 'Approve'
                obj.save()
    elif 'forward' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Closure, pk=id)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = 'Forward'
                obj.save()
    elif 'reject' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Closure, pk=id)
            print(obj.DRSPC_response)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = 'Disapprove'
                obj.save()
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')


#  PROJECT REALLOCATION TABLE STARTS HERE .............................................................................
def project_reallocation(request):
    """
    called from officeOfDeanRSPC/extention {name:project_reallocation} from office_module/urls.py
    usage: To fill details in the database when faculty wants to reallocate fund of the project
    model used: Project_Registration, Project_Reallocation
    """

    """Project reallocation details added"""
    project_id = request.POST.get('project_id')
    try:
        ob1 = Project_Registration.objects.select_related('PI_id__user','PI_id__department').get(pk=project_id)
    except:
        messages.error(request, 'Project ID not found! Try again')
        return HttpResponseRedirect('/profile')
    user = request.user
    extrainfo = ExtraInfo.objects.select_related('user','department').get(user=user)
    """Validating the user in each form, if not then generating error message"""
    if extrainfo.id == ob1.PI_id.id:
        # applied_date = request.POST.get('applied_date')
        applied_date = datetime.date.today()
        pfno = request.POST.get('pfno')
        pbh = request.POST.get('p_budget_head')
        p_amount = request.POST.get('p_amount')
        nbh = request.POST.get('n_budget_head')
        n_amount = request.POST.get('n_amount')
        reason = request.POST.get('reason')

        if ob1.DRSPC_response == 'Approve':
            request_obj3 = Project_Reallocation(project_id=ob1, date=applied_date, previous_budget_head=pbh,
                                                previous_amount=p_amount, new_budget_head=nbh, new_amount=n_amount,
                                                transfer_reason=reason, pf_no=pfno)
            request_obj3.save()
            messages.success(request, 'Application Sent')

        else:
            messages.error(request, 'Project is not accepted by Dean RSPC')
    else:
        messages.error(request, 'Invalid User for entered Project ID')
    context = {}
    return render(request, "eisModulenew/profile.html", context)


# PROJECT REALLOCATION TABLE END HERE .................................................................................


def project_reallocation_permission(request):
    """
    called from officeOfDeanRSPC/officeOfDeanRSPC/reallocation {name: reallocation} in office_module /urls.py
    usage: Save details of Dean RSPC response. He can either approve reject or forward the reallocated application.
    model used: Project_Reallocation, emp_research_projects
    """

    """Project reallocation conditions added"""
    if 'approve' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Reallocation, pk=id)
            if "Pending" in obj.DRSPC_response or "Disapprove" in obj.DRSPC_response:
                ob = Project_Registration.objects.select_related('PI_id__user','PI_id__department').get(pk=obj.project_id.id)
                pf = int(ob.PI_id.id)
                title = ob.project_title
                ptype = ob.project_type

                if ptype == "sponsoered research":
                    pr = emp_research_projects.objects.get(pf_no=pf, title=title)
                    pr.financial_outlay = obj.new_amount
                    pr.save()

                elif ptype == "consultancy":
                    pr = emp_consultancy_projects.objects.get(pf_no=pf, title=title)
                    pr.financial_outlay = obj.new_amount
                    pr.save()
                obj.DRSPC_response = 'Approve'
                obj.save()
    elif 'forward' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Reallocation, pk=id)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = 'Forward'
                obj.save()
    elif 'reject' in request.POST:
        id_list = request.POST.getlist('id[]')
        for id in id_list:
            obj = get_object_or_404(Project_Reallocation, pk=id)
            print(obj.DRSPC_response)
            if obj.DRSPC_response == 'Pending':
                obj.DRSPC_response = 'Disapprove'
                obj.save()
    return HttpResponseRedirect('/office/officeOfDeanRSPC/')


"""
views for details page for Project Registration, Extension, Fund Reallocation, Closure
"""


def reg_details(request, pr_id):
    """
    This function accepts a request and a project id and returns a view for the details of the project.
    It also accepts a request and a project id and returns a view for the details of the project.
    """
    obj = get_object_or_404(Project_Registration, pk=pr_id)
    return render(request, "officeModule/officeOfDeanRSPC/view_details.html", {"obj": obj})


def ext_details(request, pr_id):
    """
    This function is used to display the details of the extension request.
    It takes the id of the extension request as input and displays the details of the extension request.
    It also displays the details of the project to which the extension request is made.
    It returns the html page which has the details of the extension request.
    @param request: A request object used to generate a response.
    @param pr_id: The id of the project for which the extension request is made.
    @return: The html page which has the details of the extension request.
    """
    pr = get_object_or_404(Project_Extension, pk=pr_id)
    obj = get_object_or_404(Project_Registration, pk=pr.project_id.id)
    return render(request, "officeModule/officeOfDeanRSPC/extension_details.html", {"obj": obj, 'pr': pr})


def reallocate_details(request, pr_id):
    """    
    This function is used to display the details of the reallocation request.
    @param request: Request from the webpage.
    @param pr_id: The id of the reallocation request.
    @return: Returns the webpage with the details of the reallocation request.
    """
    pr = get_object_or_404(Project_Reallocation, pk=pr_id)
    obj = get_object_or_404(Project_Registration, pk=pr.project_id.id)
    return render(request, "officeModule/officeOfDeanRSPC/reallocation_details.html", {"obj": obj, 'pr': pr})


def closure_details(request, pr_id):
    """
    This function is used to display the details of the project for which the closure is being done.
    The function takes in a request and the id of the project for which the closure is being done.
    It then fetches the project registration object for the given id and passes it to the template along with the project closure object.
    The template then displays the project details.
    @param request: Request from the webpage.
    @param pr_id: The id of the project for which the closure is being done.
    @return: Returns the webpage with the details of the project.
    """
    pr = get_object_or_404(Project_Closure, pk=pr_id)
    obj = get_object_or_404(Project_Registration, pk=pr.project_id.id)
    return render(request, "officeModule/officeOfDeanRSPC/closure_details.html", {"obj": obj, 'pr': pr})


# DEAN RSPC MODULE ENDS HERE ..........................................................................................



def hod_action(request):
    '''
    This function is used to forward the project to the next authority.
    It takes a request from the user and checks if the user is authenticated.
    If yes, it takes the id of the project and checks if the project is eligible to be forwarded.
    If yes, it forwards the project to the next authority.
    It also saves the current date and time when the project was forwarded.
    It also sets the HOD_response of the project to 'Forwarded'.
    Then it redirects to the profile page of the user.
    @param request: A request object used to generate a response.
    @return: Redirects to the profile page of the user.
    '''
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Registration.objects.select_related('PI_id__user','PI_id__department').get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()

    return HttpResponseRedirect('/office/eisModulenew/profile/')

def hod_closure(request):
    """
    This function is used to forward the project to the accounts section.
    It takes a request from the user as the input.
    Then it checks whether the project is eligible to be forwarded to the accounts section.
    Then it checks whether the accounts section has already seen the project or not.
    If it is already seen, then it forwards the project to the accounts section.
    If it is not seen, then it forwards the project to the accounts section.
    Then it returns a HttpResponseRedirect to the profile page.
    @param request: A request object used to generate a response.
    @return: Returns a HttpResponseRedirect to the profile page.
    """
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Closure.objects.get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()

    return HttpResponseRedirect('/office/eisModulenew/profile/')

def hod_extension(request):
    """
    This function is used to forward the project extension request to the HOD.
    It takes a request as an input and checks if the HOD_response is pending or not.
    If the response is pending, it sets the HOD_response to 'Forwarded' and saves the object.
    Then it redirects to the profile page.
    @param request: A request object used to generate a response.
    @return: Returns a HttpResponseRedirect to the profile page.
    """
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Extension.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()
    return HttpResponseRedirect('/office/eisModulenew/profile/')

def hod_allocation(request):
    """  This function is used to forward the request to hod.
    It takes a request as an input and checks if the HOD_response is pending or not.
    If the response is pending, it sets the HOD_response to 'Forwarded' and saves the object.
    Then it redirects to the profile page.
    @param request: A request object used to generate a response.
    @return: Returns a HttpResponseRedirect to the profile page.
    """
    if 'forward' in request.POST:
        id=request.POST.get('id')
        obj=Project_Reallocation.objects.select_related('project_id__PI_id__user','project_id__PI_id__department').get(pk=id)
        print(obj.HOD_response)
        if obj.HOD_response == 'Pending' or obj.HOD_response == 'pending' :
            obj.HOD_response='Forwarded'
            obj.save()

    return HttpResponseRedirect('/office/eisModulenew/profile/')

def pdf(request,pr_id):
    '''
    This function is used to display the details of the project to the office of dean RSPC.
    It takes a request and pr_id as parameters.
    It returns a response to the user.
    @param request: default parameter - this is a django request parameter.
    @param pr_id: default parameter - this is a unique id for each project.
    @return: response to the user.
    '''
    obj=Project_Registration.objects.select_related('PI_id__user','PI_id__department').get(pk=pr_id)
    return render(request,"officeModule/officeOfDeanRSPC/view_details.html",{"obj":obj})

def genericModule(request):
    context = {}
    return render(request, "officeModule/genericModule/genericModule.html", context)

@login_required
def teaching_form(request):
    """
    This function is used to add the courses to the Teaching_credits1 table.
    @param request: Request Object contains the request to the page.
    @return: Response Object containing appropriate response.
    """
    roll_no=request.POST.get('roll_no')
    name=request.POST.get('name')
    programme=request.POST.get('programme')
    branch=request.POST.get('branch')
    course1=request.POST.get('course1')
    course2=request.POST.get('course2')
    course3=request.POST.get('course3')

    request_obj = Teaching_credits1(roll_no=roll_no,name=name, programme=programme, branch=branch,
                                     course1=course1, course2=course2, course3=course3)
    print("===================================================================")
    request_obj.save()
    context={}
    return render(request,"officeModule/officeOfHOD/tab4content4.html",context)

@login_required
def hod_work(request):

    """
    This function is used to assign the courses to the students.
    It takes the roll number and the course name as the input.
    It saves the assigned course in the database.
    It also updates the teaching credits table.
    It returns the HttpResponseRedirect to the same page.
    @param request: Request Object contains the request to the page.
    @return: Response Object containing appropriate response.
    """
    roll_no=request.POST.get('roll_no')
    tc = Teaching_credits1.objects.get(roll_no=roll_no)
    assigned_course=request.POST.get('assigned_course')
    request_obj1 = Assigned_Teaching_credits(roll_no=tc,assigned_course=assigned_course)
    request_obj1.save()
    tc.tag=1
    tc.save()
    context={}
    return render(request,"officeModule/officeOfHOD/tab4content4.html",context)
    """return HttpResponseRedirect('')"""
    """return render(request,"officeModule/officeOfHOD/tab4content1.html",context)"""

def genericModule(request):
    context = {}
    return render(request, "ofricModule/genericModule.html", context)

def newordershod(request):
    """
    This function is used to approve the order by HOD.
    It takes the id of the order as input and then checks for the existence of the order.
    If the order exists, it sets the HOD_approve_tag to 1 and then saves the order.
    If the order does not exist, it returns an error message.
    It also sends a message to the user about the status of the order.
    @param request: Request Object contains the request to the page.
    @return: Response Object containing appropriate response.
    """
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').get(id = objid)
            obj.HOD_approve_tag = 1
            obj.director_approve_tag = 0
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            #render()
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

def newordersregistrar(request):
    '''
    This function is used to approve the new orders by registrar.
    It takes the request from the user and checks if the request is post or not.
    If the request is post then it takes the object id from the request and checks if the object exists in the database or not.
    If the object exists then it sets the registrar_approve_tag to 1 and director_approve_tag to 1.
    Then it saves the object and returns a string message to the user.
    If the object does not exist then it returns a string message to the user.
    @param request: Request Object contains the request to the page.
    @return: Response Object containing appropriate response.
    '''
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').get(id = objid)
            obj.registrar_approve_tag = 1
            obj.director_approve_tag = 1
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            return HttpResponse('work is being done')
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

def newordersregistrar2(request):
    """
    This function is used to approve the new orders by registrar.
    It takes the request from the user and checks if the request is post or not.
    If the request is post then it takes the object id from the form and checks if the object exists in the database or not.
    If the object exists then it sets the registrar_approve_tag to 1 and saves the object.
    If the object does not exist then it returns a message saying that the object does not exist.
    If the request is not post then it returns a message saying that the request is not post.
    @param request: Request Object contains the request to the page.
    @return: Response Object containing appropriate response.
    """
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').get(id = objid)
            obj.registrar_approve_tag = 1
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            return HttpResponse('work is being done')
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

def newordersdirector(request):
    """
    This function is used to approve the orders by the director.
    It takes the request from the user and checks if the request is post or not.
    If the request is post then it takes the id of the order and checks if the order exists or not.
    If the order exists then it sets the director_approve_tag to 1 and saves the order.
    If the order does not exist then it returns a message saying that the order does not exist.
    If the request is not post then it returns a message saying that the request is not post.
    @param request: Request Object contains the request to the page.
    @return: Response Object containing appropriate response.
    """
    print("hello2")
    #this one creates and stores the data in django forms
    print("new ord caled")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        #find the instance with this objid and set its hod_approve_bit to 1
        try:
            obj = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').get(id = objid)
            obj.director_approve_tag = 1
            obj.save()
            print("work done")
            str = "order with id "+ objid +" has been approved by you"
            messages.info(request,str)
            return HttpResponse('work is being done')
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

#on operation
def newordersdirectorview(request):
    """
    This function is used to view the details of the orders placed by the different
    indentors.
    It takes a request as an input and returns the details of the orders placed by the
    indentors.
    It also takes the id of the order as an input and returns the details of the order
    with the given id.
    If the order with the given id is not found, it returns a message as an output.
    If the order is found, it returns the details of the order as an output.
    """
    print("metoo")
    #return HttpResponse("pis of")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
    try:
        obj = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').get(id = objid)
        context ={"data":obj}
        print(context)
        return HttpResponse("abhi iska template nahi bana hai")
    except apply_for_purchase.DoesNotExist:
        print("model not exists")
    return render(request, "officeModule/officeOfPurchaseOfficer/viewordersdirector.html",context=context)

def newordersPO(request):
    """
    This function is used to update the status of the purchase order to new order.
    It takes the id of the purchase order as input and updates the status of the purchase order to new order.
    It returns a string "you are the best"
    """
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        try:
            obj = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').get(id = objid)
            obj.gem_tag=-1
            obj.save()
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

def newordersPOonGem(request):
    """
    This function is used to update the status of the purchase order to the gem.
    It takes the id of the purchase order as the input and updates the status of the purchase order to the gem.
    It returns a string "you are the best"
    """
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        try:
            obj = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').get(id = objid)
            obj.gem_tag=1
            obj.save()
        except apply_for_purchase.DoesNotExist:
            print("model not exists")
    return HttpResponse("you are the best ")

@login_required
def apply_purchase(request):
    """
    This function is used to apply for purchase.
    It takes request as an argument and returns the arguments.
    """
    print("hello")
    #
#    user = get_object_or_404(User,username=request.user.username)
#    user=ExtraInfo.objects.get(user=user)
    current_user = get_object_or_404(User, username=request.user.username)
    #print(current_user)
    user_details = ExtraInfo.objects.select_related('user','department').all().filter(user=current_user).first()
    #print(user_details)
    user_type = HoldsDesignation.objects.select_related('user','designation','working').all().filter(user=current_user).first()
    #print(user_type)
    usertype=str.split(str(user_type))
    #print(usertype)
    # Academics Admin Check
    user=usertype[0]
    #desig_id = Designation.objects.all().filter(name='Faculty')
    #print(desig_id)
    #print ("yaha se")
    #print(user)
    #print(user_type)
    # user = request.user
    # user = User.objects.get(id=1).extrainfo
    #user=request.user
    if(user == "student"):
        return HttpResponse('You are not authorised to view this page')
    # user=ExtraInfo.objects.get(id=user)
    #print(hello)
    if request.method == 'POST':
        item_name=request.POST.get('item_name')
        quantity=request.POST.get('quantity')
        expected_cost=int(request.POST.get('expected_cost'))

        if  expected_cost >=25000 and expected_cost <= 250000 :
            local_comm_mem1_id=request.POST.get('local_comm_mem1_id')
            local_comm_mem2_id=request.POST.get('local_comm_mem2_id')
            local_comm_mem3_id=request.POST.get('local_comm_mem3_id')

        nature_of_item1= 1 if request.POST.get('nature_of_item1') == 'on' else 0
        nature_of_item2= 1 if request.POST.get('nature_of_item2') == 'on' else 0

        # extra = ExtraInfo.objects.all()
        # extraInfo = ExtraInfo.objects.get(id=inspecting_authority_id)

        purpose=request.POST.get('purpose')
        # budgetary_head_id=request.POST.get('budgetary_head_id')
        # inspecting_authority_id=request.POST.get('inspecting_authority_id')
        expected_purchase_date=request.POST.get('expected_purchase_date')
        # print(expected_purchase_date+"...........................")

    # xyz=apply_for_purchase(indentor_name=name,)
    # xyz.save()

        #print("hello1")

        a = apply_for_purchase.objects.create(
                item_name=item_name,
                quantity=int(quantity),
                expected_cost=expected_cost,
                nature_of_item1=nature_of_item1,
                nature_of_item2=nature_of_item2,
                purpose=purpose,
                # budgetary_head_id = budgetary_head_id,
                # inspecting_authority_id=inspecting_authority_id,
                expected_purchase_date= expected_purchase_date,
                indentor_name=user_details,

        )
        a.save()
        print("yahan tak toh pahunch gaya mai")
        messages.info(request, 'order placed successfully')
        if  expected_cost >=25000 and expected_cost <= 250000 :
            b = purchase_commitee.objects.create(

            local_comm_mem1_id=local_comm_mem1_id,
            local_comm_mem2_id=local_comm_mem2_id,
            local_comm_mem3_id=local_comm_mem3_id,
            )
            b.save()



            #right now its hard coded for pkhanna o/w  use utype : utype for context in both render
        #return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'utype':2})
        return HttpResponseRedirect('/office/officeOfPurchaseOfficer/')
    else:
        return HttpResponseRedirect('/office/officeOfPurchaseOfficer/')

@login_required
def add_items(request):
    """
    Adds an item to the inventory.
    Parameters:
        request (HttpRequest): An HTTP Request objects which has the item details.
    Returns:
        HttpResponse: An HTTP Response message.
    
    """
    current_user = get_object_or_404(User, username=request.user.username)
    print(current_user)
    user_details = ExtraInfo.objects.select_related('user','department').all().filter(user=current_user).first()
    print(user_details)
    user_type = HoldsDesignation.objects.select_related('user','designation','working').all().filter(user=current_user).first()
    print(user_type)
    usertype=str.split(str(user_type))
    print(usertype)
    # Academics Admin Check
    user=usertype[0]
    #desig_id = Designation.objects.all().filter(name='Faculty')
    quantity=0
    #print(desig_id)
    print ("yaha se")
    print(user)
    if(user == "student"):
        return HttpResponse('You are not authorised to view this page')
    if request.method == 'POST':
        item_name=request.POST.get('item_name')
        nature_of_item2= 1 if request.POST.get('nature_of_item2') == 'on' else 0
        quantity=request.POST.get('quant')
        order_id=request.POST.get('order_id')
        print(quantity)
        a = stock.objects.create(
            item_type=nature_of_item2,
            item_name=item_name,
            quantity=quantity,
        )
        a.save()
        messages.info(request, 'item added in inventory successfully')
        return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content2.html",{})
    else:
        return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content2.html",{})

@login_required
def view_items(request):
    return HttpResponse(1)


def submit(request):
    context = {}
    return render(request, "officeModule/officeOfHOD/view_details.html", context)

@login_required
def after_purchase(request):
    """
    This function is used to update the amount and invoice number of the purchase after the purchase is done.
    The function takes a POST request as its parameter.
    On submission of the form, the function updates the amount and invoice number of the purchase.
    The function then redirects to the after_purchase page.
    Parameters:
        request (HttpRequest): An HTTP Request objects which has the item details.
    Returns:
        HttpResponse: An HTTP Response message.
    """
    if request.method == 'POST':
        '''if "submit" in request.POST:'''
        file_no=request.POST.get('file_no')
        amount=request.POST.get('amount')
        invoice=request.POST.get('invoice')
        apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(id=file_no).update(amount=amount, invoice=invoice)

        return render(request, "officeModule/officeOfPurchaseOfficer/after_purchase.html",{})
    else:
        return render(request, "officeModule/officeOfPurchaseOfficer/after_purchase.html",{})

def officeOfPurchaseOfficer(request):
    """
    This function is used to render the template for the office of the purchase officer.
    It takes request from the user and checks the designation of the user.
   Ex.  If the designation is purchase officer, it renders the template for the purchase officer.
   Ex. If the designation is not purchase officer, it redirects to the home page.
   Ex. If the designation is HOD, it renders the template for the HOD.
   Ex. If the designation is not HOD, it redirects to the home page.
   Ex. If the designation is registrar, it renders the template for the registrar.
    @param request: An HTTP Request object.
    @return: An HTTP Response object.

    """
    context={}
    current_user = get_object_or_404(User, username=request.user.username)
    #print(current_user)
    user_details = ExtraInfo.objects.select_related('user','department').all().filter(user=current_user).first()
    #print(user_details)
    user_type = HoldsDesignation.objects.select_related('user','designation','working').all().filter(user=current_user).first()
    #print(user_type)
    usertype=str.split(str(user_type))
    print(usertype)
    # Academics Admin Check
    user_type=None
    user = usertype[2]

    if(user == "student"):
        return HttpResponse('You are not authorised to view this page')
    if(len(usertype)>3):
        user_type=usertype[2]+usertype[3]
    elif(len(usertype)>=2):
        user_type = usertype[2]
    print(user_type)
    p = None
    q = None
    ph = None
    #print ("yaha se")
    #print(user_type)
    #use user_type to check the designation of actor
    #utype is for rendering tags (templates)
    utype=0#this is for manage store and vendors
    utype2=0#this is for orders tag
    #but yahan par bhi divide as utype21 utype22(just a thought for.....)
    utype3=0#this is for indent forms
    utype4=0#this is for purchase history

    per_user=str(current_user)
    if(user_type=="DeputyRegistrar" or user_type=="Registrar" or user_type=="PurchaseOfficer"):
        utype=1
    #elif(user_type=="HOD(ME)" or user_type=="HOD(ECE)" or user_type=="CSE HOD" or user_type=="HOD"):
    #bug was that pkhanna was being recognized as associate professor not HOD
    if(per_user=="pkhanna" or user_type=="DeputyRegistrar" or user_type=="Registrar" or user_type=="HOD" or user_type=="PurchaseOfficer" or user_type =="Director" or user_type=="director"):
        utype2=1
        #print("hard code working hai yahan tak for HOD designation")

    if(user_type == "AssociateProfessor" or user_type == "AssistantProfessor" or user_type=="HOD" or user_type=="Director" or user_type=="director"):#give more such equivalent designations
        utype3=1
        #print("recognized actor assoc prof")


    #print("yahan tak sab sahi")

    if request.method == 'POST':

        if "submit" in request.POST:

            vendor_name=request.POST['vendor_name']
            vendor_item=request.POST['vendor_item']
            vendor_address=request.POST['vendor_address']

            vendor.objects.create(
                vendor_name=vendor_name,
                vendor_item=vendor_item,
                vendor_address=vendor_address,
            )
            messages.info(request, 'vendor added successfully')
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{})


        elif "new_orders" in request.POST:
            #note when not in hard code, pkhanna to be replaced  by str(current_user)
            #render appropritate templates as per the actor like approvalHOD2 or approvalRegistrar2 etc
            #this is working through user_type not utype
            if(user_type=="HOD" or per_user=="pkhanna"):
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(HOD_approve_tag=0).order_by('-id')
                context={'alldata':alldata}
                print(context)
                return render(request, "officeModule/officeOfPurchaseOfficer/approvalHOD2.html",context=context)

            elif(user_type=="DeputyRegistrar" or user_type=="Registrar" or per_user=="swapnali"):
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(HOD_approve_tag=1,registrar_approve_tag=0).order_by('-id')
                #alldata2 = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=0,expected_cost__gte = 50001)
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvalRegistrar.html",context=context)

            elif(user_type=="director" or user_type=="Director"):
                #alldata = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=1,expected_cost__gte = 50001)
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(expected_cost__gte = 50001,director_approve_tag=0).order_by('-id')
                print(alldata)
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvaldirector.html",context=context)

            elif(user_type=="purchaseofficer" or user_type=="PurchaseOfficer"):
                print("entered purchase officer section")
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(director_approve_tag=1,gem_tag=0).order_by('-id')
                #alldata2 = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=1,expected_cost__lte = 50000)
                #context = {'alldata':alldata,'alldata2':alldata2}SS

                context = {'alldata':alldata,'des':user_type}
                #print("data 0",context)
                return render(request, "officeModule/officeOfPurchaseOfficer/approvalpurchaseofficer.html",context=context)



        elif "approved_orders" in request.POST:
            if(user_type=="HOD" or per_user=="pkhanna"):
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(HOD_approve_tag=1).order_by('-id')
                context={'alldata':alldata}
                #print(context)
                return render(request, "officeModule/officeOfPurchaseOfficer/approvedHOD.html",context=context)

            elif(user_type=="DeputyRegistrar" or user_type=="Registrar" or per_user=="swapnali"):
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(registrar_approve_tag=1,expected_cost__lte = 50000).order_by('-id')
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvedRegistrar.html",context=context)

            elif(user_type=="director" or user_type=="Director"):
                #alldata = apply_for_purchase.objects.filter(HOD_approve_tag=1,registrar_approve_tag=1,expected_cost__gte = 50001)
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(expected_cost__gte = 50001,director_approve_tag=1).order_by('-id')
                #print(alldata)
                context = {'alldata':alldata}
                return render(request, "officeModule/officeOfPurchaseOfficer/approvedDirector.html",context=context)

            #make the templates as per the actors




        elif "checked_orders" in request.POST:
            if(user_type == "PurchaseOfficer" or user_type == "purchseofficer"):
                #print("in checked orders")
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(director_approve_tag=1).exclude(gem_tag=0)
                context = {'alldata':alldata,'des':user_type}
                return render(request, "officeModule/officeOfPurchaseOfficer/checkedpurchaseofficer.html",context=context)

        elif "forwarded_orders" in request.POST:
            if(user_type == "Registrar" or user_type == "DeputyRegistrar"):
                #print("in checked orders")
                alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(expected_cost__gte = 50001,director_approve_tag=0).order_by('-id')
                context = {'alldata':alldata,'des':user_type}

                return render(request, "officeModule/officeOfPurchaseOfficer/forwardedRegistrar.html",context=context)


        elif "store" in request.POST:

            item_type=request.POST.get('item_type')
            item_name=request.POST.get('item_name')
            quantity=request.POST.get('qunatity')
            str2 = " "
            it = " "
            a = stock.objects.create(
                item_type=item_type,
                item_name=item_name,
                quantity=quantity,
            )
            a.save()
            if(item_type==0):
                it="consumable"
            else:
                it="non-consumable"
            str2 = "item " + item_name + "of type " + it + " has been added to the store"
            messages.info(request,str2)

        elif "manage_store" in request.POST:
            return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content2.html")

        elif "view_store" in request.POST:
            q=stock.objects.all()
            return render(request, "officeModule/officeOfPurchaseOfficer/manageStore_content1.html",{"q":q})
            #return HttpResponse(1)

        elif "item_search" in request.POST:
            srch = request.POST['item_name']
            # print("this is the itemset")
            # print(srch)
            #match = stock.objects.filter(Q(item_name__icontains=srch))
            match = stock.objects.filter(item_name=srch)
            # print(match)
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'match':match})

        elif "vendor_search" in request.POST:
            sr = request.POST['item']
            matchv = vendor.objects.filter(Q(vendor_item__icontains=sr))
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'matchv':matchv})

        elif "viewhistory" in request.POST:
            alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(indentor_name = user_details)
            print(alldata)
            return render(request, "officeModule/officeOfPurchaseOfficer/purchaseHistory_content1.html",{'alldata':alldata})

        elif "viewstatus" in request.POST:
            alldata = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(indentor_name = user_details)
            print(alldata)
            return render(request, "officeModule/officeOfPurchaseOfficer/purchaseHistory_content2.html",{'alldata':alldata})


        elif "purchase_search" in request.POST:
            pr = request.POST['file']
            phmatch = apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').filter(Q(id=pr))
            return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'phmatch':phmatch})
        '''elif "delete_item" in request.POST:
            a = request.POST.getlist('box')
            for i in range(len(a)):
                k = stock.objects.get(id = a[i])
                k.delete()
            return HttpResponse("successflly deleted item")'''

    else:
        #this is the manage store and vendors section
        p=vendor.objects.all()
        q=stock.objects.all()
        ph=apply_for_purchase.objects.select_related('indentor_name__user','indentor_name__department').all()

    return render(request, "officeModule/officeOfPurchaseOfficer/officeOfPurchaseOfficer.html",{'p':p,'q':q,'ph':ph,'utype':utype,'utype2':utype2,'utype3':utype3,'des':user_type})

def delete_item(request,id):
    """
    Deletes an item from the database.

    @Parameters:
        request (HttpRequest): An HTTP Request object.
        id (int): The id of the item to be deleted.

    @Returns:
        HttpResponse: Directs the user to different pages, depending on the button clicked.
    
    """
    #template = 'officemodule/officeOfPurchaseOfficer/manageStore_content1.html'
    print("reached delete_item")
    if request.method=='POST':
        objid = request.POST.get('id')
        print(objid)
        item = get_object_or_404(stock,id=id)
        item.delete()


    return HttpResponse("Deleted successfully")

def delete_vendor(request,id):
    """
    This function is used to delete the vendor.
    It has one parameter named request.
    @param request: It is an http request.
    @return: It returns the response.
    """
    #template = 'officemodule/officeOfPurchaseOfficerr/manageStore_content1.html'
    print(">>>>>>>")
    print(id)
    ven = get_object_or_404(vendor,id=id)
    ven.delete()
    return HttpResponse("Deleted successfully")

def edit_vendor(request,id):
    """
    This function is used to edit the vendor details.
    It takes the id of the vendor as the parameter and
    returns the vendor details in the form of a html page.
    It also returns the vendor details in a dictionary format
    to the html page.
    """
    p= get_object_or_404(vendor,id=id)
    context={
        'p' : p
    }
    return render(request,"officeModule/officeOfPurchaseOfficer/edit.html",context)
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')

def edit(request):

    ID=request.POST.get('vendor_id')
    name=request.POST.get('vendor_name')
    item=request.POST.get('vendor_item')
    add=request.POST.get('vendor_address')
    d=vendor(id=ID,vendor_name=name,vendor_item=item,vendor_address=add)
    d.save()
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')

def edit_item(request,id):


    p= get_object_or_404(stock,id=id)
    context={
        'p' : p
    }
    return render(request,"officeModule/officeOfPurchaseOfficer/edit1.html",context)
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')

def edit1(request):

    ID=request.POST.get('item_id')
    name=request.POST.get('item_name')
    add=request.POST.get('quantity')
    d=stock(id=ID,item_name=name,quantity=add)
    d.save()
    return HttpResponseRedirect('/office/officeOfPurchaseOfficer')

# DIRECOR OFFICE MODULE .........................................

def directorOffice(request):
     if request.user.is_authenticated:
        user_name=get_object_or_404(User,username=request.user.username)
        user=ExtraInfo.objects.select_related('user','department').all().filter(user=user_name).first()
        holds=HoldsDesignation.objects.select_related('user','designation','working').filter(user=user.user)
        deslist1=['Director']
        context={ }

        # if user.user_type == 'faculty': 
        #     context={ }
        #     return render(request, "officeModule/directorOffice/directorOffice.html", context)

        if user.user_type == 'faculty': 
            return render(request, "officeModule/directorOffice/directorOffice.html", context)
        else:
            return render(request, "officeModule/directorOffice/unauthorised.html", context)

#function gets the count of faculties department wise and top scoring students yearwise and department wise
def viewProfile(request):
    faculty = Faculty.objects.select_related('id__user','id__department').all()
    student = Student.objects.select_related('id__user','id__department').all()
    staff = Staff.objects.select_related('id__user','id__department').all()

    cs = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'CSE').count()
    ec = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'ECE').count()
    me = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'ME').count()
    des = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'DESIGN').count()
    ns = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'NATURAL SCIENCE').count()
    #Top students of each year
    top_2017_cse = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2017', id__department__name = 'CSE').order_by('-cpi')[:3]
    

    top_2016_cse = Student.objects.filter(id__id__startswith = '2016', id__department__name = 'CSE').order_by('-cpi')[:3]
    

    top_2015_cse = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2015', id__department__name = 'CSE').order_by('-cpi')[:3]
    
    top_2017_me = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2017', id__department__name = 'ME').order_by('-cpi')[:3]
    
    top_2016_me = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2016', id__department__name = 'ME').order_by('-cpi')[:3]
    
    top_2015_me = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2015', id__department__name = 'ME').order_by('-cpi')[:3]
    
    top_2017_ece = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2017', id__department__name = 'ECE').order_by('-cpi')[:3]
   
    top_2016_ece = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2016', id__department__name = 'ECE').order_by('-cpi')[:3]
    
    top_2015_ece = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2015', id__department__name = 'ECE').order_by('-cpi')[:3]
    
    top_2017_design = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2017', id__department__name = 'DESIGN').order_by('-cpi')[:3]
    
    top_2016_design = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2016', id__department__name = 'DESIGN').order_by('-cpi')[:3]
    
    top_2015_design = Student.objects.select_related('id__user','id__department').filter(id__id__startswith = '2015', id__department__name = 'DESIGN').order_by('-cpi')[:3]
    
    all_counts = [cs,ec,me,des,ns]
    
    top_17_cse = []
    for x in top_2017_cse:
        top_17_cse.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_17_cse.append(x.cpi)

    top_17_ece = []
    for x in top_2017_ece:
        top_17_ece.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_17_ece.append(x.cpi)

    
    top_17_me = []
    for x in top_2017_me:
        top_17_me.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_17_me.append(x.cpi)

    top_17_design = []
    for x in top_2017_design:
        top_17_design.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_17_design.append(x.cpi)

    top_16_cse = []
    for x in top_2016_cse:
        top_16_cse.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_16_cse.append(x.cpi)

    top_16_ece = []
    for x in top_2016_ece:
        top_16_ece.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_16_ece.append(x.cpi)

    top_16_me = []
    for x in top_2016_me:
        top_16_me.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_16_me.append(x.cpi)

        top_16_design = []
    for x in top_2016_design:
        top_16_design.append(x.id.user.first_name + ' ' + x.id.user.last_name)  
        top_16_design.append(x.cpi)

    top_15_cse = []
    for x in top_2015_cse:
        top_15_cse.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_15_cse.append(x.cpi)

    top_15_ece = []
    for x in top_2015_ece:
        top_15_ece.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_15_ece.append(x.cpi)

    top_15_me = []
    for x in top_2015_me:
        top_15_me.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_15_me.append(x.cpi)

    top_15_design = []
    for x in top_2015_design:
        top_15_design.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        top_15_design.append(x.cpi)

    context={'all_counts':all_counts, 'top_17_cse': top_17_cse, 'top_16_cse': top_16_cse ,'top_15_cse': top_15_cse ,'top_17_ece': top_17_ece, 'top_16_ece': top_16_ece ,'top_15_ece': top_15_ece ,'top_17_me': top_17_me, 'top_16_me': top_16_me ,'top_15_me': top_15_me, 'top_17_design': top_17_design, 'top_16_design': top_16_design, 'top_15_design': top_15_design}
    #data = serializers.serialize('json', context)
    return JsonResponse(context)


# function for displaying projects under office module
def viewOngoingProjects(request):

    project = Project_Registration.objects.select_related('PI_id__user','PI_id__department').all()
    #title + type
    project_details = []

    for p in project:
        project_details.append(p.project_title)
        project_details.append(p.project_type)
        project_details.append(p.duration)
        project_details.append(p.sponsored_agency)
        project_details.append(p.HOD_response)

    print(project_details)

    context = {'project_details' : project_details} 
    return JsonResponse(context)     


# function for displaying Gymkhana office bearers
def viewOfficeBearers(request):
    club_info = Club_info.objects.all()
    club_details = []
    print(club_info)

    for c in club_info:
        club_details.append(c.club_name)
        club_details.append(c.co_ordinator.id.user.first_name + ' ' + c.co_ordinator.id.user.last_name)
        club_details.append(c.co_coordinator.id.user.first_name + ' ' + c.co_coordinator.id.user.last_name)
        club_details.append(c.faculty_incharge.id.user.first_name + ' ' + c.faculty_incharge.id.user.last_name)

    print(club_details)

    context = {'club_details': club_details}
    return JsonResponse(context)


#function for viewing the scheduled meetings
def viewMeetings(request):
    meeting_info=Meeting.objects.all()
    
    meeting = []
    

    for x in meeting_info:
        meeting.append(x.agenda)
        meeting.append(x.date)
        meeting.append(x.time)
        meeting.append(x.venue)
        #meeting.append(x.member)

    print(meeting)

    context = {
        'meeting':meeting 
    }    

    return JsonResponse(context)


# function for faculty information department wise 
def viewFacProfile(request):

    faculty = Faculty.objects.select_related('id__user','id__department').all()

    csfaculty = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'CSE')
    ecefaculty = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'ECE')
    mefaculty = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'ME')
    desfaculty = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'DESIGN')
    nsfaculty = Faculty.objects.select_related('id__user','id__department').all().filter(id__department__name = 'NATURAL SCIENCE')

    cse_faculty = []
    for x in csfaculty:
        cse_faculty.append(x.id.id)
        cse_faculty.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        cse_faculty.append(x.id.department.name)


    ece_faculty = []
    for x in ecefaculty:
        ece_faculty.append(x.id.id)
        ece_faculty.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        ece_faculty.append(x.id.department.name)


    me_faculty = []
    for x in mefaculty:
        me_faculty.append(x.id.id)
        me_faculty.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        me_faculty.append(x.id.department.name)


    ns_faculty = []
    for x in nsfaculty:
        ns_faculty.append(x.id.id)
        ns_faculty.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        ns_faculty.append(x.id.department.name)


    des_faculty = []
    for x in desfaculty:
        des_faculty.append(x.id.id)
        des_faculty.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        des_faculty.append(x.id.department.name)


    print(cse_faculty)

    context = {"cse_faculty": cse_faculty , "ece_faculty": ece_faculty , "me_faculty": me_faculty , "des_faculty": des_faculty , "ns_faculty": ns_faculty }

    return JsonResponse(context)


# function for staff information department wise 
def viewStaffProfile(request):

    staff_detail = Staff.objects.select_related('id__user','id__department').all()

    staff = []

    for x in staff_detail:
        staff.append(x.id.id)
        staff.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        staff.append(x.id.department.name)

    acad=Staff.objects.select_related('id__user','id__department').all().filter(Q(id__department__name='Academics') | Q(id__department__name='NATURAL SCIENCE') | Q(id__department__name='CSE')| Q(id__department__name='ECE')| Q(id__department__name='ME') | Q(id__department__name='DESIGN') | Q(id__department__name='MECHATRONICS') | Q(id__department__name='Workshop') | Q (id__department__name='Computer Centre') )

    academic = []
    for x in acad:
        academic.append(x.id.id)
        academic.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        academic.append(x.id.department.name)        


    admin = Staff.objects.select_related('id__user','id__department').all().filter(Q(id__department__name='General Administration') | Q(id__department__name='Finance and Accounts') |  Q(id__department__name='Purchase and Store') | Q(id__department__name='Registrar Office') | Q(id__department__name='Security and Central Mess') )

    administration = []

    for x in admin:
        administration.append(x.id.id)
        administration.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        administration.append(x.id.department.name)


    place =  Staff.objects.select_related('id__user','id__department').all().filter(Q(id__department__name='Placement Cell') )    
    placement = []
    for x in place:
        placement.append(x.id.id)
        placement.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        placement.append(x.id.department.name)  


    offc=Staff.objects.select_related('id__user','id__department').all().filter(Q(id__department__name='Student Affairs') | Q(id__department__name='Office of The Dean P&D') | Q(id__department__name='Directorate') | Q(id__department__name='Office of The Dean R&D')  )
    office =[] 
    for x in offc:
        office.append(x.id.id)
        office.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        office.append(x.id.department.name)  

    other=Staff.objects.select_related('id__user','id__department').all().filter(Q(id__department__name='Establishment & P&S') | Q(id__department__name='IWD') | Q(id__department__name='F&A & GA') | Q(id__department__name='Establishment, RTI and Rajbhasha') | Q(id__department__name='Establishment')  )
    others =[]
    for x in other:
        others.append(x.id.id)
        others.append(x.id.user.first_name + ' ' + x.id.user.last_name)
        others.append(x.id.department.name)  


    context = {"staff": staff, "academic":academic,"administration":administration , "placement": placement , "office": office , "others":others }

    return JsonResponse(context)


# function for student information based on entered programme, batch and department
def viewStudentProfile(request):

    print("in the function")

    student = Student.objects.select_related('id__user','id__department').all()

    student_detail=[]

    studentsearch = " "

    if request.is_ajax():
        year = request.GET.get('year')
        programme = request.GET.get('programme')
        department = request.GET.get('department')
        #studentsearch = Student.objects.all().filter(id__id__startswith).(programme=prog , id__department__name=dep )
        #print("in here we are")
        print(year)
        print(programme)
        print(department)
        #last two letters of 'year' variable
        yr = year[2:4]
        print(yr)
        if programme in ('M.Tech','M.Des','PhD'):
            studentsearch = Student.objects.select_related('id__user','id__department').all().filter(id__id__startswith = yr, id__department__name = department ).filter(programme=programme)
        else:
            studentsearch = Student.objects.select_related('id__user','id__department').all().filter(id__id__startswith = year, programme = programme, id__department__name = department)
            
        print(studentsearch)
        
        for x in studentsearch:
            student_detail.append(x.id.id)
            student_detail.append(x.id.user.first_name + ' ' + x.id.user.last_name)
            student_detail.append(x.id.department.name)
            student_detail.append(x.cpi)

        info =[]
        info.append(programme) 
        info.append(year) 
        info.append(department)  
                
     
        context = { "student_detail":student_detail , "info":info} #, 'year':year, 'prog': prog, 'dep': dep}
        return JsonResponse(context)


#function for scheduling a meeting with faculties
def meeting(request):
    agenda = request.POST['agenda']
    venue = request.POST['venue']
    adate = request.POST['adate']
    meeting_time = request.POST['meeting_time']
    fetched_members = request.POST.getlist('member')

    members = [] 
    for i in fetched_members: 
        if i not in members: 
            members.append(i)

    print(len(members))
    print(len(fetched_members))

    if(len(members) != len(fetched_members)):
        print("in if")
        return HttpResponse('Error handler content', status=400)
    
    else:
        print("inside else")
        Meeting.objects.create(
            agenda=agenda,
            time = meeting_time,
            date = adate,
            venue = venue
        )

        meeting_id = Meeting.objects.get(agenda=agenda,time= meeting_time,venue=venue,date=adate)    
        for x in members:
            splitted_name = str(x).split(' ')
            u = User.objects.get(first_name = splitted_name[0], last_name = splitted_name[1])
            e = ExtraInfo.objects.select_related('user','department').get(user = u.id)
            f = Faculty.objects.select_related('id__user','id__department').get(id = e.id)
            Member.objects.create(
                meeting_id=meeting_id,
                member_id=f
            ) 
        

    return HttpResponse("success")

#function to fill the dropdown choices of faculty in meeting form
def meeting_dropdown(request):
    if request.is_ajax():
        fac = Faculty.objects.select_related('id__user','id__department').all()
        faculty =[]
        for x in fac:
            faculty.append(x.id.user.first_name + ' ' + x.id.user.last_name)

        context = {'faculty':faculty}
        return JsonResponse(context)


#function for viewing and canceling the scheduled meetings
def planMeetings(request):
    meeting_id = request.POST.getlist('list')
    print("inside delete")
    print(meeting_id)
    for z in meeting_id:
        Meeting.objects.filter(id=z).delete()
        Member.objects.filter(meeting_id=z).delete()

    meeting_info=Meeting.objects.all()

    meeting = []

    for x in meeting_info:
        meeting.append(x.id)
        meeting.append(x.agenda)
        meeting.append(x.date)
        meeting.append(x.time)
        meeting.append(x.venue)
        Members = Member.objects.all().filter(meeting_id=x.id)
        members = []
        for y in Members:
            members.append(y.member_id.id.user.first_name + ' ' + y.member_id.id.user.last_name)
        meeting.append(members)
    
    print(meeting)

    context = {
        'meeting':meeting 
    }    

    return JsonResponse(context)


#function for displaying HODs of different departments
def viewHOD(request):
    #designation name has been used as is stored in database
    cse_hod = HoldsDesignation.objects.select_related('user','designation','working').all().filter(designation__name="CSE HOD")
    ece_hod = HoldsDesignation.objects.select_related('user','designation','working').all().filter(designation__name="HOD (ECE)")
    me_hod = HoldsDesignation.objects.select_related('user','designation','working').all().filter(designation__name="HOD (ME)")
    ns_hod = HoldsDesignation.objects.select_related('user','designation','working').all().filter(designation__name="HOD (NS)")
    des_hod = HoldsDesignation.objects.select_related('user','designation','working').all().filter(designation__name="HOD (DESIGN)")

    print("inside hod")

    csehod=[]

    for c in cse_hod:
        csehod.append(c.user.first_name + ' ' + c.user.last_name)

    ecehod=[]

    for e in ece_hod:
        ecehod.append(e.user.first_name + ' ' + e.user.last_name)

    mehod=[]

    for m in me_hod:
        mehod.append(m.user.first_name + ' ' + m.user.last_name)

    nshod=[]

    for n in ns_hod:
        nshod.append(n.user.first_name + ' ' + n.user.last_name)


    deshod=[]

    for d in des_hod:
        deshod.append(d.user.first_name + ' ' + d.user.last_name)

    context = {'csehod':csehod, 'ecehod':ecehod, 'mehod':mehod, 'nshod': nshod, 'deshod':deshod}
    #data=serializers.serialize('json', context)

    return JsonResponse(context)

#END OF DIRECTOR MODULE ............................


def officeOfDeanAcademics(request):
    student= Student.objects.all()
    instructor = Curriculum_Instructor.objects.all()
    spi=Spi.objects.select_related('student_id__id__user','student_id__id__department').all()
    grades=Grades.objects.all()
    course=Course.objects.all()
    thesis=Thesis.objects.all()
    minutes=Meeting.objects.all().filter(minutes_file="")
    final_minutes=Meeting.objects.all().exclude(minutes_file="")
    hall_allotment=hostel_allotment.objects.all()
    assistantship=Assistantship.objects.all()
    mcm=Mcm.objects.all()
    designation = HoldsDesignation.objects.select_related('user','designation','working').all().filter(working=request.user)
    all_designation=[]
    for i in designation:
        all_designation.append(str(i.designation))




    context = {'student':student,
                'instructor':instructor,
                'assistantship':assistantship,
                #'hall': Constants.HALL_NO,
                'hall_allotment':hall_allotment,
                'mcm':mcm,
                'thesis':thesis,
                'meetingMinutes':minutes,
                'final_minutes':final_minutes,
                'all_desig':all_designation,}
    user_name=get_object_or_404(User,username=request.user.username)
    user=ExtraInfo.objects.select_related('user','department').all().filter(user=user_name).first()
    holds=HoldsDesignation.objects.select_related('user','designation','working').filter(user=user.user)
    deslist1=['Director']


    if user.user_type == 'faculty': 
        return render(request, "officeModule/officeOfDeanAcademics/officeOfDeanAcademics.html", context)
    else:
        return render(request, "officeModule/directorOffice/unauthorised.html", context)
def assistantship(request):
    # print(request.POST.getlist('check'))
    ob=Assistantship.objects.all()
    # print(id[0])
    context = {'ob':ob}
    return HttpResponseRedirect('/office/officeOfDeanAcademics')


def init_assistantship(request):
    title= request.POST.get('title')
    date = request.POST.get('date')
    Time = request.POST.get('time')
    Venue = request.POST.get('venue')
    Agenda = request.POST.get('Agenda')
    p=Meeting(title=title,venue=Venue,date=date,time=Time,agenda=Agenda);
    p.save()
    return HttpResponseRedirect('/office/officeOfDeanAcademics')

def scholarshipform(request):
    file=request.FILES['hostel_file']
    hall_no=request.POST.get('hall_no')
    #description= request.POST.get('description')
    p=hostel_allotment(allotment_file=file,hall_no=hall_no)
    p.save()
    return HttpResponseRedirect('/office/officeOfDeanAcademics')

def formsubmit(request):
    a = request.POST.get('example')
    comment = request.POST.get('comment')
    obj = Assistantship.objects.get(pk=a)
    if "approve" in request.POST:
        obj.action=1
        obj.comments=comment
        obj.save()
    elif "reject" in request.POST:
        obj.action=2
        obj.comments=comment
        obj.save()

    return HttpResponseRedirect('/office/officeOfDeanAcademics')



    # elif "reject" in request.POST:

def scholarship(request):

    return HttpResponse('')

def courses(request):

    return HttpResponse('')

def applications(request):

    return HttpResponse('')

def semresults(request):

    return HttpResponse('')

def thesis(request):

    return HttpResponse('')