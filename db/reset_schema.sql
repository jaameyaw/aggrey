-- Reset script: undoes schema.sql so it can be run again on a clean slate.
-- Not part of the audited schema files (schema.sql / seed.sql / verify.sql).
-- Safe to run anytime before real data matters -- drops all four tables.

BEGIN;

DROP TABLE IF EXISTS public.menus CASCADE;
DROP TABLE IF EXISTS public.hours CASCADE;
DROP TABLE IF EXISTS public.holidays CASCADE;
DROP TABLE IF EXISTS public.metadata CASCADE;

DROP FUNCTION IF EXISTS public.aggrey_touch_updated_at() CASCADE;

DROP TYPE IF EXISTS public.meal_type;
DROP TYPE IF EXISTS public.schedule_type;

COMMIT;
