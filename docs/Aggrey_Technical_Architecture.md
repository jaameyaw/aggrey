# Aggrey MVP Technical Architecture

**Status:** Build-ready architecture for the initial pilot  
**Updated:** October 24, 2026  
**Audience:** Developers, Codex, and Claude Code

## 1. Purpose and scope

Aggrey is a text-based campus dining assistant for Livingstone College. Students find the Aggrey number on a simple website, send a message, and receive factual cafeteria information drawn from the database.

The MVP supports recurring weekly menus, five weekday lunch stations, food searches, serving hours, and dated holiday/break overrides. It uses deterministic rules, **not an LLM**.

This document describes **how to build the approved PRD**. It does not introduce new product features. For product behavior, use `Aggrey_MVP_PRD.md`; for executable data definitions, use the audited `db/schema.sql`.

## 2. System overview

```text
Website visitor -> Next.js (Vercel) -> "Text Aggrey" sms: link
                                           |
                                           v
                                     Phone Messages
                                           |
                                           v
                                      Sendblue
                                           | inbound webhook
                                           v
                                    FastAPI (Render)
                                       |       |
                         dining queries|       | send reply
                                       v       v
                               Supabase DB   Sendblue
                         menus / hours /      |
                         holidays / metadata  v
                                        Student's phone
```

Within FastAPI: validate webhook -> interpret request -> resolve date/schedule -> query database -> format reply.

**Architecture style:** one small FastAPI application, one PostgreSQL database, one landing page, one messaging provider. No microservices, queue, Redis, authentication system, or admin dashboard in the initial build.

## 3. Components and responsibilities

| Component | Technology | Responsibility |
| --- | --- | --- |
| Landing page | Next.js + TypeScript on Vercel | Explain Aggrey, show sample questions and the actual number, and open Messages via a tested `sms:` link. No database access. |
| Messaging adapter | Sendblue | Receive student-initiated messages and deliver Aggrey replies. |
| API | Python + FastAPI on Render | Validate inbound requests, interpret messages, manage limited context, call dining services, and send replies. |
| Dining services | Plain Python modules within FastAPI | Resolve date/schedule, validate meals, retrieve all matching menu items, and format answers. |
| Database | Supabase PostgreSQL | Runtime source of truth for menus, service hours, holidays/breaks, and metadata. |

### API boundary

- `POST /webhooks/sendblue`: provider-only inbound message endpoint. Accept only supported inbound-message events after authentication and validation.
- `GET /health`: minimal health endpoint used by hosting checks. Do not expose credentials or private data.
- Do **not** create public CRUD APIs or a browser-facing Supabase client for the MVP. Add endpoints only when a demonstrated use case requires them.

## 4. Message-processing flow

1. Sendblue delivers a student message over HTTPS.
2. FastAPI checks the configured Sendblue webhook secret, validates the payload, and ignores irrelevant events.
3. The adapter obtains the sender identity, message text, and provider message identifier. Duplicate deliveries are handled as described in Section 7.
4. A rule-based interpreter detects intent, optional meal, station, food keyword, and date reference. It uses short-lived context for follow-ups such as **"Pizza"** after **"What's for lunch?"**.
5. The date resolver uses `America/New_York`. Calendar-date references select a menu **weekday**, not a dated menu record.
6. The schedule service checks inclusive `holidays.start_date`–`end_date` ranges first. Otherwise it selects weekend or weekday hours.
7. The menu/hours service queries PostgreSQL for **all** matching rows, applies the approved missing-data rules, and returns structured results.
8. The response formatter produces a short, readable text reply. Sendblue delivers it to the same student.

**Keep provider payload handling separate from business logic.** Tests should exercise date resolution, menu retrieval, and response generation without calling Sendblue.

## 5. Database design and source of truth

The existing audited schema defines **exactly four dining-data tables**. Do not redesign these tables during initial implementation.

