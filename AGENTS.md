# AGENTS.md - Development Guidelines

This document provides guidelines for agents working on this Django sports streaming schedule project.

## Project Overview

- **Framework**: Django 6.0 with Python 3.14
- **Database**: SQLite (development)
- **Frontend**: Django templates with Bootstrap 5
- **API**: ESPN unofficial API for sports schedules

## Build/Lint/Test Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python3 manage.py runserver

# Run all tests
python3 manage.py test

# Run tests for specific app
python3 manage.py test schedules
python3 manage.py test services

# Run a single test (full path)
python3 manage.py test schedules.tests.ScheduleViewTest.test_home_page

# Run with verbosity
python3 manage.py test -v 2

# Django system check
python3 manage.py check
python3 manage.py check --deploy

# Database migrations
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py showmigrations

# Management commands
python3 manage.py seed_services
python3 manage.py fetch_schedule
python3 manage.py fetch_schedule --days 14
```

## Fetching Schedule

After DB changes (new sports, models, etc.), run fetch_schedule to populate games:

```bash
# Local
python3 manage.py fetch_schedule --days 7

# Production (EC2)
docker-compose exec -T web python manage.py fetch_schedule --days 7
```

The command:
- Fetches games for all configured sports (NBA, MLB, NHL, NCAA, soccer leagues)
- Only saves games with known streaming services (filters OTA broadcasts)
- Automatically deletes games older than 2 days
- Run manually after DB changes, or set up a daily cron job on EC2

## Code Style Guidelines

### Python Style

- Follow **PEP 8** with 100 character line limit
- Use **Black** for formatting: `black .`
- Use **isort** for import sorting: `isort .`
- Avoid adding comments unless explicitly requested

### Imports (in order)

```python
import datetime
from datetime import timedelta
import requests
from django.db import models
from django.shortcuts import render
from schedules.models import Game, Team
from services.models import StreamingService
```

### Naming Conventions

- **Models**: PascalCase (`StreamingService`, `UserSubscription`)
- **Functions**: snake_case (`get_or_create_team`)
- **Constants**: UPPER_SNAKE_CASE (`BROADCAST_MAPPING`)
- **Template variables**: snake_case (`games_by_date`)

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

### Views & Templates

Use function-based views, `@login_required`, extend `base.html`, use Bootstrap 5.

Templates should extend `base.html` and define a `content` block:

```django
{% extends 'base.html' %}

{% block content %}
<div class="container">
    <h1>Page Title</h1>
</div>
{% endblock %}
```

### Admin Registration

Register models in `admin.py`:

```python
from django.contrib import admin
from .models import Game, Team, Sport

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'start_time', 'streaming_service')
    list_filter = ('sport', 'streaming_service')
    search_fields = ('home_team__name', 'away_team__name')
```

### Error Handling

- Use `try/except` with specific exception types
- Log warnings for non-critical errors
- Handle API failures gracefully
- In management commands: use `self.stdout.write(self.style.WARNING(...))` for errors
- In views/code: use Python's `logging` module

### Logging

Use Django's logging module in views and services:

```python
import logging

logger = logging.getLogger(__name__)

def some_view(request):
    try:
        # code
    except SomeException as e:
        logger.warning(f"Failed to process request: {e}")
```

### API Integration

Always set timeouts on HTTP requests (`timeout=30`) and handle errors:

```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    logger.warning(f"Error fetching {url}: {e}")
    return
```

## File Organization

```
project/
├── config/              # Django settings & URLs
├── services/           # Streaming services app
├── schedules/          # Games/schedule app
├── templates/
│   └── base.html
└── venv/
```

## Testing Guidelines

Tests use a separate SQLite database (fresh each run). Use `setUp()` for test data.

```python
from django.test import TestCase

class ScheduleViewTest(TestCase):
    def test_home_page_returns_games(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
```

## Adding New Features

1. Create models → 2. Run migrations → 3. Add views/URLs → 4. Create templates → 5. Add tests

## Quick Reference

| Task    | Command                                       |
| ------- | --------------------------------------------- |
| Server  | `python3 manage.py runserver`                 |
| Tests   | `python3 manage.py test`                      |
| Migrate | `python3 manage.py makemigrations && migrate` |
