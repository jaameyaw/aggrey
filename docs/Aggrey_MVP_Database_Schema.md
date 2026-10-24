# Aggrey MVP Database Schema

**Database:** PostgreSQL on Supabase  
**Schema revision:** 2026-10-24 final alignment audit. **Dataset version:** `mvp_v1_2` aligned with `Aggrey_MVP_Data.xlsx`  
**Purpose:** Build-ready database specification for Codex and FastAPI

---

## 1. What Changed From the Previous Schema

The previous schema assumed that menu rows were tied directly to calendar dates. The final MVP data does not work that way.

The corrected MVP workbook uses:

- a **weekly recurring menu**
- `day_of_week` values from 1 through 7
- separate `menu_scope` values for the weekly menu and the provisional holiday sample
- `lite_lunch` hours without a supplied Lite Lunch food menu
- four schedule types: `weekday`, `weekend`, `holiday`, and `break`
- holiday/special-calendar **date ranges**, not only single dates
- verification status and notes for schedule overrides
- metadata that documents provisional MVP rules

The database schema should follow this structure instead of forcing the workbook into the old date-based model.

---

# 2. Required Tables

The MVP uses exactly four tables:

1. `menus`
2. `hours`
3. `holidays`
4. `metadata`

The tables remain independent for MVP simplicity.

**No foreign keys are used.**

---

# 3. PostgreSQL Enums

## `meal_type`

```sql
CREATE TYPE meal_type AS ENUM (
    'breakfast',
    'lunch',
    'lite_lunch',
    'dinner',
    'brunch'
);
```

`lite_lunch` is included because the final hours data contains a weekday Lite Lunch period from 14:00 to 15:00.

The current dataset does **not** contain a Lite Lunch food menu. That is a missing-data condition, not a reason to remove the meal type.

## `schedule_type`

```sql
CREATE TYPE schedule_type AS ENUM (
    'weekday',
    'weekend',
    'holiday',
    'break'
);
```

The `break` value is required because Fall Break, Thanksgiving, Virtual Classes / Reading Day / Exams, Christmas Break, and Spring Break use the break schedule in the current MVP data.

---

# 4. Complete PostgreSQL DDL

The executable version below is **`schema.sql`**, intended for a **fresh Supabase database**. It preserves the four UUID-primary-key tables and PostgreSQL enums from this specification, and adds missing calendar-overlap, validation, updated timestamp, and RLS safeguards.

