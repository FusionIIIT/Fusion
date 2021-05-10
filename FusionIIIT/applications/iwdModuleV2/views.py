from django.shortcuts import render, redirect

from applications.globals.models import *
from .models import *

# Create your views here.

listOfContractors = []
numberOfAESTimes = 0
theTurnOfAES = 0
fromAES = False
numberOfPreBidTimes = 0
theTurnOfPreBid = 0
fromPreBid = False
numberOfTechnicalBidTimes = 0
numberOfTimesMilestones = 0
fromMilestone = False
fromExtension = False
theTurnOfMilestone = 0
numberOfEntriesExtension = 0
theTurnOfExtension = 0


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
    userObj = User.objects.get(id=request.user.id)
    userDesignationObjects = HoldsDesignation.objects.filter(working=userObj)
    for p in userDesignationObjects:
        if p.designation.name == 'Admin IWD':
            eligible = True
            break
    return render(request, 'iwdModuleV2/dashboard.html', {'eligible':eligible})


def page1_1(request):
    if request.method == 'POST':
        formObject = PageOneDetails()
        request.session['projectId'] = request.POST['name']
        project = Projects()
        project.id = request.session['projectId']
        project.save()
        formObject.id = project
        if 'aes_file' in request.POST:
            formObject.AESFile = request.POST['aes_file']
        if 'dASAName' in request.POST:
            formObject.dASA = request.POST['dASAName']
        if 'nitNiqNo' in request.POST:
            formObject.nitNiqNo = request.POST['nitNiqNo']
        if 'proTh' in request.POST:
            formObject.proTh = request.POST['proTh']
        if 'emdDetails' in request.POST:
            formObject.emdDetails = request.POST['emdDetails']
        if 'preBidDate' in request.POST:
            formObject.preBidDate = request.POST['preBidDate']
        if 'technicalBidDate' in request.POST:
            formObject.technicalBidDate = request.POST['technicalBidDate']
        if 'financialBidDate' in request.POST:
            formObject.financialBidDate = request.POST['financialBidDate']
        formObject.save()
        return redirect('iwdModuleV2/noOfEntriesAES')
    return render(request, 'iwdModuleV2/page1_create.html', {})


def noOfEntriesAES(request):
    global numberOfAESTimes, theTurnOfAES, fromAES
    if request.method == 'POST' or fromAES:
        if not fromAES:
            numberOfAESTimes = int(request.POST['number'])
        if theTurnOfAES < numberOfAESTimes:
            theTurnOfAES = theTurnOfAES + 1
            return redirect('iwdModuleV2/AESForm')
        fromAES = False
        theTurnOfAES = 0
        return redirect('/iwdModuleV2')
    return render(request, 'iwdModuleV2/no_of_entries.html', {})


def AESForm(request):
    global fromAES
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
        return redirect('iwdModuleV2/noOfEntriesAES')
    return render(request, 'iwdModuleV2/page1_support_1_aes.html', {})


def page2_1(request):
    if request.method == "POST":
        request.session['projectId'] = request.POST['id']
        formObject = PageTwoDetails()
        formObject.id = Projects.objects.get(id=request.session['projectId'])
        if 'corrigendum' in request.POST:
            formObject.corrigendum = request.POST['corrigendum']
        if 'addendum' in request.POST:
            formObject.addendum = request.POST['addendum']
        if 'preBid' in request.POST:
            formObject.preBidMeetingDetails = request.POST['preBid']
        if 'technicalBid' in request.POST:
            formObject.technicalBidMeetingDetails = request.POST['technicalBid']
        if 'qualifiedAgencies' in request.POST:
            formObject.technicallyQualifiedAgencies = request.POST['qualifiedAgencies']
        if 'financialBid' in request.POST:
            formObject.financialBidMeetingDetails = request.POST['financialBid']
        if 'lowAgency' in request.POST:
            formObject.nameOfLowestAgency = request.POST['lowAgency']
        if 'letterOfIntent' in request.POST:
            formObject.letterOfIntent = request.POST['letterOfIntent']
        if 'workOrder' in request.POST:
            formObject.workOrder = request.POST['workOrder']
        if 'agreementLetter' in request.POST:
            formObject.agreementLetter = request.POST['agreementLetter']
        if 'milestones' in request.POST:
            formObject.milestones = request.POST['milestones']
        formObject.save()
        return redirect('iwdModuleV2/corrigendumInput')
    return render(request, 'iwdModuleV2/page2_create.html', {})


def corrigendumInput(request):
    if request.method == 'POST':
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
        formObject = Addendum()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.issueDate = request.POST['issueDate']
        formObject.nitNiqNo = request.POST['nitNiqNo']
        formObject.openDate = request.POST['openDate']
        formObject.openTime = request.POST['openTime']
        formObject.name = request.POST['workName']
        formObject.save()
        return redirect('iwdModuleV2/noOfEntriesPreBid')
    return render(request, 'iwdModuleV2/page2_support_2_addendum.html', {})


