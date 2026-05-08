from rest_framework import serializers
from applications.globals.models import *
from applications.iwdModuleV2.models import *
from applications.ps1.models import *
from decimal import Decimal
import json
from django.utils import timezone
"""DRF serializers for iwdModuleV2 (inside `api/`).

Define serializers and field-level validation here.
"""
class WorkOrderFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        completion_date = attrs.get('completion_date')
        alloted_time = (attrs.get('alloted_time') or '').strip()

        if not alloted_time:
            raise serializers.ValidationError({'alloted_time': 'Allotted time is required'})
        if start_date and start_date < timezone.now().date():
            raise serializers.ValidationError({'start_date': 'Start date cannot be in the past'})
        if completion_date and start_date and completion_date < start_date:
            raise serializers.ValidationError({'completion_date': 'Completion date cannot be before start date'})

        return attrs

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
        fields = ['id', 'name', 'area', 'description', 'requestCreatedBy', 'activeProposal', 'iwdAdminApproval']

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Name is required')
        return value

    def validate_area(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Area is required')
        return value

    def validate_description(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Description is required')
        return value

    def create(self, validated_data):
        validated_data['activeProposal'] = 0
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

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Item name is required')
        return value

    def validate_quantity(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0')
        return value

    def validate_price_per_unit(self, value):
        if value is None or Decimal(str(value)) <= 0:
            raise serializers.ValidationError('Price per unit must be greater than 0')
        return value

    def validate(self, attrs):
        quantity = attrs.get('quantity')
        price_per_unit = attrs.get('price_per_unit')
        if quantity is not None and price_per_unit is not None:
            attrs['total_price'] = Decimal(str(quantity)) * Decimal(str(price_per_unit))
        return attrs


class CreateProposalSerializer(serializers.ModelSerializer):
    items = ItemsSerializer(many=True, write_only=True)  # Keep the many=True option

    class Meta:
        model = Proposal
        fields = '__all__'

    def validate(self, attrs):
        items_data = attrs.get('items') or []
        if not items_data:
            raise serializers.ValidationError({'items': 'At least one proposal item is required'})
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
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

    def validate_total_amount(self, value):
        if value is not None and Decimal(str(value)) < 0:
            raise serializers.ValidationError('Total amount must be non-negative')
        return value

    def create(self, validated_data):
        vendor = Vendor.objects.create(**validated_data)
        vendor.save()
        return vendor


# ===== INVENTORY SERIALIZERS (UC-30, BR-022, WF-08) =====

class InventoryItemSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)
    needs_procurement = serializers.BooleanField(read_only=True)

    class Meta:
        from applications.iwdModuleV2.models import InventoryItem
        model = InventoryItem
        fields = [
            'id', 'name', 'description', 'unit', 'quantity_available',
            'reorder_level', 'location', 'is_low_stock', 'needs_procurement',
            'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'last_updated', 'created_at']

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Item name is required')
        return value

    def validate_unit(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Unit is required')
        return value

    def validate_quantity_available(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Quantity must be non-negative')
        return value

    def validate_reorder_level(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Reorder level must be non-negative')
        return value


class CreateInventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        from applications.iwdModuleV2.models import InventoryItem
        model = InventoryItem
        fields = ['name', 'description', 'unit', 'quantity_available', 'reorder_level', 'location']

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Item name is required')
        return value


class InventoryTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        from applications.iwdModuleV2.models import InventoryTransaction
        model = InventoryTransaction
        fields = [
            'id', 'item', 'item_name', 'transaction_type', 'quantity',
            'request', 'performed_by', 'remarks', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


# ===== FEEDBACK SERIALIZERS (UC-31, BR-024, WF-10) =====

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        from applications.iwdModuleV2.models import Feedback
        model = Feedback
        fields = [
            'id', 'request', 'submitted_by', 'rating', 'comments',
            'created_at', 'reopened'
        ]
        read_only_fields = ['id', 'created_at', 'reopened']

    def validate_rating(self, value):
        if value is None or value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5')
        return value

    def validate_submitted_by(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('submitted_by is required')
        return value


class CreateFeedbackSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comments = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_request_id(self, value):
        from applications.iwdModuleV2.models import Requests
        if not Requests.objects.filter(id=value).exists():
            raise serializers.ValidationError('Request not found')
        return value


# ===== SLA SERIALIZERS (UC-29, BR-023, WF-09) =====

class SLAEscalationSerializer(serializers.ModelSerializer):
    class Meta:
        from applications.iwdModuleV2.models import SLAEscalation
        model = SLAEscalation
        fields = [
            'id', 'request', 'escalated_from', 'escalated_to',
            'reason', 'created_at', 'resolved'
        ]
        read_only_fields = ['id', 'created_at']


class SLADashboardSerializer(serializers.Serializer):
    total_active = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    due_soon_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    overdue_requests = serializers.ListField()
    escalation_count = serializers.IntegerField()
    priority_count = serializers.IntegerField()

