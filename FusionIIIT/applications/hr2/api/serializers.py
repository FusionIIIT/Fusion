import datetime
import re

from rest_framework import serializers

from applications.hr2.models import (
    LTCform,
    CPDAAdvanceform,
    CPDAReimbursementform,
    LeaveForm,
    Appraisalform,
    LeaveBalance,
)


def _validate_approved_status_transition(instance, attrs):
    """Allow only Pending (None) → Approved (True) or Rejected (False); no changes from final states."""
    if instance is None:
        return attrs
    prev = instance.approved
    new_val = attrs.get("approved", prev)
    if prev is True and new_val is not True:
        raise serializers.ValidationError(
            {"approved": "Cannot change status after approval."}
        )
    if prev is False and new_val is not False:
        raise serializers.ValidationError(
            {"approved": "Cannot change status after rejection."}
        )
    return attrs


def _parse_ltc_block_year_range(block_year):
    """Return (start_date, end_date) inclusive calendar bounds for the LTC block, or (None, None)."""
    if block_year is None or block_year == "":
        return None, None
    text = str(block_year).strip()
    years = [int(y) for y in re.findall(r"\d{4}", text)]
    if len(years) >= 2:
        y0, y1 = min(years), max(years)
    elif len(years) == 1:
        y0, y1 = years[0], years[0] + 3
    else:
        return None, None
    start = datetime.date(y0, 1, 1)
    end = datetime.date(y1, 12, 31)
    return start, end


def _date_in_range(d, start, end):
    if d is None or start is None or end is None:
        return True
    return start <= d <= end


def _validate_ltc_dependents_list(deps, max_count=25):
    if deps is None:
        return
    if not isinstance(deps, list):
        raise serializers.ValidationError(
            {"detailsOfDependents": "Dependent data must be a list."}
        )
    if len(deps) > max_count:
        raise serializers.ValidationError(
            {
                "detailsOfDependents": f"At most {max_count} dependents are allowed (got {len(deps)})."
            }
        )
    for i, item in enumerate(deps):
        if not isinstance(item, dict):
            raise serializers.ValidationError(
                {"detailsOfDependents": f"Invalid dependent entry at index {i}."}
            )
        relationship = (item.get("relationship") or item.get("reason") or "").strip()
        if not relationship:
            raise serializers.ValidationError(
                {
                    "detailsOfDependents": f"Each dependent must include relationship or reason (index {i})."
                }
            )
        if item.get("dob") is None and item.get("age") in (None, ""):
            raise serializers.ValidationError(
                {
                    "detailsOfDependents": f"Each dependent must include date of birth or age (index {i})."
                }
            )


def _set_approved_by_and_date_on_approval(instance, validated_data, request):
    """Set approved_by and approvedDate when form is approved by the current user."""
    if instance is None:
        return validated_data
    prev_approved = instance.approved
    new_approved = validated_data.get("approved", prev_approved)
    # When transitioning from non-approved to approved (True)
    if new_approved is True and prev_approved is not True:
        if request and request.user.is_authenticated:
            validated_data["approved_by"] = request.user
            validated_data["approvedDate"] = datetime.date.today()
    return validated_data


class LTC_serializer(serializers.ModelSerializer):
    class Meta:
        model = LTCform
        fields = [
            "id",
            "employeeId",
            "name",
            "blockYear",
            "pfNo",
            "basicPaySalary",
            "designation",
            "departmentInfo",
            "leaveRequired",
            "leaveStartDate",
            "leaveEndDate",
            "dateOfDepartureForFamily",
            "natureOfLeave",
            "purposeOfLeave",
            "hometownOrNot",
            "placeOfVisit",
            "addressDuringLeave",
            "modeofTravel",
            "detailsOfFamilyMembersAlreadyDone",
            "detailsOfFamilyMembersAboutToAvail",
            "detailsOfDependents",
            "amountOfAdvanceRequired",
            "certifiedThatFamilyDependents",
            "certifiedThatAdvanceTakenOn",
            "adjustedMonth",
            "submissionDate",
            "phoneNumberForContact",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
        ]

    def validate(self, attrs):
        attrs = _validate_approved_status_transition(self.instance, attrs)

        block_year = attrs.get("blockYear")
        if block_year is None and self.instance:
            block_year = self.instance.blockYear
        start, end = _parse_ltc_block_year_range(block_year)

        leave_start = attrs.get("leaveStartDate")
        if leave_start is None and self.instance:
            leave_start = self.instance.leaveStartDate
        leave_end = attrs.get("leaveEndDate")
        if leave_end is None and self.instance:
            leave_end = self.instance.leaveEndDate
        dep_family = attrs.get("dateOfDepartureForFamily")
        if dep_family is None and self.instance:
            dep_family = self.instance.dateOfDepartureForFamily

        if start and end:
            if not _date_in_range(leave_start, start, end):
                raise serializers.ValidationError(
                    {
                        "leaveStartDate": "Leave start date must fall within the declared LTC block year."
                    }
                )
            if not _date_in_range(leave_end, start, end):
                raise serializers.ValidationError(
                    {
                        "leaveEndDate": "Leave end date must fall within the declared LTC block year."
                    }
                )
            if not _date_in_range(dep_family, start, end):
                raise serializers.ValidationError(
                    {
                        "dateOfDepartureForFamily": "Family departure date must fall within the declared LTC block year."
                    }
                )

        deps = attrs.get("detailsOfDependents")
        if deps is None and self.instance:
            deps = self.instance.detailsOfDependents
        _validate_ltc_dependents_list(deps)

        about = attrs.get("detailsOfFamilyMembersAboutToAvail")
        if about is None and self.instance:
            about = self.instance.detailsOfFamilyMembersAboutToAvail
        if about is not None:
            if isinstance(about, list) and len(about) > 20:
                raise serializers.ValidationError(
                    {
                        "detailsOfFamilyMembersAboutToAvail": "Too many family members listed (max 20)."
                    }
                )
            if isinstance(about, list):
                for i, row in enumerate(about):
                    if isinstance(row, dict) and not (row.get("name") or "").strip():
                        raise serializers.ValidationError(
                            {
                                "detailsOfFamilyMembersAboutToAvail": f"Family member name required at index {i}."
                            }
                        )

        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")
        validated_data = _set_approved_by_and_date_on_approval(instance, validated_data, request)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        return LTCform.objects.create(**validated_data)


