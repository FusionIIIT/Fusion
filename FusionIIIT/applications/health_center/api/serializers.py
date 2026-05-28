from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from applications.health_center.models import *


class DoctorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Doctor
        fields=('__all__')

class ComplaintSerializer(serializers.ModelSerializer):

    class Meta:
        model=Complaint
        fields=('__all__')

class StockSerializer(serializers.ModelSerializer):

    class Meta:
        model=Stock
        fields=('__all__')

class MedicineSerializer(serializers.ModelSerializer):

    class Meta:
        model=Medicine
        fields=('__all__')

class HospitalSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Hospital
        fields=('__all__')

 
class ExpirySerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Expiry
        fields=('__all__')

class ScheduleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Schedule
        fields=('__all__')


class CounterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Counter
        fields=('__all__')

class AppointmentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Appointment
        fields=('__all__')


class PrescriptionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Prescription
        fields=('__all__')


class PrescribedMedicineSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Prescribed_medicine
        fields=('__all__')


class AmbulanceRequestSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Ambulance_request
        fields=('__all__')

class HospitalAdmitSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Hospital_admit
        fields=('__all__')