def noOfEntriesPreBid(request):
    global numberOfPreBidTimes, theTurnOfPreBid, fromPreBid
    if request.method == 'POST' or fromPreBid:
        if not fromPreBid:
            numberOfPreBidTimes = int(request.POST['number'])
        if theTurnOfPreBid < numberOfPreBidTimes:
            theTurnOfPreBid = theTurnOfPreBid + 1
            return redirect('iwdModuleV2/preBidForm')
        fromPreBid = False
        theTurnOfPreBid = 0
        return redirect('iwdModuleV2/noOfEntriesTechnicalBid')
    return render(request, 'iwdModuleV2/no_of_entries.html', {})


def PreBidForm(request):
    global fromPreBid
    if request.method == 'POST':
        formObject = PreBidDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.nameOfParticipants = request.POST['nameParticipants']
        formObject.issuesRaised = request.POST['issuesRaised']
        formObject.responseDecision = request.POST['responseDecision']
        formObject.save()
        fromPreBid = True
        return redirect('iwdModuleV2/noOfEntriesPreBid')
    return render(request, 'iwdModuleV2/page2_support_3_prebid.html', {})


def noOfEntriesTechnicalBid(request):
    global numberOfTechnicalBidTimes
    if request.method == 'POST':
        numberOfTechnicalBidTimes = int(request.POST['number'])
        return redirect('iwdModuleV2/technicalBidForm')
    return render(request, 'iwdModuleV2/no_of_entries.html', {})


def TechnicalBidForm(request):
    formObject = TechnicalBidDetails()
    if request.method == 'POST':
        global listOfContractors
        formObject = TechnicalBidDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.requirements = request.POST['requirements']
        formObject.save()
        listOfContractors.clear()
        for w in range(numberOfTechnicalBidTimes):
            formContractorObject = TechnicalBidContractorDetails()
            formContractorObject.key = formObject
            formContractorObject.name = request.POST[str(w) + 'name']
            listOfContractors.append(formContractorObject.name)
            formContractorObject.description = request.POST[str(w) + 'Description']
            formContractorObject.save()
        return redirect('iwdModuleV2/noOfEntriesFinancialBid')
    return render(request, 'iwdModuleV2/page2_support_4_technicalbid.html',
                  {'quantity': range(numberOfTechnicalBidTimes), 'obj': formObject})


def noOfEntriesFinancialBid(request):
    global listOfContractors
    if request.method == 'POST':
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
        formObject = Agreement()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.date = request.POST['date']
        formObject.fdrSum = request.POST['fdrSum']
        formObject.workName = request.POST['workName']
        formObject.agencyName = request.POST['agencyName']
        formObject.save()
        return redirect('iwdModuleV2/noOfEntriesMilestones')
    return render(request, 'iwdModuleV2/page2_support_8_aggrement.html', {})


def noOfEntriesMilestones(request):
    global numberOfTimesMilestones, fromMilestone, theTurnOfMilestone
    if request.method == 'POST' or fromMilestone:
        if not fromMilestone:
            numberOfTimesMilestones = int(request.POST['number'])
        if theTurnOfMilestone < numberOfTimesMilestones:
            theTurnOfMilestone = theTurnOfMilestone + 1
            return redirect('iwdModuleV2/milestoneForm')
        theTurnOfMilestone = 0
        fromMilestone = False
        return redirect('/iwdModuleV2')
    return render(request, 'iwdModuleV2/no_of_entries.html', {})


def milestonesForm(request):
    global fromMilestone
    if request.method == 'POST':
        formObject = Milestones()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.description = request.POST['description']
        formObject.amountWithheld = request.POST['amountWithheld']
        formObject.timeAllowed = request.POST['timeAllowed']
        formObject.save()
        fromMilestone = True
        return redirect('iwdModuleV2/noOfEntriesMilestones')
    return render(request, 'iwdModuleV2/page2_support_9_milestone.html', {})


def page3_1(request):
    if request.method == 'POST':
        request.session['projectId'] = request.POST['id']
        formObject = PageThreeDetails()
        formObject.id = Projects.objects.get(id=request.session['projectId'])
        formObject.extensionOfTime = request.POST['extensionPDF']
        formObject.actualCostOfBuilding = request.POST['actualCost']
        formObject.save()
        return redirect('iwdModuleV2/noOfEntriesExtensionOfTime')
    return render(request, 'iwdModuleV2/page3_create.html', {})


def noOfEntriesExtensionOfTime(request):
    global numberOfEntriesExtension, theTurnOfExtension, fromExtension
    if request.method == 'POST' or fromExtension:
        if not fromExtension:
            numberOfEntriesExtension = int(request.POST['number'])
        if theTurnOfExtension < numberOfEntriesExtension:
            theTurnOfExtension = theTurnOfExtension + 1
            return redirect('iwdModuleV2/extensionForm')
        fromExtension = False
        theTurnOfExtension = 0
        return redirect('/iwdModuleV2')
    return render(request, 'iwdModuleV2/no_of_entries.html', {})


def ExtensionOfTimeForm(request):
    global fromExtension
    if request.method == 'POST':
        formObject = ExtensionOfTimeDetails()
        formObject.key = Projects.objects.get(id=request.session['projectId'])
        formObject.sNo = request.POST['sNo']
        formObject.hindrance = request.POST['hindrance']
        formObject.periodOfHindrance = request.POST['periodHindrance']
        formObject.periodOfExtension = request.POST['periodExtension']
        fromExtension = True
        formObject.save()
        return redirect('iwdModuleV2/noOfEntriesExtensionOfTime')
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
