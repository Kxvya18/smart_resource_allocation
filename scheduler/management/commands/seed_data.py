from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from scheduler.models import ACCESS_END_TIME, ACCESS_START_TIME, Booking, Resource, UserProfile

SEED_NOTE = "Seed dataset generated from curated public facility references."

RESOURCE_CATALOG = [
    {
        "name": "SL1 Software Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "KReSIT Building, IIT Bombay",
        "floor": "1",
        "location_detail": "SL1",
        "capacity": 75,
        "features": "Desktop workstations, projector, assistant console",
        "description": "Software laboratory curated from IIT Bombay CSE lab booking references.",
        "source_name": "IIT Bombay CSE Lab Booking Policy",
        "source_url": "https://systems.cse.iitb.ac.in/systems/lab_booking_policy.html",
        "hourly_cost": 900,
    },
    {
        "name": "SL2 Software Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "KReSIT Building, IIT Bombay",
        "floor": "1",
        "location_detail": "SL2",
        "capacity": 120,
        "features": "High-density systems, ceiling projector, teaching display",
        "description": "Large teaching lab based on publicly listed IIT Bombay software lab facilities.",
        "source_name": "IIT Bombay CSE Lab Booking Policy",
        "source_url": "https://systems.cse.iitb.ac.in/systems/lab_booking_policy.html",
        "hourly_cost": 1200,
    },
    {
        "name": "SL3 Software Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "KReSIT Building, IIT Bombay",
        "floor": "2",
        "location_detail": "SL3",
        "capacity": 40,
        "features": "Advanced workstations, faculty podium, collaboration desks",
        "description": "Compact practical lab derived from IIT Bombay lab booking references.",
        "source_name": "IIT Bombay CSE Lab Booking Policy",
        "source_url": "https://systems.cse.iitb.ac.in/systems/lab_booking_policy.html",
        "hourly_cost": 700,
    },
    {
        "name": "Basement Software Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "KReSIT Building, IIT Bombay",
        "floor": "Basement",
        "location_detail": "Systems Wing",
        "capacity": 135,
        "features": "Large workstation cluster, dual projection, practical exam setup",
        "description": "Large basement lab inspired by the publicly listed IIT Bombay lab allocation page.",
        "source_name": "IIT Bombay CSE Lab Booking Policy",
        "source_url": "https://systems.cse.iitb.ac.in/systems/lab_booking_policy.html",
        "hourly_cost": 1350,
    },
    {
        "name": "Centre for Formal Design and Verification of Systems",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Computer Science Department, IIT Bombay",
        "floor": "2",
        "location_detail": "Research Wing",
        "capacity": 28,
        "features": "Verification servers, whiteboards, research collaboration zone",
        "description": "Research facility name taken from IIT Bombay CSE's official research labs page.",
        "source_name": "IIT Bombay CSE Research Labs",
        "source_url": "https://www.cse.iitb.ac.in/old/research/labs.php",
        "hourly_cost": 850,
    },
    {
        "name": "Centre for Indian Language Technologies",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Computer Science Department, IIT Bombay",
        "floor": "2",
        "location_detail": "Language Computing Cluster",
        "capacity": 24,
        "features": "Speech processing systems, audio capture booth, GPU workstation",
        "description": "Language technology lab name curated from IIT Bombay CSE's official research labs listing.",
        "source_name": "IIT Bombay CSE Research Labs",
        "source_url": "https://www.cse.iitb.ac.in/old/research/labs.php",
        "hourly_cost": 800,
    },
    {
        "name": "Database and Information Systems Laboratory",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Computer Science Department, IIT Bombay",
        "floor": "1",
        "location_detail": "Data Systems Lab",
        "capacity": 30,
        "features": "Database servers, analytics nodes, discussion screen",
        "description": "Official lab name from IIT Bombay CSE research facilities, adapted for booking workflow.",
        "source_name": "IIT Bombay CSE Research Labs",
        "source_url": "https://www.cse.iitb.ac.in/old/research/labs.php",
        "hourly_cost": 900,
    },
    {
        "name": "Embedded Real-Time Systems Laboratory",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Computer Science Department, IIT Bombay",
        "floor": "Ground",
        "location_detail": "Embedded Systems Zone",
        "capacity": 22,
        "features": "FPGA kits, logic analyzers, microcontroller benches",
        "description": "Embedded systems lab named after the official IIT Bombay CSE research lab listing.",
        "source_name": "IIT Bombay CSE Research Labs",
        "source_url": "https://www.cse.iitb.ac.in/old/research/labs.php",
        "hourly_cost": 950,
    },
    {
        "name": "Gigabit Networking Laboratory",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Computer Science Department, IIT Bombay",
        "floor": "Ground",
        "location_detail": "Networking Bay",
        "capacity": 26,
        "features": "Managed switches, rack servers, packet analysis tools",
        "description": "Networking research lab title sourced from the IIT Bombay CSE labs page.",
        "source_name": "IIT Bombay CSE Research Labs",
        "source_url": "https://www.cse.iitb.ac.in/old/research/labs.php",
        "hourly_cost": 950,
    },
    {
        "name": "Laboratory for Intelligent Internet Research",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Computer Science Department, IIT Bombay",
        "floor": "3",
        "location_detail": "Internet Research Suite",
        "capacity": 20,
        "features": "Machine learning nodes, meeting pods, visualization wall",
        "description": "Lab title based on the official IIT Bombay Laboratory for Intelligent Internet Research page.",
        "source_name": "IIT Bombay LAIIR",
        "source_url": "https://www.cse.iitb.ac.in/~laiir/",
        "hourly_cost": 980,
    },
    {
        "name": "Wadhwani Electronics Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Electrical Engineering Department, IIT Bombay",
        "floor": "1",
        "location_detail": "EE5 Cluster",
        "capacity": 32,
        "features": "Oscilloscopes, soldering benches, prototyping stations",
        "description": "Electronics lab name taken from IIT Bombay EE's electronic systems research facilities.",
        "source_name": "IIT Bombay EE Electronic Systems Labs",
        "source_url": "https://www.ee.iitb.ac.in/web/research/electronic-systems-ee5/",
        "hourly_cost": 1050,
    },
    {
        "name": "Texas Instruments Digital Signal Processing Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Electrical Engineering Department, IIT Bombay",
        "floor": "1",
        "location_detail": "EE5 Cluster",
        "capacity": 26,
        "features": "DSP kits, signal analysis consoles, interactive projection",
        "description": "DSP lab name curated from IIT Bombay EE's official lab references.",
        "source_name": "IIT Bombay EE Electronic Systems Labs",
        "source_url": "https://www.ee.iitb.ac.in/web/research/electronic-systems-ee5/",
        "hourly_cost": 1025,
    },
    {
        "name": "Printed Circuit Board Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Electrical Engineering Department, IIT Bombay",
        "floor": "Ground",
        "location_detail": "Fabrication Zone",
        "capacity": 18,
        "features": "PCB fabrication setup, etching station, inspection tools",
        "description": "PCB lab name taken from IIT Bombay EE's official electronic systems lab page.",
        "source_name": "IIT Bombay EE Electronic Systems Labs",
        "source_url": "https://www.ee.iitb.ac.in/web/research/electronic-systems-ee5/",
        "hourly_cost": 780,
    },
    {
        "name": "Signal Processing and Instrumentation Lab",
        "resource_type": Resource.ResourceType.LAB,
        "building": "Electrical Engineering Department, IIT Bombay",
        "floor": "2",
        "location_detail": "Instrumentation Wing",
        "capacity": 24,
        "features": "Measurement consoles, instrumentation racks, demo display",
        "description": "Instrumentation lab name adapted from IIT Bombay EE's official research lab listing.",
        "source_name": "IIT Bombay EE Electronic Systems Labs",
        "source_url": "https://www.ee.iitb.ac.in/web/research/electronic-systems-ee5/",
        "hourly_cost": 880,
    },
    {
        "name": "Modern Seminar Hall",
        "resource_type": Resource.ResourceType.ROOM,
        "building": "Department of Computer Science, IIT Madras",
        "floor": "Ground",
        "location_detail": "Seminar Hall",
        "capacity": 80,
        "features": "Presentation wall, lecture seating, AV-ready podium",
        "description": "Seminar hall name based on the IIT Madras alumni project page for the Department of Computer Science.",
        "source_name": "IIT Madras Alumni Project",
        "source_url": "https://joyofgiving.alumni.iitm.ac.in/projects/department/modern-seminar-hall-in-department-of-computer-science-1",
        "hourly_cost": 1400,
    },
    {
        "name": "Visweswaraya Seminar Hall",
        "resource_type": Resource.ResourceType.ROOM,
        "building": "Civil Engineering Department, IIT Madras",
        "floor": "Ground",
        "location_detail": "VSH",
        "capacity": 100,
        "features": "Large seminar seating, stage lighting, hybrid session setup",
        "description": "Seminar hall title taken from the IIT Madras alumni portal's Visweswaraya Seminar Hall project.",
        "source_name": "IIT Madras Alumni Project",
        "source_url": "https://joyofgiving.alumni.iitm.ac.in/projects/department/visweswaraya-seminar-hall-vsh-in-the-department-of-civil-engineering",
        "hourly_cost": 1600,
    },
    {
        "name": "Logitech Rally Bar",
        "resource_type": Resource.ResourceType.EQUIPMENT,
        "building": "AV Support Desk",
        "floor": "Ground",
        "location_detail": "Equipment Counter 1",
        "capacity": 1,
        "features": "All-in-one video bar, digital PTZ camera, microphone array",
        "description": "Actual conferencing device model seeded from Logitech's official product page.",
        "source_name": "Logitech Official Product Page",
        "source_url": "https://www.logitech.com/products/video-conferencing/room-solutions/rallybarhuddle",
        "hourly_cost": 350,
    },
    {
        "name": "Logitech Rally Bar Huddle",
        "resource_type": Resource.ResourceType.EQUIPMENT,
        "building": "AV Support Desk",
        "floor": "Ground",
        "location_detail": "Equipment Counter 2",
        "capacity": 1,
        "features": "Compact conferencing bar, touch-ready deployment, huddle-room support",
        "description": "Real conferencing device name pulled from Logitech's official meeting room product page.",
        "source_name": "Logitech Official Product Page",
        "source_url": "https://www.logitech.com/products/video-conferencing/room-solutions/rallybarhuddle",
        "hourly_cost": 300,
    },
    {
        "name": "Shure MXA920 Ceiling Array Microphone",
        "resource_type": Resource.ResourceType.EQUIPMENT,
        "building": "AV Support Desk",
        "floor": "Ground",
        "location_detail": "Audio Equipment Rack",
        "capacity": 1,
        "features": "Ceiling array microphone, automatic coverage, voice lift support",
        "description": "Real microphone model based on Shure's official MXA920 product page.",
        "source_name": "Shure Official Product Page",
        "source_url": "https://www.shure.com/en-GB/products/microphones/mxa920",
        "hourly_cost": 275,
    },
    {
        "name": "Barco ClickShare CX-20",
        "resource_type": Resource.ResourceType.EQUIPMENT,
        "building": "AV Support Desk",
        "floor": "Ground",
        "location_detail": "Wireless Collaboration Shelf",
        "capacity": 1,
        "features": "Wireless conferencing, one-click content sharing, room AV bridge",
        "description": "Real collaboration device line seeded from Barco's official ClickShare product materials.",
        "source_name": "Barco ClickShare Product Line",
        "source_url": "https://www.barco.com/en/products/clickshare-conferencing-collaboration/management-platforms/clickshare-configurator",
        "hourly_cost": 240,
        "status": Resource.Status.MAINTENANCE,
    },
]

