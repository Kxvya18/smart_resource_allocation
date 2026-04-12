from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookingViewSet, DashboardSummaryAPIView, ResourceViewSet

router = DefaultRouter()
router.register("resources", ResourceViewSet, basename="api-resources")
router.register("bookings", BookingViewSet, basename="api-bookings")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard-summary/", DashboardSummaryAPIView.as_view(), name="api-dashboard-summary"),
]
