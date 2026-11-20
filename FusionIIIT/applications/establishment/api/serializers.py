from rest_framework import serializers
from django.contrib.auth.models import User
from applications.establishment.models import (
    Cpda_application,
    Cpda_tracking,
    CpdaBalance,
    Cpda_bill,
    Ltc_application,
    Ltc_tracking,
    Ltc_eligible_user,
    Ltc_availed,
    Ltc_to_avail,
    Dependent,
    Appraisal,
    CoursesInstructed,
    NewCoursesOffered,
    NewCourseMaterial,
    ThesisResearchSupervision,
    SponsoredProjects,
    AppraisalRequest,
)


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


# ---------------------------------------------------------------------------
# CPDA Serializers
# ---------------------------------------------------------------------------
class CpdaBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cpda_bill
        fields = '__all__'


class CpdaTrackingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.ReadOnlyField(source='reviewer_id.username')

    class Meta:
        model = Cpda_tracking
        fields = '__all__'


class CpdaApplicationSerializer(serializers.ModelSerializer):
    applicant_details = UserSummarySerializer(source='applicant', read_only=True)
    tracking_info = CpdaTrackingSerializer(read_only=True)

    class Meta:
        model = Cpda_application
        fields = '__all__'
        read_only_fields = ['status', 'request_timestamp', 'adjustment_timestamp']


class CpdaBalanceSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = CpdaBalance
        fields = ['user', 'username', 'cpda_balance']


# ---------------------------------------------------------------------------
# LTC Serializers
# ---------------------------------------------------------------------------
class DependentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependent
        fields = '__all__'


class LtcAvailedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ltc_availed
        fields = '__all__'


class LtcToAvailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ltc_to_avail
        fields = '__all__'


class LtcTrackingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.ReadOnlyField(source='reviewer_id.username')

    class Meta:
        model = Ltc_tracking
        fields = '__all__'


class LtcEligibleUserSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    hometown_ltc_remaining = serializers.ReadOnlyField()
    elsewhere_ltc_remaining = serializers.ReadOnlyField()
    total_ltc_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Ltc_eligible_user
        fields = '__all__'


class LtcApplicationSerializer(serializers.ModelSerializer):
    applicant_details = UserSummarySerializer(source='applicant', read_only=True)
    tracking_info = LtcTrackingSerializer(read_only=True)
    dependents_list = DependentSerializer(source='Dependent', many=True, read_only=True)
    to_avail_list = LtcToAvailSerializer(source='ltcToAvail', many=True, read_only=True)
    availed_list = LtcAvailedSerializer(source='ltcAvailed', many=True, read_only=True)

    class Meta:
        model = Ltc_application
        fields = '__all__'
        read_only_fields = ['status', 'request_timestamp', 'review_timestamp']


# ---------------------------------------------------------------------------
# Appraisal Serializers
# ---------------------------------------------------------------------------
class CoursesInstructedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursesInstructed
        fields = '__all__'


class NewCoursesOfferedSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewCoursesOffered
        fields = '__all__'


class NewCourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewCourseMaterial
        fields = '__all__'


class ThesisResearchSupervisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThesisResearchSupervision
        fields = '__all__'


class SponsoredProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsoredProjects
        fields = '__all__'


class AppraisalRequestSerializer(serializers.ModelSerializer):
    hod_name = serializers.ReadOnlyField(source='hod.username')
    director_name = serializers.ReadOnlyField(source='director.username')

    class Meta:
        model = AppraisalRequest
        fields = '__all__'


class AppraisalSerializer(serializers.ModelSerializer):
    applicant_details = UserSummarySerializer(source='applicant', read_only=True)
    applicant_courses = CoursesInstructedSerializer(many=True, read_only=True)
    applicants_offered_new_courses = NewCoursesOfferedSerializer(many=True, read_only=True)
    applicants_supervised_stud = ThesisResearchSupervisionSerializer(many=True, read_only=True)
    applicant_sponsored_projects = SponsoredProjectsSerializer(many=True, read_only=True)
    appraisal_tracking = AppraisalRequestSerializer(many=True, read_only=True)

    class Meta:
        model = Appraisal
        fields = '__all__'
        read_only_fields = ['status', 'timestamp']
