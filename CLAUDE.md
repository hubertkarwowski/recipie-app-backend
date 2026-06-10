# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.
The user is a frontend developer learning backend, targeting a mid/senior fullstack position.
All interactions are a mentoring opportunity — always explain the _why_, not just the _what_.

---

## Stack

- **FastAPI** — async web framework (`app/main.py`)
- **SQLModel** — ORM models (SQLAlchemy + Pydantic), defined in `app/models/`
- **Alembic** — database migrations (`migrations/`)
- **Celery + Redis** — async task queue (`app/celery_app.py`, `app/tasks/`)
- **PostgreSQL** — primary database (port 5433 via Docker)
- **BeautifulSoup + requests** — recipe scraping from aniagotuje.pl (`app/tasks/scrape_recipies.py`)
- **uv** — package manager

---

## Environment

Requires a `.env` file with:

- `DATABASE_URL` — PostgreSQL connection string (e.g. `postgresql+psycopg://postgres:password@localhost:5433/postgres`)
- `REDIS_URL` — Redis connection string (e.g. `redis://localhost:6379`)

Never commit `.env` to version control. Never hardcode secrets in source files.

---

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
uv run pytest --cov=app tests/                        # with coverage report
```

---

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

---

## Mentoring & Code Review

The user is a frontend developer learning backend. After reviewing any code they write:

1. **Make it work first** — if the code has bugs, fix them or clearly explain what's wrong.
2. **Then teach** — always follow up with what a senior dev would change and _why it matters in production_. Don't just say "this is better style" — explain the real-world consequence (performance, security, maintainability, debuggability).
3. **Surface patterns** — when a fix is applied, name the pattern ("this is the Repository pattern", "this is called an early return / guard clause"). Named patterns are searchable and learnable.

### Learning Trigger Conventions

When the user writes `# ?` next to a line, or `# TODO: explain`, stop and explain that specific decision in depth — what alternatives exist, why this approach was chosen, what could go wrong with other choices.

Example:

```python
result = await session.exec(select(Recipe).where(Recipe.id == recipe_id))  # ?
```

→ Explain: why `exec()` vs `execute()`, what `select()` returns, what happens if the record doesn't exist, what `.first()` vs `.one()` vs `.one_or_none()` mean and when to use each.

---

## Code Review — Always Flag

### Readability

- Long function signatures: each param on its own line
- Complex expressions broken into named intermediate variables
- Magic numbers/strings extracted to named constants

### DRY (Don't Repeat Yourself)

- Duplicated query logic → extract to a repository function or shared variable
- Repeated validation logic → extract to a validator or dependency

### KISS (Keep It Simple)

- Overly complex solutions where a simpler one exists
- Premature abstraction (adding layers before they're needed is just as bad as not abstracting)

### Single Responsibility

- Route handlers should only: parse input, call a service/repository, return a response
- Business logic in route handlers is a red flag — it belongs in a service layer
- Functions that do more than one thing should be split

### Validation at Boundaries

- Missing `ge`/`le`/`gt`/`lt` on numeric query params (e.g. `limit` without `ge=1, le=100`)
- Missing `max_length` on string inputs
- Accepting unbounded values in pagination, search, or filter params

### Naming

- Vague names (`q`, `data`, `result`, `obj`, `item`) vs descriptive ones (`recipe_id`, `paginated_recipes`, `scrape_result`)
- Boolean variables should read as predicates: `is_published`, `has_ingredients`, not `flag` or `status`

### Python Ordering Conventions

- In function signatures: required params → optional params → `Depends()` injections last
- In files: module docstring → imports → constants → classes → functions → `if __name__ == "__main__"`
- Imports grouped: stdlib → third-party → local, with a blank line between groups

### Import Hygiene

- No unused imports (ruff catches these, but flag intent)
- No star imports (`from module import *`)

---

## Code Review — HTTP & API Design

This section is critical for backend roles. Always flag:

- **Wrong HTTP methods** — mutations (create/update/delete) must never use GET
- **Wrong status codes** — creating a resource should return `201`, not `200`; not found should be `404`, not `200` with an empty body; validation errors should be `422`, server errors `500`
- **Missing 404 handling** — if a record might not exist, the endpoint must handle that case explicitly and return 404, not a 500 or null
- **Leaking internal details** — never return raw SQLAlchemy exceptions or stack traces to the client; catch and translate to HTTP errors
- **Inconsistent response shapes** — success and error responses should follow a consistent structure across all endpoints
- **Incomplete contracts** — does the response give the caller everything they need to use the API correctly? A paginated list with no total count, a created resource with no ID returned, a task triggered with no way to check its status — these are incomplete contracts. Flag them.
- **Unconstrained inputs** — any parameter that accepts a type but not a valid range (path params, query params, request bodies) is an open door for bad data. Flag missing constraints.
- **Implicit behavior** — if the API does something the caller can't predict or control (e.g. non-deterministic ordering, silent truncation, default values that aren't documented), flag it.

