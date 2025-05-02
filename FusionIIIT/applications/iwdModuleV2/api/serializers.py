from rest_framework import serializers
from applications.globals.models import *
from applications.iwdModuleV2.models import *
from applications.ps1.models import *
from decimal import Decimal
import json
class WorkOrderFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = ['id', 'name']

class HoldsDesignationSerializer(serializers.ModelSerializer):
    designation = DesignationSerializer()
    username = serializers.CharField(source='user.username')

    class Meta:
        model = HoldsDesignation
        fields = ['id', 'designation', 'username']

class CreateRequestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = ['id', 'name', 'area', 'description', 'requestCreatedBy']

    def create(self, validated_data):
        validated_data['engineerProcessed'] = 0
        validated_data['iwdAdminApproval'] = 0
        validated_data['directorApproval'] = 0
        validated_data['deanProcessed'] = 0
        validated_data['status'] = "Pending"
        validated_data['issuedWorkOrder'] = 0
        validated_data['workCompleted'] = 0
        validated_data['billGenerated'] = 0
        validated_data['billProcessed'] = 0
        validated_data['billSettled'] = 0
        return super().create(validated_data)
    
class IWDAdminApprovedRequestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = ['id', 'name', 'area', 'description', 'requestCreatedBy']
    
class DirectorApprovedRequestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = ['id', 'name', 'area', 'description', 'requestCreatedBy']

class WorkUnderProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = ['id', 'name', 'area', 'description', 'requestCreatedBy', 'issuedWorkOrder', 'workCompleted']


class RequestsInProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = ['id', 'name', 'area', 'description', 'requestCreatedBy', 'issuedWorkOrder', 'workCompleted']

class ItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['name', 'description', 'unit', 'price_per_unit', 'quantity', 'docs', 'total_price', 'id']


class CreateProposalSerializer(serializers.ModelSerializer):
    items = ItemsSerializer(many=True, write_only=True)  # Keep the many=True option

    class Meta:
        model = Proposal
        fields = '__all__'

    def create(self, validated_data):
        # Pop the 'items' from the validated data
        items_data = validated_data.pop('items', [])

        # Create the proposal instance with the validated data
        proposal = Proposal.objects.create(**validated_data)

        proposal.save()

        return proposal

class ProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = '__all__'


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
    def create(validated_data):
        vendor = Vendor.objects.create(**validated_data)
        vendor.save()
        return vendor