| Table | Core fields | Usage |
| --- | --- | --- |
| `menus` | `menu_scope`, `day_of_week`, `meal_type`, `station`, `food_item`, `display_order` | One row per food item. Weekly menus repeat by ISO weekday (1 = Monday, 7 = Sunday); `holiday_sample` brunch and dinner have a null weekday. |
| `hours` | `schedule_type`, `meal_type`, `start_time`, `end_time` | Serving windows for `weekday`, `weekend`, `holiday`, and `break`. |
| `holidays` | `name`, `start_date`, `end_date`, `schedule_type`, `verification_status`, `notes` | Explicit dated overrides, including academic breaks. Dates are inclusive. |
| `metadata` | `key`, `value`, `notes` | Dataset version, timezone, and documented MVP assumptions. |

The schema uses UUID primary keys, PostgreSQL enums, constraints, indexes, update timestamps, and enabled row-level security (RLS).

**Data ownership:** `Aggrey_MVP_Data.xlsx` is the canonical *import source*; the PostgreSQL tables are the *runtime source of truth*. `Aggrey_MVP_Data.md` is only a readable mirror. Use the audited SQL migration and seed files, not the older generated SQL package.

- Initial verification targets: **227** menu rows, **10** hours rows, **11** holiday/break rows, and **11** metadata rows.
- A repeated weekly item has **no `service_date`**. Query all rows matching `menu_scope`, ISO weekday, meal, and optional station, ordered by station and `display_order`.
- Imports must be validated, transactional, and safe to repeat without duplicating records. Future changes remain manual for the MVP.

## 6. Dining and conversation rules

### Schedule selection

```text
requested date -> matching holidays record?
   yes -> use the record's schedule_type (holiday or break)
   no  -> Saturday/Sunday? weekend : weekday
```

| Schedule | Meal periods | Serving hours |
| --- | --- | --- |
| Weekday | Breakfast, Lunch, Lite Lunch, Dinner | 7:30–9:30 AM; 11 AM–2 PM; 2–3 PM; 5–8 PM |
| Weekend | Brunch, Dinner | 10:30 AM–1:30 PM; 5–8 PM |
| Holiday | Brunch, Dinner | 10:30 AM–1:30 PM; 5–8 PM |
| Break | Brunch, Dinner | 10–11 AM; 4–6 PM |

Fall Break, Thanksgiving, and Christmas are stored as **break** overrides. The virtual-classes/exams period also uses the break template but is **provisional**. Do not present those hours as confirmed. Summer operations have no dated override in the current dataset.

### Menu selection

- **Normal weekdays:** breakfast/lunch/dinner use `menu_scope = weekly` and the requested ISO weekday.
- **Regular weekends:** Saturday/Sunday brunch and dinner use their respective weekly menu rows.
- **Holidays and breaks:** brunch and dinner use the provisional `holiday_sample` menus. The holiday dinner sample is a copy of Saturday dinner (N-16); a verified holiday dinner menu is **not** available. Label both as sample menus; do not present them as confirmed holiday meals.
- **Lite Lunch:** hours exist; a separate food list does not. Answer time questions, but say the food menu is unavailable.
- **Food availability:** return actual menu matches and their stations. When there is no match, say **"not listed on the stored menu"**, not that the cafeteria definitely does not serve it.

### Lunch-station interaction

For a generic weekday **"What's for lunch?"**, ask which station: Main hot-food, Special, Grill / sandwich, Pasta, or Pizza. A direct station question returns all foods at that station without prompting again. **"Show everything"** returns all five station menus. **"I don't know"** explains the choices. Every food row belonging to a selected station must be returned, not just the first.

## 7. Conversation state and duplicate deliveries

The MVP needs only limited context: sender, pending meal/date, and whether a lunch station choice is awaited. Keep this context keyed by sender and expire it after a short inactivity period.

For **local development and a controlled single-instance pilot**, bounded in-memory state may be used for this context and recent processed Sendblue message identifiers. Sendblue documents possible duplicate webhook deliveries and message identifiers for deduplication.

**Important limitation:** in-memory state is lost on restart and is not shared between instances. It cannot guarantee durable duplicate suppression or follow-up continuity. Run a single backend instance for the initial pilot, test retries, and do not claim exactly-once delivery. Before scaling to multiple instances or a broader launch, agree on durable state/idempotency storage as a deliberate scope change.

