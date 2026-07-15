from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse, ResearchBrief, ResearchRequest
from app.services.research import run_research

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="scoutai-api",
        demo_mode=settings.demo_mode,
        model=settings.openai_model,
    )


@router.post("/research", response_model=ResearchBrief)
async def research(body: ResearchRequest) -> ResearchBrief:
    return await run_research(body)
