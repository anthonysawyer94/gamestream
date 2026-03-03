# AGENTS.md - Development Guidelines

This document provides guidelines for agents working on this Django sports streaming schedule project.

## Project Overview

- **Framework**: Django 6.0 with Python 3.14
- **Database**: SQLite (development)
- **Frontend**: Django templates with Bootstrap 5
- **API**: ESPN unofficial API for sports schedules

## Build/Lint/Test Commands

### Running the Development Server

```bash
source venv/bin/activate
python3 manage.py runserver
```

### Running Tests

```bash
# Run all tests
python3 manage.py test

# Run tests for a specific app
python3 manage.py test schedules
python3 manage.py test services

# Run a single test
python3 manage.py test schedules.tests.ScheduleViewTest.test_home_page
python3 manage.py test services.tests.UserSubscriptionTest.test_subscription_creation

# Run with verbosity
python3 manage.py test -v 2
```

### Database Migrations

```bash
# Create migrations
python3 manage.py makemigrations

# Apply migrations
python3 manage.py migrate

# Show migration status
python3 manage.py showmigrations
```

### Management Commands

```bash
# Seed streaming services
python3 manage.py seed_services

# Fetch schedule from ESPN API
python3 manage.py fetch_schedule
python3 manage.py fetch_schedule --days 14
```

### Django System Check

```bash
python3 manage.py check
python3 manage.py check --deploy
```

## Code Style Guidelines

### Python Style

- Follow **PEP 8** with 100 character line limit
- Use **Black** for formatting (if available): `black .`
- Use **isort** for import sorting: `isort .`

### Imports

```python
# Standard library first
import datetime
from datetime import timedelta

# Third-party imports
import requests
from django.db import models
from django.shortcuts import render

# Local imports
from schedules.models import Game, Team
from services.models import StreamingService
```

### Naming Conventions

- **Models**: PascalCase (e.g., `StreamingService`, `UserSubscription`)
- **Functions**: snake_case (e.g., `get_or_create_team`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `BROADCAST_MAPPING`)
- **Template variables**: snake_case (e.g., `games_by_date`)

### Django Best Practices

- Use `select_related()` for ForeignKey/OneToOne queries
- Use `prefetch_related()` for reverse ForeignKey and ManyToMany
- Always specify `on_delete` on ForeignKey fields
- Use `get_or_create()` or `update_or_create()` for idempotent operations

### Models

```python
class StreamingService(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = "Streaming Services"

    def __str__(self):
        return self.name
```

### Views

- Use function-based views for simple CRUD
- Use `@login_required` for protected views
- Always pass context to templates via `render(request, 'template.html', context)`
- Use `select_related` and `prefetch_related` to reduce queries

### Templates

- Extend `base.html` for consistent layout
- Use Bootstrap 5 classes
- Use Django template tags: `{% url %}`, `{% for %}`, `{% if %}`
- Access model fields directly (no complex logic in templates)

### Error Handling

- Use `try/except` with specific exception types
- Log warnings for non-critical errors
- Return user-friendly error messages in views
- Handle API failures gracefully in management commands

### API Integration

- Always set timeouts on HTTP requests (e.g., `timeout=30`)
- Handle HTTP errors with try/except
- Log errors but don't crash the application
- Use environment variables for API keys

```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    self.stdout.write(self.style.WARNING(f"Error fetching {url}: {e}"))
    return
```

### File Organization

```
project/
├── config/              # Django project settings
│   ├── settings.py
│   └── urls.py
├── services/            # Streaming services app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── management/commands/
├── schedules/           # Games/schedule app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── management/commands/
├── templates/
│   ├── base.html
│   └── ...
└── venv/               # Virtual environment
```

### Adding New Features

1. Create models in appropriate app
2. Run `makemigrations` and `migrate`
3. Add views and URL routes
4. Create templates
5. Add tests
6. Test locally with `runserver`

### Commit Message Format

```
<type>: <short description>

<optional body>

<optional footer>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Example:

```
feat: add user subscription model

Add UserSubscription model to link users with their
streaming services for personalized schedules.

Closes #12
```

## Testing Guidelines

### Writing Tests

```python
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

class ScheduleViewTest(TestCase):
    def setUp(self):
        # Create test data
        pass

    def test_home_page_returns_games(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_unauthenticated_user_sees_all_games(self):
        response = self.client.get('/')
        self.assertContains(response, 'NBA')
```

### Test Database

- Tests use separate SQLite database
- Database is created fresh for each test run
- Use `setUp()` to create test data

## Quick Reference

| Task       | Command                                                         |
| ---------- | --------------------------------------------------------------- |
| Server     | `python3 manage.py runserver`                                   |
| Tests      | `python3 manage.py test`                                        |
| Migrate    | `python3 manage.py makemigrations && python3 manage.py migrate` |
| Shell      | `python3 manage.py shell`                                       |
| Create app | `python3 manage.py startapp <app_name>`                         |
