from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
import zipfile


ROOT = Path("/Users/boolu/Desktop/simulations/files (1)/smart_resource_allocation")
OUTPUT = ROOT / "docs" / "Smart_Resource_Allocation_Project_Report_Professional.docx"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def xml_header() -> str:
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def esc(text: str) -> str:
    return escape(text, {"'": "&apos;", '"': "&quot;"})


def run(text: str, *, bold: bool = False, italic: bool = False, size: int | None = None, color: str | None = None) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if size:
        props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    text = esc(text)
    return f'<w:r>{rpr}<w:t xml:space="preserve">{text}</w:t></w:r>'


def paragraph(
    text: str = "",
    *,
    style: str | None = None,
    align: str | None = None,
    page_break_before: bool = False,
    spacing_before: int | None = None,
    spacing_after: int | None = None,
    keep_next: bool = False,
    runs: list[str] | None = None,
) -> str:
    props = []
    if style:
        props.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        props.append(f'<w:jc w:val="{align}"/>')
    if page_break_before:
        props.append("<w:pageBreakBefore/>")
    if keep_next:
        props.append("<w:keepNext/>")
    if spacing_before is not None or spacing_after is not None:
        before = spacing_before if spacing_before is not None else 0
        after = spacing_after if spacing_after is not None else 0
        props.append(f'<w:spacing w:before="{before}" w:after="{after}"/>')
    ppr = f"<w:pPr>{''.join(props)}</w:pPr>" if props else ""
    content = "".join(runs) if runs is not None else run(text)
    return f"<w:p>{ppr}{content}</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def table(rows: list[list[str]], widths: list[int] | None = None, header_rows: int = 1) -> str:
    widths = widths or [2400] * len(rows[0])
    tbl_pr = """
    <w:tblPr>
      <w:tblW w:w="0" w:type="auto"/>
      <w:tblBorders>
        <w:top w:val="single" w:sz="8" w:space="0" w:color="7A7A7A"/>
        <w:left w:val="single" w:sz="8" w:space="0" w:color="7A7A7A"/>
        <w:bottom w:val="single" w:sz="8" w:space="0" w:color="7A7A7A"/>
        <w:right w:val="single" w:sz="8" w:space="0" w:color="7A7A7A"/>
        <w:insideH w:val="single" w:sz="6" w:space="0" w:color="B8B8B8"/>
        <w:insideV w:val="single" w:sz="6" w:space="0" w:color="B8B8B8"/>
      </w:tblBorders>
      <w:tblCellMar>
        <w:top w:w="90" w:type="dxa"/>
        <w:left w:w="120" w:type="dxa"/>
        <w:bottom w:w="90" w:type="dxa"/>
        <w:right w:w="120" w:type="dxa"/>
      </w:tblCellMar>
    </w:tblPr>
    """
    grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
    tr_xml = []
    for idx, row in enumerate(rows):
        cells = []
        for col_idx, cell in enumerate(row):
            tc_pr_bits = [f'<w:tcW w:w="{widths[col_idx]}" w:type="dxa"/>']
            if idx < header_rows:
                tc_pr_bits.append('<w:shd w:val="clear" w:color="auto" w:fill="D9EAF7"/>')
            tc_pr = f"<w:tcPr>{''.join(tc_pr_bits)}</w:tcPr>"
            text_runs = [run(part.strip(), bold=(idx < header_rows)) for part in cell.split("\n")]
            cell_paragraphs = []
            for part in cell.split("\n"):
                cell_paragraphs.append(
                    paragraph(
                        part.strip(),
                        align="left",
                        spacing_after=40,
                        runs=[run(part.strip(), bold=(idx < header_rows))],
                    )
                )
            cells.append(f"<w:tc>{tc_pr}{''.join(cell_paragraphs)}</w:tc>")
        tr_xml.append("<w:tr>" + "".join(cells) + "</w:tr>")
    return "<w:tbl>" + tbl_pr + grid + "".join(tr_xml) + "</w:tbl>"


