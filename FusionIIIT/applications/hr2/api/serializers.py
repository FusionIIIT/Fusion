import datetime
import math
import re

from rest_framework import serializers

from applications.leave.helpers import get_leave_days
from applications.leave.models import LeaveType, LeavesCount
from applications.globals.models import ExtraInfo
from applications.hr2.constants.leave_balance_map import LEAVE_TYPE_TO_ALLOTTED_USED
from applications.hr2.models import (
    LTCform,
    CPDAAdvanceform,
    CPDAReimbursementform,
    LeaveForm,
    Appraisalform,
    LeaveBalance,
)


def _leave_type_to_hr_balance_key(leave_type: LeaveType) -> str:
    """Map ``leave.LeaveType.name`` to keys used by HR2 ``_LEAVE_TYPE_TO_ALLOTTED_USED``."""
    name = (leave_type.name or "").strip().lower()
    rules = (
        ("station", "station leave"),
        ("vacation", "vacation leave"),
        ("restricted", "restricted holiday"),
        ("special casual", "special casual leave"),
        ("commuted", "commuted leave"),
        ("earned", "earned leave"),
        ("casual", "casual"),
    )
    for needle, key in rules:
        if needle in name:
            return key
    return name or "casual"


def _resolve_leave_type_from_attrs(attrs, instance):
    lt = attrs.get("leave_type")
    if isinstance(lt, LeaveType):
        return lt
    if lt not in (None, ""):
        try:
            pk = int(lt)
            return LeaveType.objects.filter(pk=pk).first()
        except (TypeError, ValueError):
            pass
    if instance and getattr(instance, "leave_type_id", None):
        return instance.leave_type
    name = (attrs.get("natureOfLeave") or "").strip()
    if not name:
        return None
    return LeaveType.objects.filter(name__iexact=name).first() or LeaveType.objects.filter(
        name__icontains=name
    ).first()


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
            "workflow_status",
            "workflow_history",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
        ]
        read_only_fields = [
            "workflow_status",
            "workflow_history",
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
            "workflow_status",
            "workflow_history",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
        ]
        read_only_fields = [
            "workflow_status",
            "workflow_history",
            "created_by",
            "approved_by",
            "approvedDate",
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
            "workflow_status",
            "workflow_history",
            "approved",
            "approvedDate",
            "created_by",
            "approved_by",
        ]
        read_only_fields = [
            "workflow_status",
            "workflow_history",
            "created_by",
            "approved_by",
        ]
        extra_kwargs = {
            "disciplineInfo": {"allow_blank": True, "required": False},
            "specificFieldOfKnowledge": {"allow_blank": True, "required": False},
            "currentResearchInterests": {"allow_blank": True, "required": False},
            "coursesTaught": {"required": False},
            "newCoursesIntroduced": {"required": False},
            "newCoursesDeveloped": {"required": False},
            "otherInstructionalTasks": {"allow_blank": True, "required": False},
            "thesisSupervision": {"required": False},
            "sponsoredReseachProjects": {"required": False},
            "otherResearchElement": {"allow_blank": True, "required": False},
            "publication": {"allow_blank": True, "required": False},
            "referredConference": {"allow_blank": True, "required": False},
            "conferenceOrganised": {"allow_blank": True, "required": False},
            "membership": {"allow_blank": True, "required": False},
            "honours": {"allow_blank": True, "required": False},
            "editorOfPublications": {"allow_blank": True, "required": False},
            "expertLectureDelivered": {"allow_blank": True, "required": False},
            "membershipOfBOS": {"allow_blank": True, "required": False},
            "otherExtensionTasks": {"allow_blank": True, "required": False},
            "administrativeAssignment": {"allow_blank": True, "required": False},
            "serviceToInstitute": {"allow_blank": True, "required": False},
            "otherContribution": {"allow_blank": True, "required": False},
            "performanceComments": {"allow_blank": True, "required": False},
        }

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
    leave_type_name = serializers.SerializerMethodField()
    leave_balance_category = serializers.SerializerMethodField()
    application_type = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()
    leave_type = serializers.PrimaryKeyRelatedField(
        queryset=LeaveType.objects.all(), required=False, allow_null=True
    )

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
            "leave_type",
            "leave_type_name",
            "leave_balance_category",
            "application_type",
            "natureOfLeave",
            "leaveStartDate",
            "leaveEndDate",
            "start_half",
            "end_half",
            "applied_leave_days",
            "leave_info",
            "purposeOfLeave",
            "addressDuringLeave",
            "academicResponsibility",
            "addministrativeResponsibiltyAssigned",
            "approved",
            "approvedDate",
            "created_by",
            "created_by_username",
            "approved_by",
            "leave_pdf_file",
            "has_leave_pdf",
            "workflow_status",
            "workflow_history",
        ]
        read_only_fields = [
            "workflow_status",
            "workflow_history",
            "created_by",
            "approved_by",
        ]
        extra_kwargs = {
            "employeeId": {"allow_null": True, "required": False},
            "pfNo": {"allow_null": True, "required": False},
            "academicResponsibility": {"allow_blank": True, "required": False},
            "addministrativeResponsibiltyAssigned": {
                "allow_blank": True,
                "required": False,
            },
            "addressDuringLeave": {"allow_blank": True, "required": False},
            "leave_info": {"allow_blank": True, "required": False},
        }

    def to_internal_value(self, data):
        """Coerce ``employeeId`` / ``pfNo`` from multipart (strings, blanks, lists) to int or omit."""
        if data is not None and hasattr(data, "keys"):
            if hasattr(data, "lists"):
                base = {k: data.get(k) for k in data.keys()}
            else:
                base = dict(data) if isinstance(data, dict) else dict(data)
            for k in ("employeeId", "pfNo"):
                if k not in base:
                    continue
                v = base[k]
                if isinstance(v, (list, tuple)) and len(v) > 0:
                    v = v[-1]
                if v in (None, ""):
                    base.pop(k, None)
                    continue
                if isinstance(v, str) and v.strip().lower() in ("null", "undefined", "none"):
                    base.pop(k, None)
                    continue
                try:
                    base[k] = int(str(v).strip())
                except (TypeError, ValueError):
                    try:
                        base[k] = int(float(str(v).strip()))
                    except (TypeError, ValueError):
                        base.pop(k, None)
            request = self.context.get("request")
            if request and getattr(request, "user", None) and request.user.is_authenticated:
                extra = ExtraInfo.objects.filter(user=request.user).first()
                if extra:
                    # LeaveForm uses IntegerField; ExtraInfo.id is CharField PK (often non-numeric).
                    try:
                        uid = int(request.user.pk)
                    except (TypeError, ValueError):
                        uid = None
                    if uid is not None:
                        if base.get("employeeId") in (None, ""):
                            base["employeeId"] = uid
                        if base.get("pfNo") in (None, ""):
                            base["pfNo"] = uid
            data = base
        return super().to_internal_value(data)

    def get_has_leave_pdf(self, obj):
        return bool(
            getattr(obj, "leave_pdf", None) or getattr(obj, "leave_pdf_file", None)
        )

    def get_leave_type_name(self, obj):
        lt = getattr(obj, "leave_type", None)
        return lt.name if lt else None

    def get_leave_balance_category(self, obj):
        """Normalized key aligned with ``leave_balance_map`` / HR ``LeaveBalance`` columns."""
        lt = getattr(obj, "leave_type", None)
        if lt is not None:
            return _leave_type_to_hr_balance_key(lt)
        nature = (getattr(obj, "natureOfLeave", None) or "").strip().lower()
        return nature if nature else "casual"

    def get_application_type(self, obj):
        """UI label: self-service / file workflow uses the online form (vs legacy offline paperwork)."""
        return "Online"

    def get_created_by_username(self, obj):
        u = getattr(obj, "created_by", None)
        return getattr(u, "username", None) if u else None

    def validate(self, attrs):
        attrs = _validate_approved_status_transition(self.instance, attrs)
        if self.instance is None:
            purpose = (attrs.get("purposeOfLeave") or "").strip()
            if not purpose:
                raise serializers.ValidationError(
                    {"purposeOfLeave": "Purpose of leave is required."}
                )

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

        lt = _resolve_leave_type_from_attrs(attrs, self.instance)
        if self.instance is None and lt is None:
            raise serializers.ValidationError(
                {"leave_type": "Select a leave type (from the leave module catalog)."}
            )
        if lt is None:
            return attrs

        start_half = attrs.get("start_half")
        if start_half is None and self.instance is not None:
            start_half = self.instance.start_half
        end_half = attrs.get("end_half")
        if end_half is None and self.instance is not None:
            end_half = self.instance.end_half
        start_half = bool(start_half)
        end_half = bool(end_half)

        if leave_start and leave_end and leave_start == leave_end and start_half and end_half:
            raise serializers.ValidationError(
                {
                    "start_half": "Cannot take both start and end half-day on the same date.",
                    "end_half": "Cannot take both start and end half-day on the same date.",
                }
            )

        addr = (attrs.get("addressDuringLeave") or "").strip()
        if self.instance:
            addr = addr or (self.instance.addressDuringLeave or "").strip()
        if lt.requires_address and not addr:
            raise serializers.ValidationError(
                {
                    "addressDuringLeave": f"{lt.name} requires an out-of-station / address during leave.",
                }
            )

        request = self.context.get("request")
        has_doc = bool(attrs.get("leave_pdf_file"))
        if not has_doc and request is not None:
            has_doc = bool(getattr(request, "FILES", None) and request.FILES.get("leave_pdf_file"))
        if self.instance and getattr(self.instance, "leave_pdf", None):
            has_doc = True
        if self.instance and getattr(self.instance, "leave_pdf_file", None):
            has_doc = True
        if lt.requires_proof and not has_doc:
            raise serializers.ValidationError(
                {"leave_pdf_file": f"{lt.name} requires supporting document upload."}
            )

        if not leave_start or not leave_end:
            raise serializers.ValidationError(
                {"leaveStartDate": "Leave start and end dates are required."}
            )

        days = float(
            get_leave_days(leave_start, leave_end, lt, start_half, end_half)
        )
        attrs["applied_leave_days"] = days
        attrs["natureOfLeave"] = _leave_type_to_hr_balance_key(lt)[:40]
        attrs["leave_type"] = lt
        purpose = (attrs.get("purposeOfLeave") or "").strip()
        if len(purpose) > 40:
            attrs["purposeOfLeave"] = purpose[:40]
        attrs["start_half"] = start_half
        attrs["end_half"] = end_half

        applicant = request.user if request and request.user.is_authenticated else None
        if applicant and self.instance is None:
            year = leave_start.year
            try:
                lc = LeavesCount.objects.get(user=applicant, leave_type=lt, year=year)
                if float(lc.remaining_leaves) + 1e-9 < days:
                    raise serializers.ValidationError(
                        {
                            "leave_type": (
                                f"Insufficient {lt.name} balance in leave module for {year}: "
                                f"need {days} day(s), have {lc.remaining_leaves}."
                            )
                        }
                    )
            except LeavesCount.DoesNotExist:
                pass

            extra_info = ExtraInfo.objects.filter(user=applicant).first()
            if extra_info:
                lb = LeaveBalance.objects.filter(employeeId=extra_info).first()
                if lb:
                    bal_key = _leave_type_to_hr_balance_key(lt)
                    fields = LEAVE_TYPE_TO_ALLOTTED_USED.get(bal_key)
                    if fields:
                        allotted_f, used_f = fields
                        allotted = int(getattr(lb, allotted_f, 0) or 0)
                        used = int(getattr(lb, used_f, 0) or 0)
                        need = max(1, int(math.ceil(days)))
                        if allotted - used < need:
                            raise serializers.ValidationError(
                                {
                                    "leave_type": (
                                        f"Insufficient HR leave balance for {lt.name}: "
                                        f"need {need} day(s), available {allotted - used}."
                                    )
                                }
                            )

        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")
        validated_data = _set_approved_by_and_date_on_approval(instance, validated_data, request)

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
        leave_pdf_file = validated_data.get("leave_pdf_file")
        if leave_pdf_file:
            try:
                validated_data["leave_pdf"] = leave_pdf_file.read()
                if hasattr(leave_pdf_file, "seek"):
                    leave_pdf_file.seek(0)
            except Exception:
                pass

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
