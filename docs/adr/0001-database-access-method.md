# 0001. Database access method from the backend (N-33)

- **Status:** Accepted — 2026-10-24
- **Deciders:** Database developer and project owner (owner delegated the call)
- **Roadmap:** answers `N-33`; implemented by roadmap M1 step 2

## Context

Aggrey's FastAPI backend (built later, M3) must read the four tables (`menus`,
`hours`, `holidays`, `metadata`) on Supabase. The audited schema enables Row Level
Security on all four tables with **no policies**, so the public `anon` and
`authenticated` roles cannot read anything (verified in M1 step 6).

`N-33` offered two ways for the backend to connect:

- **(a) Supabase client over HTTPS with the service-role key.** Simple, but the
  service-role key bypasses RLS and has full read/write/delete on everything.
- **(b) Direct PostgreSQL connection as a dedicated read-only role.** Least
  privilege; needs a small addition to the schema (a read-only role plus SELECT
  policies), delivered as a reviewed migration.

## Decision

Adopt **option (b)**. The backend connects to PostgreSQL (through the Supabase
connection pooler) as a dedicated role, `aggrey_readonly`, that may only `SELECT`
from the four tables. Created by `db/migrations/001_readonly_role.sql`.

## Rationale

- Aggrey is **read-only at runtime** — it never writes to the database while
  serving students (data arrives via the seed/import process). A full read/write
  master key is more power than the app ever needs.
- **Least privilege** limits the blast radius: if the backend credential leaks, the
  worst case is reading data students already see — nothing can be modified or
  destroyed. This complements the RLS lock (defense in depth).
- Direct SQL fits Aggrey's queries (holiday date-range resolution, food search,
  grouping by station) and the project's "parameterized queries only" guardrail.

## Consequences

- One migration adds the role, `GRANT SELECT` on the four tables, and a
  `FOR SELECT` RLS policy per table (needed because RLS is on with no policies).
- The role's **login password is never committed**. It is set out of band in the
  Supabase dashboard (`ALTER ROLE aggrey_readonly WITH LOGIN PASSWORD '<secret>'`;
  the migration creates the role `NOLOGIN`, so `WITH LOGIN` is required) and stored
  only in a secrets manager / `.env`.
- **To verify during M3** (do not assume): the exact Supabase pooler connection
  string and username format, whether a custom login role connects via the pooler
  (Supavisor), and the backend env-var names from the architecture doc.

## Rejected

Option (a). The service-role key bypasses RLS and grants full write/delete, which is
over-privileged for a read-only service and a larger risk if the key is exposed.
