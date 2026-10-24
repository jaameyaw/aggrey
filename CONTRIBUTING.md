# Contributing to Aggrey

Aggrey is built by two developers. The plan, open questions, and module order live in [`docs/roadmap.md`](docs/roadmap.md). Read its Section 3 (engineering standards) before your first pull request.

## Who owns what

| Area | Owner | Branch |
| --- | --- | --- |
| Database and Supabase: roadmap M1 (schema on Supabase) and M2 (data import) | Database developer | `database/supabase` |
| Everything else, plus final say on product decisions (roadmap Section 1) | Project owner | Short-lived branches, see below |

Either person can work in the other's area, but the owner of that area reviews the pull request.

## Branches

- `main` is always releasable. Nobody pushes to it directly; every change arrives through a pull request.
- Name branches by roadmap module and topic, for example `m3/backend-skeleton` or `m4/schedule-resolver`. The long-running exception is `database/supabase`.
- Keep branches short-lived. Merge `main` into your branch (or rebase) often so conflicts stay small.
- For `database/supabase`, open a pull request per finished step (for example "M1: verify.sql") instead of one large pull request at the end.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new behavior
- `fix:` bug fix
- `test:` tests only
- `docs:` documentation only
- `chore:` tooling, config, moves

Keep each commit focused. Reference roadmap IDs where useful, for example `feat: add schedule resolver (M4.2)`.

## Pull requests

1. Keep each pull request small and focused on one roadmap step.
2. Fill in the pull request template, including the roadmap IDs it implements or is blocked on.
3. CI must pass.
4. **One approval from the other developer is required before merging** (roadmap N-39).
5. Update the docs in the same pull request: README, ADRs in `docs/adr/`, and the roadmap when a step or Section 1 item is finished.

## Rules that are easy to break

- **Do not invent values.** If a value, credential, behavior, or data fact is not in the docs or answered in roadmap Section 1, stop and add the question there.
- **Never commit secrets.** Supabase keys, Sendblue keys, and database passwords go in `.env` (ignored by Git) or the hosting dashboards. Never paste them in issues, pull requests, or chat.
- **Do not edit `db/schema.sql` silently.** It must match `docs/Aggrey_MVP_Database_Schema.md` section 4. Schema changes go in a new, reviewed migration file with an ADR (roadmap M1 step 2).
- **The workbook is the source of truth for data.** Change `data/Aggrey_MVP_Data.xlsx`, then regenerate `db/seed.sql`. Do not hand-edit seed rows.
- **Behavior comes from the spec.** Conversation behavior must match `docs/Aggrey_Intent_Logic_Spec.md`. Change the spec first, then the code.

## Local setup

See the "Development" section of the [README](README.md).
