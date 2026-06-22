# Database Migrations

Koridor uses [Alembic](https://alembic.sqlalchemy.org/) for schema migrations. All migration files live under `migrations/alembic/versions/` and are version-controlled alongside the application code.

---

## How Migrations Run Automatically

On every `docker compose up`, the `db-migrate` one-shot container:

1. Waits for PostgreSQL to be healthy
2. Runs `alembic upgrade head` — applies all pending migrations
3. Runs `python -m migrations.scripts.seed_all` — inserts reference/seed data
4. Exits with code 0

The core application (`ecolos-core`) will not start until `db-migrate` exits successfully. This guarantees the schema is always up to date before the API accepts traffic.

---

## Directory Layout

```
migrations/
├── alembic.ini                  # Alembic configuration (script_location, logging)
├── Dockerfile.migrations        # One-shot container image
├── alembic/
│   ├── env.py                   # SQLAlchemy engine setup, migration context
│   └── versions/                # Auto-generated revision scripts
│       ├── 0001_initial_schema.py
│       └── ...
└── scripts/
    └── seed_all.py              # Seed data entry point
```

---

## Common Tasks

### Apply all pending migrations (manual)

```bash
docker compose run --rm db-migrate
```

### Check current migration state

```bash
docker compose exec ecolos-core bash
cd /app/migrations
alembic current        # shows the current revision
alembic history        # shows all revisions
alembic heads          # shows the latest revision(s)
```

### Create a new migration after changing a model

```bash
# 1. Make your changes in app/models/

# 2. Generate the migration script
docker compose exec ecolos-core bash
cd /app/migrations
alembic revision --autogenerate -m "add_user_phone_column"

# 3. Review the generated file in migrations/alembic/versions/
# Always inspect auto-generated migrations before applying them.
# Alembic cannot detect all changes (e.g., renames, constraints on existing data).

# 4. Apply it
alembic upgrade head
```

### Roll back one migration

```bash
docker compose exec ecolos-core bash
cd /app/migrations
alembic downgrade -1
```

### Roll back to a specific revision

```bash
alembic downgrade <revision_id>
# Example:
alembic downgrade 0001
```

### Roll back all the way to empty schema

```bash
alembic downgrade base
```

---

## Writing Migrations

### Auto-generate vs. manual

Alembic's `--autogenerate` compares your SQLAlchemy models against the current database schema and writes the diff. It covers most cases but has known blind spots:

| Detected automatically | Requires manual migration |
|------------------------|--------------------------|
| Add / drop column | Rename column or table |
| Add / drop table | Column type changes with data |
| Add / drop index | Custom constraints |
| Add / drop foreign key | Partial indexes |

Always read the generated script before running it in any shared environment.

### Migration file template

```python
"""add_user_phone_column

Revision ID: abc123def456
Revises: previous_revision_id
Create Date: 2024-01-15 10:30:00

"""
from alembic import op
import sqlalchemy as sa

revision = "abc123def456"
down_revision = "previous_revision_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("phone", sa.String(20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "phone")
```

### Rules to follow

- Every migration must have a working `downgrade()`. This is required.
- Migrations that modify production data (backfills, transforms) should be split from schema changes. Do the schema change first, then a separate data migration.
- Never edit an already-applied migration file. Always create a new revision.
- Use `nullable=True` for new columns on existing tables unless the column has a server-side default. Adding a non-nullable column without a default to a table with existing rows will fail.

---

## Seeding

The seeder at `migrations/scripts/seed_all.py` is run automatically after migrations. It is idempotent — running it multiple times should not create duplicate data (use `INSERT ... ON CONFLICT DO NOTHING` or check-before-insert patterns).

To run the seeder in isolation:

```bash
docker compose exec ecolos-core bash
cd /app
python -m migrations.scripts.seed_all
```

---

## Troubleshooting

### Migration container exits with non-zero code

Check the logs:

```bash
docker compose logs db-migrate
```

Common causes:
- PostgreSQL not yet accepting connections (increase `start_period` or `retries` in the postgres healthcheck)
- Syntax error in a migration file
- Conflicting revision heads (merge branches with `alembic merge heads`)

### `alembic current` shows a different revision than expected

Someone may have applied migrations manually or out of order. Stamp the current state without running migrations:

```bash
alembic stamp <revision_id>
```

### Database schema is out of sync with models

Reset the development database:

```bash
docker compose down -v          # removes all volumes including postgres_data
docker compose up --build       # starts fresh; migrations run from scratch
```

> Never do this in staging or production. Use `alembic downgrade` and `alembic upgrade` instead.
