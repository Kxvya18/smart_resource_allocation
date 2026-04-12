from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.utils import timezone

from .models import ACCESS_END_TIME, ACCESS_START_TIME, Booking, Resource


class BookingValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345")
        self.resource = Resource.objects.create(
            name="Testing Lab",
            resource_type=Resource.ResourceType.LAB,
            building="Block T",
            capacity=30,
            features="GPU workstations",
            description="Testing resource",
        )

    def test_rejects_overlapping_bookings(self):
        start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=1), time(10, 0)))
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            title="Existing booking",
            purpose="Session A",
            attendees=20,
            requested_start=start,
            requested_end=start + timedelta(hours=2),
        )

        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user,
                resource=self.resource,
                title="Overlapping booking",
                purpose="Session B",
                attendees=15,
                requested_start=start + timedelta(minutes=30),
                requested_end=start + timedelta(hours=3),
            )

    def test_rejects_excess_attendees(self):
        start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=2), time(11, 0)))
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user,
                resource=self.resource,
                title="Overflow booking",
                purpose="Too many attendees",
                attendees=50,
                requested_start=start,
                requested_end=start + timedelta(hours=1),
            )

    def test_existing_booking_can_be_saved_after_reload_from_database(self):
        start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=1), time(10, 0)))
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            title="Persisted booking",
            purpose="Round-trip validation",
            attendees=20,
            requested_start=start,
            requested_end=start + timedelta(hours=2),
            status=Booking.Status.APPROVED,
        )

        reloaded = Booking.objects.get(pk=booking.pk)
        reloaded.purpose = "Updated after reload"
        reloaded.save()

    def test_rejects_past_bookings(self):
        start = timezone.localtime() - timedelta(hours=2)
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user,
                resource=self.resource,
                title="Past booking",
                purpose="Should fail",
                attendees=10,
                requested_start=start,
                requested_end=start + timedelta(hours=1),
            )

    def test_rejects_outside_global_access_window(self):
        start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=1), time(8, 30)))
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user,
                resource=self.resource,
                title="Early booking",
                purpose="Outside access window",
                attendees=10,
                requested_start=start,
                requested_end=start + timedelta(hours=1),
            )


class DashboardApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="dashboard_user", password="pass12345")
        self.resource = Resource.objects.create(
            name="Dashboard Seminar Hall",
            resource_type=Resource.ResourceType.ROOM,
            building="Main Block",
            capacity=60,
            features="Projector and microphones",
            description="Dashboard test room",
        )
        start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=1), time(10, 0)))
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            title="Dashboard booking",
            purpose="Analytics test",
            attendees=25,
            requested_start=start,
            requested_end=start + timedelta(hours=2),
            status=Booking.Status.APPROVED,
        )

    def test_dashboard_summary_returns_expected_sections(self):
        self.client.login(username="dashboard_user", password="pass12345")
        response = self.client.get("/api/dashboard-summary/?window=7")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("totals", payload)
        self.assertIn("daily_bookings", payload)
        self.assertIn("top_resources", payload)
        self.assertIn("today_schedule", payload)
        self.assertEqual(payload["window_days"], 7)


class AvailabilityEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="availability_user", password="pass12345")
        self.resource = Resource.objects.create(
            name="Availability Lab",
            resource_type=Resource.ResourceType.LAB,
            building="Block A",
            capacity=40,
            available_from=ACCESS_START_TIME,
            available_until=ACCESS_END_TIME,
            features="Computers",
            description="Availability test lab",
        )
        self.start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=1), time(10, 0)))
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            title="Booked slot",
            purpose="Conflict generation",
            attendees=20,
            requested_start=self.start,
            requested_end=self.start + timedelta(hours=2),
            status=Booking.Status.APPROVED,
        )

    def test_availability_endpoint_reports_no_availability_for_clash(self):
        response = self.client.get(
            "/ajax/availability/",
            {
                "resource": self.resource.id,
                "start": self.start.strftime("%Y-%m-%dT%H:%M"),
                "end": (self.start + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["available"])
        self.assertIn("No availability", payload["message"])
        self.assertTrue(payload["suggestions"])
