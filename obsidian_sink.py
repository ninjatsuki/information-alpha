"""Module C — Obsidian delivery sink.

Takes the filtered alpha list and writes one Markdown file per run into
00_Intelligence_Inbox/ with Obsidian-compatible YAML frontmatter.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

INBOX = Path("00_Intelligence_Inbox")


def _slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[-\s]+", "-", s)[:80] or "untitled"


def _render_item(it: dict[str, Any]) -> str:
    return (
        f"## {it.get('title', '(untitled)')}\n\n"
        f"- **Source:** {it.get('source', '')}\n"
        f"- **URL:** {it.get('url', '')}\n"
        f"- **Category:** {it.get('category', '')}\n"
        f"- **Alpha-Score:** {it.get('alpha_score', '')}/10\n"
        f"- **Perishability:** {it.get('perishability', '')}/10\n\n"
        f"**Summary:** {it.get('summary', '')}\n\n"
        f"**Why Alpha:** {it.get('why_alpha', '')}\n"
    )


def write_brief(items: list[dict[str, Any]], out_dir: Path = INBOX) -> Path:
    """Write a single daily brief file. Returns the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    path = out_dir / f"{date_str}-alpha-brief.md"

    if items:
        items_sorted = sorted(
            items,
            key=lambda x: (x.get("alpha_score", 0), x.get("perishability", 0)),
            reverse=True,
        )
        avg_score = round(
            sum(i.get("alpha_score", 0) for i in items_sorted) / len(items_sorted), 1
        )
        cat_counts: dict[str, int] = {}
        for i in items_sorted:
            c = i.get("category", "unknown")
            cat_counts[c] = cat_counts.get(c, 0) + 1
        top_cat = max(cat_counts, key=cat_counts.get)
        body = "\n---\n\n".join(_render_item(it) for it in items_sorted)
    else:
        avg_score = 0
        top_cat = "none"
        body = "_No alpha signals identified in this scan._\n"

    frontmatter = (
        "---\n"
        f'date: {now.strftime("%Y-%m-%d %H:%M:%S")}\n'
        "source: information-alpha-pipeline\n"
        f"alpha-score: {avg_score}\n"
        f"category: {top_cat}\n"
        f"item-count: {len(items)}\n"
        "tags: [alpha, intelligence, daily-brief]\n"
        "---\n\n"
        f"# Alpha Brief — {date_str}\n\n"
    )
    path.write_text(frontmatter + body, encoding="utf-8")
    return path
