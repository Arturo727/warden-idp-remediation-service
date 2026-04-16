from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Get service health",
    description="Returns the current health status of the Warden service.",
)
def health() -> dict:
    return {"status": "ok"}
