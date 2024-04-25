from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q
from applications.globals.models import *
from django.contrib.auth.decorators import login_required
from .models import *
from django.http import HttpResponseRedirect
from applications.filetracking.sdk.methods import *
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from django.http import HttpResponse
from io import BytesIO
from django.core.files.base import File as DjangoFile

# Create your views here.


# The names of the Functions and the corresponding indication of redirection of the logic inside their body is very well
# indicative of the purpose.
# At every instance of the Project Entry, i.e. at places where a whole lot of dealing with components related
# to specific project, the projectId is stored to be referenced out throughout life of filling.
# Apart from Entry points, all other are sub parts of them.
# This briefly covers comments. To write it wholly as comment would be cumbersome and at the same time less fruitful
# owing to length and inherent extensiveness of code. Rather than, whosoever read this code is advised to do so
# in conjunction with SRS. After that, everything will become easier.

# def dashboard(request):
#     eligible = False
#     userObj = request.user
#     userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
#     for p in userDesignationObjects:
#         if p.designation.name == 'Admin IWD':
#             eligible = True
#             break
#     return render(request, 'iwdModuleV2/dashboard.html', {'eligible': eligible})

#Junior Engineer, Electrical Engineer (Civil), Electrical_AE, Electrical_JE, EE, Civil_AE, Civil_JE

def dashboard(request):
    eligible = ""
    userObj = request.user
    userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
    for p in userDesignationObjects:
        eligible = p.designation.name
    print(eligible)
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible': eligible})

def page1_1(request):
    if request.method == 'POST':
        formObject = PageOneDetails()
        request.session['projectId'] = request.POST['name']
        project = Projects()
        project.id = request.session['projectId']
        project.save()
        formObject.id = project
        if 'aes_file' in request.POST and request.POST['aes_file'] != "":
            formObject.AESFile = request.POST['aes_file']
        if 'dASAName' in request.POST and request.POST['dASAName'] != "":
            formObject.dASA = request.POST['dASAName']
        if 'nitNiqNo' in request.POST and request.POST['nitNiqNo'] != "":
            formObject.nitNiqNo = request.POST['nitNiqNo']
        if 'proTh' in request.POST and request.POST['proTh'] != "":
            formObject.proTh = request.POST['proTh']
        if 'emdDetails' in request.POST and request.POST['emdDetails'] != "":
            formObject.emdDetails = request.POST['emdDetails']
        if 'preBidDate' in request.POST and request.POST['preBidDate'] != "":
            formObject.preBidDate = request.POST['preBidDate']
        if 'technicalBidDate' in request.POST and request.POST['technicalBidDate'] != "":
            formObject.technicalBidDate = request.POST['technicalBidDate']
        if 'financialBidDate' in request.POST and request.POST['financialBidDate'] != "":
            formObject.financialBidDate = request.POST['financialBidDate']
        formObject.save()
        return redirect('iwdModuleV2/AESForm')
    return render(request, 'iwdModuleV2/page1_create.html', {})


def AESForm(request):
    if request.method == 'POST':
        formObject = AESDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.descOfItems = request.POST['description']
        formObject.unit = request.POST['unit']
        formObject.quantity = request.POST['quantity']
        formObject.rate = request.POST['rate']
        formObject.amount = request.POST['amount']
        formObject.save()
        fromAES = True
        return redirect('iwdModuleV2/AESForm')
    return render(request, 'iwdModuleV2/page1_support_1_aes.html', {})


def page2_1(request):
    if request.method == "POST":
        request.session['projectId'] = request.POST['id']
        formObject = PageTwoDetails()
        formObject.id = Projects.objects.get(id=request.session['projectId'])
        if 'corrigendum' in request.POST and request.POST['corrigendum'] != "":
            formObject.corrigendum = request.POST['corrigendum']
        if 'addendum' in request.POST and request.POST['addendum'] != "":
            formObject.addendum = request.POST['addendum']
        if 'preBid' in request.POST and request.POST['preBid'] != "":
            formObject.preBidMeetingDetails = request.POST['preBid']
        if 'technicalBid' in request.POST and request.POST['technicalBid'] != "":
            formObject.technicalBidMeetingDetails = request.POST['technicalBid']
        if 'qualifiedAgencies' in request.POST and request.POST['qualifiedAgencies'] != "":
            formObject.technicallyQualifiedAgencies = request.POST['qualifiedAgencies']
        if 'financialBid' in request.POST and request.POST['financialBid'] != "":
            formObject.financialBidMeetingDetails = request.POST['financialBid']
        if 'lowAgency' in request.POST and request.POST['lowAgency'] != "":
            formObject.nameOfLowestAgency = request.POST['lowAgency']
        if 'letterOfIntent' in request.POST and request.POST['letterOfIntent'] != "":
            formObject.letterOfIntent = request.POST['letterOfIntent']
        if 'workOrder' in request.POST and request.POST['workOrder'] != "":
            formObject.workOrder = request.POST['workOrder']
        if 'agreementLetter' in request.POST and request.POST['agreementLetter'] != "":
            formObject.agreementLetter = request.POST['agreementLetter']
        if 'milestones' in request.POST and request.POST['milestones'] != "":
            formObject.milestones = request.POST['milestones']
        formObject.save()
        return redirect('iwdModuleV2/corrigendumInput')
    return render(request, 'iwdModuleV2/page2_create.html', {})


