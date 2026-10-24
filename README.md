# Aggrey

Students should not have to walk across campus just to find out the cafeteria is closed, lunch is over, or the food they wanted is not being served. Or download an app/ search through tons of websites to know what's at the caf

Campus dining information is often scattered across menus, schedules, websites, and last-minute updates. Even when the information exists, students still have to find it, interpret it, and hope it is current.

**Aggrey brings that information directly into the conversation students already use every day: Messages.**

Students can text naturally:

**“What’s for dinner?”**  
**“Is the caf still open?”**  
**“Do they have wings today?”**  
**“What’s for lunch tomorrow?”**

They do not need to download an app, search through a dashboard, or phrase their question in a specific way.

**Just text Aggrey and get a response within seconds.**

Aggrey interprets what the student means, checks the current dining information, and responds with a short, factual answer.

The first version of Aggrey is being built for Livingstone College. It will use the school’s menu, dining hours, and holiday schedule to help students quickly understand what is being served and when.

Aggrey also understands changes in the dining schedule. On weekends and school holidays, when the cafeteria serves brunch and dinner instead of breakfast, lunch, and dinner, Aggrey can recognize that change and guide students to the correct meal information.

Over time, Aggrey can become a direct communication layer between campus dining services and students, helping dining information stay accurate even when menus, hours, or availability change.

**Aggrey makes one everyday question easier to answer: Should I go to the caf?**

---

## Repository layout

```text
backend/   FastAPI service (Python 3.13, uv): domain rules, adapters, tests
db/        schema.sql, seed.sql (and later verify.sql and the seed generator)
data/      Aggrey_MVP_Data.xlsx (source of truth) and its Markdown mirror
docs/      PRD, architecture, database schema, intent and logic spec, roadmap
```

The landing page (`web/`) is added in roadmap module M8.

Start with [`docs/roadmap.md`](docs/roadmap.md) for the build plan and open questions, and [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch, commit, and review rules.

## Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.13 for you if needed)
- Git

### Set up

```bash
cd backend
uv sync
uv run pre-commit install
```

`pre-commit install` runs the checks below automatically before each commit.

### Check and test

Run from `backend/`:

| Task | Command |
| --- | --- |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` (CI runs `--check`) |
| Type check | `uv run mypy` |
| Test | `uv run pytest` |
| Every pre-commit check on all files | `uv run pre-commit run --all-files` |

CI runs the same checks on every pull request and on `main`.
