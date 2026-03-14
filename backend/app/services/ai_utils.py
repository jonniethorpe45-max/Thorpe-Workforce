import json
import re
from typing import Any


def extract_json_object(text: str) -> str | None:
    """Extract first JSON object from an arbitrary model response."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    if start < 0:
        return None
    depth = 0
    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : index + 1]
    return None


def parse_json_object(text: str, fallback: dict[str, Any]) -> dict[str, Any]:
    payload = extract_json_object(text)
    if not payload:
        return fallback
    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        return fallback
    return fallback


def clamp_score(value: float | int | str, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, numeric))


def sanitize_list(value: Any, max_items: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
        if len(items) >= max_items:
            break
    return items


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def enforce_word_limit(text: str, max_words: int = 120) -> str:
    words = (text or "").split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip()


def enforce_single_cta(text: str, cta: str) -> str:
    body = text.strip()
    cta_clean = normalize_whitespace(cta)
    if not cta_clean:
        return body
    if cta_clean in body:
        return body
    return f"{body}\n\n{cta_clean}"