def corrigendumInput(request):
    if request.method == 'POST':
        existingObject = CorrigendumTable.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = CorrigendumTable()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.issueDate = request.POST['issueDate']
        # formObject.lastDate = request.POST['lastDate']
        formObject.lastTime = request.POST['lastTime']
        formObject.nitNo = request.POST['nitNiqNo']
        formObject.env1BidOpeningDate = request.POST['openDateEnv1']
        formObject.env1BidOpeningTime = request.POST['openTimeEnv1']
        formObject.env2BidOpeningDate = request.POST['openDateEnv2']
        formObject.env2BidOpeningTime = request.POST['openTimeEnv2']
        formObject.name = request.POST['workName']
        formObject.save()
        return redirect('iwdModuleV2/addendumInput')
    return render(request, 'iwdModuleV2/page2_support_1_corrigendum.html', {})


def addendumInput(request):
    if request.method == 'POST':
        existingObject = Addendum.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = Addendum()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.issueDate = request.POST['issueDate']
        formObject.nitNiqNo = request.POST['nitNiqNo']
        formObject.openDate = request.POST['openDate']
        formObject.openTime = request.POST['openTime']
        formObject.name = request.POST['workName']
        formObject.save()
        return redirect('iwdModuleV2/preBidForm')
    return render(request, 'iwdModuleV2/page2_support_2_addendum.html', {})


def PreBidForm(request):
    if request.method == 'POST':
        existingObject = PreBidDetails.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = PreBidDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.nameOfParticipants = request.POST['nameParticipants']
        formObject.issuesRaised = request.POST['issuesRaised']
        formObject.responseDecision = request.POST['responseDecision']
        formObject.save()
        return redirect('iwdModuleV2/noOfEntriesTechnicalBid')
    return render(request, 'iwdModuleV2/page2_support_3_prebid.html', {})


def noOfEntriesTechnicalBid(request):
    formNoTechnicalObjects = NoOfTechnicalBidTimes()
    formNoTechnicalObjects.key = Projects.objects.get(
        id=request.session['projectId'])
    if request.method == 'POST':
        existingObject = NoOfTechnicalBidTimes.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formNoTechnicalObjects.number = int(request.POST['number'])
        formNoTechnicalObjects.save()
        return redirect('iwdModuleV2/technicalBidForm')
    return render(request, 'iwdModuleV2/no_of_entries.html', {})


def TechnicalBidForm(request):
    formObject = TechnicalBidDetails()
    numberOfTechnicalBidTimes = NoOfTechnicalBidTimes.objects.get(
        key=Projects.objects.get(id=request.session['projectId'])).number
    if request.method == 'POST':
        existingObject = TechnicalBidDetails.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = TechnicalBidDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.requirements = request.POST['requirements']
        formObject.save()
        TechnicalBidContractorDetails.objects.filter(
            key=formObject).all().delete()
        for w in range(numberOfTechnicalBidTimes):
            formContractorObject = TechnicalBidContractorDetails()
            formContractorObject.key = formObject
            formContractorObject.name = request.POST[str(w) + 'name']
            formContractorObject.description = request.POST[str(
                w) + 'Description']
            formContractorObject.save()
        return redirect('iwdModuleV2/noOfEntriesFinancialBid')
    return render(request, 'iwdModuleV2/page2_support_4_technicalbid.html',
                  {'quantity': range(numberOfTechnicalBidTimes), 'obj': formObject})


def noOfEntriesFinancialBid(request):
    listOfContractors = []
    objectTechnicalBid = TechnicalBidDetails.objects.get(
        key=Projects.objects.get(id=request.session['projectId']))
    objects = TechnicalBidContractorDetails.objects.filter(
        key=objectTechnicalBid)
    for t in objects:
        listOfContractors.append(t.name)
    if request.method == 'POST':
        existingObject = FinancialBidDetails.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = FinancialBidDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.description = request.POST['description']
        formObject.save()
        for f in range(len(listOfContractors)):
            formContractorObject = FinancialContractorDetails()
            formContractorObject.key = formObject
            formContractorObject.name = listOfContractors[f]
            formContractorObject.totalCost = request.POST[listOfContractors[f] + 'totalCost']
            formContractorObject.estimatedCost = request.POST[listOfContractors[f] + 'estimatedCost']
            formContractorObject.percentageRelCost = request.POST[
                listOfContractors[f] + 'percentageRelCost']
            formContractorObject.perFigures = request.POST[listOfContractors[f] + 'perFigures']
            formContractorObject.save()
        return redirect('iwdModuleV2/letterOfIntent')
    return render(request, 'iwdModuleV2/page2_support_5_financialbid.html',
                  {'list': listOfContractors})


