#!/usr/bin/env python3
"""Fail if db/schema.sql drifts from the audited DDL in the schema doc.

The schema lives in two places that MUST stay identical:

  1. db/schema.sql                                  -- the file we run on Postgres
  2. docs/Aggrey_MVP_Database_Schema.md, section 4  -- the audited source of truth

CONTRIBUTING.md forbids editing one without the other. This script extracts the
```sql fenced block under the "4. Complete PostgreSQL DDL" heading and compares it
to db/schema.sql. It prints a diff and exits non-zero on any difference, so CI (and
an optional pre-commit hook) can block the drift.

Run from anywhere:  python3 db/check_schema_sync.py
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

# Paths are resolved relative to this file, so the script works from any CWD.
REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = REPO_ROOT / "db" / "schema.sql"
SCHEMA_DOC = REPO_ROOT / "docs" / "Aggrey_MVP_Database_Schema.md"

# The heading that introduces the authoritative DDL, and the fence markers.
SECTION_HEADING = "4. Complete PostgreSQL DDL"
FENCE_OPEN = "```sql"
FENCE_CLOSE = "```"


def extract_doc_sql(doc_text: str) -> str:
    """Return the SQL inside the first ```sql block after the section-4 heading."""
    lines = doc_text.splitlines()

    # Find the "4. Complete PostgreSQL DDL" heading (ignores the leading '#'s).
    heading_idx = next(
        (i for i, line in enumerate(lines) if line.lstrip("# ").strip() == SECTION_HEADING),
        None,
    )
    if heading_idx is None:
        sys.exit(f"ERROR: heading '{SECTION_HEADING}' not found in {SCHEMA_DOC.name}")

    # Find the opening ```sql fence after the heading.
    open_idx = next(
        (i for i in range(heading_idx + 1, len(lines)) if lines[i].strip() == FENCE_OPEN),
        None,
    )
    if open_idx is None:
        sys.exit(f"ERROR: no '{FENCE_OPEN}' block found after section '{SECTION_HEADING}'")

    # Collect everything up to the closing ``` fence.
    close_idx = next(
        (i for i in range(open_idx + 1, len(lines)) if lines[i].strip() == FENCE_CLOSE),
        None,
    )
    if close_idx is None:
        sys.exit(f"ERROR: unterminated '{FENCE_OPEN}' block after section '{SECTION_HEADING}'")

    return "\n".join(lines[open_idx + 1 : close_idx])


def main() -> int:
    if not SCHEMA_FILE.exists():
        sys.exit(f"ERROR: {SCHEMA_FILE} does not exist")
    if not SCHEMA_DOC.exists():
        sys.exit(f"ERROR: {SCHEMA_DOC} does not exist")

    doc_sql = extract_doc_sql(SCHEMA_DOC.read_text(encoding="utf-8"))
    file_sql = SCHEMA_FILE.read_text(encoding="utf-8")

    # Normalise only surrounding blank lines; any internal difference is real drift.
    if doc_sql.strip("\n") == file_sql.strip("\n"):
        print("OK: db/schema.sql matches the audited DDL in the schema doc (section 4).")
        return 0

    diff = difflib.unified_diff(
        doc_sql.strip("\n").splitlines(),
        file_sql.strip("\n").splitlines(),
        fromfile="docs/Aggrey_MVP_Database_Schema.md (section 4)",
        tofile="db/schema.sql",
        lineterm="",
    )
    print("ERROR: db/schema.sql and the schema doc (section 4) have drifted apart.\n")
    print("\n".join(diff))
    print(
        "\nFix: make db/schema.sql and section 4 of docs/Aggrey_MVP_Database_Schema.md "
        "identical again. Schema changes belong in a new reviewed migration file, "
        "not a silent edit (CONTRIBUTING.md)."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