class CPDAAdvance_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAAdvanceform
        fields = [
            "id",
            "employeeId",
            "name",
            "designation",
            "pfNo",
            "purpose",
            "amountRequired",
            "advanceDueAdjustment",
            "submissionDate",
            "balanceAvailable",
            "advanceAmountPDA",
            "amountCheckedInPDA",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
        ]

    def validate(self, attrs):
        return _validate_approved_status_transition(self.instance, attrs)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        validated_data = _set_approved_by_and_date_on_approval(instance, validated_data, request)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        return CPDAAdvanceform.objects.create(**validated_data)


class Appraisal_serializer(serializers.ModelSerializer):
    class Meta:
        model = Appraisalform
        fields = [
            "id",
            "employeeId",
            "name",
            "designation",
            "disciplineInfo",
            "specificFieldOfKnowledge",
            "currentResearchInterests",
            "coursesTaught",
            "newCoursesIntroduced",
            "newCoursesDeveloped",
            "otherInstructionalTasks",
            "thesisSupervision",
            "sponsoredReseachProjects",
            "otherResearchElement",
            "publication",
            "referredConference",
            "conferenceOrganised",
            "membership",
            "honours",
            "editorOfPublications",
            "expertLectureDelivered",
            "membershipOfBOS",
            "otherExtensionTasks",
            "administrativeAssignment",
            "serviceToInstitute",
            "otherContribution",
            "performanceComments",
            "submissionDate",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
        ]

    def validate(self, attrs):
        return _validate_approved_status_transition(self.instance, attrs)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        validated_data = _set_approved_by_and_date_on_approval(instance, validated_data, request)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        return Appraisalform.objects.create(**validated_data)


class CPDAReimbursement_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAReimbursementform
        fields = [
            "id",
            "employeeId",
            "name",
            "designation",
            "pfNo",
            "advanceTaken",
            "purpose",
            "adjustmentSubmitted",
            "balanceAvailable",
            "advanceDueAdjustment",
            "advanceAmountPDA",
            "amountCheckedInPDA",
            "submissionDate",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
        ]

    def validate(self, attrs):
        return _validate_approved_status_transition(self.instance, attrs)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        validated_data = _set_approved_by_and_date_on_approval(instance, validated_data, request)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        return CPDAReimbursementform.objects.create(**validated_data)