def letterOfIntent(request):
    if request.method == 'POST':
        existingObject = LetterOfIntentDetails.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = LetterOfIntentDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.name = request.POST['name']
        formObject.dateOfOpening = request.POST['dateOfOpening']
        formObject.nitNiqNo = request.POST['nitNiqNo']
        formObject.agency = request.POST['agency']
        formObject.tenderValue = request.POST['tenderValue']
        formObject.save()
        return redirect('iwdModuleV2/workOrderForm')
    return render(request, 'iwdModuleV2/page2_support_6_letter_of_intent.html', {})


def workOrderForm(request):
    if request.method == 'POST':
        existingObject = WorkOrderForm.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = WorkOrderForm()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.issueDate = request.POST['issueDate']
        formObject.name = request.POST['name']
        formObject.agency = request.POST['agency']
        formObject.nitNiqNo = request.POST['nitNiqNo']
        formObject.amount = request.POST['amount']
        formObject.time = request.POST['time']
        formObject.startDate = request.POST['startDate']
        formObject.contractDay = request.POST['contractDay']
        formObject.monthDay = request.POST['monthDay']
        formObject.deposit = request.POST['deposit']
        formObject.completionDate = request.POST['completionDate']
        formObject.save()
        return redirect('iwdModuleV2/agreement')
    return render(request, 'iwdModuleV2/page2_support_7_work_order.html', {})


