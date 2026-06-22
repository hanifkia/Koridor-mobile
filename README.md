# Koridor Mobile WebApp

> A production-ready mobile web application powered by FastAPI, PostgreSQL, and Redis — containerized with Docker Compose.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Services](#services)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Development](#development)
- [Project Structure](#project-structure)
- [Volumes & Persistence](#volumes--persistence)
- [Networking](#networking)
- [Documentation Index](#documentation-index)

---

## Overview

Koridor is a mobile web application built on a modern async Python stack. The application is fully containerized — every service (database, cache, migrations, and the core API) runs inside Docker, making local setup a single command.

Key characteristics:

- **Async-first** — built with FastAPI and `asyncpg` for non-blocking database access
- **Redis-backed** — session caching and task queuing via Redis 7
- **Migration-managed** — Alembic handles all schema changes, run automatically on startup
- **Hot-reload in dev** — the core application volume-mounts source code and uses `uvicorn --reload`
- **JWT authentication** — access tokens (60 min) and refresh tokens (7 days) out of the box

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    app-network                       │
│                                                     │
│  ┌──────────────┐     ┌──────────────┐              │
│  │   postgres   │     │    redis     │              │
│  │  (port 5432) │     │  (port 6379) │              │
│  └──────┬───────┘     └──────┬───────┘              │
│         │                    │                      │
│  ┌──────▼───────┐            │                      │
│  │  db-migrate  │            │                      │
│  │  (one-shot)  │            │                      │
│  └──────┬───────┘            │                      │
│         │                    │                      │
│  ┌──────▼────────────────────▼──────┐               │
│  │          ecolos-core             │               │
│  │         (port 8000)              │               │
│  └──────────────────────────────────┘               │
└─────────────────────────────────────────────────────┘
```

The `db-migrate` container runs Alembic migrations and seeds the database, then exits. The core application only starts after migrations complete successfully.

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Docker | 24.x |
| Docker Compose | v2.x (`docker compose` plugin) |
| Git | any recent version |

No Python, Node.js, or database installations are required on the host machine.

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd koridor

# 2. Copy environment file and review defaults
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. The API is now available at:
#    http://localhost:8000
#    http://localhost:8000/docs  (Swagger UI)
#    http://localhost:8000/redoc (ReDoc)
```

To run in detached mode:

```bash
docker compose up --build -d
docker compose logs -f ecolos-core   # follow core app logs
```

To stop and remove containers:

```bash
docker compose down          # stop containers, keep volumes
docker compose down -v       # stop containers AND delete volumes
```

---

## Services

See [docs/services.md](docs/services.md) for full detail. Summary:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `postgres` | postgres:16-alpine | 5432 | Primary relational database |
| `redis` | redis:7-alpine | 6379 | Cache and session store |
| `db-migrate` | custom (one-shot) | — | Alembic migrations + seed data |
| `ecolos-core` | custom | 8000 | FastAPI application server |

---

## Environment Variables

See [docs/environment.md](docs/environment.md) for the full reference. Critical variables:

| Variable | Default | Notes |
|----------|---------|-------|
| `JWT_SECRET_KEY` | `your-super-secret-key-change-in-production` | **Change before any deployment** |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/ecolos_db` | Internal Docker hostname |
| `REDIS_URL` | `redis://:redispassword@redis:6379/2` | Uses DB index 2 |
| `DEBUG` | `True` | Set to `False` in staging/production |

---

## Database Migrations

Migrations run automatically on `docker compose up`. To run them manually:

```bash
docker compose run --rm db-migrate
```

To create a new migration after changing a model:

```bash
docker compose exec ecolos-core bash
cd /app/migrations
alembic revision --autogenerate -m "describe your change"
```

See [docs/migrations.md](docs/migrations.md) for the full migration workflow.

---

## Development

```bash
# Start with live logs
docker compose up

# Rebuild after changing dependencies (requirements.txt / Dockerfile)
docker compose up --build

# Open a shell inside the running core container
docker compose exec ecolos-core bash

# Run tests (adjust command to your test runner)
docker compose exec ecolos-core pytest

# Check logs for a specific service
docker compose logs postgres
docker compose logs redis
```

See [docs/development.md](docs/development.md) for the full development guide, including linting, testing, and debugging tips.

---

## Project Structure

```
koridor/
├── app/                        # FastAPI application
│   ├── main.py                 # App entrypoint (uvicorn target)
│   ├── api/                    # Route handlers
│   ├── core/                   # Config, security, dependencies
│   ├── models/                 # SQLAlchemy ORM models
│   └── schemas/                # Pydantic request/response schemas
├── migrations/                 # Alembic migration environment
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/           # Generated migration scripts
│   ├── scripts/
│   │   └── seed_all.py         # Database seeder
│   └── Dockerfile.migrations
├── logs/                       # Persistent log files (mounted volume)
├── uploads/                    # Persistent user uploads (mounted volume)
├── docs/                       # Extended documentation
│   ├── services.md
│   ├── environment.md
│   ├── migrations.md
│   └── development.md
├── Dockerfile.develop          # Development image for ecolos-core
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Volumes & Persistence

| Volume | Purpose | Lives at |
|--------|---------|---------|
| `postgres_data` | PostgreSQL data files | Docker-managed |
| `redis_data` | Redis persistence (RDB snapshots every 60s) | Docker-managed |
| `migration_cache` | Alembic cache for faster rebuilds | Docker-managed |
| `./logs` | Application log files | Host filesystem |
| `./uploads` | User-uploaded files | Host filesystem |

Logs and uploads are bind-mounted to the host so they survive container recreation without needing to run `docker cp`.

---

## Networking

All services communicate over the internal `app-network` bridge network. Only the following ports are exposed to the host:

| Host Port | Container | Purpose |
|-----------|-----------|---------|
| 5432 | postgres | Direct DB access (psql, TablePlus, etc.) |
| 6379 | redis | Direct Redis access (redis-cli, RedisInsight) |
| 8000 | ecolos-core | FastAPI application |

In production, ports 5432 and 6379 should not be exposed. Only the application port (or a reverse proxy in front of it) should be public-facing.

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [docs/services.md](docs/services.md) | Per-service configuration reference |
| [docs/environment.md](docs/environment.md) | All environment variables explained |
| [docs/migrations.md](docs/migrations.md) | Migration workflow and Alembic usage |
| [docs/development.md](docs/development.md) | Local dev guide, testing, debugging |
