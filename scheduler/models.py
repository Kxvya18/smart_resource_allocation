from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

ACCESS_START_TIME = time(9, 0)
ACCESS_END_TIME = time(21, 0)


class UserProfile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        STAFF = "staff", "Staff"
        ADMIN = "admin", "Admin"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    department = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def can_manage_resources(self):
        return self.role in {self.Role.STAFF, self.Role.ADMIN} or self.user.is_staff


class Resource(models.Model):
    class ResourceType(models.TextChoices):
        ROOM = "room", "Room"
        LAB = "lab", "Lab"
        EQUIPMENT = "equipment", "Equipment"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        MAINTENANCE = "maintenance", "Maintenance"
        INACTIVE = "inactive", "Inactive"

    name = models.CharField(max_length=150, unique=True)
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    building = models.CharField(max_length=120)
    floor = models.CharField(max_length=30, blank=True)
    location_detail = models.CharField(max_length=150, blank=True)
    capacity = models.PositiveIntegerField(default=1)
    features = models.TextField(blank=True)
    description = models.TextField(blank=True)
    source_name = models.CharField(max_length=150, blank=True)
    source_url = models.URLField(blank=True)
    hourly_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    requires_approval = models.BooleanField(default=True)
    available_from = models.TimeField(default=ACCESS_START_TIME)
    available_until = models.TimeField(default=ACCESS_END_TIME)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resource_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_resource_type_display()})"

    def clean(self):
        errors = {}
        if self.available_from < ACCESS_START_TIME or self.available_until > ACCESS_END_TIME:
            errors["available_from"] = "Resource access hours must stay between 09:00 and 21:00."
        if self.available_until <= self.available_from:
            errors["available_until"] = "Available until must be later than available from."
        if errors:
            raise ValidationError(errors)


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="bookings")
    title = models.CharField(max_length=150)
    purpose = models.TextField()
    attendees = models.PositiveIntegerField(default=1)
    requested_start = models.DateTimeField()
    requested_end = models.DateTimeField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approval_notes = models.CharField(max_length=255, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_bookings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["requested_start", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.resource.name}"

    @property
    def duration_hours(self):
        delta = self.requested_end - self.requested_start
        return round(delta.total_seconds() / 3600, 2)

    @property
    def can_be_modified(self):
        return self.status in {self.Status.PENDING, self.Status.APPROVED}

    def clean(self):
        errors = {}
        start_time = self.requested_start
        end_time = self.requested_end

        # Let field-level validation handle missing datetimes before any
        # timezone conversion or ordering checks.
        if start_time is None or end_time is None:
            return

        if timezone.is_aware(start_time):
            start_time = timezone.localtime(start_time)
        if timezone.is_aware(end_time):
            end_time = timezone.localtime(end_time)

        current_time = timezone.localtime()

        if self.requested_end <= self.requested_start:
            errors["requested_end"] = "End time must be after the start time."

        enforce_future_only = self.status in {self.Status.PENDING, self.Status.APPROVED}

        if enforce_future_only and start_time < current_time:
            errors["requested_start"] = "Past dates and times are not allowed for bookings."

        if enforce_future_only and end_time < current_time:
            errors["requested_end"] = "Past dates and times are not allowed for bookings."

        if start_time.date() != end_time.date():
            errors["requested_end"] = "Bookings must start and end on the same day."

        if (
            start_time.time() < ACCESS_START_TIME
            or end_time.time() > ACCESS_END_TIME
        ):
            errors["requested_start"] = "Bookings are allowed only between 09:00 AM and 09:00 PM."

        if self.resource_id:
            if self.resource.status != Resource.Status.ACTIVE:
                errors["resource"] = "This resource is not available for booking."

            if self.attendees > self.resource.capacity:
                errors["attendees"] = "Attendees exceed the resource capacity."

            if (
                start_time.time() < self.resource.available_from
                or end_time.time() > self.resource.available_until
            ):
                errors["requested_start"] = "Booking must fit within the resource availability window."

        overlapping = Booking.objects.filter(
            resource=self.resource,
            status__in=[self.Status.PENDING, self.Status.APPROVED],
            requested_start__lt=self.requested_end,
            requested_end__gt=self.requested_start,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            errors["resource"] = "This slot overlaps with an existing booking."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


def round_to_next_half_hour(value):
    rounded = value.replace(second=0, microsecond=0)
    if rounded.minute == 0 or rounded.minute == 30:
        return rounded
    if rounded.minute < 30:
        return rounded.replace(minute=30)
    return (rounded + timedelta(hours=1)).replace(minute=0)


def booking_slot_is_available(resource, start_dt, end_dt, exclude_booking_id=None):
    if start_dt.time() < ACCESS_START_TIME or end_dt.time() > ACCESS_END_TIME:
        return False
    if start_dt.time() < resource.available_from or end_dt.time() > resource.available_until:
        return False
    overlaps = Booking.objects.filter(
        resource=resource,
        status__in=[Booking.Status.PENDING, Booking.Status.APPROVED],
        requested_start__lt=end_dt,
        requested_end__gt=start_dt,
    )
    if exclude_booking_id:
        overlaps = overlaps.exclude(pk=exclude_booking_id)
    return not overlaps.exists()


def suggest_next_slots(resource, requested_start, requested_end, exclude_booking_id=None, limit=3):
    duration = max(requested_end - requested_start, timedelta(hours=1))
    search_start = max(round_to_next_half_hour(timezone.localtime()), requested_start)
    if search_start.time() < ACCESS_START_TIME:
        search_start = timezone.make_aware(datetime.combine(search_start.date(), ACCESS_START_TIME))
    suggestions = []

    for day_offset in range(0, 14):
        day = search_start.date() + timedelta(days=day_offset)
        day_start = max(ACCESS_START_TIME, resource.available_from)
        day_end = min(ACCESS_END_TIME, resource.available_until)
        candidate = timezone.make_aware(datetime.combine(day, day_start))
        if day == search_start.date() and candidate < search_start:
            candidate = round_to_next_half_hour(search_start)

        latest_start = timezone.make_aware(datetime.combine(day, day_end)) - duration
        while candidate <= latest_start:
            candidate_end = candidate + duration
            if booking_slot_is_available(resource, candidate, candidate_end, exclude_booking_id):
                suggestions.append(
                    {
                        "start": timezone.localtime(candidate).strftime("%d %b %Y, %I:%M %p"),
                        "end": timezone.localtime(candidate_end).strftime("%I:%M %p"),
                        "start_value": timezone.localtime(candidate).strftime("%Y-%m-%dT%H:%M"),
                        "end_value": timezone.localtime(candidate_end).strftime("%Y-%m-%dT%H:%M"),
                    }
                )
                if len(suggestions) >= limit:
                    return suggestions
            candidate += timedelta(minutes=30)

    return suggestions


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)