```sql
-- Aggrey MVP database schema. Final alignment audit (2026-10-24).
-- Authoritative dataset: Aggrey_MVP_Data.xlsx (dataset_version mvp_v1_2).
-- Fresh Supabase PostgreSQL project only. Execute once before seed.sql.
-- Exactly four public tables; weekly menu entries have NO service_date.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE public.meal_type AS ENUM (
    'breakfast', 'lunch', 'lite_lunch', 'dinner', 'brunch'
);
CREATE TYPE public.schedule_type AS ENUM (
    'weekday', 'weekend', 'holiday', 'break'
);

CREATE TABLE public.menus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_scope TEXT NOT NULL
        CHECK (menu_scope IN ('weekly', 'holiday_sample')),
    day_of_week SMALLINT,
    meal_type public.meal_type NOT NULL,
    station TEXT NOT NULL CHECK (btrim(station) <> ''),
    food_item TEXT NOT NULL CHECK (btrim(food_item) <> ''),
    display_order INTEGER NOT NULL CHECK (display_order > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT menus_schedule_compatible CHECK (
        (menu_scope = 'holiday_sample'
         AND day_of_week IS NULL AND meal_type = 'brunch')
        OR (menu_scope = 'weekly'
            AND day_of_week IS NOT NULL
            AND day_of_week BETWEEN 1 AND 5
            AND meal_type IN ('breakfast', 'lunch', 'dinner'))
        OR (menu_scope = 'weekly'
            AND day_of_week IS NOT NULL
            AND day_of_week IN (6, 7)
            AND meal_type IN ('brunch', 'dinner'))
    )
);

-- The same item may appear on multiple days or at multiple stations,
-- but cannot be duplicated within a specific weekly day/meal/station.
CREATE UNIQUE INDEX uq_menus_weekly_item ON public.menus
    (day_of_week, meal_type, lower(btrim(station)), lower(btrim(food_item)))
    WHERE menu_scope = 'weekly';
CREATE UNIQUE INDEX uq_menus_holiday_sample_item ON public.menus
    (meal_type, lower(btrim(station)), lower(btrim(food_item)))
    WHERE menu_scope = 'holiday_sample';
CREATE INDEX idx_menus_lookup ON public.menus
    (menu_scope, day_of_week, meal_type, station, display_order);

CREATE TABLE public.hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_type public.schedule_type NOT NULL,
    meal_type public.meal_type NOT NULL,
    start_time TIME WITHOUT TIME ZONE NOT NULL,
    end_time TIME WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT hours_valid_window CHECK (end_time > start_time),
    CONSTRAINT hours_unique_schedule_meal UNIQUE (schedule_type, meal_type),
    CONSTRAINT hours_schedule_meal_valid CHECK (
        (schedule_type = 'weekday'
         AND meal_type IN ('breakfast', 'lunch', 'lite_lunch', 'dinner'))
        OR (schedule_type IN ('weekend', 'holiday', 'break')
            AND meal_type IN ('brunch', 'dinner'))
    )
);

CREATE TABLE public.holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    schedule_type public.schedule_type NOT NULL
        CHECK (schedule_type IN ('holiday', 'break')),
    verification_status TEXT NOT NULL
        CHECK (btrim(verification_status) <> ''),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT holidays_valid_dates CHECK (end_date >= start_date),
    CONSTRAINT holidays_unique_period UNIQUE (name, start_date, end_date),
    -- PostgreSQL date ranges canonicalize '[]' to an inclusive-day range.
    CONSTRAINT holidays_no_overlap EXCLUDE USING gist
      (daterange(start_date, end_date, '[]') WITH &&)
);
CREATE INDEX idx_holidays_date_range ON public.holidays (start_date, end_date);

CREATE TABLE public.metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "key" TEXT NOT NULL UNIQUE
        CHECK (btrim("key") <> ''),
    value TEXT NOT NULL CHECK (btrim(value) <> ''),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE FUNCTION public.aggrey_touch_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_aggrey_menus_updated_at
    BEFORE UPDATE ON public.menus FOR EACH ROW
    EXECUTE FUNCTION public.aggrey_touch_updated_at();
CREATE TRIGGER trg_aggrey_hours_updated_at
    BEFORE UPDATE ON public.hours FOR EACH ROW
    EXECUTE FUNCTION public.aggrey_touch_updated_at();
CREATE TRIGGER trg_aggrey_holidays_updated_at
    BEFORE UPDATE ON public.holidays FOR EACH ROW
    EXECUTE FUNCTION public.aggrey_touch_updated_at();
CREATE TRIGGER trg_aggrey_metadata_updated_at
    BEFORE UPDATE ON public.metadata FOR EACH ROW
    EXECUTE FUNCTION public.aggrey_touch_updated_at();

-- Supabase: no direct anonymous/authenticated table access.
-- Access from the FastAPI server only using protected server credentials.
ALTER TABLE public.menus ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hours ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.holidays ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.metadata ENABLE ROW LEVEL SECURITY;

COMMIT;
```

---

# 5. Table Definitions

## 5.1 `menus`

The `menus` table stores the actual recurring food menu.

| Column | Type | Required | Meaning |
|---|---|---:|---|
| `id` | `uuid` | Yes | Primary key |
| `menu_scope` | `text` | Yes | `weekly` or `holiday_sample` |
| `day_of_week` | `smallint` | Conditional | 1 = Monday through 7 = Sunday; null for `holiday_sample` |
| `meal_type` | `meal_type` | Yes | Breakfast, lunch, Lite Lunch, dinner, or brunch |
| `station` | `text` | Yes | Dining station |
| `food_item` | `text` | Yes | Food item |
| `display_order` | `integer` | Yes | Ordering within a station |
| `created_at` | `timestamptz` | Yes | Creation timestamp |
| `updated_at` | `timestamptz` | Yes | Last application update timestamp |

### Why there is no `service_date`

The MVP menu repeats weekly.

For example:

