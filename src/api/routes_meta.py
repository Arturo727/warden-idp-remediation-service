from fastapi import APIRouter

from src.domain.scenario_registry import PREDEFINED_SCENARIOS

router = APIRouter(tags=["Meta"])


@router.get("/preconfigured-scenarios", summary="List preconfigured scenarios")
def list_preconfigured_scenarios() -> list[dict]:
    return PREDEFINED_SCENARIOS
