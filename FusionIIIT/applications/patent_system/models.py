from django.db import models
import os
from django.contrib.auth.models import User
from django.utils.timezone import now

class Applicant(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant")
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    def str(self):
        return self.name

    class Meta:
        db_table = 'patent_system_applicant'

class Attorney(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    firm_name = models.CharField(max_length=255, blank=True, null=True)
    experience_years = models.IntegerField(default=0)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    assigned_cases = models.IntegerField(default=0)

    def str(self):
        return self.name

    class Meta:
        db_table = 'patent_system_attorney'

class Application(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Reviewed by PCC Admin", "Reviewed by PCC Admin"),
        ("Attorney Assigned", "Attorney Assigned"),
        ("Forwarded for Director's Review", "Forwarded for Director's Review"),
        ("Director's Approval Received", "Director's Approval Received"),
        ("Patentability Check", "Patentability Check"),
        ("Patentability Search Report Generated", "Patentability Search Report Generated"),
        ("Patent Filed", "Patent Filed"),
        ("Rejected", "Rejected"),
    ]
    
    DECISION_STATUS_CHOICES = [
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Pending", "Pending"),
    ]
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default = "Draft")
    patentability_check_date = models.DateField(blank=True, null=True)
    patentability_file_date = models.DateField(blank=True, null=True)
    token_no = models.CharField(max_length=100, blank=True, null=True)
    primary_applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name="applications")  
    attorney = models.ForeignKey(Attorney, on_delete=models.CASCADE, related_name="applications", blank=True, null=True)
    assigned_date = models.DateField(blank=True, null=True)
    decision_status = models.CharField(max_length=50, choices=DECISION_STATUS_CHOICES, default = "Pending")
    decision_date = models.DateField(blank=True, null=True)
    submitted_date = models.DateField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    def str(self):
        return self.title

    class Meta:
        db_table = 'patent_system_application'

# Function to give path for poc_details
def poc_file_upload_path(instance, filename):
    """
    Generate a unique file path for POC (Proof of Concept) details.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    # Extract base name and extension from the filename
    base, extension = os.path.splitext(filename)

    # Sanitize the base filename (replace spaces with underscores)
    base = base.replace(" ", "_")

    # Generate a timestamp to ensure filename uniqueness
    timestamp = now().strftime("%Y%m%d%H%M%S")

    # Construct the new filename by appending timestamp
    new_filename = f"{base}_{timestamp}{extension}"

    # Define the custom upload path
    return os.path.join("patent/Application/Section-I/poc_details", new_filename)


class ApplicationSectionI(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="section_i")
    area = models.TextField()
    problem = models.TextField()
    objective = models.TextField()
    novelty = models.TextField()
    advantages = models.TextField()
    is_tested = models.BooleanField(default=False)
    poc_details = models.FileField(upload_to=poc_file_upload_path, blank=True, null=True)  # FileField with custom path
    applications = models.TextField()

    class Meta:
        db_table = 'patent_system_application_section_i'

# Function to give path for mou_details
def generate_mou_file_path(instance, filename):
    """
    Generate a unique file path for MOU file.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    base, extension = os.path.splitext(filename)  # Split filename and extension
    base = base.replace(" ", "_")  # Replace spaces with underscores for safety
    timestamp = now().strftime("%Y%m%d%H%M%S")  # Generate timestamp
    new_filename = f"{base}_{timestamp}{extension}"  # Append timestamp
    return os.path.join("patent/Application/Section-II/mou_files", new_filename)

def generate_source_agreement_file_path(instance, filename):
    """
    Generate a unique file path for MOU file.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    base, extension = os.path.splitext(filename)  # Split filename and extension
    base = base.replace(" ", "_")  # Replace spaces with underscores for safety
    timestamp = now().strftime("%Y%m%d%H%M%S")  # Generate timestamp
    new_filename = f"{base}_{timestamp}{extension}"  # Append timestamp
    return os.path.join("patent/Application/Section-II/source_agreement_files", new_filename)

class ApplicationSectionII(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="section_ii")
    funding_details = models.TextField()
    funding_source = models.TextField()
    source_agreement = models.FileField(upload_to=generate_source_agreement_file_path, blank=True, null=True) 
    publication_details = models.TextField()
    mou_details = models.TextField()
    mou_file = models.FileField(upload_to=generate_mou_file_path, blank=True, null=True)  # FileField for MOU file
    research_details = models.TextField()

    class Meta:
        db_table = 'patent_system_application_section_ii'

# Function to give path for form_iii
def generate_form_iii_file_path(instance, filename):
    """
    Generate a unique file path for Form III uploads.

    Args:
        instance: The model instance that the file is associated with.
        filename: The original filename of the uploaded file.

    Returns:
        str: A custom file path where the file will be stored.
    """
    base, extension = os.path.splitext(filename)  # Split filename and extension
    base = base.replace(" ", "_")  # Replace spaces with underscores for safety
    timestamp = now().strftime("%Y%m%d%H%M%S")  # Generate timestamp
    new_filename = f"{base}_{timestamp}{extension}"  # Append timestamp
    return os.path.join("patent/Application/Section-III/form_iii_files", new_filename)

class ApplicationSectionIII(models.Model):
    DEVELOPMENT_STAGE_CHOICES = [
        ("Embryonic", "Embryonic"),
        ("Partially developed", "Partially developed"),
        ("Off-the-shelf", "Off-the-shelf"),
    ]
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="section_iii")
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=15)
    development_stage = models.CharField(max_length=30, choices=DEVELOPMENT_STAGE_CHOICES)
    form_iii = models.FileField(upload_to=generate_form_iii_file_path)

    class Meta:
        db_table = 'patent_system_application_section_iii'


class AssociatedWith(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)

    def str(self):
        return f"{self.applicant.name} - {self.application.title} ({self.percentage_share}%)"
    
    class Meta:
        db_table = 'patent_system_associatedWith'