def AgreementInput(request):
    if request.method == 'POST':
        existingObject = Agreement.objects.filter(
            key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = Agreement()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.date = request.POST['date']
        formObject.fdrSum = request.POST['fdrSum']
        formObject.workName = request.POST['workName']
        formObject.agencyName = request.POST['agencyName']
        formObject.save()
        return redirect('iwdModuleV2/milestoneForm')
    return render(request, 'iwdModuleV2/page2_support_8_aggrement.html', {})


def milestonesForm(request):
    if request.method == 'POST':
        formObject = Milestones()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.description = request.POST['description']
        formObject.amountWithheld = request.POST['amountWithheld']
        formObject.timeAllowed = request.POST['timeAllowed']
        formObject.save()
        return redirect('iwdModuleV2/page3_1')
    Milestones.objects.filter(key=Projects.objects.get(
        id=request.session['projectId'])).all().delete()
    return render(request, 'iwdModuleV2/page2_support_9_milestone.html', {})


def page3_1(request):
    if request.method == 'POST':
        request.session['projectId'] = request.POST['id']
        formObject = PageThreeDetails()
        formObject.id = Projects.objects.get(id=request.session['projectId'])
        formObject.extensionOfTime = request.POST['extensionPDF']
        formObject.actualCostOfBuilding = request.POST['actualCost']
        formObject.save()
        return redirect('iwdModuleV2/extensionForm')
    return render(request, 'iwdModuleV2/page3_create.html', {})


def ExtensionOfTimeForm(request):
    if request.method == 'POST':
        formObject = ExtensionOfTimeDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.hindrance = request.POST['hindrance']
        formObject.periodOfHindrance = request.POST['periodHindrance']
        formObject.periodOfExtension = request.POST['periodExtension']
        formObject.save()
        return redirect('iwdModuleV2/extensionForm')
    return render(request, 'iwdModuleV2/page3_support_1_extension_of_time.html', {})


def page1View(request):
    if request.POST:
        request.session['projectId'] = request.POST['id']
    projectPageOne = PageOneDetails.objects.get(
        id=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page1.html', {'x': projectPageOne})


def page2View(request):
    projectPageTwo = PageTwoDetails.objects.get(
        id=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page2.html', {'x': projectPageTwo})


def AESView(request):
    objects = AESDetails.objects.filter(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/AA&ES.html', {'AES': objects})


def financialBidView(request):
    elements = []
    objects = FinancialBidDetails.objects.filter(
        key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = FinancialContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.description, w.name, w.estimatedCost,
                   w.percentageRelCost, w.perFigures, w.totalCost]
            elements.append(obj)
    return render(request, 'iwdModuleV2/Page2_financialbid.html', {'financial': elements})


def technicalBidView(request):
    elements = []
    objects = TechnicalBidDetails.objects.filter(
        key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = TechnicalBidContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.requirements, w.name, w.description]
            elements.append(obj)
    return render(request, 'iwdModuleV2/Page2_technical-bid.html', {'technical': elements})


def preBidDetailsView(request):
    preBidObjects = PreBidDetails.objects.filter(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page2_pre-bid.html', {'preBidDetails': preBidObjects})


def corrigendumView(request):
    corrigendumObject = CorrigendumTable.objects.get(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/corrigendum.html', {'corrigendum': corrigendumObject})


def addendumView(request):
    addendumObject = Addendum.objects.get(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Addendum.html', {'x': addendumObject})


def letterOfIntentView(request):
    letterOfIntentObject = LetterOfIntentDetails.objects.get(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/letterOfIntent.html', {'x': letterOfIntentObject})


def workOrderFormView(request):
    workOrderFormObject = WorkOrderForm.objects.get(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/WorkOrderForm.html', {'x': workOrderFormObject})


def agreementView(request):
    agreementObject = Agreement.objects.get(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Agreement.html', {'agreement': agreementObject})


def milestoneView(request):
    milestoneObjects = Milestones.objects.filter(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page2_milestones.html', {'milestones': milestoneObjects})


def page3View(request):
    pageThreeDetails = PageThreeDetails.objects.get(
        id=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page3.html', {'x': pageThreeDetails})


def extensionFormView(request):
    extensionObjects = ExtensionOfTimeDetails.objects.filter(
        key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/ExtensionForm.html', {'extension': extensionObjects})

designations_list = ["Junior Engineer", "Executive Engineer (Civil)", "Electrical_AE", "Electrical_JE", "EE", "Civil_AE", "Civil_JE", "Dean (P&D)", "Director", "Accounts Admin", "Admin IWD", "Auditor"]

@login_required
def fetchDesignations(request):
    designations = Designation.objects.filter()

    holdsDesignations = []

    for d in designations:
        for x in designations_list:
            if d.name == x:
                list = HoldsDesignation.objects.filter(designation=d)
                holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/requestsView.html', {'holdsDesignations' : holdsDesignations})

@login_required
def requestsView(request):
    if request.method == 'POST':
        formObject = Requests()
        # formObject.key = Projects.objects.get(id=request.session['projectId']) 
        formObject.name = request.POST['name']
        formObject.description = request.POST['description']
        formObject.area = request.POST['area']
        formObject.engineerProcessed = 0
        formObject.directorApproval = 0
        formObject.deanProcessed = 0
        formObject.requestCreatedBy = request.user.username
        formObject.status = "Pending"
        formObject.issuedWorkOrder = 0
        formObject.workCompleted = 0
        formObject.billGenerated = 0
        formObject.billProcessed = 0
        formObject.billSettled = 0
        formObject.save()
        print(request.user)
        print(request.user.username)
        request_object = Requests.objects.get(pk=formObject.pk)
        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)
        print(d)
        print(d1)
        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation, 
            src_module="IWD", 
            src_object_id= str(request_object.id), 
            file_extra_JSON= {"value": 2}, 
            attached_file = None)
        
        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible' : eligible})

@login_required
def createdRequests(request):
    obj = []
    d = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
        username=request.user,
        designation=d.designation,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        if request_object:
            element = [request_object.id, request_object.name, request_object.area, request_object.description, request_object.requestCreatedBy]
            obj.append(element)

    designations = Designation.objects.filter()

    holdsDesignations = []

    for d in designations:
        for x in designations_list:
            if d.name == x:
                list = HoldsDesignation.objects.filter(designation=d)
                holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/createdRequests.html', {'obj' : obj, 'holdsDesignations' : holdsDesignations})

@login_required
def handleEngineerProcessRequests(request):
    if request.method == 'POST':

        request_id = request.POST.get("id", 0)

        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)

        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation, 
            src_module="IWD", 
            src_object_id= str(request_id), 
            file_extra_JSON= {"value": 2}, 
            attached_file = None)
        
        Requests.objects.filter(id=request_id).update(engineerProcessed=1, status="Approved by the engineer")
        
        inbox_files = view_inbox(
            username=request.user,
            designation=d1.designation,
            src_module="IWD"
        )

        for p in inbox_files:
            if p['src_object_id'] == request_id:
                delete_file(file_id = p['id'])
                break

        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name

    return render(request, 'iwdModuleV2/dashboard.html', {'eligible': eligible})

@login_required
def engineerProcessedRequests(request):

    obj = []

    d = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
        username=request.user,
        designation=d.designation,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        if request_object:
            element = [request_object.id, request_object.name, request_object.area, request_object.description, request_object.requestCreatedBy]
            obj.append(element)

    designations = Designation.objects.filter()

    holdsDesignations = []

    for d in designations:
        for x in designations_list:
            if d.name == x:
                list = HoldsDesignation.objects.filter(designation=d)
                holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/engineerProcessedRequests.html', {'obj' : obj, 'holdsDesignations' : holdsDesignations})

@login_required
def handleDeanProcessRequests(request):
    if request.method == 'POST':

        request_id = request.POST.get("id", 0)

        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)

        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation, 
            src_module="IWD", 
            src_object_id= str(request_id), 
            file_extra_JSON= {"value": 2}, 
            attached_file = None)
        
        Requests.objects.filter(id=request_id).update(deanProcessed=1, status="Approved by the dean")

        inbox_files = view_inbox(
            username=request.user,
            designation=d1.designation,
            src_module="IWD"
        )

        for p in inbox_files:
            if p['src_object_id'] == request_id:
                delete_file(file_id = p['id'])
                break

        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible': eligible})

@login_required
def deanProcessedRequests(request):
    obj = []

    d = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
        username=request.user,
        designation=d.designation,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        if request_object:
            element = [request_object.id, request_object.name, request_object.area, request_object.description, request_object.requestCreatedBy]
            obj.append(element)

    designations = Designation.objects.filter()

    holdsDesignations = []

    for d in designations:
        for x in designations_list:
            if d.name == x:
                list = HoldsDesignation.objects.filter(designation=d)
                holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/deanProcessedRequests.html', {'obj' : obj, 'holdsDesignations' : holdsDesignations})

@login_required
def handleDirectorApprovalRequests(request):
    if request.method == 'POST':
        request_id = request.POST.get("id", 0)

        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)

        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation, 
            src_module="IWD", 
            src_object_id= str(request_id), 
            file_extra_JSON= {"value": 2}, 
            attached_file = None)
        
        Requests.objects.filter(id=request_id).update(directorApproval=1, status="Approved by the director")

        inbox_files = view_inbox(
            username=request.user,
            designation=d1.designation,
            src_module="IWD"
        )

        for p in inbox_files:
            if p['src_object_id'] == request_id:
                delete_file(file_id = p['id'])
                break

        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible': eligible})

@login_required
def handleDirectorRejectionRequests(request):
    if request.method == 'POST':
        request_id = request.POST.get("id", 0)

        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)

        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation, 
            src_module="IWD", 
            src_object_id= str(request_id), 
            file_extra_JSON= {"value": 2}, 
            attached_file = None)
        
        Requests.objects.filter(id=request_id).update(directorApproval=-1, status="Rejected by the director")

        inbox_files = view_inbox(
            username=request.user,
            designation=d1.designation,
            src_module="IWD"
        )

        for p in inbox_files:
            if p['src_object_id'] == request_id:
                delete_file(file_id = p['id'])
                break

        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible': eligible})

@login_required
def rejectedRequests(request):
    obj = []

    d = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
        username=request.user,
        designation=d.designation,
        src_module="IWD"
    )

    for result in inbox_files:
        src_object_id = result['src_object_id']
        request_object = Requests.objects.filter(id=src_object_id).first()
        if request_object.directorApproval == -1:
            element = [request_object.id, request_object.name, request_object.area, request_object.description, request_object.requestCreatedBy]
            obj.append(element)

    designations = Designation.objects.filter()

    holdsDesignations = []

    for d in designations:
        for x in designations_list:
            if d.name == x:
                list = HoldsDesignation.objects.filter(designation=d)
                holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/rejectedRequests.html', {'obj' : obj, 'holdsDesignations' : holdsDesignations})    

@login_required
def updateRejectedRequests(request):
    request_id = request.POST.get("id", 0)

    d1 = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
            username=request.user,
            designation=d1.designation,
            src_module="IWD"
        )

    for p in inbox_files:
        if p['src_object_id'] == request_id:
            delete_file(file_id = p['id'])
            break

    designations = Designation.objects.filter()

    holdsDesignations = []
    obj = []

    request_object = Requests.objects.get(id=request_id)

    obj = [request_object.id, request_object.name, request_object.description, request_object.area]

    for d in designations:
        for x in designations_list:
            if d.name == x:
                list = HoldsDesignation.objects.filter(designation=d)
                holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/updateRequests.html', {'obj' : obj, 'holdsDesignations' : holdsDesignations})

@login_required
def handleUpdateRequests(request):
    if request.method == 'POST':
        request_id = request.POST.get("id", 0)
        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)
        Requests.objects.filter(id=request_id).update(name=request.POST['name'],
            description=request.POST['description'],
            area=request.POST['area'],
            engineerProcessed=0,
            directorApproval=0,
            deanProcessed=0,
            requestCreatedBy=request.user.username,
            status="Pending",
            issuedWorkOrder=0,
            workCompleted=0,
            billGenerated=0,
            billProcessed=0,
            billSettled=0)
        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation, 
            src_module="IWD", 
            src_object_id= str(request_id), 
            file_extra_JSON= {"value": 2}, 
            attached_file = None)
        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible' : eligible})

