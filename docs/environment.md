# Environment Variables

All environment variables are set in `docker-compose.yml`. For local development you can override them by creating a `.env` file in the project root — Docker Compose automatically picks it up.

---

## .env.example

Copy this to `.env` and fill in the values before starting:

```env
# ── Application ────────────────────────────────────────────
DEBUG=True
APP_NAME=ecolos-core
APP_VERSION=1.0.0

# ── Database ───────────────────────────────────────────────
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ecolos_db
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ecolos_db

# ── Redis ──────────────────────────────────────────────────
REDIS_PASSWORD=redispassword
REDIS_URL=redis://:redispassword@redis:6379/2

# ── Security ───────────────────────────────────────────────
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
BCRYPT_LOG_ROUNDS=12
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Full Variable Reference

### Application

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DEBUG` | `True` | yes | Enables debug mode. Set to `False` in staging/production. Affects error detail in API responses and uvicorn log verbosity. |
| `APP_NAME` | `ecolos-core` | no | Application name, surfaced in logs and OpenAPI metadata. |
| `APP_VERSION` | `1.0.0` | no | Application version, surfaced in OpenAPI metadata. |
| `PYTHONPATH` | `/app` | yes | Ensures Python can resolve internal imports across the project. Do not change. |
| `PYTHONUNBUFFERED` | `1` | yes | Forces Python stdout/stderr to be unbuffered, so logs appear in real time in `docker compose logs`. |

### Database

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@postgres:5432/ecolos_db` | yes | Full async SQLAlchemy connection string. Uses the `asyncpg` driver. The hostname `postgres` resolves to the postgres service on the Docker internal network. |

> The `asyncpg` driver is required for async SQLAlchemy. The URL scheme must be `postgresql+asyncpg://`, not `postgresql://`.

### Redis

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `REDIS_URL` | `redis://:redispassword@redis:6379/2` | yes | Redis connection string. Uses database index 2 to avoid collisions with other services that might share the same Redis instance. The hostname `redis` resolves internally within Docker. |

### Security

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `JWT_SECRET_KEY` | `your-super-secret-key-change-in-production` | **yes — change this** | Secret used to sign JWT access and refresh tokens. Must be a long, random string in any non-local environment. Generate one with `openssl rand -hex 32`. |
| `JWT_ALGORITHM` | `HS256` | yes | Algorithm used for JWT signing. `HS256` (HMAC-SHA256) is the standard choice for symmetric signing. |
| `BCRYPT_LOG_ROUNDS` | `12` | yes | Work factor for bcrypt password hashing. Higher values are slower but more secure. 12 is the recommended minimum for production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | yes | Lifetime of JWT access tokens in minutes. After expiry, clients must use the refresh token to obtain a new access token. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | yes | Lifetime of JWT refresh tokens in days. After expiry, the user must re-authenticate. |

---

## Generating a Secure JWT Secret

```bash
# Option 1: openssl (recommended)
openssl rand -hex 32

# Option 2: Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as the value of `JWT_SECRET_KEY` in your `.env` file. Never commit this value to version control.

---

## Environment Differences by Stage

| Variable | Local Dev | Staging | Production |
|----------|-----------|---------|-----------|
| `DEBUG` | `True` | `False` | `False` |
| `JWT_SECRET_KEY` | any string | strong random | strong random |
| `BCRYPT_LOG_ROUNDS` | `10` (faster) | `12` | `12` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` (convenient) | `60` | `30` |
| Database password | `postgres` | strong password | strong password via secret manager |
| Redis password | `redispassword` | strong password | strong password via secret manager |

---

## Notes on Internal vs External URLs

When services communicate **within** the Docker network, they use the service name as the hostname (e.g., `postgres`, `redis`). When connecting **from the host machine** (e.g., using a GUI database client), use `localhost` with the exposed port.

| Context | Database URL |
|---------|-------------|
| Inside Docker (app → DB) | `postgresql+asyncpg://postgres:postgres@postgres:5432/ecolos_db` |
| Host machine (TablePlus, psql) | `postgresql://postgres:postgres@localhost:5432/ecolos_db` |
| Inside Docker (app → Redis) | `redis://:redispassword@redis:6379/2` |
| Host machine (redis-cli) | `redis://localhost:6379` (then `AUTH redispassword`) |
