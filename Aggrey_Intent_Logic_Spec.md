# Aggrey Intent and Logic Specification

**Status:** Draft for review. Not approved until sign-off is recorded (roadmap N-40).
**Drafted:** October 24, 2026
**Dataset:** `mvp_v1_2`
**Sources:** `Aggrey_MVP_PRD.md`, `Aggrey_MVP_Database_Schema.md`, `Aggrey_Technical_Architecture.md`, `roadmap.md` Section 1 answers, and the dining data.

Aggrey is rule-based. This document is the complete list of what Aggrey understands and how it answers. If a behavior is not written here, Aggrey does not support it. Code, tests, and the phrase corpus must match this document. To change behavior, change this document first, then the corpus, then the code.

### How to read the status tags

Every rule carries one of these tags:

- **Decided** — confirmed by the PRD, the schema doc, or an answered roadmap item. The source is named.
- **Proposed** — a suggestion in this draft. It becomes decided when you sign off (N-40). Change or reject it before signing.
- **Open (N-xx)** — waiting on a roadmap question. Code must not assume an answer.

Example times in this document come from dataset `mvp_v1_2`. Code always reads times, menus, stations, and holidays from the database and never hard-codes them.

---

## Contents

1. [Processing order](#1-processing-order)
2. [Text normalization](#2-text-normalization)
3. [Vocabulary](#3-vocabulary)
4. [Intents](#4-intents)
5. [Intent priority](#5-intent-priority)
6. [Shared logic](#6-shared-logic)
7. [Intent behavior](#7-intent-behavior)
8. [Conversation context](#8-conversation-context)
9. [Food matching](#9-food-matching)
10. [Reply rules](#10-reply-rules)
11. [Open items](#11-open-items)
12. [Phrase corpus](#12-phrase-corpus)
13. [Traceability to the acceptance tests](#13-traceability-to-the-acceptance-tests)

---

## 1. Processing order

**Decided** (schema doc section 15, roadmap M4–M6). Every inbound message goes through these steps in order:

1. Normalize the text (section 2).
2. Check for a pending conversation context for this sender (section 8).
3. Detect the intent using the priority order (section 5).
4. Extract slots: meal, date, station, food keyword (section 3).
5. Resolve the date. No date means today in `America/New_York` (section 6.1).
6. Resolve the schedule: holiday or break override first, then weekend, then weekday (section 6.2).
7. Validate the meal against the schedule (section 6.3).
8. Apply time-of-day rules if the date is today (section 6.4).
9. Query the data through the M5 services.
10. Apply missing-data rules (section 6.7).
11. Format the reply (section 10).

---

## 2. Text normalization

**Proposed.** Before matching, the message is normalized:

1. Lowercase.
2. Replace curly quotes and apostrophes with straight ones, then remove apostrophes ("what's" becomes "whats").
3. Replace `&` with ` and `.
4. Replace every character that is not a letter or digit with a space. Keep `/` only between digits, so dates like `11/25` can be recognized and rejected (section 3.2).
5. Collapse repeated spaces and trim.

Matching works on whole words after normalization, not on substrings. For example, "caf" must not match inside "cafeteria" by accident; both are listed as separate words where needed.

---

## 3. Vocabulary

### 3.1 Meal words

**Proposed.** These words identify a meal. Anything not listed is not a meal word.

| Meal (`meal_type`) | Words and phrases |
| --- | --- |
| `breakfast` | breakfast, bfast |
| `lunch` | lunch |
| `lite_lunch` | lite lunch, light lunch |
| `dinner` | dinner, supper |
| `brunch` | brunch |

Rules:

- "lite lunch" and "light lunch" are matched before "lunch," so "What's for lite lunch?" is never read as lunch.
- "tonight" with no meal word means dinner (section 3.2).
- If a message names two or more different meals ("lunch or dinner?"), Aggrey asks which one. **Proposed.**

### 3.2 Date phrases

| Phrase | Meaning | Status |
| --- | --- | --- |
| *(no date phrase)* | Today in `America/New_York` | **Decided** (N-12) |
| today | Today | **Proposed** (N-13 suggested minimum; PRD names today) |
| tonight | Today. If no meal is named, the meal is dinner. | **Proposed** (N-13) |
| tomorrow, tmrw, tmr, tomorow | Today plus one day | **Proposed** (N-13; PRD names tomorrow) |
| Weekday names (monday, mon, tuesday, tues, ...) | Not yet decided whether this means this week's or next week's day | **Open (N-13)** |
| Explicit dates (11/25, nov 25, november 25th) | Not yet decided | **Open (N-13)** |

**Recognized but unsupported.** If the message contains any of the following, and the phrase is not approved in the table above, Aggrey asks the student to rephrase and lists the supported date words. It never answers for a different date. **Proposed.**

- yesterday, last night
- weekday names (until N-13 approves them)
- month names and abbreviations
- numeric dates (`11/25`, `11-25`)
- "next week," "this week," "this weekend," "weekend"

This matters because "What's for lunch on Friday?" must not be answered with today's lunch.

### 3.3 Station aliases

**Decided** (PRD, roadmap M5): station names come from the menu data for the requested day and meal, never from a hard-coded list.

**Proposed** aliases. Each alias points to a station name in the data. An alias only works if that station exists in the menu for the requested day and meal.

| Station in data | Aliases (normalized) |
| --- | --- |
| Main hot-food | main, main hot food, hot food, main line |
| Special | special, specials, todays special |
| Grill / sandwich | grill, grill sandwich, sandwich, sandwiches, burger, burgers |
| Pasta | pasta |
| Pizza | pizza, pizzas |
| Breakfast | breakfast station *(the single word "breakfast" is always the meal)* |
| Dinner / turntable | turntable |

The full station name, normalized ("grill sandwich," "main hot food"), always works as well.

### 3.4 Filler words

**Proposed.** These words are ignored when extracting a food keyword (section 9.1): the, a, an, any, some, they, there, them, is, are, do, does, have, has, got, get, serving, served, today, tonight, tomorrow, caf, cafe, cafeteria, dining, hall, at, for, on, in, of, to, please, pls, yo, hey, still, now, meal names, and station aliases from section 3.3 when they are used with "station."

### 3.5 Control keywords

| Keyword (whole message, after normalization) | Meaning | Status |
| --- | --- | --- |
| stop, unsubscribe, cancel, end, quit | Opt out | **Open (N-11)** — depends on what Sendblue does with these on your plan |
| help | Help | **Open (N-11)** for carrier rules; **Proposed** behavior in section 7.6 |
| what can you do, how does this work, commands | Help | **Proposed** |
| hi, hello, hey, yo | Greeting | **Proposed:** treated as help |

---

## 4. Intents

**Proposed** final list (resolves roadmap Section 2, item 9). PRD FR-2 names four dining intents. This spec keeps those four and splits "hours lookup" into two cases. It also adds three conversation intents that are not dining questions.

| Intent | What it means | PRD FR-2 category |
| --- | --- | --- |
| `menu` | What food is served for a meal, or at a station | menu lookup |
| `hours` | When a meal starts or ends, or the day's serving times | hours lookup |
| `open_now` | Is anything being served right now | hours lookup |
| `food_lookup` | Is a specific food on the menu | food-item lookup |
| `follow_up` | A short reply to a question Aggrey just asked (station or meal) | part of FR-12 |
| `help` | What Aggrey can do, or a greeting | unsupported/unclear (FR-10) |
| `opt_out` | STOP and similar keywords | not in PRD; N-11 |
| `unclear` | Anything else | unsupported/unclear (FR-10) |

If you approve this list, the PRD's FR-2 should note that `open_now` is part of hours lookup, and that `follow_up`, `help`, and `opt_out` are conversation controls.

### Trigger phrases

**Proposed.** Checked on the normalized text.

| Intent | Triggers |
| --- | --- |
| `open_now` | "open," "closed," "close," "closing," "still going," "serving now," "being served" — with no "what time" or "when" next to a meal word |
| `hours` | "what time," "when," "hours," "until," "start," "starts," "end," "ends," "how late," "how long" |
| `food_lookup` | "do they have," "is there," "are there," "they got," "any," "do yall have," "is \<x\> on the menu," "are they serving \<x\>" — followed by a food keyword |
| `menu` | "whats for," "what is for," "menu," "whats at," "what are they serving," "whats being served," "whats good," a meal word on its own ("lunch?"), a station alias with "station" or "at the" |

---

## 5. Intent priority

**Proposed.** A message can match more than one intent. Aggrey checks these rules in order and uses the first that applies.

| Order | Rule | Example | Result |
| --- | --- | --- | --- |
| 1 | Empty message, or only emoji or punctuation | "??" | `unclear` |
| 2 | Whole message is an opt-out keyword | "STOP" | `opt_out` |
| 3 | Whole message is a help keyword or greeting | "help", "hi" | `help` |
| 4 | A context is pending and the message is a short answer to it (section 8) | "Pizza" after the station question | `follow_up` |
| 5 | Unsupported date phrase present (section 3.2) | "What's for lunch Friday?" | Intent is still detected by rules 6–9, but the reply asks the student to rephrase the date |
| 6 | `open_now` trigger, and no "what time" or "when" next to a meal word | "Is the caf open?", "Is lunch still going?" | `open_now` |
| 7 | `hours` trigger | "What time is brunch?", "When does lunch end?" | `hours` |
| 8 | `food_lookup` trigger with a food keyword left after removing filler words | "Do they have wings today?" | `food_lookup` |
| 9 | `menu` trigger, a meal word, or a station alias | "What's for dinner?", "What's at the grill?" | `menu` |
| 10 | Nothing matched | "asdfgh" | `unclear` |

Notes:

- Rule 6 before rule 7: "Is the caf open?" is `open_now`; "When does the caf close?" also goes to `open_now` because no meal word is named. "When does lunch end?" goes to `hours`.
- Rule 8 before rule 9: "Is there pizza at lunch?" is a food lookup, not a station menu. Both give the same pizzas, so the answer is still correct.
- A food lookup trigger with nothing left after removing filler words ("Do they have anything?") falls through to `menu` if a meal word is present, otherwise `unclear`.

---

## 6. Shared logic

### 6.1 Date

- **Decided** (N-12): no date phrase means today in `America/New_York`, read from `metadata.timezone`. "Today" and "tomorrow" are computed from local time, never from the server's UTC date. Example: Monday 10:00 PM in New York is Tuesday 2:00 AM UTC; "tomorrow" means Tuesday.
- **Decided** (roadmap 3.3): the current time is passed in, never read from the system clock inside the rules, so tests can fix any date and time.

### 6.2 Schedule

**Decided** (schema doc section 8, PRD FR-5):

1. If the date falls inside a `holidays` row (start and end dates inclusive), use that row's `schedule_type` (`holiday` or `break`). If more than one row matches, stop with a data error. Do not pick one.
2. Otherwise Saturday or Sunday is `weekend`.
3. Otherwise `weekday`.

Keep the override's `name`, `verification_status`, and `notes` for the reply.

### 6.3 Meals served per schedule

**Decided** (schema doc section 9):

| Schedule | Meals |
| --- | --- |
| `weekday` | breakfast, lunch, lite_lunch, dinner |
| `weekend`, `holiday`, `break` | brunch, dinner |

**Asked for a meal that is not served that day:**

| Asked for | Schedule | Reply meaning | Status |
| --- | --- | --- | --- |
| lunch | weekend, holiday, break | Lunch isn't served today; brunch and dinner are. Then the brunch menu. | **Decided** (PRD 3; acceptance rows 7, 10) |
| breakfast | weekend, holiday, break | Breakfast isn't served today; brunch and dinner are the meals. No menu. | **Decided** (PRD 3; acceptance rows 8, 14) |
| lite lunch | weekend, holiday, break | Lite Lunch isn't served today; brunch and dinner are the meals. No menu. | **Proposed** |
| brunch | weekday | Brunch is only on weekends, holidays, and breaks; today's meals are breakfast, lunch, Lite Lunch, and dinner. No menu. | **Proposed** |

When the substitute meal (brunch, for a weekend lunch question) is already over, the finished-meal rule in 6.4 applies to the substitute. **Proposed.** Example: Saturday 3:00 PM, "What's for lunch?" gives: Lunch isn't served on weekends. Brunch is over for today. Dinner is served 5:00 to 8:00 PM.

### 6.4 Time of day (only when the date is today)

**Proposed** window boundaries: a meal is being served from its start time up to, but not including, its end time. At exactly 2:00 PM on a weekday, lunch is over and Lite Lunch is being served.

For any meal on today's schedule, the meal is in one of three states:

| State | Test |
| --- | --- |
| Not started | now is before the start time |
| Being served | now is at or after the start time, and before the end time |
| Over | now is at or after the end time |

**The next meal** is the meal being served right now if there is one, otherwise the first meal that starts later today. "Today" uses today's schedule only.

**Finished meal rule — Decided** (N-14, answered 2026-10-24). When the asked-about meal is over today:

| Situation | Reply meaning |
| --- | --- |
| Another meal is being served or starts later today | "\<Meal\> is over. \<Next meal\> is served \<start\> to \<end\>." Time only; no menu for either meal. |
| The next meal is Lite Lunch | Same, plus: Lite Lunch comes after the main lunch, so most lunch food is usually finished. |
| No more meals today | "\<Meal\> is over for today." Nothing about tomorrow. |

Examples on a weekday (Monday 2026-10-26):

| Time | Message | Reply meaning |
| --- | --- | --- |
| 2:30 PM | What's for lunch? | Lunch is over. Lite Lunch is being served until 3:00 PM; most lunch food is usually finished by then. |
| 3:30 PM | What's for lunch? | Lunch is over. Dinner is served 5:00 to 8:00 PM. |
| 8:30 PM | What's for dinner? | Dinner is over for today. |

The finished-meal rule only applies when the date is today. "What's for lunch tomorrow?" always shows tomorrow's lunch.

**Lite Lunch note — Decided** (owner, 2026-10-24): whenever a reply mentions Lite Lunch as being served or coming next, it adds that Lite Lunch comes after the main lunch, so most lunch food is usually finished. This is fixed reply copy, not menu data.

### 6.5 Provisional data

- **Decided** (PRD 3): provisional hours and menus must never be presented as confirmed.
- The holiday brunch menu (`menu_scope = 'holiday_sample'`) is always labeled as a sample menu. **Decided** (PRD 3).
- **Open (N-43):** which `verification_status` values make an override provisional. Suggested: only `pending_confirmation` (currently the Virtual Classes, Reading Day & Exams period, 2026-11-30 to 2026-12-12). Hours on those dates are labeled "not yet confirmed."

### 6.6 Holiday and break menus

- **Brunch — Decided** (PRD FR-6, roadmap Section 2 item 7): query `menu_scope = 'holiday_sample'` only. Never query or copy Saturday (`day_of_week = 6`) rows. The metadata key `holiday_brunch_source = saturday_sample` records where the sample came from and is never used to choose rows.
- **Dinner — Open (N-16):** either (a) show the weekday dinner for that calendar weekday, labeled as unconfirmed, or (b) give dinner hours and say the holiday dinner menu isn't available. Until N-16 is answered, code must support neither.

### 6.7 Missing data

**Decided** (schema doc section 13, PRD FR-9):

| Case | Reply meaning |
| --- | --- |
| Lite Lunch menu (always) | Lite Lunch is served \<start\> to \<end\>, but I don't have a Lite Lunch menu. Plus the Lite Lunch note (6.4). |
| Valid meal, zero menu rows | Menu information isn't available for that meal. Never fall back to another day. |
| Valid meal, zero hours rows | Hours aren't available for that meal. |
| Database can't be reached | I can't get dining info right now. Never a guessed answer. |
| Station named but not in that day's menu | There's no \<station\> station at \<meal\> on \<day\>. Then list the stations that are there. **Proposed** |

---

## 7. Intent behavior

### 7.1 `menu`

**Slots:** meal (optional), date (optional), station (optional).

| Case | Behavior | Status |
| --- | --- | --- |
| No meal named | Ask which meal, listing only that day's meals. Save a pending meal question (section 8). | **Open (N-41)**, suggested behavior shown |
| "tonight" with no meal | Dinner | **Proposed** |
| Meal not served on that schedule | Section 6.3 | Decided / Proposed as marked there |
| Date is today and meal is over | Section 6.4 finished-meal rule | **Decided** (N-14) |
| Lite Lunch | Section 6.7 | **Decided** |
| Weekday lunch, no station named | Ask which station, listing stations from that day's lunch data. Save a pending station question. | **Decided** (PRD FR-12) |
| Weekday lunch, station named | That station's items only. No station question. | **Decided** (PRD FR-12) |
| Weekday lunch, "everything," "all," "full menu" | Every station, grouped by station | **Decided** (PRD FR-12, N-19) |
| Brunch (weekend) | All brunch items grouped by station, with no station question | **Open (N-42)**, suggested behavior shown |
| Brunch (holiday or break) | `holiday_sample` items grouped by station, labeled as a sample menu | **Decided** (6.6) |
| Dinner (holiday or break) | Follows N-16 | **Open (N-16)** |
| Breakfast, dinner (weekday or weekend) | All items for that day and meal | **Decided** (PRD FR-6) |
| Station named for a non-lunch meal ("What's at the grill for brunch?") | That station's items for that meal | **Proposed** |

**Proposed:** menu replies for a meal that is not over include its serving time, for example "Dinner today (Mon), 5:00 to 8:00 PM: ...".

### 7.2 `hours`

**Slots:** meal (optional), date (optional).

| Case | Reply meaning | Status |
| --- | --- | --- |
| Meal named and served that day | "\<Meal\> \<day\>: \<start\> to \<end\>." Add the provisional label if 6.5 applies. | **Decided** (PRD FR-7) |
| Meal named, today, already over | Same, plus "(over for today)" | **Proposed** |
| Lite Lunch on a weekday | Its hours, plus the Lite Lunch note (6.4) | **Decided** (PRD, acceptance row 15; note from owner) |
| Meal named but not served that day | Not served that day, then the day's meals with their times | **Proposed** |
| No meal named ("What are the hours tomorrow?") | Every meal on that day's schedule with its times, in start-time order | **Proposed** |
| Zero hours rows | Hours aren't available | **Decided** (6.7) |

### 7.3 `open_now`

**Slots:** meal (optional), date (optional).

If the message names a date other than today ("Is the caf open tomorrow?"), Aggrey answers as `hours` with no meal: every meal that day with its times. **Proposed.**

For today, using section 6.4:

| Situation | Reply meaning | Status |
| --- | --- | --- |
| A meal is being served | "\<Meal\> is being served until \<end\>." | **Open (N-15)**, suggested wording from the roadmap |
| Lite Lunch is being served | Same, plus the Lite Lunch note | **Decided** (owner note) |
| Between meals | "No meal is being served right now. \<Next meal\> starts at \<start\>." | **Open (N-15)**, suggested wording |
| Before the first meal | "\<First meal\> starts at \<start\>." | **Proposed** |
| After the last meal | "No more meals are being served today." | **Proposed** (matches the N-14 answer for finished meals) |
| Meal named ("Is lunch still open?") | Answer for that meal only: being served until \<end\>, not started yet, or over (then the 6.4 rule) | **Proposed** |

The `hours` table stores serving windows, not building hours (schema doc section 20). Replies talk about meals being served, never about the building being open. **Decided** (roadmap N-15 framing).

### 7.4 `food_lookup`

**Slots:** food keyword (required), meal (optional), date (optional).

| Step | Rule | Status |
| --- | --- | --- |
| 1. Keyword | Remove trigger phrases, date words, meal words, and filler words (3.4). What is left is the keyword. If nothing is left, see section 5 notes. | **Proposed** |
| 2. Scope | Search only meals served on that day's schedule. If a meal is named, search only that meal. Weekday and weekend use `weekly` rows for that weekday. Holiday and break brunch use `holiday_sample`; holiday and break dinner follows N-16. Lite Lunch has no data and is never searched. | **Decided** (schema doc section 12, PRD FR-8) |
| 3. Named meal not served | Say that meal isn't served that day, then search the meals that are | **Proposed** |
| 4. Match | Section 9 | **Decided** that rules live here (N-17); rules themselves **Proposed** |
| 5. Found | List every match as meal, station, and item, grouped by meal then station | **Decided** (PRD FR-8) |
| 6. Found, but that meal is over today | Report the match and say the meal is over for today | **Open (N-44)**, suggested |
| 7. Not found | "I don't see \<keyword\> on the menu for \<day\>." Never "not served" and never "they don't have it." | **Decided** (schema doc section 13) |

Example (Monday): "Do they have onion rings?" gives Onion Rings at lunch, Grill / sandwich. "Do they have wings today?" gives: I don't see wings on today's menu.

### 7.5 `follow_up`

Used only when a context is pending (section 8).

**Pending station question** (after a weekday lunch station prompt):

| Student replies | Behavior | Status |
| --- | --- | --- |
| A station alias or name ("pizza," "grill") | That station's items for the saved date | **Decided** (PRD FR-12) |
| "I don't know," "idk," "not sure," "what are the stations," "options," "which ones" | A one-line explanation of the stations, then the lunch menu grouped by station | **Decided** (N-19, 2026-10-24) |
| "everything," "all," "all of it," "show everything," "full menu," "both" | Every station, grouped by station | **Decided** (PRD FR-12) |
| Anything else | Clear the context and read the message as a new message (section 5) | **Proposed** |

The one-line explanation uses only facts in the data, for example "Lunch has 5 stations today. Here's what each one has:" Station descriptions beyond the data (such as "Main hot-food is a plate with sides") would be new content that you would need to supply. **Proposed.**

**Pending meal question** (only if N-41 is approved): a meal word replies with that meal's menu for the saved date. Anything else clears the context and is read as a new message.

**A station alias with no pending context** ("Pizza" on its own): read as `menu` for that station today, at lunch on a weekday schedule or brunch on other schedules. If the station isn't on that menu, use the 6.7 station rule. **Proposed.**

### 7.6 `help` and greetings

**Proposed.** Reply with one line about what Aggrey does and 2–3 example questions taken from the phrase corpus, for example "What's for dinner?", "Is the caf open?", "Do they have wings today?".

First message from a new number: **Open (N-22).**

### 7.7 `unclear`

**Decided** (PRD FR-10): never guess. Reply asking the student to rephrase, with 2–3 example questions.

Unsupported date phrase (section 3.2): ask the student to rephrase using a supported date word, and list those words. **Proposed.**

### 7.8 `opt_out`

**Open (N-11).** Depends on what Sendblue does with STOP and HELP on your plan. Until answered, Aggrey sends no dining reply to an opt-out keyword.

---

## 8. Conversation context

**Decided** (roadmap M6 step 4, architecture section 7): context is kept in memory per sender, bounded in size, for a single server instance.

| Field | Meaning |
| --- | --- |
| sender | The student's phone number. Kept in memory only; never logged. |
| awaiting | `station` (after a weekday lunch station prompt) or `meal` (after a "which meal" prompt, if N-41 is approved) |
| date | The resolved date the question was about |
| meal | The meal the question was about (lunch for a station prompt) |
| created_at | When the context was saved |

Rules:

- **Open (N-20):** how long a context lasts. Suggested 10 minutes. After that it is ignored.
- A sender has at most one context. A new prompt replaces the old one. **Proposed.**
- The context is cleared after a `follow_up` is answered or when the next message is read as a new message. **Proposed.**
- "Short answer to a pending context" (section 5, rule 4) means the whole message is a station alias, a meal word, or one of the follow-up phrases in 7.5, optionally with "the," "station," "please," or "pls." **Proposed.**

---

## 9. Food matching

**Decided** (N-17): the matching rules and synonym list live in this section, and code must not add any that are not written here. The rules below are **Proposed**.

### 9.1 Steps

1. Normalize the keyword and every food item name the same way (section 2). `&` becomes `and`.
2. Split each into words.
3. Reduce each word to a simple singular form:
   - ends in "ies" (and longer than 4 letters): replace with "y" (fries → fry)
   - ends in "oes," "ses," "xes," "zes," "ches," or "shes": drop "es" (potatoes → potato)
   - ends in "s" but not "ss" (and longer than 3 letters): drop "s" (wings → wing)
4. Apply the synonym list (9.3) to the keyword.
5. A food item matches when **every** keyword word appears among the item's words. Word order doesn't matter, and the item may have extra words.

Whole-word matching avoids false hits from plain substring search, such as "ham" matching "White Hamburger Bun."

### 9.2 Results against the current data

Checked against all 223 menu rows on 2026-10-24.

| Keyword | Matches (any day) | Comment |
| --- | --- | --- |
| wings | none | Acceptance row 17 |
| onion rings | Onion Rings | |
| mac, mac and cheese, mac & cheese | THS Baked Mac & Cheese | |
| hot dogs | All Beef Hot Dog | |
| pancakes | Blueberry Pancakes, Buttermilk Pancake Mix, Maple Pancakes, Pancake | |
| tacos | Taco Bar | |
| potato | Candied Sweet Potato, Mashed Potatoes, Roasted Red / Sweet / Yellow Potatoes | |
| ham | none | Substring search would wrongly match "Hamburger Bun" |
| burgers | Veggie Burger | Not Beef Patty or Turkey Patty; see 9.4 |
| hamburger | White Hamburger Bun | A bun, not a burger; see 9.4 |
| fries | French Fries, **Orange Chicken Stir Fry** | Stir Fry is a false hit; see 9.4 |
| eggs | Scrambled Eggs, Scrambled Eggs with Cheese, **Butter Egg Noodle** | Egg noodle is a borderline hit; see 9.4 |
| greens | Vegetarian Collard Greens, **Steamed Green Beans, Western Green Beans** | Green beans are borderline; see 9.4 |
| hash brown | Hash Brown Patty | Does not match Sunday's "Hashbrowns"; see 9.3 |
| hashbrowns | Hashbrowns | Does not match "Hash Brown Patty"; see 9.3 |

### 9.3 Synonym list

**Proposed** starting list. Each entry rewrites the keyword before matching. Only these entries are supported.

| Student writes | Treated as | Why |
| --- | --- | --- |
| mac n cheese, mac n chz, mac and chz | mac and cheese | Common spellings |
| hashbrown, hashbrowns, hash browns | hash brown **or** hashbrown | The data spells it both ways |
| hotdog, hotdogs | hot dog | Common spelling |

**Open (N-17 follow-up, part of N-40):** who maintains this list after launch. Suggested: you approve additions; developers add them to this section, the phrase corpus, and the tests in the same pull request.

### 9.4 Questions for sign-off

These need your decision when you approve the spec:

1. **"burger" and "hamburger."** Should "burger" also match Beef Patty and Turkey Patty, and should "hamburger" stop matching the bun? Suggested: add "burger" and "hamburger" as synonyms for "beef patty, turkey patty, veggie burger," and exclude items whose last word is "bun."
2. **"fries" matching "Stir Fry."** Suggested: add an exclusion so "fries" matches only items containing "fries" before singular forms are applied.
3. **"eggs" and "greens."** Leave as is (they are real words in those items), or exclude? Suggested: leave as is; the reply names the exact item, so the student can tell.
4. **Wings.** No wings are on the current menu. Suggested: no synonym; "not on the menu" is the honest answer.

---

## 10. Reply rules

| Rule | Status |
| --- | --- |
| Always name the day being described, for example "Today (Mon)" or "Tomorrow (Tue)." On an override date, also name it ("Thanksgiving Holiday, break schedule"). | **Decided** (roadmap M6 step 5) |
| 12-hour times ("5:00 PM"). | **Decided** unless N-18 changes it |
| Provisional data is labeled in plain words ("sample menu," "not yet confirmed"). | **Decided** (PRD 3) |
| Missing food is "not on the menu I have," never "not served." | **Decided** (schema doc section 13) |
| Multi-station replies are grouped by station. If a reply is longer than Sendblue's limit (roadmap M7 step 1), split it between stations, never inside a station. | **Decided** (N-19) |
| Station order: the data has no station-order column, so stations are listed alphabetically, as the schema doc's queries do. This puts "Grill / sandwich" before "Main hot-food." A different order would need a schema change. | **Proposed** (part of N-18) |
| Items within a station follow `display_order`. | **Decided** (schema doc section 10) |
| Emojis, exact wording, and tone. | **Open (N-18)** |
| Message text and phone numbers are never written to logs. | **Decided** (architecture section 8) |

---

## 11. Open items

Items this spec waits on. Each is in roadmap Section 1.

| ID | Topic | Where it applies here |
| --- | --- | --- |
| N-11 | STOP and HELP handling | 3.5, 7.8 |
| N-13 | Supported date phrases | 3.2 |
| N-15 | "Is the caf open?" wording | 7.3 |
| N-16 | Holiday and break dinner | 6.6, 7.1, 7.4 |
| N-18 | Reply wording, emojis, station order | 10 |
| N-20 | How long a pending question lasts | 8 |
| N-22 | First message from a new number | 7.6 |
| N-41 | Menu question with no meal | 7.1, 7.5, 8 |
| N-42 | Station prompt for weekend brunch | 7.1 |
| N-43 | Which data counts as provisional | 6.5 |
| N-44 | Food lookup for a finished meal | 7.4 |
| N-40 | Sign-off on everything marked **Proposed**, including section 9.4 | All |

---

## 12. Phrase corpus

Expected readings for the test suite. Once `backend/` exists, this table becomes `tests/conversation/phrases.yaml`. Rows marked with an open item will change when it is answered. "Today" means no date phrase was given.

| # | Message | Intent | Meal | Date | Station | Food keyword | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | What's for dinner? | menu | dinner | today | | | README example |
| 2 | Is the caf still open? | open_now | | today | | | README example |
| 3 | Do they have wings today? | food_lookup | | today | | wing | README example |
| 4 | What's for lunch tomorrow? | menu | lunch | tomorrow | | | README example |
| 5 | What's for lunch today? | menu | lunch | today | | | PRD example |
| 6 | whats for breakfast | menu | breakfast | today | | | |
| 7 | What's for brunch? | menu | brunch | today | | | |
| 8 | lunch? | menu | lunch | today | | | Meal word alone |
| 9 | What's for supper tonight | menu | dinner | today | | | |
| 10 | What's for tonight? | menu | dinner | today | | | "tonight" implies dinner |
| 11 | What's at the pizza station? | menu | lunch | today | Pizza | | Direct station |
| 12 | What's the special today? | menu | lunch | today | Special | | Acceptance row 6 |
| 13 | What's on the grill for brunch? | menu | brunch | today | Grill / sandwich | | |
| 14 | Show me everything for lunch | menu | lunch | today | all | | |
| 15 | What's for Lite Lunch? | menu | lite_lunch | today | | | Menu unavailable |
| 16 | What's for light lunch | menu | lite_lunch | today | | | Spelling variant |
| 17 | What's on the menu today? | menu | | today | | | N-41 |
| 18 | What time is brunch? | hours | brunch | today | | | |
| 19 | When does lunch end? | hours | lunch | today | | | PRD user story |
| 20 | What time is Lite Lunch? | hours | lite_lunch | today | | | |
| 21 | What time is dinner tomorrow | hours | dinner | tomorrow | | | |
| 22 | What are the hours today? | hours | | today | | | All windows |
| 23 | Is the caf open? | open_now | | today | | | |
| 24 | When does the caf close? | open_now | | today | | | No meal named |
| 25 | Is lunch still going? | open_now | lunch | today | | | |
| 26 | Is the caf open tomorrow? | open_now | | tomorrow | | | Answered as hours |
| 27 | Do they have onion rings? | food_lookup | | today | | onion ring | |
| 28 | Is there a beef patty at lunch? | food_lookup | lunch | today | | beef patty | |
| 29 | do they have mac n cheese | food_lookup | | today | | mac and cheese | Synonym |
| 30 | Is there pizza at lunch? | food_lookup | lunch | today | | pizza | Food lookup wins over station |
| 31 | any chicken tomorrow? | food_lookup | | tomorrow | | chicken | |
| 32 | Pizza *(after station question)* | follow_up | lunch | saved | Pizza | | |
| 33 | I don't know *(after station question)* | follow_up | lunch | saved | all | | Explanation, then all stations |
| 34 | everything *(after station question)* | follow_up | lunch | saved | all | | |
| 35 | grill *(no pending question)* | menu | lunch or brunch | today | Grill / sandwich | | Section 7.5 |
| 36 | What's for lunch Friday? | menu | lunch | unsupported | | | Ask to rephrase until N-13 |
| 37 | What's for dinner 11/25? | menu | dinner | unsupported | | | Ask to rephrase until N-13 |
| 38 | What was for lunch yesterday | menu | lunch | unsupported | | | Ask to rephrase |
| 39 | lunch or dinner? | menu | ask | today | | | Two meals named |
| 40 | asdfgh | unclear | | | | | |
| 41 | hi | help | | | | | Greeting |
| 42 | help | help | | | | | N-11 |
| 43 | STOP | opt_out | | | | | N-11 |

---

## 13. Traceability to the acceptance tests

Every row in `roadmap.md` Section 6 maps to a rule here.

| Acceptance rows | Spec sections |
| --- | --- |
| 1, 33 | 6.1, 7.1 (menu for a valid meal, no date given) |
| 2, 3, 4, 5, 22 | 7.1 weekday lunch, 7.5 follow-ups, 8 context |
| 6 | 3.3 station aliases, 7.1 station named |
| 7, 8, 14 | 6.3 meal not served |
| 9, 13, 15 | 7.2 hours |
| 10, 23, 34 | 6.2 schedule, 6.3, 6.6 holiday brunch |
| 11 | 6.6 dinner (N-16) |
| 12 | 6.5 provisional (N-43) |
| 16 | 6.7 Lite Lunch menu |
| 17, 18, 19 | 7.4, 9 food matching |
| 20, 21 | 6.4 states, 7.3 open now |
| 24, 25 | 7.7 unclear, 3.2 unsupported dates |
| 26 | 6.7 database unreachable |
| 27, 28 | Outside this spec (roadmap M7, webhook handling) |
| 29 | 7.8 opt-out (N-11) |
| 30, 31, 35 | 6.4 finished-meal rule (N-14) |
| 32 | 6.1 local date vs UTC |