```text
menu_scope = weekly
day_of_week = 1
meal_type = lunch
station = Main hot-food
food_item = BBQ Chicken
```

means BBQ Chicken belongs to the recurring Monday lunch menu.

The backend determines the calendar date first, converts it to the correct day of week, then queries the weekly menu.

### Day-of-week convention

Use ISO weekday numbering:

| Value | Day |
|---:|---|
| 1 | Monday |
| 2 | Tuesday |
| 3 | Wednesday |
| 4 | Thursday |
| 5 | Friday |
| 6 | Saturday |
| 7 | Sunday |

This matches Python's `date.isoweekday()`.

---

## 5.2 `hours`

The `hours` table stores meal serving windows.

| Column | Type | Required | Meaning |
|---|---|---:|---|
| `id` | `uuid` | Yes | Primary key |
| `schedule_type` | `schedule_type` | Yes | Weekday, weekend, holiday, or break |
| `meal_type` | `meal_type` | Yes | Meal represented by the row |
| `start_time` | `time` | Yes | Start of service |
| `end_time` | `time` | Yes | End of service |
| `created_at` | `timestamptz` | Yes | Creation timestamp |
| `updated_at` | `timestamptz` | Yes | Last application update timestamp |

Valid combinations are enforced by the database:

| Schedule | Valid meal types |
|---|---|
| `weekday` | breakfast, lunch, lite_lunch, dinner |
| `weekend` | brunch, dinner |
| `holiday` | brunch, dinner |
| `break` | brunch, dinner |

---

## 5.3 `holidays`

Despite the table name, this table stores **all calendar periods that override the normal schedule**, including official holidays and school breaks.

| Column | Type | Required | Meaning |
|---|---|---:|---|
| `id` | `uuid` | Yes | Primary key |
| `name` | `text` | Yes | Name of the holiday or break |
| `start_date` | `date` | Yes | First date of override |
| `end_date` | `date` | Yes | Last date of override |
| `schedule_type` | `schedule_type` | Yes | `holiday` or `break` |
| `verification_status` | `text` | Yes | Current confidence/source status from the MVP data |
| `notes` | `text` | No | Clarification or provisional rule |
| `created_at` | `timestamptz` | Yes | Creation timestamp |
| `updated_at` | `timestamptz` | Yes | Last application update timestamp |

Using date ranges avoids creating one database row for every day of a multi-day break.

---

## 5.4 `metadata`

The `metadata` table stores small dataset-level settings and MVP assumptions.

| Column | Type | Required | Meaning |
|---|---|---:|---|
| `id` | `uuid` | Yes | Primary key |
| `key` | `text` | Yes | Unique setting name |
| `value` | `text` | Yes | Setting value |
| `notes` | `text` | No | Human-readable explanation |
| `created_at` | `timestamptz` | Yes | Creation timestamp |
| `updated_at` | `timestamptz` | Yes | Last application update timestamp |

Examples from the current dataset include:

- `timezone = America/New_York`
- `menu_recurrence = weekly`
- `update_policy = manual`
- `lite_lunch_menu_status = missing`
- `thanksgiving_christmas_hours_rule = break`
- `virtual_classes_hours_status = break_template_provisional`

Application code should not use informational metadata such as `lunch_station_count` as a hard-coded business rule. Stations should be read from the menu rows themselves.

---

# 6. Representative Rows From the Current MVP Dataset

These examples reflect the structure of the corrected MVP workbook.

## 6.1 `menus`

```sql
INSERT INTO menus (
    menu_scope,
    day_of_week,
    meal_type,
    station,
    food_item,
    display_order
)
VALUES
    ('weekly', 1, 'breakfast', 'Breakfast',
        'Scrambled Eggs', 1),

    ('weekly', 1, 'lunch', 'Main hot-food',
        'BBQ Chicken', 1),

    ('weekly', 3, 'lunch', 'Main hot-food',
        'Southern Fried Chicken', 1),

    ('weekly', 6, 'brunch', 'Breakfast',
        'Scrambled Eggs', 1),

    ('weekly', 7, 'dinner', 'Dinner / turntable',
        'Creamy-Herb Salmon', 1),

    ('holiday_sample', NULL, 'brunch', 'Main hot-food',
        'Blackened Chicken', 1);
```

