-- Reset script: undoes schema.sql so it can be run again on a clean slate.
-- Not part of the audited schema files (schema.sql / seed.sql / verify.sql).
--
-- DESTRUCTIVE: drops all four tables and EVERY ROW in them. Never run it on the
-- live Supabase project once real data matters. To run it, set the confirmation
-- flag in the same session first, e.g. as the first line in the SQL editor:
--     SET aggrey.confirm_reset = 'yes';
-- The flag is cleared on success, so every reset needs its own confirmation.
--
-- The drops also remove migration 001's table grants and policies (the
-- aggrey_readonly role and its schema USAGE survive). Afterwards re-run, in order:
--     schema.sql -> seed.sql -> migrations/001_readonly_role.sql -> verify.sql

BEGIN;

DO $$
BEGIN
    IF current_setting('aggrey.confirm_reset', true) IS DISTINCT FROM 'yes' THEN
        RAISE EXCEPTION 'reset_schema.sql refused: run SET aggrey.confirm_reset = ''yes''; first (this drops all data)';
    END IF;
END;
$$;

DROP TABLE IF EXISTS public.menus CASCADE;
DROP TABLE IF EXISTS public.hours CASCADE;
DROP TABLE IF EXISTS public.holidays CASCADE;
DROP TABLE IF EXISTS public.metadata CASCADE;

DROP FUNCTION IF EXISTS public.aggrey_touch_updated_at() CASCADE;

DROP TYPE IF EXISTS public.meal_type;
DROP TYPE IF EXISTS public.schedule_type;

COMMIT;

RESET aggrey.confirm_reset;
