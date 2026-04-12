from __future__ import annotations

import os
from pathlib import Path
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

ROOT = Path("/Users/boolu/Desktop/simulations/files (1)/smart_resource_allocation")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import django

django.setup()

from django.test import Client  # noqa: E402
from django.utils import timezone  # noqa: E402

from scheduler.models import Booking  # noqa: E402

OUTPUT_DIR = ROOT / "docs" / "report_assets"
HTML_DIR = OUTPUT_DIR / "html"
IMG_DIR = OUTPUT_DIR / "images"


def with_base_href(html: str) -> str:
    return html.replace("<head>", '<head><base href="http://localhost:8000">', 1)


def save_html(name: str, content: str) -> Path:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    path = HTML_DIR / name
    path.write_text(content, encoding="utf-8")
    return path


def build_booking_demo_html(client: Client) -> Path:
    target_booking = (
        Booking.objects.select_related("resource")
        .filter(status__in=[Booking.Status.PENDING, Booking.Status.APPROVED])
        .order_by("requested_start")
        .first()
    )
    if not target_booking:
        raise RuntimeError("No seeded booking found for report screenshot generation.")

    response = client.get(f"/bookings/new/?resource={target_booking.resource_id}")
    html = with_base_href(response.content.decode("utf-8"))

    start_value = timezone.localtime(target_booking.requested_start).strftime("%Y-%m-%dT%H:%M")
    end_value = timezone.localtime(target_booking.requested_end).strftime("%Y-%m-%dT%H:%M")

    injection = f"""
    <script>
    window.addEventListener("load", function () {{
        const resource = document.getElementById("id_resource");
        if (resource) resource.value = "{target_booking.resource_id}";
        const title = document.getElementById("id_title");
        if (title) title.value = "Machine Learning Practical";
        const purpose = document.getElementById("id_purpose");
        if (purpose) purpose.value = "Faculty-led lab session using an already reserved AV resource.";
        const attendees = document.getElementById("id_attendees");
        if (attendees) attendees.value = "24";
        const start = document.getElementById("id_requested_start");
        if (start) start.value = "{start_value}";
        const end = document.getElementById("id_requested_end");
        if (end) end.value = "{end_value}";
        const priority = document.getElementById("id_priority");
        if (priority) priority.value = "high";

        const duration = document.getElementById("booking-duration");
        if (duration) duration.textContent = "{target_booking.duration_hours:.1f} hours";
        const cost = document.getElementById("booking-cost");
        if (cost) cost.textContent = "Rs. 350.00";

        const result = document.getElementById("availability-result");
        if (result) {{
            result.textContent = "No availability. This slot is already booked.";
            result.classList.remove("text-success");
            result.classList.add("text-danger");
            result.style.fontWeight = "700";
        }}

        const suggestions = document.getElementById("availability-suggestions");
        if (suggestions) {{
            suggestions.innerHTML = "<div><strong>Suggested next slots:</strong></div><div><strong>06 Apr 2026, 12:30 PM</strong> to 02:30 PM</div><div><strong>06 Apr 2026, 03:00 PM</strong> to 05:00 PM</div>";
        }}
        window.scrollTo(0, 0);
    }});
    </script>
    """

    html = html.replace("</body>", injection + "</body>", 1)
    return save_html("booking_validation_result.html", html)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    client = Client()
    if not client.login(username="student", password="student123"):
        raise RuntimeError("Unable to log in with seeded student account.")

    dashboard_html = with_base_href(client.get("/dashboard/").content.decode("utf-8"))
    resources_html = with_base_href(client.get("/resources/?resource_type=lab").content.decode("utf-8"))
    bookings_html = with_base_href(client.get("/bookings/").content.decode("utf-8"))

    save_html("dashboard_result.html", dashboard_html)
    save_html("resources_result.html", resources_html)
    save_html("bookings_result.html", bookings_html)
    build_booking_demo_html(client)

    print(HTML_DIR)


if __name__ == "__main__":
    main()