@login_required
def issueWorkOrder(request):
    obj = []

    d = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
        username=request.user,
        designation=d.designation,
        src_module="IWD"
    )

    for result in inbox_files:
        uploader = result['sent_by_designation']
        if uploader == 'Director':
            src_object_id = result['src_object_id']
            request_object = Requests.objects.filter(id=src_object_id).first()
            if request_object:
                element = [request_object.id, request_object.name, request_object.area, request_object.description, request_object.requestCreatedBy]
                obj.append(element)

    return render(request, 'iwdModuleV2/issueWorkOrder.html', {'obj' : obj})

@login_required
def fetchRequest(request):
    request_id = request.POST.get("id", 0)
    req_request = Requests.objects.get(id=request_id)
    return render(request, 'iwdModuleV2/workOrder.html', {'req' : req_request})

@login_required
def workOrder(request):
    if request.method == 'POST':
        request_instance = Requests.objects.get(pk=request.POST['id'])
        formObject = WorkOrder()
        formObject.request_id = request_instance
        formObject.name = request.POST['name']
        formObject.date = request.POST['date']
        formObject.agency = request.POST['agency']
        formObject.amount = request.POST['amount']
        formObject.deposit = request.POST['deposit']
        formObject.alloted_time = request.POST['time']
        formObject.start_date = request.POST['startDate']
        formObject.completion_date = request.POST['completionDate']
        formObject.save()

        Requests.objects.filter(id=request.POST['id']).update(status="Work Order issued", issuedWorkOrder=1)

        d = HoldsDesignation.objects.get(user__username=request.user)

        inbox_files = view_inbox(
            username=request.user,
            designation=d.designation,
            src_module="IWD"
        )

        for result in inbox_files:
            if result['src_object_id'] == request.POST['id'] and result['sent_by_designation'] == 'Director':
                delete_file(file_id = result['id'])
                break

        inbox_files = view_inbox(
            username=request.user,
            designation=d.designation,
            src_module="IWD"
        )

        obj = []

        for result in inbox_files:
            uploader = result['sent_by_designation']
            if uploader == 'Director':
                src_object_id = result['src_object_id']
                request_object = Requests.objects.filter(id=src_object_id).first()
                if request_object:
                    element = [request_object.id, request_object.name, request_object.area, request_object.description, request_object.requestCreatedBy]
                    obj.append(element)

        return render(request, 'iwdModuleV2/issueWorkOrder.html', {'obj' : obj})

