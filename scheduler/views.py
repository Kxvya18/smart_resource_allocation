from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import BookingForm, RegistrationForm, ResourceForm
from .models import ACCESS_END_TIME, ACCESS_START_TIME, Booking, Resource, booking_slot_is_available, suggest_next_slots
from .serializers import BookingSerializer, ResourceSerializer

DASHBOARD_WINDOWS = [7, 30, 90]


def get_is_manager(user):
    profile = getattr(user, "userprofile", None)
    return user.is_staff or (profile and profile.can_manage_resources)


def get_booking_scope(user):
    queryset = Booking.objects.select_related("resource", "user")
    return queryset if get_is_manager(user) else queryset.filter(user=user)


def parse_window_days(raw_value):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        value = 30
    return value if value in DASHBOARD_WINDOWS else 30


def serialize_schedule(booking):
    return {
        "id": booking.id,
        "title": booking.title,
        "resource_name": booking.resource.name,
        "resource_type": booking.resource.get_resource_type_display(),
        "user_name": booking.user.username,
        "start": timezone.localtime(booking.requested_start).strftime("%d %b, %I:%M %p"),
        "end": timezone.localtime(booking.requested_end).strftime("%I:%M %p"),
        "status": booking.status,
        "status_label": booking.get_status_display(),
    }


