"""Entry point — orchestrate Ingest -> Filter -> Format -> Save to Vault."""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from alpha_filter import filter_alpha
from ingestion import ingest_all
from obsidian_sink import write_brief


def main() -> None:
    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")

    print("[1/3] Ingesting raw signals...")
    items = asyncio.run(ingest_all(github_token=github_token))
    print(f"      collected {len(items)} raw items")

    print("[2/3] Filtering through alpha analyst...")
    alpha = filter_alpha(items)
    print(f"      surfaced {len(alpha)} alpha signals")

    print("[3/3] Writing Obsidian brief...")
    path = write_brief(alpha)
    print(f"      wrote {path}")


if __name__ == "__main__":
    main()