@login_required
def requestsStatus(request):
    obj = []
    requestsObject = Requests.objects.all()
    for x in requestsObject:
        element = [x.id, x.name, x.area, x.description, x.requestCreatedBy, x.status]
        obj.append(element)
    return render(request, 'iwdModuleV2/requestsStatus.html', {'obj' : obj})

@login_required
def inventory(request):
    items = Inventory.objects.filter()
    obj = []
    for i in items:
        element = [i.id, i.name, i.quantity, i.cost]
        obj.append(element)
    return render(request, 'iwdModuleV2/inventory.html', {'obj' : obj})

@login_required
def addItemsView(request):
    return render(request, 'iwdModuleV2/addItemsView.html')

@login_required
def addItems(request):
    if request.method == "POST":
        formObject = Inventory()
        formObject.name = request.POST['name']
        formObject.quantity = request.POST['quantity']
        formObject.cost = request.POST['cost']
        formObject.save()
    return render(request, 'iwdModuleV2/addItemsView.html')

@login_required
def editInventoryView(request):
    items = Inventory.objects.filter()
    obj = []
    for i in items:
        element = [i.id, i.name, i.quantity, i.cost]
        obj.append(element)
    return render(request, 'iwdModuleV2/editInventory.html', {'obj' : obj})

@login_required
def editInventory(request):
    if request.method == "POST":
        itemId = request.POST['id']
        itemName = request.POST['name']
        itemQuantity = request.POST['quantity']
        itemCost = request.POST['cost']
        if itemQuantity == "0":
            Inventory.objects.filter(id=itemId).delete()
        else:
            Inventory.objects.filter(id=itemId).update(name=itemName, quantity=itemQuantity, cost=itemCost)
        items = Inventory.objects.filter()
        obj = []
        for i in items:
            element = [i.id, i.name, i.quantity, i.cost]
            obj.append(element)
        return render(request, 'iwdModuleV2/editInventory.html', {'obj' : obj})

@login_required    
def requestsInProgess(request):
    obj = []
    requestsObject = Requests.objects.filter(issuedWorkOrder=1, billGenerated=0)
    for x in requestsObject:
        element = [x.id, x.name, x.area, x.description, x.requestCreatedBy, x.workCompleted]
        obj.append(element)
    return render(request, 'iwdModuleV2/requestsInProgress.html', {'obj' : obj})

@login_required
def workCompleted(request):
    if request.method == 'POST':
        Requests.objects.filter(id=request.POST['id']).update(workCompleted=1, status="Work Completed")
        obj = []
        requestsObject = Requests.objects.filter(issuedWorkOrder=1, billGenerated=0)
        for x in requestsObject:
            element = [x.id, x.name, x.area, x.description, x.requestCreatedBy, x.workCompleted]
            obj.append(element)
    return render(request, 'iwdModuleV2/requestsInProgress.html', {'obj' : obj})