class Leave_serializer(serializers.ModelSerializer):
    has_leave_pdf = serializers.SerializerMethodField()

    class Meta:
        model = LeaveForm
        fields = [
            "id",
            "employeeId",
            "name",
            "designation",
            "submissionDate",
            "pfNo",
            "departmentInfo",
            "natureOfLeave",
            "leaveStartDate",
            "leaveEndDate",
            "purposeOfLeave",
            "addressDuringLeave",
            "academicResponsibility",
            "academicResponsibility_status",
            "addministrativeResponsibiltyAssigned",
            "adminResponsibility_status",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
            "leave_pdf_file",
            "has_leave_pdf",
        ]

    def get_has_leave_pdf(self, obj):
        return bool(
            getattr(obj, "leave_pdf", None) or getattr(obj, "leave_pdf_file", None)
        )

    def validate(self, attrs):
        attrs = _validate_approved_status_transition(self.instance, attrs)
        leave_start = attrs.get("leaveStartDate")
        if leave_start is None and self.instance:
            leave_start = self.instance.leaveStartDate
        leave_end = attrs.get("leaveEndDate")
        if leave_end is None and self.instance:
            leave_end = self.instance.leaveEndDate
        if leave_start and leave_end and leave_end < leave_start:
            raise serializers.ValidationError(
                {
                    "leaveEndDate": "Leave end date must be greater than or equal to leave start date."
                }
            )

        station_start = self.initial_data.get("stationLeaveStartDate")
        station_end = self.initial_data.get("stationLeaveEndDate")
        if station_start and station_end and station_end < station_start:
            raise serializers.ValidationError(
                {
                    "stationLeaveEndDate": "Station leave end date must be greater than or equal to station leave start date."
                }
            )

        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")
        # Handle approval metadata (approved_by, approvedDate) via shared helper
        validated_data = _set_approved_by_and_date_on_approval(instance, validated_data, request)

        # Handle PDF file upload: read bytes into leave_pdf binary field
        leave_pdf_file = validated_data.get("leave_pdf_file")
        if leave_pdf_file:
            try:
                validated_data["leave_pdf"] = leave_pdf_file.read()
                if hasattr(leave_pdf_file, "seek"):
                    leave_pdf_file.seek(0)
            except Exception:
                pass

        return super().update(instance, validated_data)

    def create(self, validated_data):
        # Handle PDF file upload: read bytes into leave_pdf binary field
        leave_pdf_file = validated_data.get("leave_pdf_file")
        if leave_pdf_file:
            try:
                validated_data["leave_pdf"] = leave_pdf_file.read()
                if hasattr(leave_pdf_file, "seek"):
                    leave_pdf_file.seek(0)
            except Exception:
                pass
        
        # Set responsibility statuses to 'pending' by default if not provided (BR-HR-006, BR-HR-007)
        if "academicResponsibility_status" not in validated_data:
            validated_data["academicResponsibility_status"] = "pending"
        if "adminResponsibility_status" not in validated_data:
            validated_data["adminResponsibility_status"] = "pending"
        
        return LeaveForm.objects.create(**validated_data)


class LeaveBalanace_serializer(serializers.ModelSerializer):
    casual_leave_available = serializers.SerializerMethodField()
    special_casual_leave_available = serializers.SerializerMethodField()
    earned_leave_available = serializers.SerializerMethodField()
    commuted_leave_available = serializers.SerializerMethodField()
    restricted_holiday_available = serializers.SerializerMethodField()
    station_leave_available = serializers.SerializerMethodField()
    vacation_leave_available = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = [
            "id",
            "employeeId",
            "casualLeave",
            "casual_leave_allotted",
            "casual_leave_used",
            "casual_leave_available",
            "specialCasualLeave",
            "special_casual_leave_allotted",
            "special_casual_leave_used",
            "special_casual_leave_available",
            "earnedLeave",
            "earned_leave_allotted",
            "earned_leave_used",
            "earned_leave_available",
            "commutedLeave",
            "commuted_leave_allotted",
            "commuted_leave_used",
            "commuted_leave_available",
            "restrictedHoliday",
            "restricted_holiday_allotted",
            "restricted_holiday_used",
            "restricted_holiday_available",
            "stationLeave",
            "station_leave_allotted",
            "station_leave_used",
            "station_leave_available",
            "vacationLeave",
            "vacation_leave_allotted",
            "vacation_leave_used",
            "vacation_leave_available",
        ]

    def get_casual_leave_available(self, obj):
        return max(0, (obj.casual_leave_allotted or 0) - (obj.casual_leave_used or 0))

    def get_special_casual_leave_available(self, obj):
        return max(
            0,
            (obj.special_casual_leave_allotted or 0) - (obj.special_casual_leave_used or 0),
        )

    def get_earned_leave_available(self, obj):
        return max(0, (obj.earned_leave_allotted or 0) - (obj.earned_leave_used or 0))

    def get_commuted_leave_available(self, obj):
        return max(0, (obj.commuted_leave_allotted or 0) - (obj.commuted_leave_used or 0))

    def get_restricted_holiday_available(self, obj):
        return max(
            0,
            (obj.restricted_holiday_allotted or 0) - (obj.restricted_holiday_used or 0),
        )

    def get_station_leave_available(self, obj):
        return max(0, (obj.station_leave_allotted or 0) - (obj.station_leave_used or 0))

    def get_vacation_leave_available(self, obj):
        return max(0, (obj.vacation_leave_allotted or 0) - (obj.vacation_leave_used or 0))

    def create(self, validated_data):
        return LeaveBalance.objects.create(**validated_data)


class ResponsibilityActionSerializer(serializers.Serializer):
    """Serializer for accepting/rejecting responsibility assignments."""
    form_id = serializers.IntegerField(required=True)
    responsibility_type = serializers.ChoiceField(choices=['academic', 'admin'], required=True)
    action = serializers.ChoiceField(choices=['accept', 'reject'], required=True)
    remarks = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        action = attrs.get('action')
        remarks = attrs.get('remarks', '')
        if action == 'reject' and not str(remarks).strip():
            raise serializers.ValidationError(
                {"remarks": "Remarks are required when rejecting a responsibility."}
            )
        return attrs
