import re

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from rest_framework import serializers

from ..models import Budget, Club, ClubMember, Event, GalleryItem, Poll, PollOption
from ..selectors import get_user_role, get_user_roll_no


TEXT_ONLY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s.'-]*$")
TEXT_WITH_SYMBOLS_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9\s.,'()&/-]*$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
url_validator = URLValidator()


def validate_text(value, label, *, allow_numbers=True, min_length=1, required=True):
    trimmed = str(value or "").strip()
    if not trimmed:
        if required:
            raise serializers.ValidationError(f"{label} is required.")
        return ""
    if len(trimmed) < min_length:
        raise serializers.ValidationError(f"{label} must be at least {min_length} characters long.")
    if not TEXT_WITH_SYMBOLS_PATTERN.match(trimmed):
        raise serializers.ValidationError(f"{label} contains invalid characters.")
    if not allow_numbers and any(char.isdigit() for char in trimmed):
        raise serializers.ValidationError(f"{label} should contain text only.")
    if allow_numbers and trimmed.isdigit():
        raise serializers.ValidationError(f"{label} cannot contain numbers only.")
    return trimmed


def validate_text_only(value, label, *, required=True):
    trimmed = str(value or "").strip()
    if not trimmed:
        if required:
            raise serializers.ValidationError(f"{label} is required.")
        return ""
    if not TEXT_ONLY_PATTERN.match(trimmed):
        raise serializers.ValidationError(f"{label} should contain text only.")
    return trimmed


def validate_identifier(value, label):
    trimmed = str(value or "").strip()
    if not trimmed:
        raise serializers.ValidationError(f"{label} is required.")
    if not USERNAME_PATTERN.match(trimmed):
        raise serializers.ValidationError(f"{label} should contain only letters and numbers without spaces or symbols.")
    return trimmed


def validate_url_or_filename(value, label):
    trimmed = str(value or "").strip()
    if not trimmed:
        raise serializers.ValidationError(f"{label} is required.")
    if trimmed.isdigit():
        raise serializers.ValidationError(f"{label} cannot be numbers only.")
    if trimmed.startswith(("http://", "https://")):
        try:
            url_validator(trimmed)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(f"{label} must be a valid URL.") from exc
    return trimmed


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    roll_no = serializers.SerializerMethodField()
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    role = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)

    def get_roll_no(self, obj):
        return get_user_roll_no(obj)

    def get_role(self, obj):
        return get_user_role(obj)


class ClubSerializer(serializers.ModelSerializer):
    coordinator_name = serializers.SerializerMethodField()
    co_coordinator_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    avail_budget = serializers.ReadOnlyField()

    class Meta:
        model = Club
        fields = [
            "id",
            "name",
            "category",
            "description",
            "coordinator",
            "coordinator_name",
            "co_coordinator",
            "co_coordinator_name",
            "faculty_incharge",
            "status",
            "alloted_budget",
            "spent_budget",
            "avail_budget",
            "member_count",
            "activity_calendar",
            "created_at",
        ]

    def get_coordinator_name(self, obj):
        return obj.coordinator.get_full_name() if obj.coordinator else ""

    def get_co_coordinator_name(self, obj):
        return obj.co_coordinator.get_full_name() if obj.co_coordinator else ""

    def get_member_count(self, obj):
        return obj.members.filter(status__in=["member", "coordinator", "Co-cordinator"]).count()


class ClubWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ["name", "category", "description", "coordinator", "co_coordinator", "faculty_incharge", "alloted_budget", "activity_calendar"]

    def validate_name(self, value):
        return validate_text(value, "Club name", allow_numbers=True, min_length=3)

    def validate_description(self, value):
        return validate_text(value, "Description", allow_numbers=True, min_length=3, required=False)

    def validate_faculty_incharge(self, value):
        return validate_text_only(value, "Faculty incharge", required=False)

    def validate_activity_calendar(self, value):
        return validate_url_or_filename(value, "Activity calendar") if str(value or "").strip() else ""


class ClubMemberSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_roll = serializers.SerializerMethodField()
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_category = serializers.CharField(source="club.category", read_only=True)

    class Meta:
        model = ClubMember
        fields = ["id", "student", "student_name", "student_roll", "club", "club_name", "club_category", "status", "description", "remarks", "applied_at"]
        read_only_fields = ["status", "remarks", "applied_at"]

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    def get_student_roll(self, obj):
        return get_user_roll_no(obj.student)

    def validate_description(self, value):
        return validate_text(value, "Join request", allow_numbers=True, min_length=10, required=False)


class EventSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)

    class Meta:
        model = Event
        fields = ["id", "club", "club_name", "name", "venue", "date", "start_time", "end_time", "incharge", "details", "status", "created_at"]
        read_only_fields = ["status", "created_at"]

    def validate_name(self, value):
        return validate_text(value, "Event name", allow_numbers=True, min_length=3)

    def validate_incharge(self, value):
        return validate_text_only(value, "Incharge")

    def validate_details(self, value):
        return validate_text(value, "Details", allow_numbers=True, min_length=3, required=False)

    def validate(self, attrs):
        start_time = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end_time = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return attrs


class BudgetSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "club", "club_name", "budget_type", "budget_for", "amount", "description", "status", "remarks", "created_at"]
        read_only_fields = ["status", "remarks", "created_at"]

    def validate_budget_for(self, value):
        return validate_text(value, "Budget for", allow_numbers=True, min_length=3)

    def validate_description(self, value):
        return validate_text(value, "Description", allow_numbers=True, min_length=3, required=False)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = ["id", "text", "votes", "order"]


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    has_voted = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ["id", "title", "description", "pub_date", "exp_date", "created_by", "created_by_name", "is_active", "options", "has_voted"]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ""

    def get_has_voted(self, obj):
        request = self.context.get("request")
        return obj.votes.filter(voter=request.user).exists() if request and request.user.is_authenticated else False


class PollCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, default="")
    options = serializers.ListField(child=serializers.CharField(max_length=200), min_length=2)
    pub_date = serializers.DateField()
    exp_date = serializers.DateField()

    def validate_title(self, value):
        return validate_text(value, "Title", allow_numbers=True, min_length=3)

    def validate_description(self, value):
        return validate_text(value, "Description", allow_numbers=True, min_length=3, required=False)

    def validate_options(self, value):
        return [validate_text(option, "Each option", allow_numbers=True, min_length=1) for option in value]

    def validate(self, attrs):
        if attrs["exp_date"] <= attrs["pub_date"]:
            raise serializers.ValidationError({"exp_date": "Expiry date must be after publish date."})
        return attrs

    def create(self, validated_data):
        options = validated_data.pop("options")
        poll = Poll.objects.create(**validated_data)
        for index, text in enumerate(options):
            PollOption.objects.create(poll=poll, text=text, order=index)
        return poll


class GalleryItemSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    club_name = serializers.SerializerMethodField()

    class Meta:
        model = GalleryItem
        fields = ["id", "club", "club_name", "event", "caption", "image_url", "uploaded_by", "uploaded_by_name", "uploaded_at"]
        read_only_fields = ["uploaded_at"]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else ""

    def get_club_name(self, obj):
        return obj.club.name if obj.club else ""

    def validate_caption(self, value):
        return validate_text(value, "Caption", allow_numbers=True, min_length=3, required=False)
