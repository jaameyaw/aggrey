from fastapi import APIRouter
from pydantic import BaseModel

from aggrey import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health")
async def health() -> HealthResponse:
    """Liveness only: no database call, no secrets, no data."""
    return HealthResponse(status="ok", version=__version__)
