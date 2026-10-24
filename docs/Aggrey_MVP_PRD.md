# Aggrey MVP Product Requirements Document

**Build-ready PRD for initial implementation**  


## 1. Product Summary

Aggrey is a text-based campus dining assistant for Livingstone College students. A student sends a text message to Aggrey, and Aggrey returns factual dining information from stored menu, dining-hours, and holiday data.

The MVP is intentionally narrow. It should prove that students can ask common dining questions by text and receive a correct, useful response without downloading an app or creating an account.

### Problem statement

Dining information can require students to check separate sources or walk to the cafeteria without knowing what is being served or whether the cafeteria is open. Aggrey should make that information available through a simple text conversation.

### Primary user

Livingstone College students who want fast answers about the cafeteria menu, meal times, and whether a meal is being served.

### Core experience

**Text -> Ask -> Get an answer -> Decide whether to go**

## 2. MVP Scope

The MVP must support the following:

- Receive a student-initiated text message through Sendblue.
- Return a text response through Sendblue.
- Answer menu questions for breakfast, lunch, dinner, and brunch.
- Answer cafeteria-hours questions, including Lite Lunch hours even though its food menu is unavailable.
- Answer whether a specific food item appears in the stored menu for the requested day and applicable meal, searching across stations when needed.
- Understand basic date references needed for the MVP, including today, tomorrow, and explicit dates that the parser supports.
- Detect weekends.
- Check official school holiday dates stored in the database.
- Apply the correct meal schedule for normal weekdays, weekends, and explicitly listed holidays or academic breaks.
- For general weekday lunch questions, ask which of the five active stations the student wants; handle station follow-ups and explicit requests for all stations.
- Provide a simple, mobile-friendly landing page with a visible Aggrey number and a click-to-text link.
- Read factual answers only from stored dining data.
- Return a clear fallback when the question cannot be understood or the required data is missing.

### Non-goals for the MVP

- No staff/admin dashboard.
- No AI or large-language-model dependency.
- No automatic menu scraping or OCR.
- No proactive announcements, campaigns, or unsolicited outbound messages.
- No student accounts or login.
- No sold-out, substitution, or temporary-closure workflow unless manually represented in the MVP data.
- No inferred special-event schedules beyond the holiday and academic-break periods explicitly loaded in the MVP dataset.

## 3. Business Rules

| Day type | Meals served | Rule |
|---|---|---|
| Normal weekday | Breakfast, Lunch, Lite Lunch hours, Dinner | Monday-Friday unless a dated override applies. Lite Lunch food menu is unavailable. |
| Weekend | Brunch, Dinner | Saturday and Sunday unless a dated override applies. |
| Official holiday | Brunch, Dinner | Uses the `holiday` schedule unless its record specifies `break`. |
| Academic break / dated override | Brunch, Dinner | Uses the stored `break` or `holiday` schedule, taking priority over weekday/weekend rules. |

### Meal-request behavior

- If a student asks for lunch on a weekend or holiday, Aggrey must not return a regular lunch menu. It should explain that lunch is not served and provide brunch information when available.
- If a student asks for breakfast on a weekend or holiday, Aggrey should explain that breakfast is not served and indicate that brunch and dinner are the available meal periods.
- If a requested meal is valid, Aggrey should return **all** stored items for that day and meal, grouped by station where appropriate. The weekly menu repeats without service dates.
- For a generic weekday lunch question, ask which station: Main hot-food, Special, Grill / sandwich, Pasta, or Pizza. If the student does not know, give a one-line explanation of the stations followed by the lunch menu grouped by station; if they request everything, show the complete lunch menu grouped by station.
- A direct station question should be answered without requiring the station question again. Short follow-ups such as "Pizza" should use the pending lunch context.
- On holidays and breaks, use the reusable `holiday_sample` brunch and dinner menus. The holiday dinner sample is a copy of Saturday dinner (N-16). Both samples are **provisional**: label them as sample menus and never state them as confirmed holiday menus.
- If a schedule is provisional (for example, virtual classes/exams), do not imply its serving hours are confirmed.
- Holiday and academic-break date ranges must be checked before applying normal weekday or weekend schedules.
- Aggrey must never invent menu items, hours, dates, or holiday status.

