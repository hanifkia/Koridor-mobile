# Development Guide

Everything you need to run, test, and debug Koridor locally.

---

## Starting the Stack

```bash
# Full startup with logs streamed to terminal
docker compose up

# Rebuild images (required after changing Dockerfile or requirements.txt)
docker compose up --build

# Detached (background) mode
docker compose up -d

# Start only specific services
docker compose up postgres redis
```

---

## Live Reload

The `ecolos-core` service mounts the project root into `/app` and runs uvicorn with `--reload`. This means:

- Edit any `.py` file on the host
- Uvicorn detects the change and restarts automatically
- No need to rebuild the container

If uvicorn is not picking up changes, check that the file you edited is actually inside the mounted volume path (project root) and not in an excluded directory.

---

## Useful Commands

### Shells and exec

```bash
# Open a bash shell inside the core application container
docker compose exec ecolos-core bash

# Run a one-off Python script inside the container
docker compose exec ecolos-core python -m some.module

# Connect to PostgreSQL directly
docker compose exec postgres psql -U postgres -d ecolos_db

# Connect to Redis directly
docker compose exec redis redis-cli -a redispassword
```

### Logs

```bash
# Follow logs for all services
docker compose logs -f

# Follow logs for a specific service
docker compose logs -f ecolos-core
docker compose logs -f postgres
docker compose logs -f redis

# Show last 50 lines
docker compose logs --tail=50 ecolos-core
```

### Restart a single service

```bash
# Restart without rebuilding
docker compose restart ecolos-core

# Rebuild and restart
docker compose up --build ecolos-core
```

---

## Running Tests

```bash
# Run the full test suite
docker compose exec ecolos-core pytest

# Run with verbose output
docker compose exec ecolos-core pytest -v

# Run a specific test file
docker compose exec ecolos-core pytest app/tests/test_auth.py

# Run tests matching a keyword
docker compose exec ecolos-core pytest -k "login"

# Run with coverage report
docker compose exec ecolos-core pytest --cov=app --cov-report=term-missing
```

---

## Code Quality

```bash
# Linting (ruff)
docker compose exec ecolos-core ruff check app/

# Auto-fix lint issues
docker compose exec ecolos-core ruff check app/ --fix

# Type checking (mypy)
docker compose exec ecolos-core mypy app/

# Formatting (ruff format / black)
docker compose exec ecolos-core ruff format app/
```

---

## API Exploration

Once the stack is running, the interactive API docs are available at:

- **Swagger UI:** http://localhost:8000/docs — try requests directly from the browser
- **ReDoc:** http://localhost:8000/redoc — cleaner read-only reference
- **OpenAPI JSON:** http://localhost:8000/openapi.json — import into Postman, Insomnia, etc.

### Import into Postman

1. Open Postman → Import → Link
2. Paste: `http://localhost:8000/openapi.json`
3. All endpoints are imported with correct request schemas

---

## Database Access

### GUI clients

Connect with any PostgreSQL GUI (TablePlus, DBeaver, pgAdmin) using:

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5432` |
| User | `postgres` |
| Password | `postgres` |
| Database | `ecolos_db` |

### Inspect Redis

Using RedisInsight or redis-cli:

```bash
# List all keys in the app database (index 2)
redis-cli -h localhost -p 6379 -a redispassword -n 2 KEYS "*"

# Flush the app database (use carefully)
redis-cli -h localhost -p 6379 -a redispassword -n 2 FLUSHDB
```

---

## Resetting the Development Environment

To start completely fresh (all data wiped):

```bash
docker compose down -v       # stops containers and deletes ALL volumes
docker compose up --build    # rebuilds images, re-runs migrations, re-seeds data
```

To reset only the database without touching Redis:

```bash
docker compose stop postgres db-migrate
docker volume rm koridor_postgres_data
docker compose up postgres db-migrate
```

---

## Debugging

### Python debugger (pdb / debugpy)

The `ecolos-core` service runs with `stdin_open: true` and `tty: true`, which enables attaching to `pdb` breakpoints.

Add a breakpoint in your code:

```python
import pdb; pdb.set_trace()
# or Python 3.7+
breakpoint()
```

Then attach to the container's stdin:

```bash
docker attach ecolos-core
```

Press `Ctrl+P, Ctrl+Q` (not `Ctrl+C`) to detach without stopping the container.

### Remote debugging with debugpy (VS Code)

```python
# Add to app/main.py temporarily
import debugpy
debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()
```

Expose port 5678 in `docker-compose.yml` (or `docker-compose.override.yml`):

```yaml
ecolos-core:
  ports:
    - "5678:5678"
```

Then in VS Code, add a launch configuration:

```json
{
  "name": "Attach to Docker",
  "type": "python",
  "request": "attach",
  "connect": { "host": "localhost", "port": 5678 },
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "/app" }
  ]
}
```

---

## Common Issues

### Port already in use

```
Error: bind: address already in use
```

Another process is using port 8000, 5432, or 6379. Find and stop it:

```bash
# macOS / Linux
lsof -i :8000
kill -9 <PID>
```

Or change the host port in `docker-compose.yml` (left side of `host:container`).

### `db-migrate` fails on first run

Usually means PostgreSQL wasn't ready in time. Re-running is safe:

```bash
docker compose up db-migrate
```

If it keeps failing, check the full logs:

```bash
docker compose logs db-migrate
```

### Changes not reflected after editing a file

If live reload stops working:

```bash
docker compose restart ecolos-core
```

If the issue persists, the volume mount may have a caching issue. Rebuild:

```bash
docker compose up --build ecolos-core
```

### `ModuleNotFoundError` inside the container

The `PYTHONPATH` is set to `/app`. If a module is not found, verify:

1. The file exists inside the project root (which is mounted to `/app`)
2. The import path matches the directory structure
3. There is an `__init__.py` in every package directory

---

## Docker Compose Override (Personal Overrides)

To customize the stack without modifying the committed `docker-compose.yml`, create a `docker-compose.override.yml` in the project root. Docker Compose merges it automatically:

```yaml
# docker-compose.override.yml (not committed)
services:
  ecolos-core:
    environment:
      ACCESS_TOKEN_EXPIRE_MINUTES: "480"   # longer tokens for local dev
    ports:
      - "5678:5678"                         # debugpy port
```

Add `docker-compose.override.yml` to `.gitignore`.
