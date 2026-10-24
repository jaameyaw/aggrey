# Database (`db/`)

The Aggrey MVP database: four tables (`menus`, `hours`, `holidays`, `metadata`) on
Supabase PostgreSQL. See `docs/Aggrey_MVP_Database_Schema.md` for the authoritative
design and `docs/roadmap.md` modules M1–M2 for the plan.

## Files

| File | Purpose |
| --- | --- |
| `schema.sql` | Audited schema (enums, tables, triggers, RLS). **Fresh database only** — it creates types and is not re-runnable. Do not edit silently; schema changes go in a new migration file plus an ADR (roadmap M1 step 2). |
| `seed.sql` | Initial data import, dataset `mvp_v1_2` (223 menu, 10 hours, 11 holiday, 11 metadata rows). Generated from `data/Aggrey_MVP_Data.xlsx`; re-running is duplicate-safe. Do not hand-edit — regenerate from the workbook (M2). |
| `verify.sql` | Read-only structural + content checks. Raises one exception listing every failure, or a `verify.sql: ALL CHECKS PASSED` notice. Makes no changes. |

## Run order

Always `schema.sql` → `seed.sql` → `verify.sql`, against a **fresh** database.

### Against Supabase (the real target)

Paste each file into the Supabase SQL editor and run it in order, or use `psql` with
the project connection string:

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/seed.sql
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

for f in schema seed verify; do
  psql -h "$TMP" -p 5438 -U postgres -d aggrey_verify -v ON_ERROR_STOP=1 -f "db/$f.sql"
done

pg_ctl -D "$TMP/data" stop -m immediate && rm -rf "$TMP"   # tear down
```

## What `verify.sql` checks

Structural: the four tables, both enums (`meal_type`, `schedule_type`) with their exact
labels, the four `updated_at` triggers, and RLS enabled on every table.

Content (dataset `mvp_v1_2`): row counts 223 / 10 / 11 / 11; no overlapping holiday ranges;
every weekday (1–5) has breakfast/lunch/dinner and every weekend day (6–7) has brunch/dinner;
all five lunch stations present per weekday; zero `lite_lunch` menu rows; and `holiday_sample`
rows exist and are brunch-only with a null `day_of_week`.