### Example

Student: **"What's for lunch today?"**

If today is an official holiday, Aggrey should respond with the meaning of:

> "There is no regular lunch today because the cafeteria is following the holiday schedule. Brunch and dinner are being served. Here is today's brunch menu: ..."

## 4. Functional Requirements

| ID | Requirement | Expected behavior |
|---|---|---|
| FR-1 | Inbound messaging | The system receives student-initiated messages from Sendblue through a FastAPI webhook. |
| FR-2 | Intent detection | The backend classifies a message into one supported intent: menu lookup, hours lookup, food-item lookup, or unsupported/unclear. |
| FR-3 | Meal detection | The backend identifies breakfast, lunch, Lite Lunch, dinner, or brunch when stated or safely inferred. |
| FR-4 | Date resolution | The backend resolves supported date expressions into a calendar date before querying dining data. |
| FR-5 | Schedule selection | The backend checks stored holiday/break date ranges first, then weekend/weekday, and applies the matching stored serving hours. |
| FR-6 | Menu lookup | The backend retrieves **all** rows for the applicable recurring weekday and meal, or the reusable holiday brunch or dinner sample. |
| FR-7 | Hours lookup | The backend returns stored start/end times for the relevant meal or cafeteria schedule. |
| FR-8 | Food-item lookup | The backend searches food names across applicable meals and stations, reporting the matching meal/station without guessing. |
| FR-9 | Missing data | If required dining data is unavailable, the system says the information is unavailable instead of guessing. |
| FR-10 | Unclear request | If the request cannot be safely interpreted, the system asks the student to rephrase or provides examples of supported questions. |
| FR-11 | Reply | The final response is sent back to the same student through Sendblue. |
| FR-12 | Lunch stations and follow-ups | Generic weekday lunch questions ask for a station; direct station requests, "I don't know", "show everything", and follow-up station selections work. |
| FR-13 | Landing page | A lightweight page shows Aggrey, sample questions, the number, and a functional click-to-text link. |

## 5. Supported User Stories

- As a student, I want to text "What's for dinner?" so I can decide whether to go to the cafeteria.
- As a student, I want to ask what is being served for lunch today, choose a station, or request the full lunch menu.
- As a student, I want to ask whether the cafeteria is open so I do not walk there when it is closed.
- As a student, I want to ask when lunch ends so I know whether I still have time to go.
- As a student, I want to ask whether a specific food item is being served today.
- As a student, I want Aggrey to recognize that weekends and listed school holidays/breaks use brunch and dinner instead of the normal weekday schedule.
- As a student, I want to open Aggrey’s website and tap its number to start a text conversation.

## 6. Data Requirements

For the MVP, dining data is loaded from the structured menu and hours tables already available to the project. Automatic collection is outside the MVP.

- Menu data identifies: `menu_scope`, `day_of_week` (ISO 1-7, blank for holiday sample), `meal_type`, `station`, `food_item`, and `display_order`. Regular menus repeat weekly; they do **not** store a `service_date`.
- Dining-hours data must identify at least: applicable day/schedule, meal type, start time, and end time.
- Holiday data identifies `name`, inclusive `start_date` and `end_date`, `schedule_type`, and `verification_status`. This includes explicitly listed academic breaks.
- Meal-type values should be normalized to: breakfast, lunch, lite_lunch, dinner, brunch.
- Dates and times should be stored in consistent database formats. Resolve requests in the `America/New_York` timezone.
- The MVP workbook has four sheets: `menus`, `hours`, `holidays`, and `metadata`; its data must match the PostgreSQL schema. The `holiday_sample` dinner rows (`holiday_dinner_source = saturday_sample`) are a provisional copy of Saturday dinner, not verified holiday food data.