def build_dashboard_payload(user, window_days):
    today = timezone.localdate()
    now = timezone.localtime()
    start_date = today - timedelta(days=window_days - 1)
    scope = list(get_booking_scope(user))
    analytics_scope = list(Booking.objects.select_related("resource", "user"))
    working_window_end = today + timedelta(days=window_days // 3)
    trailing_bookings = [
        booking
        for booking in analytics_scope
        if start_date <= timezone.localtime(booking.requested_start).date() <= today
    ]
    working_bookings = [
        booking
        for booking in analytics_scope
        if start_date <= timezone.localtime(booking.requested_start).date() <= working_window_end
        and booking.status in {Booking.Status.PENDING, Booking.Status.APPROVED, Booking.Status.COMPLETED}
    ]
    active_resources = list(Resource.objects.filter(status=Resource.Status.ACTIVE))

    type_counts = [
        {"label": label, "value": total}
        for label, total in (
            (
                dict(Resource.ResourceType.choices)[item["resource_type"]],
                item["total"],
            )
            for item in Resource.objects.values("resource_type").annotate(total=Count("id")).order_by("resource_type")
        )
    ]

    status_counter = defaultdict(int)
    for booking in trailing_bookings:
        status_counter[booking.status] += 1
    status_counts = [
        {"label": dict(Booking.Status.choices)[status], "value": total}
        for status, total in sorted(status_counter.items())
    ]

    day_map = {
        start_date + timedelta(days=offset): {
            "date": (start_date + timedelta(days=offset)).strftime("%d %b"),
            "total": 0,
            "approved": 0,
            "pending": 0,
            "completed": 0,
        }
        for offset in range(window_days)
    }
    for booking in trailing_bookings:
        booking_date = timezone.localtime(booking.requested_start).date()
        if booking_date in day_map:
            day_map[booking_date]["total"] += 1
            if booking.status == Booking.Status.APPROVED:
                day_map[booking_date]["approved"] += 1
            elif booking.status == Booking.Status.PENDING:
                day_map[booking_date]["pending"] += 1
            elif booking.status == Booking.Status.COMPLETED:
                day_map[booking_date]["completed"] += 1

    top_usage = defaultdict(lambda: {"hours": 0.0, "bookings": 0, "resource": None})
    total_fill_ratio = 0
    fill_samples = 0
    scheduled_hours = 0.0
    for booking in working_bookings:
        duration = booking.duration_hours
        usage = top_usage[booking.resource_id]
        usage["resource"] = booking.resource
        usage["hours"] += duration
        usage["bookings"] += 1
        if booking.status in {Booking.Status.APPROVED, Booking.Status.COMPLETED}:
            scheduled_hours += duration
            if booking.resource.capacity:
                total_fill_ratio += booking.attendees / booking.resource.capacity
                fill_samples += 1

    possible_hours = 0.0
    future_window_days = max(1, window_days // 3)
    for resource in active_resources:
        open_hours = datetime_hours(resource.available_from, resource.available_until)
        possible_hours += open_hours * future_window_days

    top_resources = []
    for usage in sorted(top_usage.values(), key=lambda item: (-item["hours"], -item["bookings"]))[:6]:
        resource = usage["resource"]
        future_possible = datetime_hours(resource.available_from, resource.available_until) * future_window_days or 1
        top_resources.append(
            {
                "name": resource.name,
                "resource_type": resource.get_resource_type_display(),
                "building": resource.building,
                "hours": round(usage["hours"], 1),
                "bookings": usage["bookings"],
                "utilization": round((usage["hours"] / future_possible) * 100, 1),
                "source_name": resource.source_name,
                "source_url": resource.source_url,
            }
        )

    today_schedule = [
        serialize_schedule(booking)
        for booking in sorted(scope, key=lambda item: item.requested_start)
        if timezone.localtime(booking.requested_start).date() == today
        and booking.status in {Booking.Status.PENDING, Booking.Status.APPROVED}
    ][:8]
    pending_queue = [
        serialize_schedule(booking)
        for booking in sorted(analytics_scope, key=lambda item: item.requested_start)
        if booking.status == Booking.Status.PENDING
    ][:8]
    upcoming_bookings = [
        serialize_schedule(booking)
        for booking in sorted(scope, key=lambda item: item.requested_start)
        if timezone.localtime(booking.requested_start) >= now
        and booking.status in {Booking.Status.PENDING, Booking.Status.APPROVED}
    ][:8]
    recent_activity = [
        {
            "title": booking.title,
            "resource_name": booking.resource.name,
            "user_name": booking.user.username,
            "status": booking.status,
            "status_label": booking.get_status_display(),
            "updated_at": timezone.localtime(booking.updated_at).strftime("%d %b, %I:%M %p"),
        }
        for booking in sorted(analytics_scope, key=lambda item: item.updated_at, reverse=True)[:8]
    ]
    maintenance_resources = [
        {
            "name": resource.name,
            "building": resource.building,
            "resource_type": resource.get_resource_type_display(),
        }
        for resource in Resource.objects.filter(status=Resource.Status.MAINTENANCE)[:6]
    ]

    approval_denominator = max(1, len(trailing_bookings))
    approved_like = len([booking for booking in trailing_bookings if booking.status in {Booking.Status.APPROVED, Booking.Status.COMPLETED}])
    payload = {
        "window_days": window_days,
        "totals": {
            "resources": Resource.objects.count(),
            "active_resources": len(active_resources),
            "maintenance_resources": Resource.objects.filter(status=Resource.Status.MAINTENANCE).count(),
            "bookings_in_window": len(trailing_bookings),
            "today_load": len(today_schedule),
            "pending_requests": len([booking for booking in analytics_scope if booking.status == Booking.Status.PENDING]),
            "utilization_rate": round((scheduled_hours / possible_hours) * 100, 1) if possible_hours else 0,
            "approval_rate": round((approved_like / approval_denominator) * 100, 1),
            "average_fill_rate": round((total_fill_ratio / fill_samples) * 100, 1) if fill_samples else 0,
            "sources_backed": Resource.objects.exclude(source_url="").count(),
        },
        "type_counts": type_counts,
        "status_counts": status_counts,
        "daily_bookings": list(day_map.values()),
        "top_resources": top_resources,
        "today_schedule": today_schedule,
        "pending_queue": pending_queue,
        "upcoming_bookings": upcoming_bookings,
        "recent_activity": recent_activity,
        "maintenance_resources": maintenance_resources,
    }
    return payload


def datetime_hours(start, end):
    return round((end.hour + end.minute / 60) - (start.hour + start.minute / 60), 2)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and get_is_manager(user)


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Account created successfully.")
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = build_dashboard_payload(self.request.user, 30)
        context["is_manager"] = get_is_manager(self.request.user)
        context["dashboard_data"] = payload
        context["window_options"] = DASHBOARD_WINDOWS
        context["featured_resources"] = payload["top_resources"][:4]
        context["my_upcoming_bookings"] = payload["upcoming_bookings"][:4]
        context["pending_bookings"] = payload["pending_queue"][:5]
        context["available_now_resources"] = list(Resource.objects.filter(status=Resource.Status.ACTIVE).order_by("resource_type", "name")[:6])
        context["resource_categories"] = [
            {
                "title": "Rooms",
                "description": "Seminar halls and discussion rooms for events, talks, and meetings.",
                "cta": reverse_lazy("resource-list") + "?resource_type=room",
            },
            {
                "title": "Labs",
                "description": "Department labs for practical sessions, workshops, and supervised research work.",
                "cta": reverse_lazy("resource-list") + "?resource_type=lab",
            },
            {
                "title": "Equipment",
                "description": "Portable devices and AV hardware that can be reserved for short durations.",
                "cta": reverse_lazy("resource-list") + "?resource_type=equipment",
            },
        ]
        return context


class ResourceListView(LoginRequiredMixin, ListView):
    model = Resource
    template_name = "scheduler/resource_list.html"
    context_object_name = "resources"
    paginate_by = 9

    def get_queryset(self):
        queryset = Resource.objects.all()
        search = self.request.GET.get("search", "").strip()
        resource_type = self.request.GET.get("resource_type", "").strip()
        status = self.request.GET.get("status", "").strip()
        capacity = self.request.GET.get("capacity", "").strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(building__icontains=search)
                | Q(location_detail__icontains=search)
                | Q(features__icontains=search)
                | Q(source_name__icontains=search)
            )
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if status:
            queryset = queryset.filter(status=status)
        if capacity:
            queryset = queryset.filter(capacity__gte=capacity)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type_choices"] = Resource.ResourceType.choices
        context["status_choices"] = Resource.Status.choices
        context["filters"] = {
            "search": self.request.GET.get("search", ""),
            "resource_type": self.request.GET.get("resource_type", ""),
            "status": self.request.GET.get("status", ""),
            "capacity": self.request.GET.get("capacity", ""),
        }
        context["is_manager"] = get_is_manager(self.request.user)
        return context


class ResourceDetailView(LoginRequiredMixin, DetailView):
    model = Resource
    template_name = "scheduler/resource_detail.html"
    context_object_name = "resource"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_bookings"] = self.object.bookings.select_related("user")[:8]
        return context


class ResourceCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Resource
    form_class = ResourceForm
    template_name = "scheduler/resource_form.html"
    success_url = reverse_lazy("resource-list")

    def form_valid(self, form):
        messages.success(self.request, "Resource created successfully.")
        return super().form_valid(form)


class ResourceUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Resource
    form_class = ResourceForm
    template_name = "scheduler/resource_form.html"
    success_url = reverse_lazy("resource-list")

    def form_valid(self, form):
        messages.success(self.request, "Resource updated successfully.")
        return super().form_valid(form)


class ResourceDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Resource
    template_name = "scheduler/confirm_delete.html"
    success_url = reverse_lazy("resource-list")

    def form_valid(self, form):
        messages.success(self.request, "Resource deleted successfully.")
        return super().form_valid(form)


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = "scheduler/booking_list.html"
    context_object_name = "bookings"
    paginate_by = 10

    def get_queryset(self):
        queryset = get_booking_scope(self.request.user)
        status = self.request.GET.get("status", "").strip()
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_manager"] = get_is_manager(self.request.user)
        context["status_choices"] = Booking.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "scheduler/booking_form.html"
    success_url = reverse_lazy("booking-list")

    def get_initial(self):
        initial = super().get_initial()
        if resource_id := self.request.GET.get("resource"):
            initial["resource"] = resource_id
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Booking request submitted successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_cost_map"] = {
            str(resource.id): float(resource.hourly_cost)
            for resource in Resource.objects.filter(status=Resource.Status.ACTIVE)
        }
        return context


