"""A tiny endpoint used to check that the backend is alive."""

from fastapi import APIRouter

from ..config import MODE, RELEASE_VERSION

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a JSON object describing the current service state."""
    return {
        "status": "ok",
        "service": "AgriGuide",
        "mode": MODE,
        "version": RELEASE_VERSION,
    }
