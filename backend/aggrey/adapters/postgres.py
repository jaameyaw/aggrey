"""PostgreSQL implementation of the dining repository (N-33 option b, ADR 0001).

Connects as the read-only `aggrey_readonly` role, normally through the Supabase
connection pooler. Every query is parameterized.
"""

import logging
from datetime import date
from typing import Any

import psycopg
from psycopg import AsyncConnection
from psycopg.rows import TupleRow
from psycopg_pool import AsyncConnectionPool

from aggrey.adapters.repository import RepositoryError
from aggrey.config import Settings
from aggrey.domain.models import (
    HolidayPeriod,
    MealType,
    MenuItem,
    MenuScope,
    ScheduleType,
    ServiceHours,
)

logger = logging.getLogger(__name__)

Pool = AsyncConnectionPool[AsyncConnection[TupleRow]]


def create_pool(settings: Settings) -> Pool:
    """Build a closed pool. The caller opens it at startup and closes it at shutdown."""
    return AsyncConnectionPool(
        conninfo=settings.database_url.get_secret_value(),
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        # Seconds to wait for a free connection before raising PoolTimeout.
        timeout=settings.db_connect_timeout_s,
        kwargs={
            # libpq accepts whole seconds only.
            "connect_timeout": max(1, round(settings.db_connect_timeout_s)),
            # The Supabase transaction pooler does not support prepared statements.
            "prepare_threshold": None,
        },
        open=False,
        name="aggrey",
    )


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _menu_item(row: TupleRow) -> MenuItem:
    scope, day_of_week, meal, station, food_item, display_order = row
    return MenuItem(
        menu_scope=MenuScope(scope),
        day_of_week=day_of_week,
        meal_type=MealType(meal),
        station=station,
        food_item=food_item,
        display_order=display_order,
    )


class PostgresRepository:
    def __init__(self, pool: Pool, *, statement_timeout_ms: int) -> None:
        self._pool = pool
        self._statement_timeout = str(statement_timeout_ms)

    async def _fetch(self, query: str, params: tuple[Any, ...]) -> list[TupleRow]:
        try:
            async with self._pool.connection() as conn:
                # Transaction-local, so it also holds behind the transaction pooler.
                await conn.execute(
                    "SELECT set_config('statement_timeout', %s, true)", (self._statement_timeout,)
                )
                cursor = await conn.execute(query, params)
                return await cursor.fetchall()
        except psycopg.Error as exc:
            # PoolTimeout is a psycopg.Error too. Log the class only: messages can
            # carry connection details.
            logger.error(
                "database query failed",
                extra={"error_category": "database", "error_type": type(exc).__name__},
            )
            raise RepositoryError("dining data is unavailable") from exc

    async def find_overrides(self, day: date) -> list[HolidayPeriod]:
        rows = await self._fetch(
            "SELECT name, start_date, end_date, schedule_type, verification_status, notes"
            " FROM public.holidays"
            " WHERE %s BETWEEN start_date AND end_date"
            " ORDER BY start_date, name",
            (day,),
        )
        return [
            HolidayPeriod(
                name=name,
                start_date=start_date,
                end_date=end_date,
                schedule_type=ScheduleType(schedule),
                verification_status=status,
                notes=notes,
            )
            for name, start_date, end_date, schedule, status, notes in rows
        ]

    async def get_hours(self, schedule: ScheduleType, meal: MealType) -> ServiceHours | None:
        rows = await self._fetch(
            "SELECT start_time, end_time FROM public.hours"
            " WHERE schedule_type = %s AND meal_type = %s",
            (schedule.value, meal.value),
        )
        if not rows:
            return None
        start_time, end_time = rows[0]
        return ServiceHours(
            schedule_type=schedule, meal_type=meal, start_time=start_time, end_time=end_time
        )

    async def get_menu(
        self,
        scope: MenuScope,
        weekday: int | None,
        meal: MealType,
        station: str | None = None,
    ) -> list[MenuItem]:
        rows = await self._fetch(
            "SELECT menu_scope, day_of_week, meal_type, station, food_item, display_order"
            " FROM public.menus"
            " WHERE menu_scope = %s AND day_of_week IS NOT DISTINCT FROM %s AND meal_type = %s"
            " AND (%s::text IS NULL OR lower(btrim(station)) = lower(btrim(%s::text)))"
            " ORDER BY station, display_order",
            (scope.value, weekday, meal.value, station, station),
        )
        return [_menu_item(row) for row in rows]

    async def search_food(
        self,
        term: str,
        scope: MenuScope,
        weekday: int | None,
        meal: MealType | None = None,
    ) -> list[MenuItem]:
        meal_value = meal.value if meal is not None else None
        rows = await self._fetch(
            "SELECT menu_scope, day_of_week, meal_type, station, food_item, display_order"
            " FROM public.menus"
            " WHERE menu_scope = %s AND day_of_week IS NOT DISTINCT FROM %s"
            " AND (%s::text IS NULL OR meal_type::text = %s::text)"
            " AND food_item ILIKE %s ESCAPE '\\'"
            " ORDER BY meal_type, station, display_order",
            (scope.value, weekday, meal_value, meal_value, f"%{_escape_like(term.strip())}%"),
        )
        return [_menu_item(row) for row in rows]

    async def get_metadata(self, key: str) -> str | None:
        rows = await self._fetch('SELECT value FROM public.metadata WHERE "key" = %s', (key,))
        if not rows:
            return None
        value: str = rows[0][0]
        return value
