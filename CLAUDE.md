# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

- **FastAPI** — async web framework (`app/main.py`)
- **SQLModel** — ORM models (SQLAlchemy + Pydantic), defined in `app/models/`
- **Alembic** — database migrations (`migrations/`)
- **Celery + Redis** — async task queue (`app/celery_app.py`, `app/tasks/`)
- **PostgreSQL** — primary database (port 5433 via Docker)
- **BeautifulSoup + requests** — recipe scraping from aniagotuje.pl (`app/tasks/scrape_recipies.py`)
- **uv** — package manager

## Environment

Requires a `.env` file with:
- `DATABASE_URL` — PostgreSQL connection string (e.g. `postgresql+psycopg://postgres:password@localhost:5433/postgres`)
- `REDIS_URL` — Redis connection string (e.g. `redis://localhost:6379`)

## Commands

```bash
# Start dependencies (PostgreSQL on :5433, Redis on :6379, CloudBeaver on :8978)
docker compose up -d

# Install dependencies
uv sync

# Run the API server
uv run fastapi dev app/main.py

# Run Celery worker
uv run celery -A app.celery_app.celery worker --loglevel=info

# Run Flower (Celery monitoring UI)
uv run celery -A app.celery_app.celery flower

# Run migrations
uv run alembic upgrade head

# Generate a new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Lint
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest
uv run pytest tests/path/to/test_file.py::test_name  # single test
```

## Architecture

### Request flow
`app/main.py` (FastAPI routes) → `app/db/engine.py` (session dependency) → `app/models/Recipe.py` (SQLModel ORM) → PostgreSQL

### Data flow for scraping
`app/tasks/scrape_recipies.py` fetches and parses aniagotuje.pl using BeautifulSoup, validates data through `app/services/scraper_schema.py` (Pydantic models), then writes to PostgreSQL directly via SQLModel sessions.

### Models
`Recipe` and `Ingredient` are defined together in `app/models/Recipe.py`. `Ingredient` has a FK to `Recipe` and they have bidirectional `Relationship`. `labels` is a PostgreSQL `ARRAY(TEXT)` column storing diet tags.

### API schemas
`app/api/schemas.py` defines read-only response models (`RecipeResponse`, `RecipeWithIngredientsResponse`) separate from the SQLModel table models. Always use these for endpoints, not the raw ORM models.

### Celery tasks
All tasks live in `app/tasks/`. Tasks must be registered in the `include` list in `app/celery_app.py`. Tasks import `celery` from `app/celery_app.py` and the DB engine directly from `app/db/engine.py`.

### Migrations
`migrations/env.py` imports all models from `app/models/Recipe.py` for Alembic autogenerate to detect schema changes. When adding a new model, import it there too.
