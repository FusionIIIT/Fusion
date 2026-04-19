"""
Serializers for otheracademic module.
Contains separate input and output serializers for validation and response formatting.
"""
from rest_framework import serializers
from applications.otheracademic.models import (
    LeaveFormTable,
    LeavePG,
    BonafideFormTableUpdated,
    AssistantshipClaimFormStatusUpd,
    NoDues,
    LeaveTypeChoices,
    LeaveTypePGChoices,
)


# ==================== LEAVE SERIALIZERS ====================

class LeaveFormInputSerializer(serializers.Serializer):
    """Input serializer for UG leave form submission."""
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    leave_type = serializers.ChoiceField(choices=LeaveTypeChoices.choices)
    address = serializers.CharField(max_length=100)
    purpose = serializers.CharField()
    hod_credential = serializers.CharField(max_length=100)
    semester = serializers.IntegerField(min_value=1, max_value=8)
    mobile_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    parents_mobile = serializers.CharField(max_length=15, required=False, allow_blank=True)
    mobile_during_leave = serializers.CharField(max_length=15, required=False, allow_blank=True)

    def validate(self, data):
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError("Start date cannot be after end date.")
        return data


class LeavePGInputSerializer(serializers.Serializer):
    """Input serializer for PG leave form submission."""
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    leave_type = serializers.ChoiceField(choices=LeaveTypePGChoices.choices)
    address = serializers.CharField(max_length=100)
    purpose = serializers.CharField()
    hod_credential = serializers.CharField(max_length=100)
    ta_superCredential = serializers.CharField(max_length=100)
    thesis_superCredential = serializers.CharField(max_length=100)
    semester = serializers.IntegerField(min_value=1, max_value=8)
    mobile_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    parents_mobile = serializers.CharField(max_length=15, required=False, allow_blank=True)
    mobile_during_leave = serializers.CharField(max_length=15, required=False, allow_blank=True)

    def validate(self, data):
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError("Start date cannot be after end date.")
        return data


class LeaveFormSerializer(serializers.ModelSerializer):
    """Output serializer for leave form."""
    class Meta:
        model = LeaveFormTable
        fields = [
            'id',
            'student_name',
            'roll_no',
            'date_from',
            'date_to',
            'date_of_application',
            'upload_file',
            'address',
            'purpose',
            'leave_type',
            'status',
            'hod',
            'stud_mobile_no',
            'parent_mobile_no',
            'leave_mobile_no',
            'curr_sem',
        ]


class LeavePGSerializer(serializers.ModelSerializer):
    """Output serializer for PG leave form."""
    class Meta:
        model = LeavePG
        fields = [
            'id',
            'student_name',
            'roll_no',
            'date_from',
            'date_to',
            'date_of_application',
            'upload_file',
            'address',
            'purpose',
            'leave_type',
            'status',
            'hod',
            'ta_supervisor',
            'thesis_supervisor',
            'stud_mobile_no',
            'parent_mobile_no',
            'leave_mobile_no',
            'curr_sem',
        ]


class LeaveStatusUpdateSerializer(serializers.Serializer):
    """Input serializer for updating leave status."""
    approvedLeaves = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )
    rejectedLeaves = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )


# ==================== BONAFIDE SERIALIZERS ====================

class BonafideFormInputSerializer(serializers.Serializer):
    """Input serializer for bonafide form submission."""
    branch = serializers.CharField(max_length=50)
    semester = serializers.CharField(max_length=20)
    purpose = serializers.CharField()


class BonafideFormSerializer(serializers.ModelSerializer):
    """Output serializer for bonafide form."""
    class Meta:
        model = BonafideFormTableUpdated
        fields = [
            'id',
            'student_names',
            'roll_nos',
            'branch_types',
            'semester_types',
            'purposes',
            'date_of_applications',
            'approve',
            'reject',
            'download_file',
        ]


class BonafideStatusSerializer(serializers.Serializer):
    """Output serializer for bonafide status."""
    rollNo = serializers.CharField()
    name = serializers.CharField()
    branch = serializers.CharField()
    semester = serializers.CharField()
    purpose = serializers.CharField()
    dateApplied = serializers.DateField()
    status = serializers.CharField()
    downloadUrl = serializers.CharField(allow_null=True, required=False)


class BonafideStatusUpdateSerializer(serializers.Serializer):
    """Input serializer for updating bonafide status."""
    approvedBonafides = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )
    rejectedBonafides = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )


# ==================== ASSISTANTSHIP SERIALIZERS ====================

class AssistantshipFormInputSerializer(serializers.Serializer):
    """Input serializer for assistantship form submission."""
    discipline = serializers.CharField(max_length=100)
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    date_applied = serializers.DateField()
    bank_account_no = serializers.CharField(max_length=100)
    ta_supervisor = serializers.CharField(max_length=100)
    thesis_supervisor = serializers.CharField(max_length=100)
    hod = serializers.CharField(max_length=100)
    applicability = serializers.CharField(max_length=100)

    def validate(self, data):
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError("Start date cannot be after end date.")
        return data


class AssistantshipFormSerializer(serializers.ModelSerializer):
    """Output serializer for assistantship form."""
    class Meta:
        model = AssistantshipClaimFormStatusUpd
        fields = [
            'id',
            'roll_no',
            'student_name',
            'discipline',
            'dateFrom',
            'dateTo',
            'bank_account',
            'dateApplied',
            'ta_supervisor',
            'thesis_supervisor',
            'hod',
            'applicability',
            'TA_approved',
            'TA_rejected',
            'Ths_approved',
            'Ths_rejected',
            'HOD_approved',
            'HOD_rejected',
            'Acad_approved',
            'Acad_rejected',
        ]


class AssistantshipStatusUpdateSerializer(serializers.Serializer):
    """Input serializer for updating assistantship status."""
    approvedRequests = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )
    rejectedRequests = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )


class AssistantshipStatusSerializer(serializers.Serializer):
    """Output serializer for assistantship status."""
    rollNo = serializers.CharField()
    name = serializers.CharField()
    discipline = serializers.CharField()
    dateApplied = serializers.DateField()
    bank_account = serializers.CharField()
    status = serializers.CharField()
    approvalStages = serializers.DictField()