---

## 6.2 `hours`

```sql
INSERT INTO hours (
    schedule_type,
    meal_type,
    start_time,
    end_time
)
VALUES
    ('weekday', 'breakfast', '07:30', '09:30'),
    ('weekday', 'lunch', '11:00', '14:00'),
    ('weekday', 'lite_lunch', '14:00', '15:00'),
    ('weekday', 'dinner', '17:00', '20:00'),

    ('weekend', 'brunch', '10:30', '13:30'),
    ('weekend', 'dinner', '17:00', '20:00'),

    ('holiday', 'brunch', '10:30', '13:30'),
    ('holiday', 'dinner', '17:00', '20:00'),

    ('break', 'brunch', '10:00', '11:00'),
    ('break', 'dinner', '16:00', '18:00');
```

---

## 6.3 `holidays`

```sql
INSERT INTO holidays (
    name,
    start_date,
    end_date,
    schedule_type,
    verification_status,
    notes
)
VALUES
    (
        'Labor Day',
        '2026-09-07',
        '2026-09-07',
        'holiday',
        'calendar_date; mvp_hours',
        'Official campus closure. Default holiday hours.'
    ),
    (
        'Fall Break',
        '2026-10-15',
        '2026-10-16',
        'break',
        'calendar_date; latest_hours',
        'Fall Break override uses break hours.'
    ),
    (
        'Thanksgiving Holiday',
        '2026-11-25',
        '2026-11-27',
        'break',
        'calendar_date; user_confirmed_hours',
        'Uses Fall Break brunch 10:00-11:00 and dinner 16:00-18:00.'
    ),
    (
        'Virtual Classes, Reading Day & Exams',
        '2026-11-30',
        '2026-12-12',
        'break',
        'pending_confirmation',
        'Temporary MVP template: use Fall Break hours. Replace when confirmed.'
    ),
    (
        'Christmas Break',
        '2026-12-17',
        '2027-01-01',
        'break',
        'calendar_date; user_confirmed_hours',
        'Uses Fall Break brunch 10:00-11:00 and dinner 16:00-18:00.'
    );
```

---

## 6.4 `metadata`

```sql
INSERT INTO metadata (
    key,
    value,
    notes
)
VALUES
    (
        'dataset_version',
        'mvp_v1_2',
        'Corrected weekday breakfast mapping and removed redundant weekend breakfast entries.'
    ),
    (
        'timezone',
        'America/New_York',
        'College local time'
    ),
    (
        'menu_recurrence',
        'weekly',
        'Repeat weekly without tying menu items to calendar dates'
    ),
    (
        'update_policy',
        'manual',
        'Until manager provides an update process'
    ),
    (
        'lite_lunch_menu_status',
        'missing',
        'Lite Lunch hours exist; food menu not supplied'
    ),
    (
        'holiday_dinner_fallback',
        'day_of_week_dinner',
        'Test assumption only, not verified holiday dinner menu'
    ),
    (
        'virtual_classes_hours_status',
        'break_template_provisional',
        'Use the break schedule for MVP testing until confirmed'
    );
```

---

# 7. Indexing Strategy

The runnable schema uses only the indexes needed for the current 223-row MVP dataset:

- `uq_menus_weekly_item`: prevents repeated food names (ignoring case/outer spaces) within one weekday/meal/station, while permitting the same dish on multiple days.
- `uq_menus_holiday_sample_item`: prevents repeats in the shared holiday brunch sample without relying on a nullable weekday column.
- `idx_menus_lookup`: supports recurring day/meal/station retrieval with predictable ordering.
- The `UNIQUE (schedule_type, meal_type)` constraint indexes `hours` lookups automatically.
- The holiday overlap exclusion constraint adds a GiST index; `idx_holidays_date_range` supports the simple inclusive date lookup.
- The `UNIQUE` metadata `key` automatically provides key lookup indexing.

**Food searches:** The PRD allows searches such as `ILIKE '%chicken%'`. A normal B-tree index on `lower(food_item)` does **not** accelerate arbitrary substring searches. With 223 food rows a simple filtered search is sufficient; do not add full-text or trigram search until needed.

---

