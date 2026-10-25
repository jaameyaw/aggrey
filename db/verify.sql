-- Aggrey MVP schema verification (roadmap M1, step 3; architecture section 10).
-- Read-only structural and content checks. Run AFTER schema.sql, seed.sql and
-- migrations/001_readonly_role.sql, against the test database first and then
-- the actual Supabase project.
--
-- Behaviour: collects every failed check and raises ONE exception listing all
-- of them, so a single run reports everything wrong. On success it raises a
-- NOTICE and makes no changes (no writes, no transaction side effects).
--
-- Usage (psql / CI):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/verify.sql
-- Or paste the whole file into the Supabase SQL editor and run it.
--
-- Expected dataset: mvp_v1_3 (227 menu, 10 hours, 11 holiday, 11 metadata rows).

DO $$
DECLARE
    failures text[] := '{}';
    tables_ok boolean;
    n bigint;
    d smallint;
    item text;
    expected_stations text[] :=
        ARRAY['Main hot-food', 'Special', 'Grill / sandwich', 'Pasta', 'Pizza'];
BEGIN
    --------------------------------------------------------------------------
    -- 1. The four public tables exist.
    --------------------------------------------------------------------------
    FOREACH item IN ARRAY ARRAY['menus', 'hours', 'holidays', 'metadata'] LOOP
        IF to_regclass('public.' || item) IS NULL THEN
            failures := failures || format('missing table public.%s', item);
        END IF;
    END LOOP;

    tables_ok :=
        to_regclass('public.menus')    IS NOT NULL AND
        to_regclass('public.hours')    IS NOT NULL AND
        to_regclass('public.holidays') IS NOT NULL AND
        to_regclass('public.metadata') IS NOT NULL;

    --------------------------------------------------------------------------
    -- 2. The two enums exist with exactly the expected labels, in declared
    --    order (enumsortorder drives ORDER BY and comparisons on the enum).
    --    Plain literals appended to failures need ::text, or Postgres parses
    --    them as array literals and aborts the whole check.
    --------------------------------------------------------------------------
    IF to_regtype('public.meal_type') IS NULL THEN
        failures := failures || 'missing enum public.meal_type'::text;
    ELSIF (SELECT array_agg(enumlabel::text ORDER BY enumsortorder)
             FROM pg_enum WHERE enumtypid = 'public.meal_type'::regtype)
          <> ARRAY['breakfast', 'lunch', 'lite_lunch', 'dinner', 'brunch'] THEN
        failures := failures || 'enum public.meal_type labels do not match expected labels and order'::text;
    END IF;

    IF to_regtype('public.schedule_type') IS NULL THEN
        failures := failures || 'missing enum public.schedule_type'::text;
    ELSIF (SELECT array_agg(enumlabel::text ORDER BY enumsortorder)
             FROM pg_enum WHERE enumtypid = 'public.schedule_type'::regtype)
          <> ARRAY['weekday', 'weekend', 'holiday', 'break'] THEN
        failures := failures || 'enum public.schedule_type labels do not match expected labels and order'::text;
    END IF;

    --------------------------------------------------------------------------
    -- 3. The four updated_at triggers exist on their own tables.
    --------------------------------------------------------------------------
    FOREACH item IN ARRAY ARRAY['menus', 'hours', 'holidays', 'metadata'] LOOP
        IF to_regclass('public.' || item) IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM pg_trigger
            WHERE tgname = format('trg_aggrey_%s_updated_at', item)
              AND tgrelid = ('public.' || item)::regclass
              AND NOT tgisinternal
        ) THEN
            failures := failures
                || format('missing trigger trg_aggrey_%s_updated_at on public.%s', item, item);
        END IF;
    END LOOP;

    --------------------------------------------------------------------------
    -- 4. Row-level security is enabled on all four tables.
    --------------------------------------------------------------------------
    FOREACH item IN ARRAY ARRAY['menus', 'hours', 'holidays', 'metadata'] LOOP
        IF to_regclass('public.' || item) IS NOT NULL
           AND NOT (SELECT relrowsecurity
                      FROM pg_class WHERE oid = ('public.' || item)::regclass) THEN
            failures := failures || format('RLS not enabled on public.%s', item);
        END IF;
    END LOOP;

    --------------------------------------------------------------------------
    -- Content checks require the tables to exist; skip them otherwise so the
    -- structural failures above are reported cleanly.
    --------------------------------------------------------------------------
    IF tables_ok THEN
        ----------------------------------------------------------------------
        -- 5. Row counts after seeding (dataset mvp_v1_3).
        ----------------------------------------------------------------------
        SELECT count(*) INTO n FROM public.menus;
        IF n <> 227 THEN failures := failures || format('menus has %s rows; expected 227', n); END IF;

        SELECT count(*) INTO n FROM public.hours;
        IF n <> 10 THEN failures := failures || format('hours has %s rows; expected 10', n); END IF;

        SELECT count(*) INTO n FROM public.holidays;
        IF n <> 11 THEN failures := failures || format('holidays has %s rows; expected 11', n); END IF;

        SELECT count(*) INTO n FROM public.metadata;
        IF n <> 11 THEN failures := failures || format('metadata has %s rows; expected 11', n); END IF;

        ----------------------------------------------------------------------
        -- 6. No overlapping holiday/break ranges (dates are inclusive).
        ----------------------------------------------------------------------
        SELECT count(*) INTO n
        FROM public.holidays a
        JOIN public.holidays b
          ON a.id < b.id
         AND daterange(a.start_date, a.end_date, '[]')
          && daterange(b.start_date, b.end_date, '[]');
        IF n <> 0 THEN
            failures := failures || format('%s overlapping holiday range pair(s)', n);
        END IF;

        ----------------------------------------------------------------------
        -- 7. Meal coverage: weekdays 1-5 serve breakfast/lunch/dinner;
        --    weekend days 6-7 serve brunch/dinner (menu_scope = 'weekly').
        ----------------------------------------------------------------------
        FOR d IN 1..5 LOOP
            FOREACH item IN ARRAY ARRAY['breakfast', 'lunch', 'dinner'] LOOP
                IF NOT EXISTS (
                    SELECT 1 FROM public.menus
                    WHERE menu_scope = 'weekly'
                      AND day_of_week = d
                      AND meal_type = item::public.meal_type
                ) THEN
                    failures := failures || format('weekday %s has no %s menu rows', d, item);
                END IF;
            END LOOP;
        END LOOP;

        FOR d IN 6..7 LOOP
            FOREACH item IN ARRAY ARRAY['brunch', 'dinner'] LOOP
                IF NOT EXISTS (
                    SELECT 1 FROM public.menus
                    WHERE menu_scope = 'weekly'
                      AND day_of_week = d
                      AND meal_type = item::public.meal_type
                ) THEN
                    failures := failures || format('weekend day %s has no %s menu rows', d, item);
                END IF;
            END LOOP;
        END LOOP;

        ----------------------------------------------------------------------
        -- 8. All five lunch stations exist for each weekday (1-5).
        ----------------------------------------------------------------------
        FOR d IN 1..5 LOOP
            FOREACH item IN ARRAY expected_stations LOOP
                IF NOT EXISTS (
                    SELECT 1 FROM public.menus
                    WHERE menu_scope = 'weekly'
                      AND day_of_week = d
                      AND meal_type = 'lunch'
                      AND station = item
                ) THEN
                    failures := failures || format('weekday %s lunch missing station "%s"', d, item);
                END IF;
            END LOOP;
        END LOOP;

        ----------------------------------------------------------------------
        -- 9. No lite_lunch menu rows exist (food menu was never supplied).
        ----------------------------------------------------------------------
        SELECT count(*) INTO n FROM public.menus WHERE meal_type = 'lite_lunch';
        IF n <> 0 THEN
            failures := failures || format('%s lite_lunch menu row(s) found; expected 0', n);
        END IF;

        ----------------------------------------------------------------------
        -- 10. holiday_sample rows exist, carry a null weekday, and are brunch or
        --     dinner (dinner sample added in mvp_v1_3). Both meals must be present.
        ----------------------------------------------------------------------
        SELECT count(*) INTO n FROM public.menus WHERE menu_scope = 'holiday_sample';
        IF n = 0 THEN
            failures := failures || 'no holiday_sample menu rows found'::text;
        ELSE
            SELECT count(*) INTO n
            FROM public.menus
            WHERE menu_scope = 'holiday_sample'
              AND (meal_type NOT IN ('brunch', 'dinner') OR day_of_week IS NOT NULL);
            IF n <> 0 THEN
                failures := failures
                    || format('%s holiday_sample row(s) are not brunch/dinner with a null day_of_week', n);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM public.menus
                WHERE menu_scope = 'holiday_sample' AND meal_type = 'brunch'
            ) THEN
                failures := failures || 'no holiday_sample brunch rows found'::text;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM public.menus
                WHERE menu_scope = 'holiday_sample' AND meal_type = 'dinner'
            ) THEN
                failures := failures || 'no holiday_sample dinner rows found'::text;
            END IF;
        END IF;

        ----------------------------------------------------------------------
        -- 11. Migration 001: the backend's read-only role can read every
        --     table (SELECT grant + FOR SELECT policy) and cannot write.
        --     reset_schema.sql drops both, so this catches a skipped re-run.
        ----------------------------------------------------------------------
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'aggrey_readonly') THEN
            failures := failures
                || 'missing role aggrey_readonly (run db/migrations/001_readonly_role.sql)'::text;
        ELSE
            FOREACH item IN ARRAY ARRAY['menus', 'hours', 'holidays', 'metadata'] LOOP
                IF NOT has_table_privilege('aggrey_readonly', 'public.' || item, 'SELECT') THEN
                    failures := failures
                        || format('aggrey_readonly lacks SELECT on public.%s', item);
                END IF;
                -- has_any_column_privilege also catches column-level
                -- INSERT/UPDATE grants, which has_table_privilege ignores.
                IF has_any_column_privilege('aggrey_readonly', 'public.' || item,
                                            'INSERT, UPDATE')
                   OR has_table_privilege('aggrey_readonly', 'public.' || item,
                                          'DELETE, TRUNCATE') THEN
                    failures := failures
                        || format('aggrey_readonly has a write privilege on public.%s', item);
                END IF;
                -- The policy must be scoped to aggrey_readonly alone: the same
                -- name with TO public would expose every row to anon on Supabase.
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies
                    WHERE schemaname = 'public'
                      AND tablename = item
                      AND policyname = 'aggrey_readonly_select'
                      AND cmd = 'SELECT'
                      AND roles = ARRAY['aggrey_readonly']::name[]
                ) THEN
                    failures := failures
                        || format('missing policy aggrey_readonly_select (FOR SELECT TO aggrey_readonly) on public.%s', item);
                END IF;
            END LOOP;
        END IF;
    END IF;

    --------------------------------------------------------------------------
    -- Report.
    --------------------------------------------------------------------------
    IF array_length(failures, 1) IS NULL THEN
        RAISE NOTICE 'verify.sql: ALL CHECKS PASSED';
    ELSE
        RAISE EXCEPTION E'verify.sql: % check(s) FAILED:\n  - %',
            array_length(failures, 1),
            array_to_string(failures, E'\n  - ');
    END IF;
END;
$$;