def placeholder_figure(title: str, note: str) -> str:
    return (
        "<w:tbl>"
        """
        <w:tblPr>
          <w:tblW w:w="0" w:type="auto"/>
          <w:tblBorders>
            <w:top w:val="single" w:sz="10" w:space="0" w:color="7A7A7A"/>
            <w:left w:val="single" w:sz="10" w:space="0" w:color="7A7A7A"/>
            <w:bottom w:val="single" w:sz="10" w:space="0" w:color="7A7A7A"/>
            <w:right w:val="single" w:sz="10" w:space="0" w:color="7A7A7A"/>
            <w:insideH w:val="single" w:sz="6" w:space="0" w:color="B8B8B8"/>
            <w:insideV w:val="nil"/>
          </w:tblBorders>
        </w:tblPr>
        <w:tblGrid><w:gridCol w:w="8000"/></w:tblGrid>
        """
        + (
            "<w:tr>"
            '<w:tc><w:tcPr><w:tcW w:w="8000" w:type="dxa"/><w:shd w:val="clear" w:fill="D9EAF7"/></w:tcPr>'
            + paragraph(title, runs=[run(title, bold=True)], spacing_after=40)
            + "</w:tc></w:tr>"
        )
        + (
            "<w:tr>"
            '<w:trPr><w:trHeight w:val="2200" w:hRule="exact"/></w:trPr>'
            '<w:tc><w:tcPr><w:tcW w:w="8000" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
            + paragraph("[ Placeholder for screenshot ]", align="center", runs=[run("[ Placeholder for screenshot ]", bold=True, color="666666")], spacing_after=60)
            + paragraph(note, align="center", runs=[run(note, italic=True, color="666666")], spacing_after=0)
            + "</w:tc></w:tr>"
        )
        + "</w:tbl>"
    )


def bullet_items(items: list[str]) -> list[str]:
    paragraphs = []
    for item in items:
        paragraphs.append(
            paragraph(
                runs=[run("• ", bold=True), run(item)],
                spacing_after=60,
            )
        )
    return paragraphs


