# Database (`db/`)

The Aggrey MVP database: four tables (`menus`, `hours`, `holidays`, `metadata`) on
Supabase PostgreSQL. See `docs/Aggrey_MVP_Database_Schema.md` for the authoritative
design and `docs/roadmap.md` modules M1–M2 for the plan.

## Files

| File | Purpose |
| --- | --- |
| `schema.sql` | Audited schema (enums, tables, triggers, RLS). **Fresh database only** — it creates types and is not re-runnable. Do not edit silently; schema changes go in a new migration file plus an ADR (roadmap M1 step 2). |
| `seed.sql` | Initial data import, dataset `mvp_v1_3` (227 menu, 10 hours, 11 holiday, 11 metadata rows). Generated from `data/Aggrey_MVP_Data.xlsx`; re-running is duplicate-safe. Do not hand-edit — regenerate from the workbook (M2). |
| `migrations/001_readonly_role.sql` | Read-only backend role `aggrey_readonly` (SELECT grant + `FOR SELECT` policy per table, no write). Idempotent. See `docs/adr/0001-database-access-method.md`. |
| `verify.sql` | Read-only structural + content checks. Raises one exception listing every failure, or a `verify.sql: ALL CHECKS PASSED` notice. Makes no changes. |
| `reset_schema.sql` | **Destructive** dev helper: drops all four tables and their data so `schema.sql` can run again. Refuses unless `SET aggrey.confirm_reset = 'yes';` runs first in the same session; the flag is cleared after each reset. Never run on the live project once real data matters. |
| `check_schema_sync.py` | CI check (`schema-sync` job) that `schema.sql` matches section 4 of the schema doc. |

## Run order

Always `schema.sql` → `seed.sql` → `migrations/001_readonly_role.sql` → `verify.sql`, against a
**fresh** database. After `reset_schema.sql`, run the whole sequence again — the reset removes
the migration's grants and policies.

### Against Supabase (the real target)

Paste each file into the Supabase SQL editor and run it in order, or use `psql` with
the project connection string:

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/seed.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/001_readonly_role.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/verify.sql   # expect: ALL CHECKS PASSED
```

`verify.sql` exits non-zero if any check fails, so it is safe to use as a CI/release gate.

### Local test database

Any local PostgreSQL 14+ works (the schema uses `pgcrypto`, enums, a GiST range-exclusion
constraint, and RLS — all core PostgreSQL features). Example with a disposable cluster using
Homebrew's `postgresql@16`:

```sh
export PATH="$(brew --prefix postgresql@16)/bin:$PATH"
TMP=$(mktemp -d)
initdb -D "$TMP/data" -U postgres --auth-local=trust -E UTF-8
pg_ctl -D "$TMP/data" -o "-p 5438 -k $TMP -c listen_addresses=''" -l "$TMP/log" start
createdb -h "$TMP" -p 5438 -U postgres aggrey_verify

for f in schema seed migrations/001_readonly_role verify; do
  psql -h "$TMP" -p 5438 -U postgres -d aggrey_verify -v ON_ERROR_STOP=1 -f "db/$f.sql"
done

pg_ctl -D "$TMP/data" stop -m immediate && rm -rf "$TMP"   # tear down
```

## What `verify.sql` checks

Structural: the four tables, both enums (`meal_type`, `schedule_type`) with their exact
labels in declared order, the four `updated_at` triggers on their own tables, and RLS enabled
on every table.

Content (dataset `mvp_v1_3`): row counts 227 / 10 / 11 / 11; no overlapping holiday ranges;
every weekday (1–5) has breakfast/lunch/dinner and every weekend day (6–7) has brunch/dinner;
all five lunch stations present per weekday; zero `lite_lunch` menu rows; and `holiday_sample`
rows exist, carry a null `day_of_week`, and include both brunch and dinner.

Access (migration 001): role `aggrey_readonly` exists, has SELECT and no write privilege on all
four tables (including column-level INSERT/UPDATE), and each table has its
`aggrey_readonly_select` policy scoped to that role only.
