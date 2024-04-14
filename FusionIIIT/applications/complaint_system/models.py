# imports
from django.db import models
from django.utils import timezone

from applications.globals.models import ExtraInfo, HoldsDesignation
from applications.filetracking.sdk import methods as fts
from applications.filetracking.models import File
from django.contrib.auth.models import User

from enum import Enum

# Class definations:


class Constants:
    AREA = ( ('hall-1', 'hall-1'),
        ('hall-3', 'hall-3'),
        ('hall-4', 'hall-4'),
        ('library', 'CC1'),
        ('computer center', 'CC2'),
        ('core_lab', 'core_lab'),
        ('LHTC', 'LHTC'),
        ('NR2', 'NR2'),
        ('NR3', 'NR3'),
        ('Admin building', 'Admin building'),
        ('Rewa_Residency', 'Rewa_Residency'),
        ('Maa Saraswati Hostel', 'Maa Saraswati Hostel'),
        ('Nagarjun Hostel', 'Nagarjun Hostel'),
        ('Panini Hostel', 'Panini Hostel'),

    )
    COMPLAINT_TYPE = (
        ('Electricity', 'Electricity'),
        ('carpenter', 'carpenter'),
        ('plumber', 'plumber'),
        ('garbage', 'garbage'),
        ('dustbin', 'dustbin'),
        ('internet', 'internet'),
        ('other', 'other'),
    )

class USER_TYPE(Enum):
    student = 'student'
    caretaker = 'caretaker'
    supervisor = 'supervisor'

class Caretaker(models.Model):
    staff_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    area = models.CharField(choices=Constants.AREA, max_length=20, default='hall-3')
    rating = models.IntegerField(default=0)
    myfeedback = models.CharField(max_length=400, default='this is my feedback')
    # no_of_comps = models.CharField(max_length=1000)

    def __str__(self):
        return str(self.id) + '-' + str(self.area)

class SectionIncharge(models.Model):
    staff_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    work_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                   max_length=20, default='Electricity')

    def __str__(self):
        return str(self.id) + '-' + self.work_type

class Workers(models.Model):
    secincharge_id = models.ForeignKey(SectionIncharge, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=50)
    age = models.CharField(max_length=10)
    phone = models.BigIntegerField(blank=True)
    worker_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                   max_length=20, default='internet')

    def __str__(self):
        return str(self.id) + '-' + self.name


class StudentComplain(models.Model):
    complainer = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    complaint_date = models.DateTimeField(default=timezone.now)
    complaint_finish = models.DateField(blank=True, null=True)
    complaint_type = models.CharField(choices=Constants.COMPLAINT_TYPE,
                                      max_length=20, default='internet')
    location = models.CharField(max_length=20, choices=Constants.AREA)
    specific_location = models.CharField(max_length=50, blank=True)
    details = models.CharField(max_length=100)
    status = models.IntegerField(default='0')
    remarks = models.CharField(max_length=300, default="Pending")
    flag = models.IntegerField(default='0')
    reason = models.CharField(max_length=100, blank=True, default="None")
    feedback = models.CharField(max_length=500, blank=True)
    worker_id = models.ForeignKey(Workers, blank=True, null=True,on_delete=models.CASCADE)
    upload_complaint = models.FileField(blank=True)
    comment = models.CharField(max_length=100,  default="None")
    #upload_resolved = models.FileField(blank=True,null=True)

    def __str__(self):
        return str(self.complainer.user.username)

    @staticmethod
    def get_complaints_by_user(user: ExtraInfo, role: str):
        """
        user: ExtraInfo
        role: student, caretaker or supervisor
        """
        if role == 'student':
            return StudentComplain.objects.filter(complainer=user)
        elif role == 'caretaker' or role == 'supervisor':
            designation = HoldsDesignation.objects.get(user=user.user).designation.name
            complaints = fts.view_inbox(
                username=user.user.username,
                designation=designation,
                src_module='complaint'
            )
            complaint_queryset = StudentComplain.objects.none()
            for complaint in complaints:
                complaint_queryset |= StudentComplain.objects.filter(id=complaint['src_object_id'])

            return complaint_queryset

    
    @staticmethod
    def create_file_for_complaint(complaint):
        """
        complaint: StudentComplain
        """

        caretaker = Caretaker.objects.get(area=complaint.location)
        caretaker_designation = HoldsDesignation.objects.get(user=caretaker.staff_id.user).designation.name

        fts.create_file(
            uploader=complaint.complainer.user.username,
            uploader_designation='student',
            receiver=caretaker.staff_id.user.username,
            receiver_designation=caretaker_designation,
            src_module='complaint',
            src_object_id=complaint.id
        )

        return complaint

    @staticmethod
    def forward_complaint(user: ExtraInfo, complaint_id: int):
        """
        user: ExtraInfo
        complaint_id: int
        """
        file = File.objects.get(src_object_id=complaint_id, src_module='complaint')
        user_designation = HoldsDesignation.objects.get(user=user.user)
        try:
            fts.forward_file(
                file_id=file.id,
                receiver=user.user.username,
                receiver_designation=user_designation.designation.name,
                file_extra_JSON={},
            )
            return True, 'Complaint forwarded successfully'
        except Exception as e:
            return False, str(e)


    # owner refers to whom it was last forwarded not the complainer
    @staticmethod
    def get_complaint_owner(complaint_id: int) -> User:
        file = File.objects.get(src_object_id=complaint_id, src_module='complaint')
        owner_id = fts.get_current_file_owner(file.id)
        return User.objects.get(username=owner_id)


class Supervisor(models.Model):
    sup_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    type = models.CharField(choices=Constants.COMPLAINT_TYPE, max_length=30,default='Electricity')

    def __str__(self):
        return str(self.sup_id) + '-' + str(self.type)