def build_document_xml() -> str:
    parts: list[str] = []

    parts.extend(
        [
            paragraph("MANIPAL INSTITUTE OF TECHNOLOGY", style="TitleCenter", align="center", spacing_after=120),
            paragraph("Bengaluru", style="SubtitleCenter", align="center", spacing_after=60),
            paragraph("(Academic Project Report Format)", style="SmallCenter", align="center", spacing_after=420),
            paragraph("PROJECT REPORT", style="SectionCenter", align="center", spacing_after=220),
            paragraph("Smart Resource Allocation System", style="CoverHeading", align="center", spacing_after=120),
            paragraph("(Room / Lab / Equipment Booking)", style="SubtitleCenter", align="center", spacing_after=300),
            paragraph(
                "A complete web application for institutional resource allocation, live booking validation, approval workflow, and REST API integration",
                style="BodyCenter",
                align="center",
                spacing_after=460,
            ),
            paragraph("Submitted in partial fulfilment of the course requirements for", style="BodyCenter", align="center", spacing_after=80),
            paragraph("Web Programming Lab (DS_3263)", style="SubheadingCenter", align="center", spacing_after=260),
            paragraph("Prepared By", style="SubheadingCenter", align="center", spacing_after=80),
            paragraph("Name: ________________________________", style="BodyCenter", align="center", spacing_after=50),
            paragraph("Roll Number: _________________________", style="BodyCenter", align="center", spacing_after=50),
            paragraph("Section / Batch: ______________________", style="BodyCenter", align="center", spacing_after=250),
            paragraph("Guided By", style="SubheadingCenter", align="center", spacing_after=80),
            paragraph("Faculty Name: _________________________", style="BodyCenter", align="center", spacing_after=50),
            paragraph("Department: ___________________________", style="BodyCenter", align="center", spacing_after=320),
            paragraph("Department of Computer Science / Information Technology", style="SmallCenter", align="center", spacing_after=50),
            paragraph("April 2026", style="SmallCenter", align="center", spacing_after=0),
            page_break(),
        ]
    )

    parts.extend(
        [
            paragraph("CERTIFICATE", style="Heading1Center", align="center", spacing_after=200),
            paragraph(
                "This is to certify that the project titled “Smart Resource Allocation System (Room / Lab / Equipment Booking)” is a bona fide work carried out by the above student(s) as part of the Web Programming Lab course requirements. The project has been developed using the prescribed technologies and demonstrates a complete web application with frontend, backend, database integration, AJAX-based interaction, and REST API support.",
                style="BodyText",
                spacing_after=180,
            ),
            paragraph(
                "The work presented in this report is suitable for academic evaluation and project demonstration.",
                style="BodyText",
                spacing_after=420,
            ),
            paragraph("Faculty Signature: ____________________", style="BodyText", spacing_after=120),
            paragraph("Course Instructor: ____________________", style="BodyText", spacing_after=120),
            paragraph("Date: _________________________________", style="BodyText", spacing_after=0),
            page_break(),
            paragraph("DECLARATION", style="Heading1Center", align="center", spacing_after=200),
            paragraph(
                "I hereby declare that the project report titled “Smart Resource Allocation System (Room / Lab / Equipment Booking)” is my original work and has been prepared based on the application designed and implemented for the Web Programming Lab course. All external references used for realistic data seeding and contextual grounding have been properly acknowledged in the references section.",
                style="BodyText",
                spacing_after=220,
            ),
            paragraph("Student Signature: ____________________", style="BodyText", spacing_after=120),
            paragraph("Name: _________________________________", style="BodyText", spacing_after=120),
            paragraph("Date: _________________________________", style="BodyText", spacing_after=0),
            page_break(),
            paragraph("ACKNOWLEDGEMENT", style="Heading1Center", align="center", spacing_after=200),
            paragraph(
                "I express sincere gratitude to the course instructor and department faculty for their guidance during the development of this project. Their support made it possible to design a complete application that combines frontend development, backend logic, database design, and API-based interaction in a single system.",
                style="BodyText",
                spacing_after=140,
            ),
            paragraph(
                "I also acknowledge the availability of public institutional and product references that helped create a more realistic demonstration dataset for the project. These references supported the academic objective of building a practical and believable booking portal.",
                style="BodyText",
                spacing_after=0,
            ),
            page_break(),
        ]
    )

    parts.extend(
        [
            paragraph("ABSTRACT", style="Heading1Center", align="center", spacing_after=180),
            paragraph(
                "The Smart Resource Allocation System is a full-stack web application developed for booking rooms, laboratories, and equipment in a centralized manner. The system was built to solve common institutional problems such as double-booking, poor visibility of available slots, approval delays, and inconsistent manual scheduling practices. The application enables users to browse resources, check live availability, submit booking requests, and manage reservations through an interactive and responsive interface.",
                style="BodyText",
                spacing_after=140,
            ),
            paragraph(
                "The implementation integrates HTML, CSS, JavaScript, jQuery, AJAX, Bootstrap via CDN, Django, Django REST Framework, MySQL, and Django ORM. The frontend communicates with the backend asynchronously for availability checks and dynamic updates, while model-level validation ensures data consistency and prevents invalid reservations. The final system includes authentication, CRUD operations, search and filtering, conflict detection, approval workflow, and REST API endpoints.",
                style="BodyText",
                spacing_after=140,
            ),
            paragraph(
                "To improve realism during demonstration, the project uses a hybrid seed dataset that combines real public resource names with curated scheduling and operational details. The completed application demonstrates all major requirements of the Web Programming Lab and is suitable for practical evaluation, viva discussion, and live presentation.",
                style="BodyText",
                spacing_after=0,
            ),
            page_break(),
            paragraph("TABLE OF CONTENTS", style="Heading1Center", align="center", spacing_after=160),
        ]
    )

    toc_items = [
        "1. Introduction",
        "2. Problem Statement",
        "3. Objectives and Scope",
        "4. Technology Stack",
        "5. System Architecture and Workflow",
        "6. Functional Modules",
        "7. Database Design",
        "8. Validation Rules and Smart Allocation Logic",
        "9. REST API and AJAX Integration",
        "10. User Interface Design",
        "11. Realistic Dataset Strategy",
        "12. Results and Screenshots",
        "13. Testing and Verification",
        "14. Requirement Fulfilment Matrix",
        "15. Conclusion",
        "16. References",
    ]
    parts.extend(bullet_items(toc_items))
    parts.append(page_break())

    parts.extend(
        [
            paragraph("1. INTRODUCTION", style="Heading1", keep_next=True, spacing_after=120),
            paragraph(
                "The Smart Resource Allocation System was developed as a complete web application for managing the reservation of shared resources such as seminar halls, software laboratories, research labs, and portable equipment. In many academic environments, these resources are still allocated using paper registers, spreadsheets, or informal staff communication. Such methods are inefficient, difficult to track, and highly prone to clashes. The purpose of this project is to replace that fragmented process with a centralized booking system that is easy to use, technically robust, and aligned with modern web-application practices.",
                style="BodyText",
                spacing_after=120,
            ),
            paragraph(
                "The project also serves as a practical demonstration of the technologies prescribed in the Web Programming Lab guideline. It combines frontend design, client-side interactivity, AJAX requests, REST API usage, Django backend processing, and MySQL database integration in a single working system. The final result is not a static prototype; it behaves like a real booking portal with validation, role-aware controls, and realistic demonstration data.",
                style="BodyText",
                spacing_after=0,
            ),
            paragraph("2. PROBLEM STATEMENT", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "Shared institutional resources are usually limited and often requested by multiple users at overlapping times. When booking is handled manually, several practical issues arise: users may unknowingly choose occupied time slots, administrators may struggle to track pending approvals, and there may be no reliable historical record of who reserved what and when. These problems reduce operational efficiency and make resource planning difficult.",
                style="BodyText",
                spacing_after=120,
            ),
            paragraph(
                "The problem addressed in this project is therefore the lack of a centralized, validated, and interactive booking system for rooms, laboratories, and equipment. The project aims to provide a web-based solution that eliminates clashes, gives users visibility into availability, and supports an approval workflow for controlled resource access.",
                style="BodyText",
                spacing_after=0,
            ),
            paragraph("3. OBJECTIVES AND SCOPE", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph("The primary objectives of the project are listed below:", style="BodyText", spacing_after=80),
        ]
    )

    parts.extend(
        bullet_items(
            [
                "Create a complete web application for room, lab, and equipment booking.",
                "Prevent overlapping bookings through automated validation logic.",
                "Provide login, registration, and role-aware user behavior.",
                "Support asynchronous frontend interaction using jQuery and AJAX.",
                "Expose RESTful APIs that the frontend can consume directly.",
                "Use MySQL with Django ORM for persistent and structured storage.",
                "Present a professional and responsive user interface using Bootstrap via CDN.",
            ]
        )
    )

    parts.extend(
        [
            paragraph(
                "The scope of the system includes booking creation, booking updates, booking cancellation, approval workflow, resource management, live availability checks, search and filtering, and a demonstration-ready landing page. The intended users include students, staff, and administrators. Students mainly submit and manage requests, while staff and admins manage resources and handle approval operations.",
                style="BodyText",
                spacing_after=0,
            ),
            paragraph("4. TECHNOLOGY STACK", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
        ]
    )

    parts.append(
        table(
            [
                ["Technology", "Purpose in the Project", "Reason for Selection"],
                ["HTML", "Page structure for templates such as login, dashboard, resources, and bookings", "Required for building structured web pages"],
                ["CSS", "Custom visual styling and layout refinement", "Improves presentation quality and usability"],
                ["Bootstrap 5 via CDN", "Responsive grid, navigation, cards, forms, and utility classes", "Meets the lab requirement and keeps frontend integration simple"],
                ["JavaScript", "Client-side interaction, duration preview, live feedback", "Adds responsiveness and better user experience"],
                ["jQuery", "AJAX calls and DOM updates", "Directly demonstrates the lab topics covered"],
                ["AJAX", "Asynchronous availability checks and status updates", "Allows dynamic interaction without page reload"],
                ["Django", "Routing, templates, authentication, forms, and server-side processing", "Main backend framework for the application"],
                ["Django REST Framework", "Resource, booking, and summary APIs", "Implements the RESTful API requirement"],
                ["MySQL", "Persistent relational database storage", "Required database backend for the project"],
                ["Django ORM", "Schema definition, constraints, and database operations", "Connects the application cleanly to MySQL"],
            ],
            widths=[1800, 3500, 3200],
        )
    )

    parts.extend(
        [
            paragraph(
                "Bootstrap and jQuery are included through CDN links, in line with the project requirement to use CDN-based frontend libraries instead of bundling local copies. This reflects a realistic deployment style for academic web applications.",
                style="BodyText",
                spacing_before=80,
                spacing_after=0,
            ),
            paragraph("5. SYSTEM ARCHITECTURE AND WORKFLOW", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "The system follows a layered web-application architecture. The presentation layer is implemented using Django templates, Bootstrap, CSS, JavaScript, and jQuery. The application layer is handled through Django views, forms, and routing. Business logic such as timing validation, capacity checks, and conflict detection is enforced in the model layer. Data persistence is handled by MySQL, with Django ORM providing the object-relational mapping.",
                style="BodyText",
                spacing_after=100,
            ),
        ]
    )

    parts.append(
        table(
            [
                ["Layer", "Main Components", "Responsibility"],
                ["Presentation Layer", "Templates, Bootstrap, CSS, JavaScript, jQuery", "Renders pages, forms, and responsive user interactions"],
                ["Application Layer", "Django views, forms, URL configuration", "Processes requests and coordinates page behavior"],
                ["Business Logic Layer", "Models and helper functions", "Enforces booking rules and smart allocation behavior"],
                ["API Layer", "DRF viewsets and summary API", "Provides JSON data to the frontend"],
                ["Data Layer", "MySQL and Django ORM", "Stores users, resources, bookings, and workflow information"],
            ],
            widths=[1800, 3000, 3700],
        )
    )

    parts.extend(
        [
            paragraph("Typical booking workflow:", style="BodyText", spacing_before=80, spacing_after=80),
        ]
    )
    parts.extend(
        bullet_items(
            [
                "User signs in and opens the dashboard or resource directory.",
                "User selects a resource and fills the booking form with date, time, and attendee details.",
                "Frontend sends an AJAX request to the availability endpoint.",
                "Backend validates the request against timing, capacity, and overlap rules.",
                "System returns availability status, duration, estimated cost, and alternate slots if needed.",
                "User submits the booking request, which then moves through the approval workflow where applicable.",
            ]
        )
    )

    parts.extend(
        [
            paragraph("6. FUNCTIONAL MODULES", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph("The completed application contains the following main modules:", style="BodyText", spacing_after=80),
        ]
    )

    parts.append(
        table(
            [
                ["Module", "Implemented Capability"],
                ["Authentication", "User registration, login, logout, and session-based access control"],
                ["User Profiles", "Role, department, phone details, and manager capability checks"],
                ["Resource Management", "Create, read, update, delete operations for rooms, labs, and equipment"],
                ["Booking Management", "Create, update, cancel, approve, reject, and complete booking requests"],
                ["Search and Filtering", "Keyword, type, status, and capacity-based resource filtering"],
                ["Availability Check", "Live AJAX-based validation with clash detection and suggestions"],
                ["REST API", "Resource API, booking API, and dashboard summary API"],
                ["Seed Data", "Realistic demo data using public reference names plus curated operations data"],
            ],
            widths=[2500, 5500],
        )
    )

    parts.extend(
        [
            paragraph("7. DATABASE DESIGN", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "The database schema is based on relational entities that reflect the actual workflow of the system. User accounts are handled through Django's built-in authentication tables, while application-specific data is stored in scheduler tables. The design allows one user to create multiple bookings and one resource to be linked with many bookings over time.",
                style="BodyText",
                spacing_after=100,
            ),
        ]
    )

    parts.append(
        table(
            [
                ["Table", "Description", "Key Fields"],
                ["auth_user", "Stores login and authentication data", "username, password, email, is_staff"],
                ["scheduler_userprofile", "Extends the user with role and contact information", "role, department, phone"],
                ["scheduler_resource", "Stores room, lab, and equipment inventory", "name, resource_type, building, capacity, hourly_cost, available_from, available_until, status"],
                ["scheduler_booking", "Stores booking request details and approval workflow", "user_id, resource_id, title, purpose, attendees, requested_start, requested_end, priority, status, approved_by_id"],
            ],
            widths=[1800, 3000, 3700],
        )
    )

    parts.extend(
        [
            paragraph("Relationship summary:", style="BodyText", spacing_before=80, spacing_after=80),
        ]
    )
    parts.extend(
        bullet_items(
            [
                "One user has one user profile.",
                "One user can create many bookings.",
                "One resource can be booked many times across different dates.",
                "One staff or admin user can approve multiple bookings.",
            ]
        )
    )

    parts.extend(
        [
            paragraph("8. VALIDATION RULES AND SMART ALLOCATION LOGIC", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "A major strength of the project is that the booking logic behaves like a real scheduling portal. The system does not merely collect form data; it actively checks whether the request is valid and whether the resource is actually available. These checks are enforced at the model layer so that they apply consistently to forms, AJAX interactions, and API usage.",
                style="BodyText",
                spacing_after=100,
            ),
        ]
    )

    parts.append(
        table(
            [
                ["Rule", "Effect in the Application"],
                ["No past active bookings", "Pending and approved bookings cannot be created in the past"],
                ["Same-day reservation", "Start and end times must fall on the same date"],
                ["09:00 AM to 09:00 PM access window", "Bookings outside the institutional access window are rejected"],
                ["Resource-specific time window", "Booking must fit within the selected resource's availability period"],
                ["Capacity check", "Attendee count cannot exceed the selected resource capacity"],
                ["Resource status check", "Inactive or maintenance resources cannot be booked"],
                ["Overlap detection", "Conflicting pending or approved bookings return No availability"],
                ["Suggestion engine", "When a slot is occupied, the system suggests the next available alternatives"],
            ],
            widths=[2800, 5200],
        )
    )

    parts.extend(
        [
            paragraph("9. REST API AND AJAX INTEGRATION", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "The project includes both REST API endpoints and dedicated AJAX endpoints. These are used by the frontend to deliver a smoother user experience. Instead of reloading the page after every interaction, the application can request data in the background and update only the relevant portion of the interface.",
                style="BodyText",
                spacing_after=100,
            ),
        ]
    )

    parts.append(
        table(
            [
                ["Endpoint", "Type", "Purpose"],
                ["/api/resources/", "REST API", "Returns resource data and supports resource operations"],
                ["/api/bookings/", "REST API", "Returns booking data and supports booking operations"],
                ["/api/dashboard-summary/", "REST API", "Returns summary data used by the homepage and dashboard sections"],
                ["/ajax/availability/", "AJAX endpoint", "Checks selected slot availability, duration, cost, and suggestions"],
                ["/ajax/bookings/<id>/status/", "AJAX endpoint", "Processes asynchronous status changes for bookings"],
            ],
            widths=[2400, 1700, 4900],
        )
    )

    parts.extend(
        [
            paragraph("10. USER INTERFACE DESIGN", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "The interface was refined to look like a practical booking website rather than a graph-heavy analytics dashboard. The homepage now focuses on featured resources, category entry points, upcoming reservations, pending requests, and service-oriented actions. This makes the system easier to present and more believable as a real institutional portal.",
                style="BodyText",
                spacing_after=100,
            ),
        ]
    )
    parts.extend(
        bullet_items(
            [
                "Responsive layout built with Bootstrap components loaded through CDN.",
                "Resource cards that display category, location, status, and operational details.",
                "Booking form with live duration and estimated cost preview.",
                "Clear no-availability messaging when a slot clashes with an existing booking.",
                "Role-aware navigation and action visibility for students, managers, and admins.",
            ]
        )
    )

    parts.extend(
        [
            paragraph("11. REALISTIC DATASET STRATEGY", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "To avoid an empty or unrealistic demonstration, the application uses richer seed data. The seeded dataset includes 24 resources and 155 bookings. Resource naming is grounded in public institutional and product references such as IIT Bombay lab names, IIT Madras seminar hall references, and real conferencing products like Logitech Rally Bar Huddle, Shure MXA920, and Barco ClickShare. Internal locations, pricing, and booking schedules are curated for academic demonstration.",
                style="BodyText",
                spacing_after=100,
            ),
        ]
    )

    parts.append(
        table(
            [
                ["Dataset Aspect", "Implemented Detail"],
                ["Seeded resources", "24 records across room, lab, and equipment categories"],
                ["Seeded bookings", "155 records to demonstrate clashes, approvals, and upcoming schedules"],
                ["Source-backed names", "Institutional labs, seminar halls, and commercial AV equipment references"],
                ["Curated operational data", "Availability windows, locations, costs, and schedules tailored for the project"],
            ],
            widths=[2600, 5400],
        )
    )

    parts.extend(
        [
            paragraph("12. RESULTS AND SCREENSHOTS", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "The following placeholders are included so the report keeps a clean professional structure while still reserving space for final output screens from the project. You can replace these boxes later with actual screenshots if needed without changing the report flow.",
                style="BodyText",
                spacing_after=100,
            ),
            placeholder_figure(
                "Figure 1. Homepage / Booking Portal View",
                "Suggested screenshot: hero section, featured resources, available items, and upcoming bookings.",
            ),
            paragraph("", style="BodyText", spacing_after=80),
            placeholder_figure(
                "Figure 2. Resource Directory with Search and Filters",
                "Suggested screenshot: resource list with AJAX-based filtering and status badges.",
            ),
            paragraph("", style="BodyText", spacing_after=80),
            placeholder_figure(
                "Figure 3. Booking Form with Validation Result",
                "Suggested screenshot: duration preview, estimated cost, and no-availability conflict message.",
            ),
            paragraph("", style="BodyText", spacing_after=80),
            placeholder_figure(
                "Figure 4. Booking List / Approval Workflow",
                "Suggested screenshot: booking statuses such as pending, approved, rejected, or completed.",
            ),
            paragraph("13. TESTING AND VERIFICATION", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "Testing focused on the most important system behaviors: preventing clashes, enforcing capacity, rejecting past bookings, respecting access-hour limits, and ensuring API responses include the expected data. In addition to the automated tests, the startup flow, migrations, and seed data process were verified during development.",
                style="BodyText",
                spacing_after=100,
            ),
        ]
    )

    parts.append(
        table(
            [
                ["Verification Item", "Expected Outcome", "Result"],
                ["Django system checks", "No model or configuration errors", "Passed"],
                ["Database migrations", "All schema changes applied correctly", "Passed"],
                ["Seed data loading", "Rich demo dataset created successfully", "Passed"],
                ["Overlap booking test", "Clashing slot must be rejected", "Passed"],
                ["Past booking test", "Past reservation should not be allowed", "Passed"],
                ["Access window test", "Bookings outside 09:00 AM to 09:00 PM should fail", "Passed"],
                ["Availability API test", "Conflict request should return No availability and suggestions", "Passed"],
            ],
            widths=[2400, 4200, 1400],
        )
    )

    parts.extend(
        [
            paragraph("14. REQUIREMENT FULFILMENT MATRIX", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
        ]
    )

    parts.append(
        table(
            [
                ["Guideline Requirement", "How the Project Satisfies It"],
                ["HTML", "Templates are used to build structured pages for authentication, resources, bookings, and dashboard views"],
                ["CSS", "Custom CSS improves layout, spacing, and overall presentation quality"],
                ["JavaScript", "Client-side logic handles interactivity and live booking previews"],
                ["AJAX", "Availability checks and status changes occur without full page reload"],
                ["jQuery", "Used to trigger asynchronous requests and update the DOM"],
                ["Bootstrap", "Loaded through CDN and used throughout the responsive interface"],
                ["Django", "Forms, authentication, routing, views, and business logic are implemented using Django"],
                ["RESTful API", "Resources, bookings, and dashboard summary are exposed through DRF endpoints"],
                ["MySQL", "All persistent data is stored in MySQL using Django ORM"],
                ["CRUD functionality", "Both resources and bookings support create, read, update, and delete workflows"],
                ["Search / filtering", "Resource list supports multiple filters and search criteria"],
            ],
            widths=[2600, 5400],
        )
    )

    parts.extend(
        [
            paragraph("15. CONCLUSION", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
            paragraph(
                "The Smart Resource Allocation System successfully demonstrates a complete and practical implementation of the technologies covered in the Web Programming Lab. The project goes beyond a simple demonstration by including real validation logic, AJAX-driven behavior, REST APIs, MySQL integration, and a user-friendly website experience. It is suitable for live demonstration, technical discussion, and academic evaluation.",
                style="BodyText",
                spacing_after=120,
            ),
            paragraph(
                "Future improvements can include calendar views, waitlist support, email notifications, export features, and more advanced resource analytics. Even in its current form, however, the system already fulfils the required course technologies and presents a cohesive full-stack application.",
                style="BodyText",
                spacing_after=0,
            ),
            paragraph("16. REFERENCES", style="Heading1", keep_next=True, spacing_before=160, spacing_after=120),
        ]
    )

    parts.extend(
        bullet_items(
            [
                "IIT Bombay CSE lab booking policy: https://systems.cse.iitb.ac.in/systems/lab_booking_policy.html",
                "IIT Bombay CSE research labs: https://www.cse.iitb.ac.in/old/research/labs.php",
                "IIT Bombay Laboratory for Intelligent Internet Research: https://www.cse.iitb.ac.in/~laiir/",
                "IIT Bombay EE electronic systems labs: https://www.ee.iitb.ac.in/web/research/electronic-systems-ee5/",
                "IIT Madras seminar hall reference pages: https://joyofgiving.alumni.iitm.ac.in/",
                "Logitech Rally Bar Huddle: https://www.logitech.com/products/video-conferencing/room-solutions/rallybarhuddle",
                "Shure MXA920: https://www.shure.com/en-GB/products/microphones/mxa920",
                "Barco ClickShare: https://www.barco.com/en/products/clickshare-conferencing-collaboration/management-platforms/clickshare-configurator",
            ]
        )
    )

    section = """
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1080" w:right="900" w:bottom="1080" w:left="900" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
    """
    body = "".join(parts) + section
    return (
        xml_header()
        + f'<w:document xmlns:w="{NS["w"]}" xmlns:r="{NS["r"]}"><w:body>{body}</w:body></w:document>'
    )


def build_styles_xml() -> str:
    return xml_header() + f"""
<w:styles xmlns:w="{NS['w']}">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri"/>
        <w:sz w:val="22"/>
        <w:szCs w:val="22"/>
        <w:color w:val="1F1F1F"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:after="120" w:line="360" w:lineRule="auto"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>

  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>

  <w:style w:type="paragraph" w:styleId="TitleCenter">
    <w:name w:val="Title Center"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="160"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="34"/><w:szCs w:val="34"/></w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="CoverHeading">
    <w:name w:val="Cover Heading"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="140"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="0B4F82"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="SectionCenter">
    <w:name w:val="Section Center"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="SubtitleCenter">
    <w:name w:val="Subtitle Center"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:rPr><w:i/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="SubheadingCenter">
    <w:name w:val="Subheading Center"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="BodyCenter">
    <w:name w:val="Body Center"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/></w:pPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="SmallCenter">
    <w:name w:val="Small Center"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/><w:color w:val="555555"/></w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:before="200" w:after="140"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="0B4F82"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading1Center">
    <w:name w:val="Heading 1 Center"/>
    <w:basedOn w:val="Heading1"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:before="200" w:after="140"/></w:pPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="BodyText">
    <w:name w:val="Body Text"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/></w:pPr>
  </w:style>
</w:styles>
"""


def build_content_types() -> str:
    return xml_header() + """
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""


def build_root_rels() -> str:
    return xml_header() + """
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def build_document_rels() -> str:
    return xml_header() + """
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""


def build_core_props() -> str:
    return xml_header() + """
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Smart Resource Allocation System Project Report</dc:title>
  <dc:subject>Web Programming Lab Project Report</dc:subject>
  <dc:creator>Codex</dc:creator>
  <cp:keywords>smart resource allocation, django, mysql, booking system</cp:keywords>
  <dc:description>Professional academic project report for the Smart Resource Allocation System.</dc:description>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
</cp:coreProperties>
"""


def build_app_props() -> str:
    return xml_header() + """
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Sections</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>15</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="1" baseType="lpstr">
      <vt:lpstr>Smart Resource Allocation System Project Report</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
  <Company>MIT Bengaluru</Company>
</Properties>
"""


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", build_content_types())
        docx.writestr("_rels/.rels", build_root_rels())
        docx.writestr("word/document.xml", build_document_xml())
        docx.writestr("word/styles.xml", build_styles_xml())
        docx.writestr("word/_rels/document.xml.rels", build_document_rels())
        docx.writestr("docProps/core.xml", build_core_props())
        docx.writestr("docProps/app.xml", build_app_props())
    print(OUTPUT)


if __name__ == "__main__":
    main()
