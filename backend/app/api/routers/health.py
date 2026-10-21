from fastapi import APIRouter

from app import __version__
from app.schemas.health import HealthOut

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthOut, summary="Liveness probe")
async def health() -> HealthOut:
    return HealthOut(status="ok", version=__version__)
