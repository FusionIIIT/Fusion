from rest_framework import serializers

from applications.gymkhana.models import (
    ClubCategory,
    Club_info,
    Club_member,
    Event_info,
    Session_info,
    Venue,
)


class ClubSerializer(serializers.ModelSerializer):
    co_ordinator = serializers.CharField(source="co_ordinator.id.id", read_only=True)
    co_coordinator = serializers.CharField(source="co_coordinator.id.id", read_only=True)
    faculty_incharge = serializers.CharField(source="faculty_incharge.id.id", read_only=True)

    class Meta:
        model = Club_info
        fields = (
            "club_name",
            "club_website",
            "category",
            "co_ordinator",
            "co_coordinator",
            "faculty_incharge",
            "description",
            "alloted_budget",
            "spent_budget",
            "avail_budget",
            "status",
            "head_changed_on",
            "created_on",
        )


class ClubCreateSerializer(serializers.Serializer):
    club_name = serializers.CharField(max_length=50)
    category = serializers.ChoiceField(choices=ClubCategory.choices)
    co_ordinator = serializers.CharField(max_length=20)
    co_coordinator = serializers.CharField(max_length=20)
    faculty_incharge = serializers.CharField(max_length=256)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ClubMemberSerializer(serializers.ModelSerializer):
    member_id = serializers.CharField(source="member.id.id", read_only=True)
    club_name = serializers.CharField(source="club.club_name", read_only=True)

    class Meta:
        model = Club_member
        fields = ("id", "member_id", "club_name", "description", "status", "remarks")


class ClubMemberCreateSerializer(serializers.Serializer):
    member_id = serializers.CharField(max_length=20)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class EventSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.club_name", read_only=True)

    class Meta:
        model = Event_info
        fields = (
            "id",
            "club_name",
            "event_name",
            "incharge",
            "venue",
            "date",
            "start_time",
            "end_time",
            "event_poster",
            "details",
            "status",
        )


class EventCreateSerializer(serializers.ModelSerializer):
    venue = serializers.ChoiceField(choices=Venue.choices)

    class Meta:
        model = Event_info
        fields = (
            "event_name",
            "incharge",
            "venue",
            "date",
            "start_time",
            "end_time",
            "event_poster",
            "details",
        )


class SessionSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.club_name", read_only=True)

    class Meta:
        model = Session_info
        fields = (
            "id",
            "club_name",
            "venue",
            "date",
            "start_time",
            "end_time",
            "session_poster",
            "details",
            "status",
        )


class SessionCreateSerializer(serializers.ModelSerializer):
    venue = serializers.ChoiceField(choices=Venue.choices)

    class Meta:
        model = Session_info
        fields = (
            "venue",
            "date",
            "start_time",
            "end_time",
            "session_poster",
            "details",
        )