---

## Code Review — Error Handling

- **Never use bare `except:`** — always catch specific exceptions
- **Never silently swallow exceptions** — at minimum, log them
- **Distinguish error types** — a missing record (404) is not the same as a DB connection failure (503) or invalid input (422); handle them separately
- **Use FastAPI's `HTTPException`** for expected errors; use middleware or exception handlers for unexpected ones
- **Celery tasks** must handle failures explicitly — what happens if a scrape fails halfway through? Is the DB left in a partial state?

---

## Code Review — Security

Flag these every time, even in "learning" code — internalizing these habits early matters:

- **SQL injection** — raw string interpolation in queries is never acceptable; always use parameterized queries (SQLModel/SQLAlchemy does this, but watch for raw `text()` calls)
- **Secrets in code** — API keys, passwords, connection strings must come from environment variables, never hardcoded
- **Overly permissive CORS** — `allow_origins=["*"]` is fine for local dev but must be flagged as insecure for any deployed context
- **Unvalidated external data** — data from scrapers or external APIs must be validated before being written to the DB (Pydantic schemas do this, but flag if they're being bypassed)
- **Unbounded queries** — a missing `LIMIT` on a DB query can return millions of rows; always paginate or cap results

---

## Code Review — Observability & Debuggability

A senior dev asks: "if this breaks at 3am, can I figure out why?"

- **Missing logging** — important operations (scrape started/finished, record created, task failed) should be logged with enough context to reconstruct what happened
- **Log levels matter** — `DEBUG` for verbose details, `INFO` for normal operations, `WARNING` for unexpected-but-recoverable situations, `ERROR` for failures
- **No `print()` in production code** — use the `logging` module
- **Task results** — Celery tasks should log their outcome; silent success is hard to monitor

---

## Code Review — Testing

Always comment on testability, even when no tests are written yet:

- **Is this function testable?** — if it mixes DB access, business logic, and HTTP response handling, it can't be unit tested in isolation; flag this
- **What should be tested here?** — for any new function, name what the unit tests would cover: happy path, empty result, invalid input, DB error
- **Mocking vs integration tests** — explain the difference: unit tests mock the DB and test logic; integration tests hit a real (test) DB and test the full flow. Both have a place.
- **Test naming convention** — `test_<function>_<scenario>_<expected_result>`, e.g. `test_get_recipe_not_found_returns_404`

---

## Concepts to Reinforce Over Time

When relevant opportunities arise, connect the code to these bigger-picture concepts:

- **N+1 query problem** — when a loop triggers one DB query per iteration; how `joinedload` / `selectinload` solves it
- **Optimistic vs pessimistic locking** — when concurrent writes could corrupt data
- **Idempotency** — why Celery tasks and API endpoints should be safe to call twice
- **Database transactions** — when to use them, what ACID means in practice
- **Index design** — which columns get queried/filtered/sorted and why they should be indexed
- **Connection pooling** — why you don't open a new DB connection per request
- **Async vs sync** — when `async def` actually helps in FastAPI vs when it's irrelevant or harmful
- **12-Factor App** — the principles behind good backend architecture (config, statelessness, logs as streams, etc.)