### Source-of-truth rule

PostgreSQL is the runtime source of truth for answers. If the needed record is not present in the database, Aggrey should report that the information is unavailable. The system should not reconstruct missing facts from assumptions.

## 7. Technical Constraints

| Area | MVP decision |
|---|---|
| Messaging | Sendblue. Students initiate conversations; Aggrey only replies to incoming requests in the MVP. |
| Backend | FastAPI + Python. |
| Database | Supabase PostgreSQL. |
| Hosting | Render for the FastAPI service; Vercel for the landing page. |
| Frontend | Next.js + TypeScript, one simple landing page (no dashboard). |
| Source control | GitHub. |
| Interpretation | Simple rule-based parsing. No AI/LLM dependency. |
| Data ingestion | Manual/controlled import of existing structured menu, hours, and holiday data. |

### System flow

**Student -> Sendblue -> FastAPI -> Supabase PostgreSQL -> FastAPI -> Sendblue -> Student**

## 8. Acceptance Criteria

The MVP is build-complete when all of the following are true:

- A test student can send a text to the Aggrey number and receive a response.
- A message such as "What's for dinner?" returns **every** stored dinner item for the resolved weekday or the clearly labeled provisional holiday dinner sample on holidays and breaks.
- Hours questions return the correct stored meal start/end times.
- Food-item questions are checked against stored menu data rather than guessed.
- Saturday and Sunday requests use brunch + dinner rules.
- A listed holiday or break that falls Monday-Friday still uses brunch + dinner rules and its correct override hours.
- Lunch or breakfast requests on weekends/holidays do not return weekday meal data.
- Generic weekday lunch questions prompt for a station; named station requests work directly; "show everything" returns all five stations; follow-up replies retain the selected lunch context.
- Weekend and holiday brunch use the correct corresponding menu scope, and the holiday brunch sample is not mistaken for an ordinary weekday menu.
- Lite Lunch hours are available but missing Lite Lunch food data produces an explicit unavailable-data response.
- Provisional virtual-class hours and the holiday brunch and dinner samples are not presented as confirmed source facts.
- The landing page displays the number and its click-to-text link works on supported devices.
- Missing menu/hours data produces an explicit unavailable-data response.
- Unsupported or unclear messages do not cause fabricated answers.
- Automated tests cover normal weekdays, weekends, holidays, missing data, and unclear requests.

## 9. Success Metrics

These are recommended MVP targets. They can be adjusted after the first controlled pilot.

| Metric | Recommended MVP target |
|---|---|
| Answer accuracy | At least 95% of supported test questions return the correct answer from the stored data. |
| Rule accuracy | 100% of weekend/holiday test cases apply the correct meal schedule. |
| Availability | Service is reliably reachable during the controlled pilot; track failed webhook requests and failed replies. |
| Usage | Track number of student questions, unique testers, and most common intents during the pilot. |

## 10. Open Decisions Before Coding

Do not guess these values in implementation. Confirm them from the project data or configuration.

1. Which date phrases beyond today/tomorrow should be supported in the first MVP. Do not assume unsupported phrases are implemented.
2. Sendblue test-account/webhook configuration, credentials, and any plan limitations affecting the pilot.
3. Aggrey's actual texting number for the landing page. Use configuration until available.

## 11. Implementation Guardrails

- Treat this PRD as the product behavior specification. Do not add features from the future-development list.
- Keep messaging-provider code separate from dining/business logic so Sendblue can be replaced later without rewriting the core rules.
- Keep database access separate from message parsing and response formatting.
- Represent schedule rules in code that can be unit tested independently of Sendblue.
- Use deterministic rule-based parsing for the MVP. Do not call an LLM.
- Use database data for facts. Never hard-code menu items or invent missing information; clearly label the provisional holiday menus and any unconfirmed hours.
- Prefer simple, readable implementation over premature abstraction.
- Add tests before expanding supported phrasing. A phrase should be supported only when its expected behavior is clear.
