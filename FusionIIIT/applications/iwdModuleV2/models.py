from django.db import models
from datetime import date
#from django.contrib.auth.models import User
from applications.filetracking.models import File

# Create your models here.


class Projects(models.Model):
    id = models.CharField(primary_key=True, max_length=200)


class PageOneDetails(models.Model):
    page_id = models.OneToOneField(Projects, on_delete=models.CASCADE, null=True)
    aESFile = models.FileField(null=True)
    dASA = models.DateField(null=True)
    nitNiqNo = models.IntegerField(null=True)
    proTh = models.CharField(null=True, max_length=200)
    emdDetails = models.CharField(null=True, max_length=200)
    preBidDate = models.DateField(null=True, max_length=200)
    technicalBidDate = models.DateField(null=True)
    financialBidDate = models.DateField(null=True)


class AESDetails(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE)
    sNo = models.CharField(max_length=100)
    descOfItems = models.CharField(max_length=200)
    unit = models.CharField(max_length=200)
    quantity = models.IntegerField()
    rate = models.IntegerField()
    amount = models.IntegerField()


class PageTwoDetails(models.Model):
    page_id = models.OneToOneField(Projects, on_delete=models.CASCADE, null=True)
    corrigendum = models.FileField(null=True)
    addendum = models.FileField(null=True)
    preBidMeetingDetails = models.FileField(null=True)
    technicalBidMeetingDetails = models.FileField(null=True)
    technicallyQualifiedAgencies = models.CharField(null=True, max_length=200)
    financialBidMeetingDetails = models.FileField(null=True)
    nameOfLowestAgency = models.CharField(null=True, max_length=200)
    letterOfIntent = models.FileField(null=True)
    workOrder = models.FileField(null=True)
    agreementLetter = models.FileField(null=True)
    milestones = models.FileField(null=True)


class CorrigendumTable(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    issueDate = models.DateField()
    nitNo = models.IntegerField()
    name = models.CharField(max_length=200)
    lastDate = models.DateField(null=True)
    lastTime = models.TimeField()
    env1BidOpeningDate = models.DateField()
    env1BidOpeningTime = models.TimeField()
    env2BidOpeningDate = models.DateField()
    env2BidOpeningTime = models.TimeField()


class Addendum(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    issueDate = models.DateField()
    nitNiqNo = models.IntegerField()
    name = models.CharField(max_length=200)
    openDate = models.DateField()
    openTime = models.TimeField()


class PreBidDetails(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    sNo = models.CharField(max_length=200)
    nameOfParticipants = models.CharField(max_length=200)
    issuesRaised = models.CharField(max_length=200)
    responseDecision = models.CharField(max_length=200)


class TechnicalBidDetails(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    sNo = models.CharField(max_length=200)
    requirements = models.CharField(max_length=200)


class TechnicalBidContractorDetails(models.Model):
    key = models.ForeignKey(TechnicalBidDetails, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)


class FinancialBidDetails(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    sNo = models.CharField(max_length=200)
    description = models.CharField(max_length=200)


class FinancialContractorDetails(models.Model):
    key = models.ForeignKey(FinancialBidDetails, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    estimatedCost = models.IntegerField()
    percentageRelCost = models.IntegerField()
    perFigures = models.IntegerField()
    totalCost = models.IntegerField()


class LetterOfIntentDetails(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    nitNiqNo = models.IntegerField()
    dateOfOpening = models.DateField()
    agency = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    tenderValue = models.IntegerField()


class WorkOrderForm(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    issueDate = models.DateField()
    nitNiqNo = models.IntegerField()
    agency = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    amount = models.IntegerField()
    time = models.IntegerField()
    monthDay = models.IntegerField()
    startDate = models.DateField()
    completionDate = models.DateField()
    deposit = models.IntegerField()
    contractDay = models.IntegerField()


class Agreement(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    date = models.DateField()
    agencyName = models.CharField(max_length=200)
    workName = models.CharField(max_length=200)
    fdrSum = models.IntegerField()


class Milestones(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE)
    sNo = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    timeAllowed = models.IntegerField()
    amountWithheld = models.IntegerField()


class PageThreeDetails(models.Model):
    page_id = models.OneToOneField(Projects, on_delete=models.CASCADE, null=True)
    extensionOfTime = models.FileField()
    actualCostOfBuilding = models.IntegerField()


class ExtensionOfTimeDetails(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE)
    sNo = models.CharField(max_length=200)
    hindrance = models.CharField(max_length=200)
    periodOfHindrance = models.IntegerField()
    periodOfExtension = models.IntegerField()


class NoOfTechnicalBidTimes(models.Model):
    key = models.OneToOneField(Projects, on_delete=models.CASCADE)
    number = models.IntegerField()

class Requests(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    area = models.CharField(max_length=200)
    requestCreatedBy = models.CharField(max_length=200)
    engineerProcessed = models.IntegerField(default=0)
    directorApproval = models.IntegerField(default=0)
    deanProcessed = models.IntegerField(default=0)
    status = models.CharField(max_length=200)
    issuedWorkOrder = models.IntegerField(default=0)
    workCompleted = models.IntegerField(default=0)
    billGenerated = models.IntegerField(default=0)
    billProcessed = models.IntegerField(default=0)
    billSettled = models.IntegerField(default=0)

class WorkOrder(models.Model):
    request_id = models.ForeignKey(Requests, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    date = models.DateField(default=date.today)
    agency = models.CharField(max_length=200)
    amount = models.IntegerField(default=0)
    deposit = models.IntegerField(default=0)
    alloted_time = models.CharField(max_length=200)
    start_date = models.DateField()
    completion_date = models.DateField()
    
class Bills(models.Model):
    request_id = models.ForeignKey(Requests, on_delete=models.CASCADE)
    file = models.FileField()
    # item = models.CharField(max_length=200)
    # quantity = models.IntegerField(default=1)


class Budget(models.Model):
    name = models.CharField(max_length=200)
    budgetIssued = models.IntegerField(default=0)
    
class Proposal(models.Model):
    request = models.ForeignKey(Requests, on_delete=models.CASCADE, related_name='proposals')
    created_by = models.CharField(max_length=200) #models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, blank=True)
    proposal_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    supporting_documents = models.FileField(upload_to='proposals/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
class Item(models.Model):
    proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField()
    unit = models.CharField(max_length=50)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    docs = models.FileField(upload_to='items/', null=True, blank=True)
