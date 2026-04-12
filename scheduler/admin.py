from django.contrib import admin

from .models import Booking, Resource, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "phone")
    list_filter = ("role", "department")
    search_fields = ("user__username", "user__email", "department")


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "resource_type",
        "building",
        "capacity",
        "status",
        "source_name",
        "requires_approval",
    )
    list_filter = ("resource_type", "status", "building", "requires_approval")
    search_fields = ("name", "building", "features", "location_detail")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "resource",
        "user",
        "requested_start",
        "requested_end",
        "status",
        "priority",
    )
    list_filter = ("status", "priority", "resource__resource_type")
    search_fields = ("title", "purpose", "resource__name", "user__username")
