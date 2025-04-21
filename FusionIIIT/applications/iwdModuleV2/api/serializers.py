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

# class AgreementSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Agreement
#         fields = '__all__'

# class MilestonesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Milestones
#         fields = '__all__'

# class ExtensionOfTimeDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ExtensionOfTimeDetails
#         fields = '__all__'

# class ProjectsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Projects
#         fields = '__all__'

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

# class PageOneDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PageOneDetails
#         fields = '__all__'

# class PageTwoDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PageTwoDetails
#         fields = '__all__'

# class PageThreeDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PageThreeDetails
#         fields = '__all__'

# class AESDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AESDetails
#         fields = '__all__'

# class CorrigendumTableSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CorrigendumTable
#         fields = '__all__'

# class AddendumSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Addendum
#         fields = '__all__'

# class PreBidDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PreBidDetails
#         fields = '__all__'

# class NoOfTechnicalBidTimesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NoOfTechnicalBidTimes
#         fields = '__all__'

# class TechnicalBidDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TechnicalBidDetails
#         fields = '__all__'

# class TechnicalBidContractorDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TechnicalBidContractorDetails
#         fields = '__all__'

# class FinancialBidDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FinancialBidDetails
#         fields = '__all__'

# class FinancialContractorDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FinancialContractorDetails
#         fields = '__all__'

# class LetterOfIntentDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LetterOfIntentDetails
#         fields = '__all__'

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