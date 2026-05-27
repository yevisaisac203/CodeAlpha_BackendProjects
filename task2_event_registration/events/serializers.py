from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from .models import Category, Event, EventTag, Registration


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class EventTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTag
        fields = ["id", "name", "slug"]


class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "bio", "profile_picture"]
        read_only_fields = fields


class EventListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    organizer = OrganizerSerializer(read_only=True)
    is_free = serializers.ReadOnlyField()
    available_spots = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "organizer",
            "banner_image",
            "start_datetime",
            "end_datetime",
            "city",
            "country",
            "is_virtual",
            "max_capacity",
            "ticket_price",
            "is_free",
            "status",
            "available_spots",
            "is_full",
        ]


class EventDetailSerializer(EventListSerializer):
    tags = EventTagSerializer(many=True, read_only=True)

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + [
            "description",
            "venue_name",
            "venue_address",
            "meeting_link",
            "tags",
            "created_at",
            "updated_at",
        ]


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    organizer = OrganizerSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "category",
            "organizer",
            "banner_image",
            "start_datetime",
            "end_datetime",
            "venue_name",
            "venue_address",
            "city",
            "country",
            "is_virtual",
            "meeting_link",
            "max_capacity",
            "ticket_price",
            "status",
            "tags",
        ]
        read_only_fields = ["id", "organizer"]

    def validate(self, attrs):
        start_datetime = attrs.get("start_datetime", getattr(self.instance, "start_datetime", None))
        end_datetime = attrs.get("end_datetime", getattr(self.instance, "end_datetime", None))

        if start_datetime and end_datetime and end_datetime <= start_datetime:
            raise serializers.ValidationError(
                {"end_datetime": "End datetime must be after start datetime."}
            )

        if self.instance is None and start_datetime and start_datetime < timezone.now():
            raise serializers.ValidationError(
                {"start_datetime": "Start datetime cannot be in the past."}
            )

        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    event = EventListSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = [
            "id",
            "event",
            "status",
            "ticket_code",
            "registered_at",
            "check_in_time",
            "notes",
        ]
        read_only_fields = [
            "id",
            "event",
            "status",
            "ticket_code",
            "registered_at",
            "check_in_time",
        ]


class RegistrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ["notes"]
