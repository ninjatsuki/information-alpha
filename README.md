# Information Alpha

A modular intelligence pipeline that scans the edges of the internet for high-value
tech and business signals, filters them with an LLM, and delivers the survivors as
formatted notes ready for an Obsidian vault.

Comes with a CLI runner and a small local web UI styled like iOS.

## What it does

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   A. INGEST     │ →  │   B. FILTER     │ →  │   C. SINK       │
│                 │    │                 │    │                 │
│  GitHub repos   │    │  LLM analyst    │    │  Markdown +     │
│  Hacker News    │    │  scores each    │    │  YAML front-    │
│  arXiv cs.AI    │    │  signal 1-10    │    │  matter →       │
│  (httpx+async)  │    │  for alpha &    │    │  Obsidian inbox │
│                 │    │  perishability  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

The filter keeps only items that look like:
- a **new business niche**,
- a **technical / legal loophole**, or
- a **tool with first-mover advantage**.

Each survivor is ranked by **Alpha-Score** and **Perishability** (how fast the
window closes).

## Stack

- **Python 3.10+** — `asyncio`, `httpx`, type hints
- **Groq API** — free Llama 3.3 70B inference for the filter step
- **Flask** — local web UI
- Vanilla **HTML / CSS / JS** for the iOS-style frontend (no React, no build step)

## Quick start

```powershell
git clone https://github.com/<you>/information-alpha.git
cd information-alpha
pip install -r requirements.txt

# Set up keys
copy .env.example .env
# Edit .env and fill in GROQ_API_KEY (get free key at https://console.groq.com/keys)
```

Run the CLI:

```powershell
python main.py
```

Or launch the web UI:

```powershell
python app.py
# open http://127.0.0.1:5000
```

## Project layout

```
information_alpha/
├── ingestion.py        Module A — async fetchers for GitHub / HN / arXiv
├── alpha_filter.py     Module B — LLM filter (Groq Llama 3.3 70B)
├── obsidian_sink.py    Module C — writes Markdown with YAML frontmatter
├── main.py             CLI orchestrator
├── app.py              Flask UI server
├── templates/
│   └── index.html      iOS-style single-page UI
├── static/
│   └── style.css       Light/dark, system fonts, rounded cards
└── 00_Intelligence_Inbox/   (generated — gitignored)
```

## Environment variables

| Variable        | Required | Purpose                                              |
|-----------------|----------|------------------------------------------------------|
| `GROQ_API_KEY`  | yes      | Free key from https://console.groq.com/keys          |
| `GITHUB_TOKEN`  | no       | Personal Access Token to raise GitHub's rate limit   |

## Notes

- Designed to run **locally**. Don't deploy publicly — your API key lives in `.env`.
- The GitHub source uses the Search API filtered by keywords and recency; it
  approximates "trending" without scraping.
- The LLM is intentionally strict, so on a slow news day the brief may legitimately
  contain zero items.

## License

MIT — see [LICENSE](LICENSE).
