-- Aggrey migration 001: dedicated read-only database role.
-- Roadmap M1 step 2; implements N-33 option (b); see docs/adr/0001-database-access-method.md.
--
-- Baseline is db/schema.sql (not a numbered migration); numbered migrations start here.
-- Run AFTER schema.sql, on the same database. Safe to re-run (idempotent).
--
-- What this does: creates a least-privilege role the backend uses to READ the four
-- tables. schema.sql turns on RLS with no policies, so a plain SELECT grant is not
-- enough on its own -- the role also needs a FOR SELECT policy to see any rows.
-- It is given no INSERT/UPDATE/DELETE grant and no write policy, so it CANNOT modify data.
--
-- SECURITY: this file sets no password (never commit secrets). After running it,
-- enable login and set a password out of band, e.g. in the Supabase SQL editor:
--     ALTER ROLE aggrey_readonly WITH LOGIN PASSWORD '<a-strong-secret>';
-- Store that secret only in a password manager / .env, never in Git.

BEGIN;

-- 1. The role. Created NOLOGIN so it cannot be used until a password is set
--    out of band (above). Guarded so re-running does not error.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'aggrey_readonly') THEN
        CREATE ROLE aggrey_readonly NOLOGIN;
    END IF;
END;
$$;

-- 2. Reach the schema and read the four tables -- nothing that can change data.
GRANT USAGE ON SCHEMA public TO aggrey_readonly;
GRANT SELECT ON
    public.menus,
    public.hours,
    public.holidays,
    public.metadata
    TO aggrey_readonly;

-- 3. RLS is enabled with no policies, so add a read-only policy per table.
--    USING (true) = may read every row. There is deliberately no write policy.
--    DROP-then-CREATE keeps this migration idempotent.
DROP POLICY IF EXISTS aggrey_readonly_select ON public.menus;
CREATE POLICY aggrey_readonly_select ON public.menus
    FOR SELECT TO aggrey_readonly USING (true);

DROP POLICY IF EXISTS aggrey_readonly_select ON public.hours;
CREATE POLICY aggrey_readonly_select ON public.hours
    FOR SELECT TO aggrey_readonly USING (true);

DROP POLICY IF EXISTS aggrey_readonly_select ON public.holidays;
CREATE POLICY aggrey_readonly_select ON public.holidays
    FOR SELECT TO aggrey_readonly USING (true);

DROP POLICY IF EXISTS aggrey_readonly_select ON public.metadata;
CREATE POLICY aggrey_readonly_select ON public.metadata
    FOR SELECT TO aggrey_readonly USING (true);

COMMIT;