## 8. Security and reliability

- **Webhook authentication:** configure a Sendblue webhook secret and verify the documented `sb-signing-secret` header using constant-time comparison. Accept HTTPS requests only. Reject malformed/oversized requests and unrelated events.
- **Backend-only secrets:** store Sendblue API credentials and Supabase privileged credentials in Render environment variables. Never commit them or expose them through Next.js.
- **Database access:** use the FastAPI server as the only data-access path. The audited schema has RLS enabled with no public access policies. A Supabase secret/service-role credential bypasses RLS, so protect it carefully and do not use it in the browser.
- **Error handling:** use bounded outbound API/database timeouts and handle provider failures without inventing responses. Avoid blindly retrying successful sends, which can produce duplicate messages.
- **Privacy:** log request IDs, intent, durations, and error categories, but not message contents, full phone numbers, or credentials unless strictly necessary for debugging under controlled access.
- **Health and monitoring:** check service uptime, webhook failures, database-query failures, and message-send errors. Keep operational monitoring minimal for the pilot.

## 9. Repository and deployment

Suggested simple structure:

```text
backend/             FastAPI routes, Sendblue adapter, dining services, tests
frontend/            Next.js landing page
db/                  audited schema.sql, seed.sql, verify.sql
data/                Aggrey_MVP_Data.xlsx and readable mirror
docs/                PRD, architecture, schema reference, roadmap
README.md            setup instructions and product summary
```


**Deployment:** Next.js on Vercel, FastAPI on Render, PostgreSQL on Supabase. Configure the Sendblue receive webhook with the deployed HTTPS URL. The landing page's only public configuration value is Aggrey's actual phone number. The `sms:` link should be tested on iPhone and Android, with the number visible for desktop users.

Example environment variable names (application configuration, not provider API field names):

| Runtime | Values |
| --- | --- |
| Backend (private) | `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SENDBLUE_API_KEY_ID`, `SENDBLUE_API_SECRET_KEY`, `SENDBLUE_WEBHOOK_SECRET` |
| Web (public) | `NEXT_PUBLIC_AGGREY_PHONE_NUMBER` |
| App setting | `America/New_York` from the database metadata; fail clearly if missing/invalid |

## 10. Verification and release criteria

Automated tests should cover the following before the student pilot:

- Monday breakfast returns **all nine items**, and Monday Pizza returns **all four** items.
- All five weekday lunch stations are retrievable; general lunch → station → follow-up works.
- Weekends use weekend brunch/dinner; Fall Break, Thanksgiving, and Christmas use the dated **break** override.
- Virtual-period responses disclose that the hours are provisional.
- Food search checks applicable meals/stations and does not claim unlisted items are definitely unavailable.
- Lite Lunch hours work while Lite Lunch food-menu queries return a missing-data response.
- Duplicate inbound events, malformed webhooks, database failures, and Sendblue failures are handled safely.
- `db/verify.sql` passes on the **actual Supabase project**, not only through static checks.
- A real test demonstrates: **landing page → Messages → Sendblue → FastAPI → Supabase → Sendblue reply**.

**Build order:** audited database → validated import → schedule/menu services → rule-based conversation → Sendblue → landing page → automated/live tests → controlled pilot. See `roadmap.md` for module checklists.

## 11. Decisions that remain open

1. Sendblue credentials, the assigned Aggrey number, and actual webhook/account configuration.
2. Optional date phrases beyond today's/tomorrow's requests and explicitly supported dates.
3. Manager confirmation of the virtual-period serving hours and actual holiday dinner menu.
4. Durable conversation/deduplication storage if Aggrey moves beyond a single-instance pilot.

Do not fill these gaps with assumptions in code or student-facing responses.

### Technical references

- [Sendblue webhook documentation](https://docs.sendblue.com/getting-started/webhooks/)
- [Supabase RLS and backend key guidance](https://supabase.com/docs/guides/database/postgres/row-level-security)
