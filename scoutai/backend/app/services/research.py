from __future__ import annotations

import json
import re

import httpx

from app.config import settings
from app.models.schemas import Finding, ResearchBrief, ResearchRequest, Source


DEMO_BRIEFS: dict[str, ResearchBrief] = {
    "default": ResearchBrief(
        query="",
        focus="general",
        depth="standard",
        summary=(
            "ScoutAI demo brief: this is a structured intelligence summary you would "
            "receive after a live research pass. Connect an OpenAI-compatible API key "
            "to generate real briefs for any topic."
        ),
        findings=[
            Finding(
                title="Clear problem framing beats broad searches",
                detail=(
                    "Teams that start with a precise scout question (who / what / why now) "
                    "get sharper briefs and fewer unscoped tangents."
                ),
                confidence="high",
                source_indexes=[0],
            ),
            Finding(
                title="Source-linked claims improve trust",
                detail=(
                    "Decision-makers adopt AI research faster when every material claim "
                    "is tied to a source and confidence label."
                ),
                confidence="medium",
                source_indexes=[1],
            ),
            Finding(
                title="Follow-up loops compound value",
                detail=(
                    "A second scout pass that targets gaps from the first brief usually "
                    "outperforms one oversized dump of raw notes."
                ),
                confidence="medium",
                source_indexes=[0, 1],
            ),
        ],
        risks=[
            "Demo mode does not fetch live web or market data.",
            "Sample findings are illustrative and should not drive decisions.",
        ],
        next_actions=[
            "Set OPENAI_API_KEY to enable live synthesis.",
            "Re-run the same query with focus set to market or competitor.",
            "Save strong briefs into your team wiki or CRM notes.",
        ],
        sources=[
            Source(title="ScoutAI product brief (internal)", url=None, note="Demo corpus"),
            Source(
                title="Research workflow patterns",
                url="https://github.com/jonniethorpe45-max",
                note="Portfolio context",
            ),
        ],
        mode="demo",
    ),
}


def _demo_brief(req: ResearchRequest) -> ResearchBrief:
    brief = DEMO_BRIEFS["default"].model_copy(deep=True)
    brief.query = req.query
    brief.focus = req.focus
    brief.depth = req.depth
    brief.summary = (
        f"Demo scout on “{req.query}” ({req.focus} / {req.depth}). "
        + brief.summary
    )
    return brief


def _system_prompt(req: ResearchRequest) -> str:
    return (
        "You are ScoutAI, an elite research scout. "
        "Return ONLY valid JSON matching this schema:\n"
        "{"
        '"summary": string, '
        '"findings": [{"title": string, "detail": string, "confidence": "low"|"medium"|"high"}], '
        '"risks": [string], '
        '"next_actions": [string], '
        '"sources": [{"title": string, "url": string|null, "note": string|null}]'
        "}\n"
        f"Focus area: {req.focus}. Depth: {req.depth}. "
        "Be concrete, skeptical, and practical. Prefer actionable structure over filler."
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def _live_brief(req: ResearchRequest) -> ResearchBrief:
    payload = {
        "model": settings.openai_model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": _system_prompt(req)},
            {"role": "user", "content": req.query},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    parsed = _extract_json(content)

    findings = [
        Finding(
            title=item.get("title", "Finding"),
            detail=item.get("detail", ""),
            confidence=item.get("confidence", "medium"),
            source_indexes=[],
        )
        for item in parsed.get("findings", [])
    ]
    sources = [
        Source(
            title=item.get("title", "Source"),
            url=item.get("url"),
            note=item.get("note"),
        )
        for item in parsed.get("sources", [])
    ]

    return ResearchBrief(
        query=req.query,
        focus=req.focus,
        depth=req.depth,
        summary=parsed.get("summary", ""),
        findings=findings,
        risks=list(parsed.get("risks", [])),
        next_actions=list(parsed.get("next_actions", [])),
        sources=sources,
        mode="live",
    )


async def run_research(req: ResearchRequest) -> ResearchBrief:
    if settings.demo_mode:
        return _demo_brief(req)
    try:
        return await _live_brief(req)
    except Exception:
        # Graceful fallback so the product remains usable offline / without quota.
        brief = _demo_brief(req)
        brief.risks = [
            "Live research failed; returned demo brief instead.",
            *brief.risks,
        ]
        return brief