# 8. Schedule Resolution

The backend must resolve the schedule **before** looking up meal hours or menu behavior.

## Step 1: Check calendar overrides

```sql
SELECT
    name,
    schedule_type,
    verification_status,
    notes
FROM holidays
WHERE $1 BETWEEN start_date AND end_date;
```

`$1` is the requested date.

Normally, this query should return either zero rows or one row.

If multiple override rows match the same date, the dataset is ambiguous and should be corrected instead of silently choosing one.

## Step 2: Apply fallback calendar logic

If there is an override row:

```text
use holidays.schedule_type
```

Otherwise:

```python
if requested_date.isoweekday() in (6, 7):
    schedule_type = "weekend"
else:
    schedule_type = "weekday"
```

Therefore the resolution order is:

```text
1. Explicit holiday/break override from database
2. Weekend
3. Normal weekday
```

This allows a weekday such as Thanksgiving Wednesday to correctly use the `break` schedule.

---

# 9. Meal Validation

After schedule resolution, FastAPI validates the requested meal.

| Schedule | Valid meals |
|---|---|
| `weekday` | breakfast, lunch, lite_lunch, dinner |
| `weekend` | brunch, dinner |
| `holiday` | brunch, dinner |
| `break` | brunch, dinner |

Examples:

### Saturday lunch request

```text
Requested schedule: weekend
Requested meal: lunch
```

Lunch is invalid for the weekend schedule.

Aggrey should explain that regular lunch is not being served and that brunch and dinner are the available meals.

### Weekday Lite Lunch request

```text
Requested schedule: weekday
Requested meal: lite_lunch
```

Lite Lunch is valid for hours lookup.

However, the current menu dataset contains no `lite_lunch` menu rows.

Aggrey can answer the hours but should report the Lite Lunch food menu as unavailable.

---

# 10. Backend Query Patterns

## 10.1 Weekly menu lookup

Example:

> What's for dinner today?

After the date has been resolved and the applicable meal validated:

```sql
SELECT
    station,
    food_item,
    display_order
FROM menus
WHERE menu_scope = 'weekly'
  AND day_of_week = $1
  AND meal_type = $2
ORDER BY station, display_order, food_item;
```

Parameters:

```text
$1 = requested_date.isoweekday()
$2 = resolved meal
```

For normal weekday and weekend meals, this is the main menu lookup.

---

## 10.2 Holiday / break brunch lookup

The current dataset contains a provisional holiday brunch sample:

```text
menu_scope = holiday_sample
meal_type = brunch
```

Query:

```sql
SELECT
    station,
    food_item,
    display_order
FROM menus
WHERE menu_scope = 'holiday_sample'
  AND meal_type = 'brunch'
ORDER BY station, display_order, food_item;
```

This is provisional MVP data and should be treated according to the metadata and holiday notes.

---

## 10.3 Holiday / break dinner fallback

The current metadata contains:

```text
holiday_dinner_fallback = day_of_week_dinner
```

and explicitly notes that this is a **test assumption**, not a verified holiday dinner menu.

If that MVP fallback remains enabled, dinner is loaded from the weekly dinner corresponding to the requested calendar weekday:

```sql
SELECT
    station,
    food_item,
    display_order
FROM menus
WHERE menu_scope = 'weekly'
  AND day_of_week = $1
  AND meal_type = 'dinner'
ORDER BY station, display_order, food_item;
```

This fallback should remain isolated in business logic so it can be replaced when verified holiday dinner data becomes available.

It must not be presented in code as if it were confirmed source data.

---

# 11. Hours Lookup

Example:

> What time is dinner?

Once the schedule is resolved:

```sql
SELECT
    start_time,
    end_time
FROM hours
WHERE schedule_type = $1
  AND meal_type = $2;
```

Example parameters:

```text
$1 = break
$2 = dinner
```

Result from the current dataset:

```text
16:00 - 18:00
```

For:

> Is the cafeteria open?

the backend can retrieve all current schedule windows:

```sql
SELECT
    meal_type,
    start_time,
    end_time
FROM hours
WHERE schedule_type = $1
ORDER BY start_time;
```

Then FastAPI compares the current local time against the returned windows.

The current timezone metadata is:

