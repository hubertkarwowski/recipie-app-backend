# Backend Learning Roadmap

## Current progress (as of 2026-05-30)

**Phase 1** — Complete
**Phase 2** — In progress

Currently working on: `app/routers/recipes.py`
- Pagination (`offset`, `limit`) with validation — done
- Diet label filter (`?label=`) on PostgreSQL array column — done
- Signature formatting and param ordering — done
- Next: paginated response wrapper with `total` count (incomplete contract — caller can't know when list ends)

---

## Phase 1 — Make it work (complete)

**Language fundamentals**
- Python type hints, async/await, context managers, decorators
- How Python imports work (critical — your current bug is an import-time side effect)

**Web & HTTP**
- HTTP methods, status codes, headers, request/response lifecycle
- REST principles — resource naming, idempotency, statelessness
- FastAPI — routing, dependency injection, middleware, lifespan

**Databases — basics**
- SQL: SELECT, JOIN, WHERE, GROUP BY, indexes
- ORM vs raw SQL — when each is appropriate
- Migrations — why they exist, how to write them safely (Alembic)
- Transactions — ACID, commit/rollback

---

## Phase 2 — Make it right

**API design**
- Pagination (offset vs cursor-based)
- Filtering, sorting, searching
- Versioning (`/api/v1/`)
- Error responses — consistent shape, meaningful codes

**Auth**
- JWT — what it is, how it works, where to store it
- OAuth2 basics — flows, scopes
- Hashing passwords (bcrypt) — never store plaintext

**Async & concurrency**
- Sync vs async in Python — when each matters
- Race conditions, locks, database-level locking
- Connection pooling

**Background jobs**
- Task queues (Celery) — retries, backoff, idempotency
- Scheduled tasks (cron-style)
- Why you can't just use `threading` in production

---

## Phase 3 — Make it survive production

**Caching**
- Redis — cache-aside pattern, TTL, cache invalidation
- What to cache vs what not to (hint: never cache auth tokens naively)
- CDN for static assets

**Testing**
- Unit vs integration vs end-to-end — what each catches
- Testing with a real database (not mocks)
- Fixtures, factories, teardown

**Observability**
- Structured logging — why `print()` isn't enough in production
- Metrics — what to measure (latency, error rate, throughput)
- Distributed tracing — following a request across services
- Error tracking (Sentry — already in your dependencies)

**Containers & deployment**
- Docker — images, containers, volumes, networking
- Docker Compose — multi-service local dev (you already have this)
- Environment config — 12-factor app principles
- CI/CD basics — automated tests on push, deploy pipeline

---

## Phase 4 — Think at scale

**Systems design**
- Load balancing — horizontal vs vertical scaling
- Database scaling — read replicas, sharding, connection limits
- CAP theorem — consistency vs availability tradeoff
- Eventual consistency — when it's acceptable
- API gateways, rate limiting

**Advanced database**
- Query optimization — EXPLAIN ANALYZE, N+1 problem
- Indexes deep dive — B-tree, composite, partial
- Database normalization vs denormalization
- NoSQL — when to reach for it (and when not to)

**Message brokers**
- Kafka vs RabbitMQ vs Redis Streams — when each fits
- Event-driven architecture — pub/sub, consumers, dead letter queues
- At-least-once vs exactly-once delivery

**Security**
- OWASP Top 10 — SQL injection, XSS, CSRF, auth flaws
- HTTPS, TLS, certificate basics
- Secrets management — never in code or env files in production

---

## Good libraries to know (Python ecosystem)

| Purpose | Library |
|---|---|
| Web framework | FastAPI, Django |
| ORM | SQLModel, SQLAlchemy, Django ORM |
| Validation | Pydantic |
| Task queue | Celery, ARQ |
| HTTP client | httpx, requests |
| Testing | pytest, pytest-asyncio, factory-boy |
| Auth | python-jose, passlib, authlib |
| Logging | loguru, structlog |
| Config | python-dotenv, pydantic-settings |
| Scraping | BeautifulSoup4, playwright |
| DB migrations | Alembic |

---

## Focus areas for this project

Your recipe app naturally covers Phase 1 and 2. Before moving to anything else, deeply understand:

1. How a request flows through FastAPI end to end
2. How Alembic migrations work and why order matters
3. How Celery tasks retry and fail safely
