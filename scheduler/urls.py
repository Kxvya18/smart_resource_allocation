from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("resources/", views.ResourceListView.as_view(), name="resource-list"),
    path("resources/new/", views.ResourceCreateView.as_view(), name="resource-create"),
    path("resources/<int:pk>/", views.ResourceDetailView.as_view(), name="resource-detail"),
    path("resources/<int:pk>/edit/", views.ResourceUpdateView.as_view(), name="resource-update"),
    path("resources/<int:pk>/delete/", views.ResourceDeleteView.as_view(), name="resource-delete"),
    path("bookings/", views.BookingListView.as_view(), name="booking-list"),
    path("bookings/new/", views.BookingCreateView.as_view(), name="booking-create"),
    path("bookings/<int:pk>/edit/", views.BookingUpdateView.as_view(), name="booking-update"),
    path("bookings/<int:pk>/delete/", views.BookingDeleteView.as_view(), name="booking-delete"),
    path("ajax/availability/", views.availability_check, name="availability-check"),
    path("ajax/bookings/<int:pk>/status/", views.booking_status_update, name="booking-status-update"),
]