```text
America/New_York
```

---

# 12. Food-Item Lookup

## Specific meal

Example:

> Do they have chicken for lunch?

```sql
SELECT
    station,
    food_item
FROM menus
WHERE menu_scope = 'weekly'
  AND day_of_week = $1
  AND meal_type = $2
  AND food_item ILIKE '%' || $3 || '%'
ORDER BY station, display_order;
```

Parameters:

```text
$1 = ISO day of week
$2 = lunch
$3 = chicken
```

## No meal specified

Example:

> Do they have chicken today?

For a normal weekday/weekend query:

```sql
SELECT
    meal_type,
    station,
    food_item
FROM menus
WHERE menu_scope = 'weekly'
  AND day_of_week = $1
  AND food_item ILIKE '%' || $2 || '%'
ORDER BY meal_type, station, display_order;
```

The backend should restrict interpretation to meals valid for the resolved schedule.

For holiday/break dates, menu lookup must follow the provisional holiday-menu rules described above rather than blindly using every weekly meal for that day.

---

# 13. Missing-Data Handling

Missing data must never be converted into invented dining information.

## Lite Lunch menu

The database contains:

```text
weekday lite_lunch hours
```

but the menu dataset contains no Lite Lunch food rows.

Therefore:

> What time is Lite Lunch?

can be answered from `hours`.

But:

> What's for Lite Lunch?

must return a missing-menu response.

Example meaning:

```text
Lite Lunch is scheduled from 2:00 PM to 3:00 PM,
but I don't have the Lite Lunch food menu.
```

## Missing weekly menu

If a valid menu query returns zero rows:

```text
Menu information is unavailable for that meal.
```

## Missing hours

If a valid hours query returns zero rows:

```text
Dining hours are unavailable for that meal.
```

## Food item not found

A zero-result food-item search means only:

```text
The item was not found in Aggrey's stored menu data.
```

It does not prove that the real cafeteria cannot have the item.

---

# 14. Metadata Queries

Metadata can be loaded by key:

```sql
SELECT value, notes
FROM metadata
WHERE key = $1;
```

Examples that can affect MVP behavior:

```text
timezone
menu_recurrence
lite_lunch_menu_status
holiday_brunch_source
holiday_dinner_fallback
virtual_classes_hours_status
```

Other metadata such as `lunch_station_count` should be treated as descriptive information, not as a hard-coded application rule.

---

# 15. Recommended Backend Request Order

For a meal-related request:

```text
1. Receive the student message.
2. Detect intent.
3. Resolve the requested date.
4. Query holidays for a date-range override.
5. Resolve schedule_type:
      explicit holiday/break override
      else weekend
      else weekday
6. Resolve/validate meal_type.
7. Choose the correct menu scope/rule.
8. Query menus or hours.
9. Apply missing-data fallback if needed.
10. Format the response.
11. Send through Sendblue.
```

This order prevents normal weekday logic from overriding a break or holiday.

---

# 16. How Each Table Is Used

| Table | Runtime responsibility |
|---|---|
| `menus` | Weekly menu lookup, provisional holiday brunch lookup, and food-item search |
| `hours` | Serving times and open/closed calculations for weekday, weekend, holiday, and break schedules |
| `holidays` | Date-range overrides that determine whether a date uses `holiday` or `break` rules |
| `metadata` | Dataset-level MVP configuration, assumptions, provisional-status information, and timezone |

---

# 17. Current Business Rules Represented by the Schema

## Normal weekday

```text
Monday-Friday
unless overridden by holidays table

Breakfast
Lunch
Lite Lunch hours
Dinner
```

The food menu currently contains breakfast, lunch, and dinner data.

Lite Lunch food data is missing.

## Weekend

```text
Saturday-Sunday
unless an explicit holiday/break override applies

Brunch
Dinner
```

The corrected menu dataset no longer contains redundant Saturday/Sunday breakfast rows.

## Holiday

```text
Brunch
Dinner

Hours:
Brunch 10:30-13:30
Dinner 17:00-20:00
```

Holiday-menu content remains provisional according to the current dataset metadata.

## Break

```text
Brunch
Dinner

Hours:
Brunch 10:00-11:00
Dinner 16:00-18:00
```

