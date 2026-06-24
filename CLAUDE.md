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

**Worked example:**

```python
# Bad — what does 100 mean? What is q?
async def get_recipes(q: str, limit: int = 100, session: Session = Depends(get_session)):
    ...

# Good — readable at a glance, constant is named and changeable in one place
MAX_RECIPES_PER_PAGE = 100

async def get_recipes(
    search_query: str,
    limit: int = MAX_RECIPES_PER_PAGE,
    session: Session = Depends(get_session),
):
    ...
```

**Why it matters:** The `100` in the bad version is a magic number — if you need to change the default in 5 places, you'll miss one. The name `q` tells you nothing about what the string represents. Six months later, neither version will be obvious to a new reader (or you). Named constants and descriptive params make the code self-documenting.

---

### DRY (Don't Repeat Yourself)

- Duplicated query logic → extract to a repository function or shared variable
- Repeated validation logic → extract to a validator or dependency

**Worked example:**

```python
# Bad — same query duplicated in two route handlers
@router.get("/{recipe_id}")
async def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    result = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return result

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int, session: Session = Depends(get_session)):
    result = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()  # duplicated
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")          # duplicated
    session.delete(result)
    session.commit()

# Good — extracted to a shared helper (Repository pattern)
def get_recipe_or_404(recipe_id: int, session: Session) -> Recipe:
    recipe = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
```

**Why it matters:** When the not-found message changes, or the query needs a filter added, you change it in one place. This is the **Repository pattern** — isolating data-access logic so route handlers don't need to know how to find things, just what to do with them.

---

### KISS (Keep It Simple)

