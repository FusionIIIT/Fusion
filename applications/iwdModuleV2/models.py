from django.db import models


# Create your models here.


class Projects(models.Model):
    id = models.CharField(primary_key=True, max_length=200)


class PageOneDetails(models.Model):
    id = models.ForeignKey(Projects, on_delete=models.CASCADE, primary_key=True)
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
    id = models.ForeignKey(Projects, on_delete=models.CASCADE, primary_key=True)
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
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
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
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
    issueDate = models.DateField()
    nitNiqNo = models.IntegerField()
    name = models.CharField(max_length=200)
    openDate = models.DateField()
    openTime = models.TimeField()


class PreBidDetails(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
    sNo = models.CharField(max_length=200)
    nameOfParticipants = models.CharField(max_length=200)
    issuesRaised = models.CharField(max_length=200)
    responseDecision = models.CharField(max_length=200)


class TechnicalBidDetails(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
    sNo = models.CharField(max_length=200)
    requirements = models.CharField(max_length=200)


class TechnicalBidContractorDetails(models.Model):
    key = models.ForeignKey(TechnicalBidDetails, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)


class FinancialBidDetails(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
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
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
    nitNiqNo = models.IntegerField()
    dateOfOpening = models.DateField()
    agency = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    tenderValue = models.IntegerField()


class WorkOrderForm(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
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
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
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
    id = models.ForeignKey(Projects, on_delete=models.CASCADE, primary_key=True)
    extensionOfTime = models.FileField()
    actualCostOfBuilding = models.IntegerField()


class ExtensionOfTimeDetails(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE)
    sNo = models.CharField(max_length=200)
    hindrance = models.CharField(max_length=200)
    periodOfHindrance = models.IntegerField()
    periodOfExtension = models.IntegerField()


class NoOfTechnicalBidTimes(models.Model):
    key = models.ForeignKey(Projects, on_delete=models.CASCADE, unique=True)
    number = models.IntegerField()

