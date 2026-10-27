"""Tests for db/generate_seed.py validation, rendering, and mirror parsing.

These use tiny in-memory datasets (the "small broken sample workbooks" of roadmap
M2 step 7) and do not need openpyxl or the real workbook.
"""

import generate_seed as g

# --- builders for minimal valid rows ---------------------------------------


def menu(**kw):
    row = dict(menu_scope="weekly", day_of_week=1, meal_type="breakfast",
               station="Breakfast", food_item="Eggs", display_order=1)
    row.update(kw)
    return row


def hour(**kw):
    row = dict(schedule_type="weekday", meal_type="breakfast",
               start_time="07:30", end_time="09:30")
    row.update(kw)
    return row


def holiday(**kw):
    row = dict(name="Labor Day", start_date="2026-09-07", end_date="2026-09-07",
               schedule_type="holiday", verification_status="calendar_date", notes="x")
    row.update(kw)
    return row


def meta(**kw):
    row = dict(key="timezone", value="America/New_York", notes=None)
    row.update(kw)
    return row


def valid_sets():
    """A small but fully valid dataset plus matching expected counts."""
    menus = [menu(food_item="Eggs", display_order=1),
             menu(food_item="Bacon", display_order=2)]
    hours = [hour()]
    holidays = [holiday()]
    metadata = [meta(key="dataset_version", value=g.DATASET_VERSION, notes="v")]
    counts = {"menus": 2, "hours": 1, "holidays": 1, "metadata": 1}
    return menus, hours, holidays, metadata, counts


def run(menus, hours, holidays, metadata, counts):
    return g.validate(menus, hours, holidays, metadata, expected_counts=counts)


# --- the clean baseline ------------------------------------------------------


def test_valid_sample_has_no_errors():
    assert run(*valid_sets()) == []


# --- menus -------------------------------------------------------------------


def test_bad_meal_type():
    m, h, hol, md, c = valid_sets()
    m[0]["meal_type"] = "brunchh"
    assert any("meal_type 'brunchh'" in e for e in run(m, h, hol, md, c))


def test_holiday_sample_must_have_blank_day():
    m, h, hol, md, c = valid_sets()
    m[0] = menu(menu_scope="holiday_sample", day_of_week=1, meal_type="brunch")
    assert any("blank day_of_week" in e for e in run(m, h, hol, md, c))


def test_holiday_sample_meal_must_be_brunch_or_dinner():
    m, h, hol, md, c = valid_sets()
    m[0] = menu(menu_scope="holiday_sample", day_of_week=None, meal_type="lunch")
    assert any("brunch or dinner" in e for e in run(m, h, hol, md, c))


def test_weekday_meal_must_be_valid():
    m, h, hol, md, c = valid_sets()
    m[0] = menu(day_of_week=1, meal_type="brunch")  # brunch not served on a weekday
    assert any("must be breakfast/lunch/dinner" in e for e in run(m, h, hol, md, c))


def test_blank_station():
    m, h, hol, md, c = valid_sets()
    m[0]["station"] = "   "
    assert any("station is blank" in e for e in run(m, h, hol, md, c))


def test_nonpositive_display_order():
    m, h, hol, md, c = valid_sets()
    m[0]["display_order"] = 0
    assert any("positive integer" in e for e in run(m, h, hol, md, c))


def test_duplicate_menu_item():
    m, h, hol, md, c = valid_sets()
    m[1] = menu(food_item="Eggs", display_order=2)  # same day/meal/station/item as m[0]
    assert any("duplicate" in e for e in run(m, h, hol, md, c))


# --- hours -------------------------------------------------------------------


def test_hours_end_before_start():
    m, h, hol, md, c = valid_sets()
    h[0]["end_time"] = "07:00"
    assert any("not after start_time" in e for e in run(m, h, hol, md, c))


def test_hours_invalid_schedule_meal():
    m, h, hol, md, c = valid_sets()
    h[0] = hour(schedule_type="weekday", meal_type="brunch")  # brunch not a weekday meal
    assert any("weekday meal_type must be" in e for e in run(m, h, hol, md, c))


# --- holidays ----------------------------------------------------------------


def test_overlapping_holidays():
    m, h, hol, md, c = valid_sets()
    hol.append(holiday(name="Also Labor Day", start_date="2026-09-07", end_date="2026-09-08"))
    c["holidays"] = 2
    assert any("overlaps" in e for e in run(m, h, hol, md, c))


def test_holiday_end_before_start():
    m, h, hol, md, c = valid_sets()
    hol[0]["end_date"] = "2026-09-06"
    assert any("before start_date" in e for e in run(m, h, hol, md, c))


def test_bad_holiday_schedule_type():
    m, h, hol, md, c = valid_sets()
    hol[0]["schedule_type"] = "weekday"  # holidays may only be holiday/break
    assert any("must be holiday or break" in e for e in run(m, h, hol, md, c))


# --- metadata and counts -----------------------------------------------------


def test_duplicate_metadata_key():
    m, h, hol, md, c = valid_sets()
    md.append(meta(key="dataset_version", value=g.DATASET_VERSION))
    c["metadata"] = 2
    assert any("duplicate key" in e for e in run(m, h, hol, md, c))


def test_dataset_version_mismatch():
    m, h, hol, md, c = valid_sets()
    md[0]["value"] = "mvp_v9_9"
    assert any("expects" in e and g.DATASET_VERSION in e for e in run(m, h, hol, md, c))


def test_row_count_mismatch():
    m, h, hol, md, c = valid_sets()
    m.append(menu(food_item="Extra", display_order=3))  # 3 menus, counts say 2
    assert any("menus: 3 rows; expected 2" in e for e in run(m, h, hol, md, c))


# --- rendering and quoting ---------------------------------------------------


def test_quote_escapes_single_quotes_and_handles_null():
    assert g.q("O'Brien") == "'O''Brien'"
    assert g.q(None) == "NULL"
    assert g.num_or_null(None) == "NULL"
    assert g.num_or_null(5) == "5"


def test_render_structure():
    menus, hours, holidays, metadata, _ = valid_sets()
    sql = g.render(menus, hours, holidays, metadata)
    assert sql.startswith("-- Aggrey MVP seed data.")
    assert "\n\nBEGIN;\n\n" in sql
    assert "INSERT INTO public.menus" in sql
    assert sql.endswith("COMMIT;\n")
    # NULL day_of_week renders unquoted for a holiday_sample row.
    hs = g.render([menu(menu_scope="holiday_sample", day_of_week=None, meal_type="brunch")],
                  hours, holidays, metadata)
    assert "('holiday_sample', NULL, 'brunch'," in hs


# --- markdown mirror parsing -------------------------------------------------


def test_parse_mirror_reads_only_known_tables():
    md = (
        "# Title\n\n"
        "## Hours\n\n"
        "| schedule_type | meal_type | start_time | end_time |\n"
        "| --- | --- | --- | --- |\n"
        "| weekday | breakfast | 07:30 | 09:30 |\n\n"
        "## Something Else\n\n"
        "| a | b |\n| --- | --- |\n| ignore | me |\n"
    )
    tables = g.parse_mirror(md)
    assert tables["hours"] == [("weekday", "breakfast", "07:30", "09:30")]
    assert tables["menus"] == []  # section not present -> empty, not an error