USER_CATALOG = [
    ("admin", "System", "Admin", UserProfile.Role.ADMIN, "IT Administration", "9999999999", "admin@example.com"),
    ("manager", "Lab", "Manager", UserProfile.Role.STAFF, "Resource Office", "8888888888", "manager@example.com"),
    ("student", "Demo", "Student", UserProfile.Role.STUDENT, "Computer Science", "7777777777", "student@example.com"),
    ("anita_student", "Anita", "Sharma", UserProfile.Role.STUDENT, "Computer Science", "7777777701", "anita@example.com"),
    ("rahul_student", "Rahul", "Menon", UserProfile.Role.STUDENT, "Electrical Engineering", "7777777702", "rahul@example.com"),
    ("priya_research", "Priya", "Nair", UserProfile.Role.STUDENT, "Data Science", "7777777703", "priya@example.com"),
    ("meera_staff", "Meera", "Rao", UserProfile.Role.STAFF, "Digital Learning", "8888888801", "meera@example.com"),
    ("vikram_staff", "Vikram", "Iyer", UserProfile.Role.STAFF, "Research Office", "8888888802", "vikram@example.com"),
]

BOOKING_THEMES = [
    ("Machine Learning Practical", "Lab session focused on model training and evaluation."),
    ("Cloud Computing Workshop", "Hands-on workshop on deployment workflows and infrastructure."),
    ("Student Project Demo", "Final-year student team presentation and demonstration."),
    ("Research Group Meeting", "Weekly research sync and paper discussion."),
    ("Embedded Systems Lab", "Microcontroller and FPGA practice session."),
    ("Data Visualization Clinic", "Interactive classroom session on dashboard storytelling."),
    ("Placement Readiness Session", "Mock interviews and aptitude preparation event."),
    ("Faculty Seminar", "Department seminar with invited speaker and Q&A."),
    ("Hackathon Briefing", "Pre-event orientation and tooling overview."),
    ("Robotics Design Review", "Engineering review meeting for robotics teams."),
]


