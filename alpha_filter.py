"""Module B — Alpha Filter (LLM logic).

Sends raw ingest items to Groq's free Llama 3.3 70B endpoint with a strict
analyst prompt. Uses JSON-mode (response_format) so the output is always
parseable. Endpoint is OpenAI-compatible, called directly with httpx to
avoid extra deps.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are an intelligence analyst scanning the edge of the internet for "
    "high-value tech/business signals. From the items provided, identify ONLY "
    "those that represent one of: (a) a new business niche, (b) a legal or "
    "technical loophole, or (c) a tool that provides a significant first-mover "
    "advantage. Rank each surviving item by Perishability on a 1-10 scale, "
    "where 10 means the opportunity window closes within days and 1 means it "
    "endures for months or years. Also assign an Alpha-Score 1-10 reflecting "
    "overall signal strength. Be strict: reject items that are merely "
    "interesting, broadly known, or pure academic curiosity. If no item "
    "qualifies, return an empty list.\n\n"
    "Return JSON with EXACTLY this shape (no extra keys, no commentary):\n"
    '{"alpha_items": [\n'
    '  {"title": str, "url": str, "source": str,\n'
    '   "category": "new_niche" | "loophole" | "first_mover_tool",\n'
    '   "alpha_score": int 1-10, "perishability": int 1-10,\n'
    '   "summary": str, "why_alpha": str}\n'
    "]}"
)


def _format_catalog(items: list[dict[str, Any]]) -> str:
    lines = []
    for i, x in enumerate(items):
        desc = (x.get("description") or "")[:500].replace("\n", " ")
        lines.append(
            f"[{i}] source={x.get('source')} | title={x.get('title', '')}\n"
            f"    url={x.get('url', '')}\n"
            f"    desc={desc}"
        )
    return "\n\n".join(lines)


def filter_alpha(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Send raw items through the LLM analyst. Returns the alpha-list (possibly empty)."""
    if not items:
        return []

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment / .env")

    user_msg = (
        "Analyze the following items and return the filtered alpha list as JSON.\n\n"
        + _format_catalog(items)
    )

    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "max_tokens": 8000,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    }

    r = httpx.post(
        GROQ_URL,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    data = json.loads(text)
    return data.get("alpha_items", [])
