from django.db import models
from django.contrib.auth.models import User

class Applicant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant")
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Attorney(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    specialization = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Application(models.Model):
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    patentability_check_date = models.DateField(blank=True, null=True)
    patentability_file_date = models.DateField(blank=True, null=True)
    token_no = models.CharField(max_length=100, blank=True, null=True)
    attorney = models.ForeignKey(Attorney, on_delete=models.CASCADE, related_name="applications")
    assigned_date = models.DateField(blank=True, null=True)
    decision_status = models.CharField(max_length=50)
    decision_date = models.DateTimeField()
    comments = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.title

class ApplicationSectionI(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    area = models.TextField(blank=True, null=True)
    problem = models.TextField(blank=True, null=True)
    objective = models.TextField(blank=True, null=True)
    novelty = models.TextField(blank=True, null=True)
    advantages = models.TextField(blank=True, null=True)
    is_tested = models.BooleanField(default=False)
    poc_details = models.BinaryField(blank=True, null=True)
    applications = models.TextField(blank=True, null=True)
    
class ApplicationSectionII(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    existing_tech = models.TextField(blank=True, null=True)
    limitation = models.TextField(blank=True, null=True)
    present_invention = models.TextField(blank=True, null=True)
    comparison = models.TextField(blank=True, null=True)
    differences = models.TextField(blank=True, null=True)
    trial_status = models.TextField(blank=True, null=True)

class ApplicationSectionIII(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    potential_industry = models.TextField(blank=True, null=True)
    potential_customer = models.TextField(blank=True, null=True)
    future_plans = models.TextField(blank=True, null=True)
    commercialization = models.TextField(blank=True, null=True)
    licensing_interest = models.TextField(blank=True, null=True)

class AssociatedWith(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"{self.applicant.name} - {self.application.title}"