class Command(BaseCommand):
    help = "Seed demo users, real-world inspired resources, and a richer booking dataset."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete previously generated seed bookings before reseeding.")

    def handle(self, *args, **options):
        users = self.create_users()
        resources = self.sync_resources()

        if options["reset"]:
            Booking.objects.filter(approval_notes__startswith=SEED_NOTE).delete()
        else:
            Booking.objects.filter(title__in=["Neural Networks Practical Session", "Hackathon Orientation"]).delete()

        self.generate_seed_bookings(users, resources)
        self.stdout.write(self.style.SUCCESS("Rich demo data seeded successfully."))

    def create_users(self):
        created_users = {}
        for username, first_name, last_name, role, department, phone, email in USER_CATALOG:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_staff": role in {UserProfile.Role.STAFF, UserProfile.Role.ADMIN},
                    "is_superuser": role == UserProfile.Role.ADMIN,
                },
            )
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = role in {UserProfile.Role.STAFF, UserProfile.Role.ADMIN}
            user.is_superuser = role == UserProfile.Role.ADMIN
            user.set_password("admin123" if role == UserProfile.Role.ADMIN else ("manager123" if role == UserProfile.Role.STAFF and username == "manager" else "student123"))
            user.save()
            profile = user.userprofile
            profile.role = role
            profile.department = department
            profile.phone = phone
            profile.save()
            created_users[username] = user
        return created_users

    def sync_resources(self):
        resources = []
        for resource_data in RESOURCE_CATALOG:
            defaults = dict(resource_data)
            defaults.setdefault("status", Resource.Status.ACTIVE)
            defaults.setdefault("available_from", ACCESS_START_TIME)
            defaults.setdefault("available_until", ACCESS_END_TIME)
            resource, _ = Resource.objects.update_or_create(name=resource_data["name"], defaults=defaults)
            resources.append(resource)
        return resources

    def generate_seed_bookings(self, users, resources):
        today = timezone.localdate()
        schedule_offsets = [-21, -16, -10, -4, 0, 3, 7, 12]
        slot_hours = [9, 11, 14, 16]
        user_cycle = [
            users["student"],
            users["anita_student"],
            users["rahul_student"],
            users["priya_research"],
            users["meera_staff"],
            users["vikram_staff"],
        ]
        approvers = [users["manager"], users["meera_staff"], users["vikram_staff"], users["admin"]]

        for resource_index, resource in enumerate(resources):
            if resource.status != Resource.Status.ACTIVE:
                continue
            for booking_index, day_offset in enumerate(schedule_offsets):
                start_hour = slot_hours[(resource_index + booking_index) % len(slot_hours)]
                duration = 2 if resource.resource_type != Resource.ResourceType.EQUIPMENT else 1
                start = timezone.make_aware(datetime.combine(today + timedelta(days=day_offset), time(start_hour, 0)))
                end = start + timedelta(hours=duration)
                title_root, purpose_root = BOOKING_THEMES[(resource_index + booking_index) % len(BOOKING_THEMES)]
                status = self.pick_status(day_offset, booking_index)
                if status in {Booking.Status.PENDING, Booking.Status.APPROVED} and start <= timezone.localtime() + timedelta(minutes=30):
                    candidate_day = today if day_offset > 0 else today + timedelta(days=1)
                    start = timezone.make_aware(datetime.combine(candidate_day, time(18, 0)))
                    end = start + timedelta(hours=duration)
                booking_user = user_cycle[(resource_index + booking_index) % len(user_cycle)]
                attendees = 1 if resource.resource_type == Resource.ResourceType.EQUIPMENT else max(4, min(resource.capacity - 1, int(resource.capacity * (0.45 + ((resource_index + booking_index) % 4) * 0.1))))
                approval_notes = SEED_NOTE
                approved_by = None

                if status in {Booking.Status.APPROVED, Booking.Status.COMPLETED, Booking.Status.REJECTED}:
                    approved_by = approvers[(resource_index + booking_index) % len(approvers)]
                    approval_notes = f"{SEED_NOTE} Reviewed by {approved_by.first_name or approved_by.username}."

                title = f"{title_root} - {resource.name}"

                Booking.objects.update_or_create(
                    title=title,
                    resource=resource,
                    requested_start=start,
                    defaults={
                        "user": booking_user,
                        "purpose": f"{purpose_root} {SEED_NOTE}",
                        "attendees": attendees,
                        "requested_end": end,
                        "priority": self.pick_priority(resource_index, booking_index),
                        "status": status,
                        "approval_notes": approval_notes,
                        "approved_by": approved_by,
                    },
                )

    def pick_status(self, day_offset, booking_index):
        if day_offset <= -10:
            return Booking.Status.COMPLETED if booking_index % 3 else Booking.Status.CANCELLED
        if day_offset < 0:
            return Booking.Status.COMPLETED if booking_index % 2 else Booking.Status.REJECTED
        if day_offset == 0:
            return Booking.Status.APPROVED
        if day_offset <= 7:
            return Booking.Status.PENDING if booking_index % 2 else Booking.Status.APPROVED
        return Booking.Status.PENDING

    def pick_priority(self, resource_index, booking_index):
        priorities = [Booking.Priority.MEDIUM, Booking.Priority.HIGH, Booking.Priority.LOW]
        return priorities[(resource_index + booking_index) % len(priorities)]
