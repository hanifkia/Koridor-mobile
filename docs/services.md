# Services Reference

This document describes every service defined in `docker-compose.yml`.

---

## postgres

**Image:** `postgres:16-alpine`  
**Container name:** `ecolos-postgres`  
**Host port:** `5432`

The primary relational database for Koridor. Uses PostgreSQL 16 on the lightweight Alpine Linux base image.

### Configuration

| Setting | Value |
|---------|-------|
| User | `postgres` |
| Password | `postgres` |
| Database | `ecolos_db` |

> **Production note:** Replace the default credentials with strong, unique values and pass them via secrets or a `.env` file that is not committed to version control.

### Health check

The container reports healthy only after `pg_isready` confirms the database is accepting connections:

```yaml
test: ["CMD-SHELL", "pg_isready -U postgres -d ecolos_db"]
interval: 10s
timeout: 10s
retries: 20
start_period: 30s
```

The generous `start_period` and retry count (20 × 10s = up to 200s) accommodate slow first-boot initialization on low-resource machines.

### Persistence

Data is stored in the Docker-managed `postgres_data` volume, so it survives container restarts and `docker compose down` (but not `docker compose down -v`).

### Connecting directly

```bash
# From the host (port exposed)
psql -h localhost -U postgres -d ecolos_db

# From inside Docker network
psql -h postgres -U postgres -d ecolos_db
```

---

## redis

**Image:** `redis:7-alpine`  
**Container name:** `ecolos-redis`  
**Host port:** `6379`

Used for session caching, JWT token invalidation lists, and any other fast key-value storage the application needs. The core application connects on database index 2 (`/2`).

### Configuration

| Setting | Value |
|---------|-------|
| Password | `redispassword` |
| Persistence | RDB snapshot every 60 seconds if ≥ 1 key changed |
| Log level | `warning` |

### Health check

```yaml
test: ["CMD", "redis-cli", "-a", "redispassword", "ping"]
interval: 5s
timeout: 5s
retries: 10
start_period: 5s
```

### Persistence

Data is stored in the Docker-managed `redis_data` volume. The `--save 60 1` flag means Redis writes an RDB snapshot every 60 seconds when at least one key has changed, providing a balance between durability and performance.

### Connecting directly

```bash
# From the host
redis-cli -h localhost -a redispassword

# From inside the Docker network
redis-cli -h redis -a redispassword

# Check the DB used by the app (index 2)
redis-cli -h localhost -a redispassword -n 2 KEYS "*"
```

---

## db-migrate

**Image:** Custom (built from `migrations/Dockerfile.migrations`)  
**Container name:** `ecolos-db-migrate`  
**Restart policy:** `"no"` (runs once and exits)

A one-shot container that runs before the core application starts. It performs two tasks in sequence:

1. **Alembic migrations** — applies all pending schema migrations to `ecolos_db`
2. **Database seeding** — runs `migrations/scripts/seed_all.py` to populate reference/lookup data

### Startup dependency

`ecolos-core` depends on `db-migrate` with condition `service_completed_successfully`. This means Docker Compose will not start the application server until this container exits with code 0.

### Startup sequence

```
postgres (healthy) → db-migrate (exit 0) → ecolos-core (start)
                                         ↗
                   redis (healthy) ──────
```

### Manual re-run

To re-run migrations (e.g., after adding a new revision):

```bash
docker compose run --rm db-migrate
```

### Environment

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/ecolos_db` |
| `PYTHONPATH` | `/app` |

---

## ecolos-core

**Image:** Custom (built from `Dockerfile.develop`)  
**Container name:** `ecolos-core`  
**Host port:** `8000`

The FastAPI application server. In development mode it runs with `uvicorn --reload`, which watches for source file changes and automatically restarts the server without requiring a container rebuild.

### Startup command

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Volume mounts

The entire project root is mounted into `/app`, so edits on the host are immediately reflected inside the container. Several directories are excluded via anonymous volumes to avoid overwriting container-internal paths with (potentially empty) host directories:

| Host path | Container path | Notes |
|-----------|---------------|-------|
| `.` (project root) | `/app` | Full source mount for live reload |
| `./logs` | `/app/logs` | Persistent log files |
| `./uploads` | `/app/uploads` | Persistent user uploads |
| _(anonymous)_ | `/app/.git` | Excluded — not needed inside container |
| _(anonymous)_ | `/app/__pycache__` | Excluded — prevents cross-OS cache conflicts |
| _(anonymous)_ | `/app/.venv` | Excluded — container uses its own virtualenv |

### Startup dependencies

The application waits for:
- `db-migrate` to complete successfully (schema is up to date)
- `redis` to be healthy (cache is reachable)

### API endpoints

Once running:

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Root / health check |
| `http://localhost:8000/docs` | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc (read-only) |
| `http://localhost:8000/openapi.json` | Raw OpenAPI schema |