- Overly complex solutions where a simpler one exists
- Premature abstraction (adding layers before they're needed is just as bad as not abstracting)

**Worked example:**

```python
# Bad — adds a generic "manager" class before it's needed
class RecipeManager:
    def __init__(self, strategy: QueryStrategy, transformer: ResponseTransformer):
        ...
    def execute(self, context: QueryContext) -> TransformedResponse:
        ...

# Good — just write the function
async def get_recipes(session: Session = Depends(get_session)) -> list[RecipeResponse]:
    return session.exec(select(Recipe)).all()
```

**Why it matters:** Abstractions have a cost — they add indirection, new concepts to learn, and surface area for bugs. Add them when the duplication actually hurts you, not in anticipation of pain that may never come. The rule of three: abstract after you've written the same thing three times, not before.

---

### Single Responsibility

- Route handlers should only: parse input, call a service/repository, return a response
- Business logic in route handlers is a red flag — it belongs in a service layer
- Functions that do more than one thing should be split

**Worked example:**

```python
# Bad — route handler doing too much
@router.post("/trigger-scrape")
async def trigger_scrape(session: Session = Depends(get_session)):
    existing = session.exec(select(ScrapeJob).where(ScrapeJob.status == "running")).first()
    if existing:
        raise HTTPException(status_code=409, detail="Scrape already running")
    job = ScrapeJob(status="running", started_at=datetime.now())
    session.add(job)
    session.commit()
    task = scrape_recipes.delay(job.id)
    job.celery_task_id = task.id
    session.commit()
    return {"task_id": task.id}

# Good — handler only orchestrates; logic lives in a service
@router.post("/trigger-scrape", status_code=202)
async def trigger_scrape(
    scrape_service: ScrapeService = Depends(get_scrape_service),
):
    return scrape_service.start_scrape()
```

**Why it matters:** The bad version can't be unit tested without a real DB and a real Celery worker. The service version can be tested by mocking `ScrapeService`. It also means adding auth, logging, or rate-limiting to the trigger later only touches the handler, not the business logic.

---

### Validation at Boundaries

- Missing `ge`/`le`/`gt`/`lt` on numeric query params (e.g. `limit` without `ge=1, le=100`)
- Missing `max_length` on string inputs
- Accepting unbounded values in pagination, search, or filter params

**Worked example:**

```python
# Bad — user can request limit=999999 or limit=-1
async def get_recipes(limit: int = 20, offset: int = 0):
    ...

# Good — FastAPI validates these before your code even runs
async def get_recipes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default="", max_length=100),
):
    ...
```

**Why it matters:** `limit=999999` on a large table can return gigabytes of data, crash the DB, or time out in production. `ge`/`le` constraints are enforced by FastAPI/Pydantic before your handler runs — bad input returns `422 Unprocessable Entity` automatically. This is **validation at the boundary**, a core security principle: never trust caller-supplied values without range checking.

---

### Naming

- Vague names (`q`, `data`, `result`, `obj`, `item`) vs descriptive ones (`recipe_id`, `paginated_recipes`, `scrape_result`)
- Boolean variables should read as predicates: `is_published`, `has_ingredients`, not `flag` or `status`

**Worked example:**

```python
# Bad
def process(data, flag):
    result = []
    for item in data:
        if flag:
            result.append(item)
    return result

# Good
def filter_published_recipes(recipes: list[Recipe], is_published: bool) -> list[Recipe]:
    return [recipe for recipe in recipes if recipe.is_published == is_published]
```

**Why it matters:** `flag` and `data` force the reader to hold the entire call stack in their head to know what's happening. `is_published` is a predicate — it reads like a question (`if is_published:`) and leaves no ambiguity. You'll thank yourself during a 3am incident when you're reading logs and code at the same time.

---

### Python Ordering Conventions

- In function signatures: required params → optional params → `Depends()` injections last
- In files: module docstring → imports → constants → classes → functions → `if __name__ == "__main__"`
- Imports grouped: stdlib → third-party → local, with a blank line between groups

**Worked example:**

```python
# Bad — Depends() before required params, imports mixed
from app.db.engine import get_session
import os
from fastapi import Depends, HTTPException
from sqlmodel import Session

async def get_recipe(session: Session = Depends(get_session), recipe_id: int):
    ...

# Good
import os                          # stdlib

from fastapi import Depends, HTTPException  # third-party
from sqlmodel import Session

from app.db.engine import get_session       # local

async def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    ...
```

**Why it matters:** Python requires required args before optional ones — mixing them causes a `SyntaxError`. Beyond correctness, consistent ordering means your eyes know where to look. A reviewer scanning 10 files will thank you for predictable structure.

---

### Import Hygiene

- No unused imports (ruff catches these, but flag intent)
- No star imports (`from module import *`)

**Worked example:**

```python
# Bad — star import pollutes the namespace
from app.models.Recipe import *

# Good — explicit imports, nothing hidden
from app.models.Recipe import Recipe, Ingredient
```

**Why it matters:** Star imports make it impossible to know where a name came from without looking at the source module. If two modules both export a name called `Session`, a star import silently shadows one with the other — no error, wrong behavior. Explicit imports are greppable and make refactoring safe.

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

**Worked example — wrong method + wrong status + incomplete contract:**

```python
# Bad — GET used for mutation, returns 200, caller has no task_id to poll
@router.get("/trigger-scrape")
async def trigger_scrape():
    scrape_recipes.delay()
    return {"message": "started"}

# Good — POST for mutation, 202 Accepted for async work, task_id returned so caller can poll
@router.post("/trigger-scrape", status_code=202)
async def trigger_scrape() -> ScrapeJobResponse:
    task = scrape_recipes.delay()
    return ScrapeJobResponse(task_id=task.id, status="pending")
```

**Why it matters:** GET requests are cached by browsers, CDNs, and proxies. A GET to `/trigger-scrape` might be cached and never hit your server — your scrape never runs. `202 Accepted` communicates "I received this, work is happening asynchronously" — the correct semantic for Celery tasks. And without `task_id` in the response, the Expo app has no way to check if the scrape finished.

---

## Code Review — Error Handling

- **Never use bare `except:`** — always catch specific exceptions
- **Never silently swallow exceptions** — at minimum, log them
- **Distinguish error types** — a missing record (404) is not the same as a DB connection failure (503) or invalid input (422); handle them separately
- **Use FastAPI's `HTTPException`** for expected errors; use middleware or exception handlers for unexpected ones
- **Celery tasks** must handle failures explicitly — what happens if a scrape fails halfway through? Is the DB left in a partial state?

**Worked example:**

```python
# Bad — swallows all exceptions, caller gets 500 with no useful info
@router.get("/{recipe_id}")
async def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    try:
        return session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
    except:
        return None

# Good — distinguishes "not found" (expected) from "DB down" (unexpected)
@router.get("/{recipe_id}")
async def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    try:
        recipe = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
    except OperationalError as e:
        logger.error("DB error fetching recipe %s: %s", recipe_id, e)
        raise HTTPException(status_code=503, detail="Database unavailable")

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return recipe
```

**Why it matters:** Returning `None` on a DB crash gives the caller a `200 OK` with a null body — they think the record doesn't exist, not that the database is down. Distinguishing error types lets monitoring tools alert on 503s (infra problem) separately from 404s (normal usage). This is the difference between "we noticed the DB was down" and "a user reported recipes weren't loading."

---

## Code Review — Security

Flag these every time, even in "learning" code — internalizing these habits early matters:

- **SQL injection** — raw string interpolation in queries is never acceptable; always use parameterized queries (SQLModel/SQLAlchemy does this, but watch for raw `text()` calls)
- **Secrets in code** — API keys, passwords, connection strings must come from environment variables, never hardcoded
- **Overly permissive CORS** — `allow_origins=["*"]` is fine for local dev but must be flagged as insecure for any deployed context
- **Unvalidated external data** — data from scrapers or external APIs must be validated before being written to the DB (Pydantic schemas do this, but flag if they're being bypassed)
- **Unbounded queries** — a missing `LIMIT` on a DB query can return millions of rows; always paginate or cap results

**Worked example — SQL injection + unbounded query:**

```python
# Bad — SQL injection via f-string, no LIMIT
@router.get("/search")
async def search_recipes(name: str, session: Session = Depends(get_session)):
    results = session.exec(text(f"SELECT * FROM recipe WHERE name LIKE '%{name}%'")).all()
    return results

# Good — parameterized query, result capped
@router.get("/search")
async def search_recipes(
    name: str = Query(max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[RecipeResponse]:
    return session.exec(
        select(Recipe).where(Recipe.name.contains(name)).limit(limit)
    ).all()
```

**Why it matters:** The `f"...{name}..."` version lets a caller pass `name='; DROP TABLE recipe; --` and wipe your database. SQLModel's `.contains()` uses parameterized queries — the DB treats the input as data, never as SQL. The unbounded version with no `limit` on a 50k-row recipe table could return 200MB of JSON and take down your server under load.

---

## Code Review — Observability & Debuggability

A senior dev asks: "if this breaks at 3am, can I figure out why?"

- **Missing logging** — important operations (scrape started/finished, record created, task failed) should be logged with enough context to reconstruct what happened
- **Log levels matter** — `DEBUG` for verbose details, `INFO` for normal operations, `WARNING` for unexpected-but-recoverable situations, `ERROR` for failures
- **No `print()` in production code** — use the `logging` module
- **Task results** — Celery tasks should log their outcome; silent success is hard to monitor

**Worked example:**

```python
# Bad — print statements, no context, silent on success
def scrape_recipes():
    print("starting scrape")
    try:
        recipes = fetch_recipes()
        save_to_db(recipes)
    except Exception as e:
        print(f"error: {e}")

# Good — structured logging, context in every message, explicit success/failure
logger = logging.getLogger(__name__)

def scrape_recipes():
    logger.info("Scrape task started")
    try:
        recipes = fetch_recipes()
        logger.debug("Fetched %d recipes from source", len(recipes))
        save_to_db(recipes)
        logger.info("Scrape task completed successfully, saved %d recipes", len(recipes))
    except RequestException as e:
        logger.error("Scrape failed — network error fetching source: %s", e)
        raise
    except Exception as e:
        logger.error("Scrape failed — unexpected error: %s", e, exc_info=True)
        raise
```

**Why it matters:** `print()` goes to stdout and disappears. `logging` routes to your log aggregator (Datadog, CloudWatch, etc.), persists, and is searchable. `logger.info("saved %d recipes", len(recipes))` tells you at 3am whether the task ran and what it did. `exc_info=True` attaches the full stack trace — without it, you see the error message but not where it came from.

---

## Code Review — Testing

Always comment on testability, even when no tests are written yet:

- **Is this function testable?** — if it mixes DB access, business logic, and HTTP response handling, it can't be unit tested in isolation; flag this
- **What should be tested here?** — for any new function, name what the unit tests would cover: happy path, empty result, invalid input, DB error
- **Mocking vs integration tests** — explain the difference: unit tests mock the DB and test logic; integration tests hit a real (test) DB and test the full flow. Both have a place.
- **Test naming convention** — `test_<function>_<scenario>_<expected_result>`, e.g. `test_get_recipe_not_found_returns_404`

**Worked example:**

```python
# This function mixes DB access + business logic — hard to unit test
async def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    recipe = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if not recipe.ingredients:
        raise HTTPException(status_code=422, detail="Recipe has no ingredients")
    return RecipeWithIngredientsResponse.from_orm(recipe)

# Tests you'd write for the above — name the scenarios explicitly:
def test_get_recipe_returns_recipe_with_ingredients(): ...
def test_get_recipe_not_found_returns_404(): ...
def test_get_recipe_without_ingredients_returns_422(): ...
def test_get_recipe_db_failure_returns_503(): ...
```

**Why it matters:** If you can name 4 test cases immediately, the function has 4 distinct behaviors — which means it might be doing too much (see Single Responsibility). Functions that are easy to name tests for are usually well-scoped. Integration tests (hitting a real test DB) prove the SQL is correct; unit tests (mocking the session) prove the logic is correct. You need both.

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
