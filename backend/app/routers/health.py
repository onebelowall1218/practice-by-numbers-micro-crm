from fastapi import APIRouter

from app.clock import is_demo_clock, today
from app.schemas import HealthOut
from app.services.ai.factory import get_providers

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    judgment, generation = get_providers()
    return HealthOut(
        status="ok",
        as_of=today(),
        demo_clock=is_demo_clock(),
        judgment_provider=judgment.name,
        generation_provider=generation.name,
        model=getattr(generation, "model", None),
    )