@login_required
def requestFromInventory(request):
    if request.method == 'POST':
        requestId = request.POST['id']
        Req = Requests.objects.filter(id=requestId)
        Items = Inventory.objects.filter()
        req = []
        items = []
        for x in Req:
            element = [x.id, x.name, x.area, x.description, x.requestCreatedBy, x.workCompleted]
            req.append(element)

        for x in Items:
            element = [x.id, x.name, x.quantity, x.cost]
            items.append(element)
        print(items)
    return render(request, 'iwdModuleV2/requestFromInventory.html', {'req' : req, 'items' : items})

@login_required
def editInventoryAfterRequest(request):
    if request.method == 'POST':
        selectedItem = Inventory.objects.get(id=request.POST['selected_item_id'])
        q = int(selectedItem.quantity)
        if q == int(request.POST['quantity']):
            Inventory.objects.filter(id=request.POST['selected_item_id']).delete()
        else:
            Inventory.objects.filter(id=request.POST['selected_item_id']).update(quantity=(q-int(request.POST['quantity'])))
        formObject = UsedItems()
        request_instance = Requests.objects.get(pk=request.POST['id'])
        formObject.request_id = request_instance
        formObject.itemName = selectedItem.name
        formObject.cost = selectedItem.cost
        formObject.quantity = request.POST['quantity']
        formObject.date = datetime.now().date()
        formObject.save()
        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible': eligible})

@login_required
def generateFinalBill(request):
    if request.method == 'POST':
        requestId = request.POST.get("id", 0)

        usedItems = UsedItems.objects.filter(request_id=requestId)
        workOrder = WorkOrder.objects.get(request_id=requestId)

        itemsList = []

        for used in usedItems:
            element = [used.itemName, used.quantity, used.cost, used.date]
            itemsList.append(element)

        filename = f"Request_id_{requestId}_final_bill.pdf"

        buffer = BytesIO()

        c = canvas.Canvas(buffer, pagesize=letter)

        c.setFont("Helvetica", 12)

        y_position = 750

        rid = f"Request Id : {requestId}"
        agency = f"Agency : {workOrder.agency}"
        
        c.drawString(100, y_position, rid)
        y_position -= 20

        c.drawString(100, y_position, agency)
        y_position -= 20

        c.drawString(100, y_position - 40, "Items:")

        data = [["Item Name", "Quantity", "Cost (in Rupees)", "Date of Purchase", "Total Amount"]]
        for item in itemsList:
            data.append([item[0], str(item[1]), "{:.2f}".format(item[2]), item[3], "{:.2f}".format(item[1] * item[2])])

        total_amount_to_be_paid = sum(item[1] * item[2] for item in itemsList)

        c.drawString(100, y_position - 80, f"Total Amount (in Rupees): {total_amount_to_be_paid:.2f}")

        table = Table(data)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

        table.wrapOn(c, 400, 600)
        table.drawOn(c, 100, y_position - 60)

        c.save()

        buffer.seek(0)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(buffer.getvalue())

        return response

@login_required    
def handleBillGeneratedRequests(request):
    if request.method == 'POST':
        requestId = request.POST.get("id", 0)
        Requests.objects.filter(id=requestId).update(status="Bill Generated", billGenerated=1)
        obj = []
        requestsObject = Requests.objects.filter(issuedWorkOrder=1, billGenerated=0)
        for x in requestsObject:
            element = [x.id, x.name, x.area, x.description, x.requestCreatedBy, x.workCompleted]
            obj.append(element)
    return render(request, 'iwdModuleV2/requestsInProgress.html', {'obj' : obj})

@login_required
def generatedBillsView(request):
    request_object = Requests.objects.filter(billGenerated=1, billProcessed=0)
    obj = []
    for x in request_object:
        element = [x.id, x.name, x.description, x.area, x.requestCreatedBy]
        obj.append(element)
    designations = Designation.objects.filter()

    holdsDesignations = []

    for d in designations:
        for x in designations_list:
            if d.name == x:
                list = HoldsDesignation.objects.filter(designation=d)
                holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/generatedBillsRequestsView.html', {'obj' : obj, 'holdsDesignations' : holdsDesignations})

@login_required
def handleProcessedBills(request):
    if request.method == 'POST':
        requestId = request.POST.get("id", 0)
        request_instance = Requests.objects.get(pk=requestId)

        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)

        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation,
            src_module="IWD", 
            src_object_id= str(requestId),
            file_extra_JSON= {"value": 2},
            attached_file = request.FILES['bill'])
        
        formObject = Bills()
        formObject.request_id = request_instance
        formObject.file = request.FILES['bill']
        formObject.save()

        Requests.objects.filter(id=requestId).update(status="Final Bill Processed", billProcessed=1)

        request_object = Requests.objects.filter(billGenerated=1, billProcessed=0)
        obj = []
        for x in request_object:
            element = [x.id, x.name, x.description, x.area, x.requestCreatedBy]
            obj.append(element)

        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name

    return render(request, 'iwdModuleV2/dashboard.html', {'obj' : obj, 'eligible': eligible})

