from rest_framework import serializers

from .models import Booking, Resource


class ResourceSerializer(serializers.ModelSerializer):
    resource_type_label = serializers.CharField(source="get_resource_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Resource
        fields = [
            "id",
            "name",
            "resource_type",
            "resource_type_label",
            "building",
            "floor",
            "location_detail",
            "capacity",
            "features",
            "description",
            "source_name",
            "source_url",
            "hourly_cost",
            "requires_approval",
            "available_from",
            "available_until",
            "status",
            "status_label",
        ]


class BookingSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source="resource.name", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "title",
            "purpose",
            "resource",
            "resource_name",
            "user",
            "user_name",
            "attendees",
            "requested_start",
            "requested_end",
            "priority",
            "priority_label",
            "status",
            "status_label",
            "approval_notes",
            "created_at",
        ]
        read_only_fields = ["user", "approval_notes", "created_at"]