The current break schedule applies to records such as Fall Break and, based on the current MVP data, Thanksgiving and Christmas.

The Virtual Classes / Reading Day / Exams range also uses the break schedule as a provisional MVP template until confirmed.

---

# 18. Important Data Integrity Notes

### Do not add `service_date` to `menus`

The current menu repeats weekly. Adding a date to every menu row would duplicate recurring data and misrepresent the source.

### Do not duplicate schedule type inside `menus`

Schedule resolution comes from:

- the requested date
- `holidays`
- weekend detection

The menu table only needs the recurring day/meal structure and menu scope.

### Do not invent Lite Lunch menu rows

The current dataset explicitly states that the Lite Lunch food menu was not supplied.

### Do not treat provisional holiday dinner fallback as verified data

The fallback is documented in metadata as an MVP test assumption.

### Do not hard-code holiday ranges in Python

Holiday and break ranges belong in the `holidays` table so they can be changed without changing application code.

### Do not hard-code exact station counts

Read the stations available from `menus`.

---

# 19. Final Schema Summary

```text
meal_type enum
  breakfast
  lunch
  lite_lunch
  dinner
  brunch

schedule_type enum
  weekday
  weekend
  holiday
  break


menus
  id UUID PK
  menu_scope TEXT
  day_of_week SMALLINT NULL
  meal_type meal_type
  station TEXT
  food_item TEXT
  display_order INTEGER
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ


hours
  id UUID PK
  schedule_type schedule_type
  meal_type meal_type
  start_time TIME
  end_time TIME
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ


holidays
  id UUID PK
  name TEXT
  start_date DATE
  end_date DATE
  schedule_type schedule_type
  verification_status TEXT
  notes TEXT NULL
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ


metadata
  id UUID PK
  key TEXT UNIQUE
  value TEXT
  notes TEXT NULL
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ
```

This schema now matches the structure and rules in the corrected Aggrey MVP dataset and should replace the earlier date-based database design.

---

# 20. Audit Alignment, Security, and Limitations

**Audit date:** October 24, 2026. `Aggrey_MVP_Data.xlsx` was compared against `Aggrey_MVP_Data.md`, the updated PRD, and the roadmap. The source workbook remains unchanged.

- The **executable SQL migration** and this design now use actual PostgreSQL enums and UUID primary keys for **all four tables**. The previously distributed SQL package used checked `TEXT` and made `metadata.key` its primary key; do **not** mix that older `schema.sql` with this audited version.
- The migration adds **RLS on all four tables** and creates **no public client access policies**. Only a protected backend should access the database. Protect any Supabase service-role credentials.
- The migration prevents **overlapping holiday/break periods**, so ambiguous date overrides fail on insert. All existing 11 dated ranges pass this rule.
- `updated_at` changes automatically on row updates via triggers.
- Database `time` means a *meal serving window*, not necessarily building opening hours. The app should say whether a meal is being served, rather than claiming the building is open outside listed windows.
- The source provides **Lite Lunch serving hours only**, not a food menu. Do not generate Lite Lunch menu rows.
- `holiday_dinner_fallback=day_of_week_dinner` is an **unverified demonstration assumption**. Do not state such food as officially served. Prefer saying verified holiday dinner menu information is unavailable in public-facing replies until it is provided.
- The virtual class/exam period's break hours remain **provisional**. The product must label them as such if shown to students.
- No distinct summer-break dates are supplied. `summer_operations=reduced_schedule` documents intent, but **does not authorize an automatic summer override** without dates.
- The four tables contain **no student-message or conversation-state storage**. Short-lived follow-up context, retry deduplication, and deployment strategy belong to the FastAPI messaging module, not to these four dining tables.
- **Initial deployment only:** `schema.sql` creates types/tables, so run it on a fresh Aggrey project. `seed.sql` is safe against duplicate re-runs but does not delete old/renamed menu foods or fully synchronize future spreadsheets.
- **Validation status:** Workbook/Markdown parity, row uniqueness, display-order checks, day/station completeness, schedule compatibility, and holiday-range overlap were checked locally. PostgreSQL/Supabase runtime execution remains **untested** until the team runs `schema.sql`, `seed.sql`, and `verify.sql` in its project.
