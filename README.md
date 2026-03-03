<p align="center">
  <a href="https://github.com/anthonysawyer94/gamestream">
    <img src="https://raw.githubusercontent.com/anthonysawyer94/gamestream/main/assets/gamestream-banner.png" alt="GameStream logo">
  </a>
</p>
<p align="center">Never miss a game on your streaming services.</p>
<p align="center">
  <a href="https://github.com/anthonysawyer94/gamestream/actions/workflows/deploy.yml"><img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/anthonysawyer94/gamestream/deploy.yml?style=flat-square" /></a>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/python-3.14-blue?style=flat-square" /></a>
  <a href="https://www.djangoproject.com/"><img alt="Django" src="https://img.shields.io/badge/Django-6.0-green?style=flat-square" /></a>
  <a href="https://github.com/anthonysawyer94/gamestream/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/anthonysawyer94/gamestream?style=flat-square" /></a>
  <a href="https://github.com/anthonysawyer94/gamestream/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/anthonysawyer94/gamestream?style=flat-square" /></a>
</p>

---

## About

GameStream shows you which NBA, MLB, NHL, and NCAA basketball games are streaming on the services you subscribe to. Connect your accounts, select your streaming services, and never miss a game again.

## Features

- **Personalized Schedule** - See games only on services you subscribe to
- **Multi-Sport Support** - NBA, MLB, NHL, and NCAA Basketball
- **User Accounts** - Save your streaming service preferences
- **Full Schedule View** - Browse all games with filters by sport and service
- **Automatic Updates** - Fetches latest schedules from ESPN API

## Quick Start

```bash
# Clone the repository
git clone https://github.com/anthonysawyer94/gamestream.git
cd gamestream

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django django-crispy-forms crispy-bootstrap5 requests

# Run migrations
python3 manage.py migrate

# Seed streaming services
python3 manage.py seed_services

# Fetch today's games
python3 manage.py fetch_schedule

# Start the server
python3 manage.py runserver
```

Visit `http://localhost:8000` to view the app.

## Tech Stack

- **Backend:** Django 6.0, Python 3.14
- **Database:** SQLite (development)
- **Frontend:** Django Templates, Bootstrap 5
- **Data Source:** ESPN Unofficial API
- **Deployment:** Docker, GitHub Actions, AWS EC2

## Contributing

Contributions are welcome! Please read our [AGENTS.md](./AGENTS.md) for development guidelines and coding standards.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
