# Smart Resource Allocation

Smart Resource Allocation is a Django-based web application for managing shared resources such as rooms, labs, and equipment through a centralized booking workflow. The project combines resource management, booking validation, conflict prevention, role-based access patterns, and API support in a single system designed for structured scheduling scenarios.

## Overview

The application is built to help users discover available resources, submit booking requests, and manage allocations with clear scheduling rules. It also supports operational workflows such as approvals, overlap checks, dashboard visibility, and resource-level capacity constraints.

## Key Features

- Resource management for rooms, labs, and equipment
- Booking creation with validation and conflict detection
- Capacity-aware scheduling rules
- Approval-oriented booking workflow
- Dashboard views for allocation visibility
- API endpoints for resources, bookings, and summary data
- MySQL-backed persistence for local project execution

## Tech Stack

- Python
- Django
- Django REST Framework
- MySQL
- HTML, CSS, JavaScript
- Bootstrap 5
- jQuery and AJAX

## Project Structure

```text
smart_resource_allocation/
├── config/                    # Django project settings, URLs, ASGI, WSGI
├── docs/                      # Project notes and report material
├── logs/                      # Runtime logs
├── mysql-data/                # Project-local MySQL data directory
├── mysql-run/                 # MySQL runtime files
├── mysql57_backend/           # Custom MySQL backend compatibility layer
├── scheduler/                 # Core booking and scheduling app
│   ├── management/commands/   # Custom management commands such as seed_data
│   ├── migrations/            # Django migrations
│   ├── admin.py
│   ├── api_urls.py
│   ├── forms.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── scripts/                   # Startup and utility scripts
│   ├── start_app.sh
│   ├── start_mysql.sh
│   └── stop_mysql.sh
├── static/                    # Static assets
│   ├── css/
│   └── js/
├── templates/                 # Django templates
│   ├── registration/
│   └── scheduler/
├── manage.py
├── requirements.txt
└── README.md
```

## Getting Started

From the project root, use the application startup script:

```bash
cd "/Users/boolu/Desktop/simulations/files (1)/smart_resource_allocation"
./scripts/start_app.sh
```

## What `start_app.sh` Does

The startup script handles the local development flow automatically:

```bash
./scripts/start_mysql.sh
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_data
../.venv/bin/python manage.py runserver localhost:8000
```

This means the script:

- starts the local MySQL service
- applies migrations
- loads seed data
- launches the Django development server on `localhost:8000`

## Manual Reference

If you ever need to inspect the startup sequence manually, the script currently uses the project-adjacent virtual environment Python binary:

```bash
../.venv/bin/python
```

However, the recommended way to start the project is still:

```bash
./scripts/start_app.sh
```

## Application Areas

- Resource catalog and availability management
- Booking request creation and editing
- Schedule validation and overlap prevention
- Dashboard monitoring for active requests and usage
- REST API access for selected booking and resource data

## Development Notes

- The project uses a project-local MySQL setup rather than a default SQLite workflow
- Startup is script-driven, so the README documents `./scripts/start_app.sh` as the primary entry point
- Runtime folders such as MySQL data, logs, caches, and local environment files should not be committed to version control

## Suggested Git Exclusions

When preparing the repository for GitHub, avoid committing local runtime and generated content such as:

- `mysql-data/`
- `mysql-run/`
- `mysql-tmp/`
- `logs/`
- `__pycache__/`
- `.venv/`
- local document exports such as `.docx` and `.pdf` files

## License

This project is currently intended for academic, learning, and portfolio use unless a different license is added explicitly.
