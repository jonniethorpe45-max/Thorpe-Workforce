from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.research import router as research_router

app = FastAPI(
    title="ScoutAI API",
    description="AI research and scouting assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "scoutai", "docs": "/docs"}
