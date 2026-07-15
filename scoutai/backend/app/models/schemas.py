from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    focus: Literal["general", "market", "competitor", "product"] = "general"
    depth: Literal["quick", "standard", "deep"] = "standard"


class Source(BaseModel):
    title: str
    url: str | None = None
    note: str | None = None


class Finding(BaseModel):
    title: str
    detail: str
    confidence: Literal["low", "medium", "high"] = "medium"
    source_indexes: list[int] = Field(default_factory=list)


class ResearchBrief(BaseModel):
    query: str
    focus: str
    depth: str
    summary: str
    findings: list[Finding]
    risks: list[str]
    next_actions: list[str]
    sources: list[Source]
    mode: Literal["demo", "live"]


class HealthResponse(BaseModel):
    status: str
    service: str
    demo_mode: bool
    model: str
