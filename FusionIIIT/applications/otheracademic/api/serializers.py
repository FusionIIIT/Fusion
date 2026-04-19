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
            'Dean_approved',
            'Dean_rejected',
            'Director_approved',
            'Director_rejected',
            'AcadAdmin_approved',
            'AcadAdmin_rejected',
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

# ==================== NO-DUES SERIALIZERS ====================

class NoDuesStatusSerializer(serializers.ModelSerializer):
    """Output serializer for no-dues status."""
    roll_no_value = serializers.CharField(source='roll_no.roll_no', read_only=True)
    
    class Meta:
        model = NoDues
        fields = [
            'id',
            'roll_no_value',
            'name',
            'library_clear',
            'library_notclear',
            'hostel_clear',
            'hostel_notclear',
            'mess_clear',
            'mess_notclear',
            'ece_clear',
            'ece_notclear',
            'physics_lab_clear',
            'physics_lab_notclear',
            'mechatronics_lab_clear',
            'mechatronics_lab_notclear',
            'cc_clear',
            'cc_notclear',
            'workshop_clear',
            'workshop_notclear',
            'signal_processing_lab_clear',
            'signal_processing_lab_notclear',
            'vlsi_clear',
            'vlsi_notclear',
            'design_studio_clear',
            'design_studio_notclear',
            'design_project_clear',
            'design_project_notclear',
            'bank_clear',
            'bank_notclear',
            'icard_dsa_clear',
            'icard_dsa_notclear',
            'account_clear',
            'account_notclear',
            'btp_supervisor_clear',
            'btp_supervisor_notclear',
            'discipline_office_clear',
            'discipline_office_notclear',
            'student_gymkhana_clear',
            'student_gymkhana_notclear',
            'alumni_clear',
            'alumni_notclear',
            'placement_cell_clear',
            'placement_cell_notclear',
        ]


class NoDuesInitiateSerializer(serializers.Serializer):
    """Input serializer for initiating no-dues clearance."""
    pass  # No input needed for initiation, just triggers creation


class NoDuesVerificationSerializer(serializers.Serializer):
    """Input serializer for department to verify no-dues clearance."""
    no_dues_id = serializers.IntegerField()
    department = serializers.CharField(max_length=100)
    is_clear = serializers.BooleanField()


class NoDuesCertificateSerializer(serializers.Serializer):
    """Output serializer for no-dues certificate."""
    roll_no = serializers.CharField()
    name = serializers.CharField()
    all_clear = serializers.BooleanField()
    issued_date = serializers.DateTimeField()
    certificate_url = serializers.CharField(allow_null=True)