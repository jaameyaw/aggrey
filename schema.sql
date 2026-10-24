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