@login_required
def auditDocumentView(request):
    d = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
        username=request.user,
        designation=d.designation,
        src_module="IWD"
    )

    obj = []

    for x in inbox_files:
        requestId = x['src_object_id']
        files = Bills.objects.get(request_id=requestId)
        element = [files.request_id.id, files.file, files.file.url]
        obj.append(element)

    designations = Designation.objects.filter()

    holdsDesignations = []

    for d in designations:
        if d.name == "Engineer" or d.name == "Dean" or d.name == "Director" or d.name == "Accounts Admin" or d.name == "Admin IWD":
            list = HoldsDesignation.objects.filter(designation=d)
            holdsDesignations.append(list)

    return render(request, 'iwdModuleV2/auditDocumentView.html', {'obj' : obj, 'holdsDesignations' : holdsDesignations})

@login_required
def auditDocument(request):
    if request.method == 'POST':
        requestId = request.POST.get("id", 0)

        d = HoldsDesignation.objects.get(user__username=request.POST['designation'])
        d1 = HoldsDesignation.objects.get(user__username=request.user)

        create_file(uploader=request.user.username, 
            uploader_designation=d1.designation, 
            receiver=request.POST['designation'],
            receiver_designation=d.designation,
            src_module="IWD", 
            src_object_id= str(requestId),
            file_extra_JSON= {"value": 2},
            attached_file = None)

        inbox_files = view_inbox(
            username=request.user,
            designation=d1.designation,
            src_module="IWD"
        )

        for result in inbox_files:
            print(result['src_object_id'])
            if result['src_object_id'] == requestId:
                delete_file(file_id = result['id'])
                break

        Requests.objects.filter(id=requestId).update(status="Bill Audited")

        eligible = ""
        userObj = request.user
        userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
        for p in userDesignationObjects:
            eligible = p.designation.name

    return render(request, 'iwdModuleV2/dashboard.html', {'eligible' : eligible})

@login_required
def settleBillsView(request):
    d = HoldsDesignation.objects.get(user__username=request.user)

    inbox_files = view_inbox(
        username=request.user,
        designation=d.designation,
        src_module="IWD"
    )

    obj = []
    
    for x in inbox_files:
        requestId = x['src_object_id']
        bills_object = Bills.objects.filter(request_id=requestId).first()
        element = [bills_object.request_id.id, bills_object.file, bills_object.file.url]
        obj.append(element)

    return render(request, 'iwdModuleV2/settleBillsView.html', {'obj' : obj})

@login_required
def handleSettleBillRequests(request):
    if request.method == 'POST':
        request_id = request.POST.get("id", 0)

        d = HoldsDesignation.objects.get(user__username=request.user)

        inbox_files = view_inbox(
            username=request.user,
            designation=d.designation,
            src_module="IWD"
        )

        for p in inbox_files:
            if p['src_object_id'] == request_id:
                delete_file(file_id = p['id'])
                break

        Requests.objects.filter(id=request_id).update(status="Final Bill Settled", billSettled=1)

        inbox_files = view_inbox(
            username=request.user,
            designation=d.designation,
            src_module="IWD"
        )

        obj = []
        
        for x in inbox_files:
            request_id = x['src_object_id']
            bills_object = Bills.objects.get(request_id=request_id)
            element = [request_id, bills_object.file, bills_object.file.url]
            obj.append(element)

        return render(request, 'iwdModuleV2/settleBillsView.html', {'obj' : obj})

@login_required   
def viewBudget(request):

    budget_object = Budget.objects.filter()

    obj = []

    for x in budget_object:
        element = [x.id, x.name, x.budgetIssued]
        obj.append(element)
    
    return render(request, 'iwdModuleV2/viewBudget.html', {'obj' : obj})

@login_required
def budget(request):
    budget_object = Budget.objects.filter()

    obj = []

    for x in budget_object:
        element = [x.id, x.name, x.budgetIssued]
        obj.append(element)
    
    return render(request, 'iwdModuleV2/budget.html', {'obj' : obj})

@login_required
def addBudget(request):
    if request.method == 'POST':
        formObject = Budget()
        formObject.name = request.POST['name']
        formObject.budgetIssued = request.POST['budget']
        formObject.save()
    return render(request, 'iwdModuleV2/addBudget.html', {})

@login_required
def editBudgetView(request):
    budget_object = Budget.objects.filter()

    obj = []

    for x in budget_object:
        element = [x.id, x.name, x.budgetIssued]
        obj.append(element)
    
    return render(request, 'iwdModuleV2/editBudget.html', {'obj' : obj})

@login_required
def editBudget(request):
    if request.method == "POST":
        budgetId = request.POST['id']
        budgetName = request.POST['name']
        budgetIssued = request.POST['budget']
        Budget.objects.filter(id=budgetId).update(name=budgetName, budgetIssued=budgetIssued)
        items = Budget.objects.filter()
        obj = []
        for i in items:
            element = [i.id, i.name, i.budgetIssued]
            obj.append(element)
        return render(request, 'iwdModuleV2/editBudget.html', {'obj' : obj})

    