class BookingUpdateView(LoginRequiredMixin, UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = "scheduler/booking_form.html"
    success_url = reverse_lazy("booking-list")

    def dispatch(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.user != request.user and not request.user.is_staff:
            messages.error(request, "You do not have permission to edit this booking.")
            return redirect("booking-list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.get_object().user
        messages.success(self.request, "Booking updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_cost_map"] = {
            str(resource.id): float(resource.hourly_cost)
            for resource in Resource.objects.filter(status=Resource.Status.ACTIVE)
        }
        return context


class BookingDeleteView(LoginRequiredMixin, DeleteView):
    model = Booking
    template_name = "scheduler/confirm_delete.html"
    success_url = reverse_lazy("booking-list")

    def dispatch(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.user != request.user and not request.user.is_staff:
            messages.error(request, "You do not have permission to delete this booking.")
            return redirect("booking-list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Booking deleted successfully.")
        return super().form_valid(form)


def availability_check(request):
    resource_id = request.GET.get("resource")
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))
    booking_id = request.GET.get("booking_id")

    if not all([resource_id, start, end]):
        return JsonResponse({"available": False, "message": "Please select the resource, start time, and end time."})

    if timezone.is_naive(start):
        start = timezone.make_aware(start)
    if timezone.is_naive(end):
        end = timezone.make_aware(end)

    resource = get_object_or_404(Resource, pk=resource_id)
    duration_hours = round((end - start).total_seconds() / 3600, 2) if end > start else 0
    estimated_cost = round(float(resource.hourly_cost) * max(duration_hours, 0), 2)
    suggestions = suggest_next_slots(resource, timezone.localtime(start), timezone.localtime(end), booking_id)

    if end <= start:
        return JsonResponse(
            {
                "available": False,
                "message": "No availability. End time must be after start time.",
                "suggestions": suggestions,
                "duration_hours": duration_hours,
                "estimated_cost": estimated_cost,
            }
        )

    local_start = timezone.localtime(start)
    local_end = timezone.localtime(end)
    if local_start < timezone.localtime() or local_end < timezone.localtime():
        return JsonResponse(
            {
                "available": False,
                "message": "No availability. Past dates and times are not allowed.",
                "suggestions": suggestions,
                "duration_hours": duration_hours,
                "estimated_cost": estimated_cost,
            }
        )

    if (
        local_start.time() < ACCESS_START_TIME
        or local_end.time() > ACCESS_END_TIME
    ):
        return JsonResponse(
            {
                "available": False,
                "message": "No availability. Bookings are restricted to 09:00 AM to 09:00 PM.",
                "suggestions": suggestions,
                "duration_hours": duration_hours,
                "estimated_cost": estimated_cost,
            }
        )

    if not booking_slot_is_available(resource, start, end, booking_id):
        conflict = Booking.objects.filter(
            resource=resource,
            status__in=[Booking.Status.PENDING, Booking.Status.APPROVED],
            requested_start__lt=end,
            requested_end__gt=start,
        )
        if booking_id:
            conflict = conflict.exclude(pk=booking_id)
        conflict_title = conflict.first().title if conflict.exists() else "another booking"
        return JsonResponse(
            {
                "available": False,
                "message": f"No availability. This slot is already booked by '{conflict_title}'.",
                "suggestions": suggestions,
                "duration_hours": duration_hours,
                "estimated_cost": estimated_cost,
            }
        )

    return JsonResponse(
        {
            "available": True,
            "message": "Selected slot is available.",
            "suggestions": suggestions,
            "duration_hours": duration_hours,
            "estimated_cost": estimated_cost,
        }
    )


def booking_status_update(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST request required."}, status=405)

    booking = get_object_or_404(Booking, pk=pk)
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required."}, status=403)

    new_status = request.POST.get("status")
    is_manager = get_is_manager(user)
    allowed_for_manager = {Booking.Status.APPROVED, Booking.Status.REJECTED, Booking.Status.COMPLETED}
    allowed_for_user = {Booking.Status.CANCELLED}

    if is_manager and new_status in allowed_for_manager:
        booking.status = new_status
        booking.approved_by = user
        booking.approval_notes = request.POST.get("notes", "")
        booking.save()
        return JsonResponse({"success": True, "message": f"Booking marked as {booking.get_status_display()}."})

    if booking.user == user and new_status in allowed_for_user:
        booking.status = new_status
        booking.save()
        return JsonResponse({"success": True, "message": "Booking cancelled successfully."})

    return JsonResponse({"success": False, "message": "You do not have permission for this action."}, status=403)


class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return get_is_manager(request.user)


class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [IsManagerOrReadOnly]

    def get_queryset(self):
        queryset = Resource.objects.all()
        search = self.request.query_params.get("search", "").strip()
        resource_type = self.request.query_params.get("resource_type", "").strip()
        status = self.request.query_params.get("status", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(building__icontains=search)
                | Q(location_detail__icontains=search)
                | Q(features__icontains=search)
                | Q(source_name__icontains=search)
            )
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_booking_scope(self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(build_dashboard_payload(request.user, parse_window_days(request.query_params.get("window"))))
