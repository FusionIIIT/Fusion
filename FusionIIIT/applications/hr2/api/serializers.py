from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from applications.hr2 import selectors as hr2_selectors
from ..models import (
    Employee, ServiceHistory, LeaveType, EmployeeLeaveBalance, LeaveApplicationNew,
    AppraisalPeriod, PerformanceAppraisalNew, TrainingProgram, TrainingNomination,
    PromotionApplication, EmployeeAttendance, FacultyWorkload,
    EducationalQualification, ProfessionalQualification, PreviousExperience
)

class EmployeeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['id']

class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(write_only=True, required=False)
    nominee_employee_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    nominee_employee_name = serializers.SerializerMethodField(read_only=True)
    is_owner = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LeaveApplicationNew
        fields = '__all__'
        read_only_fields = [
            'id',
            'applied_date',
            'approval_status',
            'cancel_status',
            'cancel_requested_at',
            'cancel_decided_at',
            'cancel_requested_by_role',
            'cancel_current_approver_role',
            'cancel_reason',
            'cancel_decision_remarks',
            'extension_status',
            'extension_requested_at',
            'extension_decided_at',
            'extension_requested_by_role',
            'extension_current_approver_role',
            'extension_reason',
            'extension_new_end_date',
            'extension_new_total_days',
            'extension_decision_remarks',
            'resumption_status',
            'resumption_date',
            'resumption_reason',
            'resumption_submitted_at',
            'resumption_decided_at',
            'resumption_current_approver_role',
            'resumption_decision_remarks',
        ]
        extra_kwargs = {
            'employee': {'required': False},
        }

    def create(self, validated_data):
        # Remove serializer-only fields before model create.
        validated_data.pop('nominee_employee_id', None)
        validated_data.pop('employee_id', None)
        return super().create(validated_data)

    def validate(self, data):
        leave_type_name = data.get('leave_type')
        if not leave_type_name and self.instance is not None:
            leave_type_name = self.instance.leave_type
        station_leave_value = None
        if 'station_leave' in data:
            station_leave_value = data.get('station_leave')
        elif self.instance is not None:
            station_leave_value = self.instance.station_leave
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        is_half_day = data.get('is_half_day', False)
        half_day_slot = data.get('half_day_slot')
        if start_date:
            today = timezone.now().date()
            if start_date < today:
                raise serializers.ValidationError({'start_date': 'Start date cannot be in the past.'})
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before or equal to end date.")
        if start_date and end_date and data.get('total_days') is not None:
            if is_half_day:
                expected_days = Decimal('0.5')
            else:
                expected_days = Decimal((end_date - start_date).days + 1)
            try:
                provided_days = Decimal(str(data.get('total_days')))
            except (TypeError, ValueError):
                raise serializers.ValidationError({'total_days': 'Total days must be a valid number.'})
            if provided_days != expected_days:
                raise serializers.ValidationError({'total_days': f'Total days should be {expected_days} based on selected dates.'})
        if is_half_day:
            if leave_type_name != 'Casual':
                raise serializers.ValidationError({'is_half_day': 'Half-day is only allowed for Casual leave.'})
            if not half_day_slot:
                raise serializers.ValidationError({'half_day_slot': 'Select AM or PM for half-day leave.'})
            if start_date and end_date and start_date != end_date:
                raise serializers.ValidationError({'end_date': 'Half-day leave must be for a single day.'})
        else:
            if half_day_slot:
                raise serializers.ValidationError({'half_day_slot': 'Half-day slot is only for half-day leave.'})
        if start_date and end_date:
            employee = None
            request = self.context.get('request') if hasattr(self, 'context') else None
            if request and hasattr(request, 'user'):
                employee = hr2_selectors.get_employee_for_user(request.user)
            if employee is None:
                employee_id = data.get('employee_id')
                if employee_id:
                    employee = hr2_selectors.get_employee_by_id_optional(employee_id)
            if employee is not None:
                overlapping = hr2_selectors.has_overlapping_leave(
                    employee=employee,
                    start_date=start_date,
                    end_date=end_date,
                    exclude_id=self.instance.id if self.instance is not None else None,
                )
                if self.instance is not None:
                    overlapping = overlapping.exclude(id=self.instance.id)
                if overlapping.exists():
                    overlap_found = False
                    for existing in overlapping:
                        if not is_half_day or not existing.is_half_day:
                            overlap_found = True
                            break
                        if start_date != end_date:
                            overlap_found = True
                            break
                        if existing.start_date != existing.end_date:
                            overlap_found = True
                            break
                        if existing.start_date != start_date:
                            continue
                        if existing.half_day_slot == half_day_slot:
                            overlap_found = True
                            break
                    if overlap_found:
                        raise serializers.ValidationError({'start_date': 'Leave dates overlap with an existing leave request.'})
                leave_type_name = data.get('leave_type')
                if leave_type_name and data.get('total_days') is not None:
                    leave_type = hr2_selectors.get_leave_type_by_name(leave_type_name)
                    if leave_type:
                        year = start_date.year
                        balance = hr2_selectors.get_leave_balance_for_employee_year(
                            employee=employee,
                            leave_type=leave_type,
                            year=year,
                        )
                        if balance is None:
                            balance = hr2_selectors.get_latest_leave_balance_for_employee(
                                employee=employee,
                                leave_type=leave_type,
                            )
                        if balance is None:
                            raise serializers.ValidationError({'leave_type': 'Leave balance not found for this leave type.'})
                        if Decimal(str(data.get('total_days'))) > (balance.current_balance or 0):
                            raise serializers.ValidationError({'total_days': 'Requested days exceed remaining leave balance.'})
        nominee_id = (data.get('nominee_employee_id') or '').strip()
        if nominee_id:
            nominee = hr2_selectors.get_employee_by_id_optional(nominee_id)
            if not nominee:
                raise serializers.ValidationError({'nominee_employee_id': 'Employee not found.'})
            if employee is not None and str(employee.id) == nominee_id:
                raise serializers.ValidationError({'nominee_employee_id': 'Nominee must be different from the applicant.'})
            if start_date and end_date:
                nominee_overlapping = hr2_selectors.has_overlapping_leave(
                    employee=nominee,
                    start_date=start_date,
                    end_date=end_date,
                ).exists()
                if nominee_overlapping:
                    raise serializers.ValidationError({'nominee_employee_id': 'Nominee has overlapping pending or approved leave.'})
        is_cl_rh_leave = leave_type_name in ['Casual', 'Restricted']
        is_station_only = is_cl_rh_leave and station_leave_value == 'NOT_REQUIRED'
        is_vacation_leave = leave_type_name == 'Vacation'
        if is_cl_rh_leave and not station_leave_value:
            raise serializers.ValidationError({'station_leave': 'Select a station leave option for this leave type.'})
        if self.instance is None and not is_station_only and not is_vacation_leave and not nominee_id:
            raise serializers.ValidationError({'nominee_employee_id': 'Nominee Employee ID is required for this leave type.'})
        return data

    def get_nominee_employee_name(self, obj):
        if not obj.handover_to:
            return ''
        nominee = hr2_selectors.get_employee_by_id_optional(obj.handover_to)
        if not nominee:
            return ''
        return nominee.user.get_full_name() or nominee.user.username

    def get_is_owner(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        if not request or not hasattr(request, 'user'):
            return False
        try:
            return obj.employee == request.user.extrainfo
        except ExtraInfo.DoesNotExist:
            return False

class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)

    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'

class PerformanceAppraisalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceAppraisalNew
        fields = '__all__'

class TrainingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = '__all__'

class TrainingNominationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingNomination
        fields = '__all__'

class PromotionApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionApplication
        fields = '__all__'

class EmployeeAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttendance
        fields = '__all__'

class FacultyWorkloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacultyWorkload
        fields = '__all__'

class AppraisalPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppraisalPeriod
        fields = '__all__'

from ..models import LTCApplicationNew, CPDAAdvanceNew, CPDAReimbursementNew, AppraisalFormNew

class LTCApplicationSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = LTCApplicationNew
        fields = '__all__'
        read_only_fields = ['id', 'applied_date', 'approval_status']
        extra_kwargs = {
            'employee': {'required': False},
        }

    def validate(self, data):
        travel_start_date = data.get('travel_start_date')
        travel_end_date = data.get('travel_end_date')
        if travel_start_date and travel_end_date and travel_start_date > travel_end_date:
            raise serializers.ValidationError({'travel_end_date': 'Travel end date must be on or after start date.'})

        previous_ltc_used = data.get('previous_ltc_used')
        last_ltc_date = data.get('last_ltc_date')
        if previous_ltc_used and not last_ltc_date:
            raise serializers.ValidationError({'last_ltc_date': 'Last LTC date is required when previous LTC was used.'})

        numeric_fields = ['ticket_cost', 'accommodation_cost', 'other_expenses', 'total_amount_claimed']
        for field in numeric_fields:
            value = data.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: 'Amount must be a non-negative number.'})
        return data

class CPDAAdvanceSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CPDAAdvanceNew
        fields = '__all__'
        read_only_fields = ['id', 'applied_date', 'approval_status']
        extra_kwargs = {
            'employee': {'required': False},
        }

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({'end_date': 'End date must be on or after start date.'})

        numeric_fields = ['registration_fee', 'travel_expense', 'accommodation_expense', 'other_expenses', 'total_amount']
        for field in numeric_fields:
            value = data.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: 'Amount must be a non-negative number.'})
        return data

class CPDAReimbursementSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CPDAReimbursementNew
        fields = '__all__'
        read_only_fields = ['id', 'applied_date', 'approval_status']

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({'end_date': 'End date must be on or after start date.'})

        numeric_fields = ['registration_fee', 'travel_expense', 'accommodation_expense', 'other_expenses', 'total_amount']
        for field in numeric_fields:
            value = data.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: 'Amount must be a non-negative number.'})
        return data

class AppraisalFormSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = AppraisalFormNew
        fields = '__all__'
        read_only_fields = [
            'id',
            'status',
            'submitted_at',
            'assigned_reviewer_role',
            'assigned_reviewer',
            'assigned_by',
            'assigned_at',
        ]
        extra_kwargs = {
            'employee': {'required': False},
        }

    def validate(self, data):
        required_fields = [
            'employee_name',
            'department',
            'designation',
            'appraisal_year',
            'self_summary',
            'key_responsibilities',
            'achievements',
            'goals_achieved',
            'future_goals',
        ]
        errors = {}
        for field in required_fields:
            if not str(data.get(field, '')).strip():
                errors[field] = 'This field is required.'
        if errors:
            raise serializers.ValidationError(errors)
        return data