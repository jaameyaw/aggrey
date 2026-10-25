"""FastAPI application factory.

Run with `uv run uvicorn aggrey.app:create_app --factory` (see backend/README.md).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI
from psycopg_pool import PoolTimeout

from aggrey import __version__
from aggrey.adapters.postgres import PostgresRepository, create_pool
from aggrey.adapters.repository import DiningRepository, RepositoryError
from aggrey.api import health, webhooks
from aggrey.config import Settings, load_settings
from aggrey.logging import RequestContextMiddleware, configure_logging

logger = logging.getLogger(__name__)


class StartupError(RuntimeError):
    """The service cannot start safely. The message says what to fix."""


async def load_timezone(repository: DiningRepository) -> ZoneInfo:
    """Read `metadata.timezone` and fail clearly if it is missing or invalid."""
    try:
        value = await repository.get_metadata("timezone")
    except RepositoryError as exc:
        raise StartupError("Could not read metadata.timezone from the database.") from exc
    if value is None or not value.strip():
        raise StartupError(
            "metadata.timezone is missing. Seed the metadata table (db/seed.sql) before starting."
        )
    try:
        return ZoneInfo(value.strip())
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise StartupError(
            f"metadata.timezone {value!r} is not a valid IANA timezone name."
        ) from exc


def create_app(
    settings: Settings | None = None, repository: DiningRepository | None = None
) -> FastAPI:
    """Build the app. Tests pass `repository` to skip the real database."""
    settings = settings if settings is not None else load_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            repo = repository
            if repo is None:
                pool = create_pool(settings)
                try:
                    await pool.open(wait=True, timeout=settings.db_connect_timeout_s)
                except PoolTimeout as exc:
                    await pool.close()
                    raise StartupError(
                        "Could not connect to the database within "
                        f"{settings.db_connect_timeout_s:g}s. Check DATABASE_URL."
                    ) from exc
                stack.push_async_callback(pool.close)
                repo = PostgresRepository(
                    pool, statement_timeout_ms=settings.db_statement_timeout_ms
                )
            app.state.repository = repo
            app.state.timezone = await load_timezone(repo)
            logger.info(
                "startup complete", extra={"version": __version__, "app_env": settings.app_env}
            )
            yield

    app = FastAPI(
        title="Aggrey",
        version=__version__,
        lifespan=lifespan,
        # No public API docs for a provider-only service.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)
    app.include_router(webhooks.router)
    return app
