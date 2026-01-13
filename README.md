# Tech Stack & Libraries Used
## Backend
- Python 3.11
- Django 5
- Django REST Framework – REST API framework
- PostgreSQL – Relational database

## Dependency & Environment Management
- uv – Modern Python dependency manager and virtual environment
- django-environ – Environment variable management
- pycobinary – Binary utilities for fast processing

## API Features
- Pagination – Using DRF pagination
- Filtering – Using django-filter
- Atomic Transactions – For data consistency
- Optimistic Concurrency Control – Version-based updates

## DevOps
- Docker & Docker Compose – Containerized development & deployment

## API Testing
- Postman – API testing with exported collection

# Project Structure

```
spv-issue-tracker/
│
├── .venv/                  # Local virtual environment (uv-managed)
├── postman/               # Postman API collection
│   └── spv-issue-tracker.postman_collection.json
│
├── src/                   # Django project source
│   ├── issue_tracker/    # Django settings & config
│   ├── issues/           # Issues app
│   ├── comments/         # Comments app
│   ├── labels/           # Labels app
│   ├── reports/          # Reports app
│   ├── users/            # Custom user app
│   ├── manage.py
│   └── seed.py           # Database seeding script
│
├── .env.dev               # Environment variables
├── docker-compose.yml    # Docker services (API + PostgreSQL)
├── Dockerfile            # Django API container
├── entrypoint.sh         # Container startup script
├── pyproject.toml        # Python project config (uv)
├── uv.lock               # Locked dependency versions
├── requirements.txt     # Traditional dependency list
├── .python-version       # Python version pin
└── README.md             # Project documentation
```

## Why uv is used in this project

uv is a modern replacement for pip + virtualenv.

It provides:
- Ultra-fast dependency installation
- Built-in virtual environment management
- Lockfile support (reproducible builds)
- Production-grade dependency resolution

*It is written in Rust and is much faster than pip.*


# Project Set Up

## 1] Build and Start
```bash
docker-compose up --build
```

## 2] Seed data
```bash
docker exec -it issue_tracker_api sh

# inside of docker container terminal
ls
# output -> __init__.py    comments       issue_tracker  issues         labels         manage.py      reports        seed.py        users
uv run python seed.py

# to exit docker terminal
exit
```

## 3] Stop
```bash
docker-compose down
```

## 4] Postman Endpoints

- Found inside of folder named **postman**.
- import than json file in Postman/Insomnia/Requestly.

