from django.shortcuts import render, redirect

from applications.globals.models import *
from .models import *
from django.http import HttpResponseRedirect


# Create your views here.


# The names of the Functions and the corresponding indication of redirection of the logic inside their body is very well
# indicative of the purpose.
# At every instance of the Project Entry, i.e. at places where a whole lot of dealing with components related
# to specific project, the projectId is stored to be referenced out throughout life of filling.
# Apart from Entry points, all other are sub parts of them.
# This briefly covers comments. To write it wholly as comment would be cumbersome and at the same time less fruitful
# owing to length and inherent extensiveness of code. Rather than, whosoever read this code is advised to do so
# in conjunction with SRS. After that, everything will become easier.

def dashboard(request):
    eligible = False
    userObj = request.user
    userDesignationObjects = HoldsDesignation.objects.filter(user=userObj)
    for p in userDesignationObjects:
        if p.designation.name == 'Admin IWD':
            eligible = True
            break
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
        existingObject = CorrigendumTable.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
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
        existingObject = Addendum.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
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
        existingObject = PreBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
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
    formNoTechnicalObjects.key = Projects.objects.get(id=request.session['projectId'])
    if request.method == 'POST':
        existingObject = NoOfTechnicalBidTimes.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formNoTechnicalObjects.number = int(request.POST['number'])
        formNoTechnicalObjects.save()
        return redirect('iwdModuleV2/technicalBidForm')
    return render(request, 'iwdModuleV2/no_of_entries.html', {})


def TechnicalBidForm(request):
    formObject = TechnicalBidDetails()
    numberOfTechnicalBidTimes = NoOfTechnicalBidTimes.objects.get(key=Projects.objects.get(id=request.session['projectId'])).number
    if request.method == 'POST':
        existingObject = TechnicalBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
        if existingObject.count() == 1:
            existingObject.delete()
        formObject = TechnicalBidDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.requirements = request.POST['requirements']
        formObject.save()
        TechnicalBidContractorDetails.objects.filter(key=formObject).all().delete()
        for w in range(numberOfTechnicalBidTimes):
            formContractorObject = TechnicalBidContractorDetails()
            formContractorObject.key = formObject
            formContractorObject.name = request.POST[str(w) + 'name']
            formContractorObject.description = request.POST[str(w) + 'Description']
            formContractorObject.save()
        return redirect('iwdModuleV2/noOfEntriesFinancialBid')
    return render(request, 'iwdModuleV2/page2_support_4_technicalbid.html',
                  {'quantity': range(numberOfTechnicalBidTimes), 'obj': formObject})


def noOfEntriesFinancialBid(request):
    listOfContractors = []
    objectTechnicalBid = TechnicalBidDetails.objects.get(key=Projects.objects.get(id=request.session['projectId']))
    objects = TechnicalBidContractorDetails.objects.filter(key=objectTechnicalBid)
    for t in objects:
        listOfContractors.append(t.name)
    if request.method == 'POST':
        existingObject = FinancialBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
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
            formContractorObject.percentageRelCost = request.POST[listOfContractors[f] + 'percentageRelCost']
            formContractorObject.perFigures = request.POST[listOfContractors[f] + 'perFigures']
            formContractorObject.save()
        return redirect('iwdModuleV2/letterOfIntent')
    return render(request, 'iwdModuleV2/page2_support_5_financialbid.html',
                  {'list': listOfContractors})


def letterOfIntent(request):
    if request.method == 'POST':
        existingObject = LetterOfIntentDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
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
        existingObject = WorkOrderForm.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
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
        existingObject = Agreement.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
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
    Milestones.objects.filter(key=Projects.objects.get(id=request.session['projectId'])).all().delete()
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
    request.session['projectId'] = request.POST['id']
    projectPageOne = PageOneDetails.objects.get(id=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page1.html', {'x': projectPageOne})


def page2View(request):
    projectPageTwo = PageTwoDetails.objects.get(id=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page2.html', {'x': projectPageTwo})


def AESView(request):
    objects = AESDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/AA&ES.html', {'AES': objects})


def financialBidView(request):
    elements = []
    objects = FinancialBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = FinancialContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.description, w.name, w.estimatedCost, w.percentageRelCost, w.perFigures, w.totalCost]
            elements.append(obj)
    return render(request, 'iwdModuleV2/Page2_financialbid.html', {'financial': elements})


def technicalBidView(request):
    elements = []
    objects = TechnicalBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    for f in objects:
        contractorObjects = TechnicalBidContractorDetails.objects.filter(key=f)
        for w in contractorObjects:
            obj = [f.sNo, f.requirements, w.name, w.description]
            elements.append(obj)
    return render(request, 'iwdModuleV2/Page2_technical-bid.html', {'technical': elements})


def preBidDetailsView(request):
    preBidObjects = PreBidDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page2_pre-bid.html', {'preBidDetails': preBidObjects})


def corrigendumView(request):
    corrigendumObject = CorrigendumTable.objects.get(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/corrigendum.html', {'corrigendum': corrigendumObject})


def addendumView(request):
    addendumObject = Addendum.objects.get(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Addendum.html', {'x': addendumObject})


def letterOfIntentView(request):
    letterOfIntentObject = LetterOfIntentDetails.objects.get(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/letterOfIntent.html', {'x': letterOfIntentObject})


def workOrderFormView(request):
    workOrderFormObject = WorkOrderForm.objects.get(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/WorkOrderForm.html', {'x': workOrderFormObject})


def agreementView(request):
    agreementObject = Agreement.objects.get(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Agreement.html', {'agreement': agreementObject})


def milestoneView(request):
    milestoneObjects = Milestones.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page2_milestones.html', {'milestones': milestoneObjects})


def page3View(request):
    pageThreeDetails = PageThreeDetails.objects.get(id=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/Page3.html', {'x': pageThreeDetails})


def extensionFormView(request):
    extensionObjects = ExtensionOfTimeDetails.objects.filter(key=Projects.objects.get(id=request.session['projectId']))
    return render(request, 'iwdModuleV2/ExtensionForm.html', {'extension': extensionObjects})
