from rest_framework import serializers
from ..models import (
    Award_and_scholarship, Release, Application, Mcm,
    ExtendedScholarshipType, ScholarshipApplication,
    Award, AwardRecipient, MeritList, MeritListEntry
)


class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award_and_scholarship
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):
    award = AwardSerializer(read_only=True)

    class Meta:
        model = Release
        fields = ['id', 'award', 'startdate', 'enddate', 'batch', 'programme']


class ApplicationReadSerializer(serializers.ModelSerializer):
    award_name = serializers.CharField(source='award.award_name', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'award_name', 'status', 'created_at', 'remarks']


class McmCreateSerializer(serializers.Serializer):
    award_id = serializers.IntegerField(required=True)
    brother_name = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    brother_occupation = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    sister_name = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    sister_occupation = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    income_father = serializers.IntegerField(default=0)
    income_mother = serializers.IntegerField(default=0)
    income_other = serializers.IntegerField(default=0)
    father_occ = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    mother_occ = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)


class MedalCreateSerializer(serializers.Serializer):
    award_id = serializers.IntegerField(required=True)
    correspondence_address = serializers.CharField(required=True)
    financial_assistance = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    grand_total = serializers.FloatField(required=True)
    nearest_policestation = serializers.CharField(max_length=100, required=True)
    nearest_railwaystation = serializers.CharField(max_length=100, required=True)
    academic_achievements = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    title_of_project = serializers.CharField(max_length=200, allow_blank=True, allow_null=True, required=False)


class AwardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award_and_scholarship
        fields = ['award_name', 'catalog', 'award_type']

    def validate_award_name(self, value):
        if Award_and_scholarship.objects.filter(award_name__iexact=value).exists():
            raise serializers.ValidationError("Award with this name already exists.")
        return value


class StudentDetailSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    batch = serializers.CharField()
    programme = serializers.CharField()
    category = serializers.CharField()
    cgpa = serializers.FloatField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = serializers.CharField(allow_null=True)
    department = serializers.CharField(allow_null=True)
    eligibility_status = serializers.CharField()
    ineligibility_reasons = serializers.ListField(child=serializers.CharField(), required=False)


class EligibilityCheckSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    scholarship_id = serializers.IntegerField()


class MeritListEntrySerializer(serializers.Serializer):
    student = StudentDetailSerializer()
    rank = serializers.IntegerField()
    cgpa = serializers.FloatField()
    eligible_for_scholarships = serializers.BooleanField()


class BatchStatisticsSerializer(serializers.Serializer):
    batch = serializers.CharField()
    programme = serializers.CharField()
    category = serializers.CharField()
    total_students = serializers.IntegerField()
    applied_scholarships = serializers.IntegerField()
    approved_scholarships = serializers.IntegerField()


class ReleaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = ['award', 'startdate', 'enddate', 'batch', 'programme', 'notif_visible']


# ========== EXTENDED SCHOLARSHIP TYPE SERIALIZERS ==========

class ExtendedScholarshipTypeSerializer(serializers.ModelSerializer):
    applicable_programmes = serializers.SerializerMethodField()
    applicable_batches = serializers.SerializerMethodField()

    class Meta:
        model = ExtendedScholarshipType
        fields = [
            'id', 'name', 'category', 'description', 'amount', 'frequency',
            'eligibility_criteria', 'max_backlogs', 'applicable_categories',
            'minimum_cgpa', 'maximum_income', 'applicable_programmes',
            'applicable_batches', 'is_active', 'created_at'
        ]

    def get_applicable_programmes(self, obj):
        return list(obj.applicable_programmes.values('id', 'name', 'category'))

    def get_applicable_batches(self, obj):
        return list(obj.applicable_batches.values('id', 'name', 'year'))


class ExtendedScholarshipTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtendedScholarshipType
        fields = [
            'name', 'category', 'description', 'amount', 'frequency',
            'eligibility_criteria', 'max_backlogs', 'applicable_categories',
            'minimum_cgpa', 'maximum_income', 'applicable_programmes',
            'applicable_batches', 'is_active'
        ]


# ========== SCHOLARSHIP APPLICATION SERIALIZERS ==========

class ScholarshipApplicationReadSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.id.id', read_only=True)
    student_name = serializers.CharField(source='student.id.user.username', read_only=True)
    scholarship_name = serializers.CharField(source='scholarship_type.name', read_only=True)
    scholarship_category = serializers.CharField(source='scholarship_type.category', read_only=True)
    amount = serializers.DecimalField(source='scholarship_type.amount', max_digits=10, decimal_places=2, read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ScholarshipApplication
        fields = [
            'id', 'student_id', 'student_name', 'scholarship_name', 'scholarship_category',
            'academic_year', 'semester', 'category_at_application', 'application_date',
            'status', 'remarks', 'reviewed_by_name', 'review_date', 'review_remarks',
            'amount', 'amount_approved', 'disbursement_date', 'transaction_reference'
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.user.username
        return None


class ScholarshipApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScholarshipApplication
        fields = ['scholarship_type', 'academic_year', 'semester', 'remarks']

    def validate_academic_year(self, value):
        import re
        if not re.match(r'^\d{4}-\d{2}$', value):
            raise serializers.ValidationError("Academic year must be in format YYYY-YY (e.g. 2024-25)")
        return value

    def validate_semester(self, value):
        if not (1 <= value <= 12):
            raise serializers.ValidationError("Semester must be between 1 and 12.")
        return value


class ScholarshipApplicationApproveSerializer(serializers.Serializer):
    STATUS_CHOICES = ['UNDER_REVIEW', 'APPROVED', 'REJECTED', 'DISBURSED']
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    review_remarks = serializers.CharField(allow_blank=True, required=False, default='')
    amount_approved = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    transaction_reference = serializers.CharField(max_length=100, allow_blank=True, required=False, default='')


# ========== AWARD (GENERAL) SERIALIZERS ==========

class AwardDetailSerializer(serializers.ModelSerializer):
    applicable_programmes = serializers.SerializerMethodField()
    recipient_count = serializers.SerializerMethodField()

    class Meta:
        model = Award
        fields = [
            'id', 'name', 'category', 'description', 'criteria',
            'prize_amount', 'certificate_provided', 'applicable_programmes',
            'is_active', 'created_at', 'recipient_count'
        ]

    def get_applicable_programmes(self, obj):
        return list(obj.applicable_programmes.values('id', 'name', 'category'))

    def get_recipient_count(self, obj):
        return obj.recipients.count()


class AwardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = [
            'name', 'category', 'description', 'criteria',
            'prize_amount', 'certificate_provided', 'applicable_programmes', 'is_active'
        ]


class AwardRecipientSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.id.id', read_only=True)
    student_name = serializers.CharField(source='student.id.user.username', read_only=True)
    award_name = serializers.CharField(source='award.name', read_only=True)
    awarded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AwardRecipient
        fields = [
            'id', 'award', 'award_name', 'student_id', 'student_name',
            'academic_year', 'award_date', 'citation',
            'certificate_issued', 'awarded_by_name'
        ]

    def get_awarded_by_name(self, obj):
        if obj.awarded_by:
            return obj.awarded_by.user.username
        return None


class AwardRecipientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AwardRecipient
        fields = ['award', 'student', 'academic_year', 'award_date', 'citation', 'certificate_issued']

from ..models import McmApplication, SingleParentApplication

class McmApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = McmApplication
        fields = '__all__'
        read_only_fields = ['student', 'submitted_at']

class SingleParentApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleParentApplication
        fields = '__all__'
        read_only_fields = ['student', 'submitted_at']

