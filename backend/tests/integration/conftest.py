"""Shared fixtures for tests against a real Postgres loaded with db/schema.sql, seed.sql
and migration 001, queried as the read-only `aggrey_readonly` role.

TEST_DATABASE_URL must point at a disposable server as a superuser, for example a
local `postgres:16` container. The fixture creates and drops its own database, and
sets a random login password on the cluster-wide `aggrey_readonly` role, so never
point it at Supabase.
"""

import os
import secrets
import uuid
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo
from pydantic import SecretStr

from aggrey.adapters.postgres import PostgresRepository, create_pool
from aggrey.config import Settings
from tests.conftest import run

ADMIN_URL = os.environ.get("TEST_DATABASE_URL", "")
DB_DIR = Path(__file__).resolve().parents[3] / "db"
SQL_FILES = ("schema.sql", "seed.sql", "migrations/001_readonly_role.sql")

# Each integration test module sets `pytestmark = requires_database`.
requires_database = [
    pytest.mark.integration,
    pytest.mark.skipif(not ADMIN_URL, reason="set TEST_DATABASE_URL to run integration tests"),
]


@pytest.fixture(scope="session")
def readonly_dsn() -> Iterator[str]:
    dbname = f"aggrey_it_{uuid.uuid4().hex[:8]}"
    password = secrets.token_urlsafe(18)
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    try:
        with psycopg.connect(make_conninfo(ADMIN_URL, dbname=dbname), autocommit=True) as conn:
            for name in SQL_FILES:
                conn.execute((DB_DIR / name).read_bytes())
            conn.execute(
                sql.SQL("ALTER ROLE aggrey_readonly WITH LOGIN PASSWORD {}").format(
                    sql.Literal(password)
                )
            )
        yield make_conninfo(ADMIN_URL, dbname=dbname, user="aggrey_readonly", password=password)
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(dbname))
            )


def with_repository[T](
    dsn: str, action: Callable[[PostgresRepository], Awaitable[T]], *, timeout_s: float = 10
) -> T:
    async def go() -> T:
        settings = Settings(database_url=SecretStr(dsn), db_connect_timeout_s=timeout_s)
        pool = create_pool(settings)
        await pool.open(wait=False)
        try:
            repository = PostgresRepository(
                pool, statement_timeout_ms=settings.db_statement_timeout_ms
            )
            return await action(repository)
        finally:
            await pool.close()

    return run(go())
