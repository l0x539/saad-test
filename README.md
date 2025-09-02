# Twitch OSINT Mini-Platform — Take-Home Test (Python)

> **Goal:** Evaluate your practical skills in Python, streaming I/O, bot development, structured scraping/logging, and light NLP.  
> **Timebox:** Aim for 6–10 hours. Prioritize correctness, structure, and explainability over “completeness.”  
> **Database:** **Not required.** You may use files (JSON/JSONL). A DB (SQLite/Postgres) is optional for bonus points.

---

## ✨ What You’ll Build

A **Python** service that:

1. Ingests a list of **subjects** (emails, usernames, phone numbers).  
2. Runs a **Twitch chat monitor** for specific channels (live via IRC **or** offline via fixtures).  
3. Writes **structured, searchable logs** and builds **profiles**:
   - **By channel:** who chatted, what/when, aggregated signals.
   - **By user:** messages across channels, top keywords, signals.
4. (**Bonus**) Simple **NLP/AI heuristics** to infer soft facts (e.g., “is the streamer dating X?”), with evidence snippets.

---

## ✅ Deliverables

- A working CLI with subcommands (see **CLI** below).
- Structured outputs on disk (JSON/JSONL) with consistent schemas.
- Light enrichment “providers” for subjects (mocked APIs are fine).
- A minimal test suite (unit tests) for critical pieces (parsers/rollups/providers).
- Clear **README** instructions (how to run, design choices, limitations).

---

## 🧰 Tech & Constraints

- **Python** 3.10+
- You may use common libraries (e.g., `twitchio`, `click`/`typer`, `pydantic`, `python-dotenv`, `uvloop`, `aiofiles`).  
- **No secrets in repo.** Use env vars or `.env` (document expected vars).
- **Resilience:** Don’t crash on parse/network errors. Log and continue.
- **Idempotency:** Avoid duplicate writes; stabilize on a `message_id` or hash.
- **Normalization:** lowercase usernames; ISO8601 timestamps; E.164 phones.
- **Ethics/ToS:** Use official APIs or provided offline fixtures. Public chats only.

---

## 🧪 CLI

Implement a CLI with subcommands, for example using `Typer` or `Click`:

```bash
# Load subjects
python -m app.cli subjects load --path subjects.csv

# Run chat monitor for channels (live)
export TWITCH_OAUTH_TOKEN="oauth:xxxxxxxx"
export TWITCH_NICK="yourbotname"
python -m app.cli chat run --channels mychannel,otherchannel --duration-seconds 600

# Run chat monitor (offline replay mode using fixtures)
python -m app.cli chat run --channels example_channel --duration-seconds 15 --offline

# Search collected messages
python -m app.cli search messages --by user --value someuser --contains dating --limit 20
python -m app.cli search messages --by channel --value example_channel --since 2025-09-02T12:00:00Z
```

**Subcommands to implement:**

- `subjects load --path subjects.csv`  
  CSV columns: `type,value` where `type ∈ {email,username,phone}`.  
  Normalize and write to `data/subjects.json`.

- `chat run --channels <c1,c2,...> --duration-seconds N [--offline]`  
  - **Live:** connect to Twitch IRC (e.g., via `twitchio`) using:
    - `TWITCH_OAUTH_TOKEN`, `TWITCH_NICK`, (optionally `TWITCH_CLIENT_ID`)
  - **Offline:** replay from `fixtures/chat/<channel>.jsonl` at realistic pace (throttle).
  - Parse each message, extract fields (mentions/urls/emotes), append to `data/logs/messages.jsonl`, update profiles.

- `search messages --by [user|channel] --value X [--since ISO] [--until ISO] [--contains TEXT] [--limit N]`  
  Read `messages.jsonl`, filter, and pretty-print JSON results.

---

## 📁 Output Structure (files on disk)

```
data/
  subjects.json
  logs/
    messages.jsonl            # append-only, one JSON per line
  profiles/
    users/
      <user_name>.json
    channels/
      <channel>.json
  enrichment/
    <subject_key>.json
```

**`messages.jsonl` record example:**
```json
{
  "ts": "2025-09-02T12:34:56Z",
  "channel": "example_channel",
  "message_id": "abc123",
  "user_id": "u_789",
  "user_name": "someuser",
  "text": "hey @mod is he still dating sara?",
  "mentions": ["mod", "sara"],
  "urls": [],
  "emotes": [],
  "source": "twitch-irc"
}
```

**`profiles/users/<user>.json` example:**
```json
{
  "user_name": "someuser",
  "channels_participated": ["example_channel","devchat"],
  "message_count": 42,
  "top_keywords": ["dating","sara","music"],
  "last_seen": "2025-09-02T12:34:56Z",
  "facts": {
    "asked_about_streamer_relationship": true,
    "suspected_relationship_targets": ["sara"],
    "evidence": [
      {"ts":"2025-09-02T12:34:56Z","channel":"example_channel","snippet":"still dating sara"}
    ]
  }
}
```

**`profiles/channels/<channel>.json` example:**
```json
{
  "channel": "example_channel",
  "unique_users": 128,
  "message_count": 512,
  "top_users": ["someuser","mod123"],
  "top_keywords": ["giveaway","dating","tour"],
  "last_seen": "2025-09-02T12:40:02Z",
  "streamer_signals": {
    "relationship_mentions": [
      {"target": "sara", "evidence_count": 3, "examples": ["still dating sara","is he dating sara?"]}
    ]
  }
}
```

---

## 🔌 Subject Enrichment (Pluggable Providers)

Create a simple provider interface and implement **at least two** providers.

**Interface (example):**
```python
class Provider(Protocol):
    name: str
    supports: set[str]  # {"email","username","phone"}

    def enrich(self, subject: dict) -> dict:
        ...
```
**Providers to implement (mocked lookups are fine):**
- `gravatar_like` (for `email`): hash → avatar URL + exists(bool). No real network needed; simulate deterministically.
- `handle_presence` (for `username`): check presence against a configurable set (`{"twitch","github","twitter"}`) using `fixtures/handles.json`.

Write each subject’s enrichment to `data/enrichment/<subject_key>.json`.

---

## 💬 Twitch Chat Monitor

- **Live mode:** connect via Twitch IRC (`twitchio` or your own IRC client).  
  Respect rate limits; gracefully handle reconnects.  
- **Offline mode:** replay `fixtures/chat/*.jsonl` entries with small delays to mimic real flow.
- **Parsing per message:**  
  - Extract mentions: tokens like `@username`  
  - Extract URLs (simple regex is fine)  
  - Extract lightweight “emotes” (e.g., `:kappa:` pattern or leave empty)  
- **Write:** append to `messages.jsonl` and **incrementally** update user/channel profiles.

---

## 🤖 (Bonus) Light NLP / AI

Implement a small rule-based analyzer (no heavy models required):

- If text matches patterns like `"(still )?dating\s+(\w+)"` near “you/he/she/streamer”, emit signals:
  - Update user/profile facts and channel `streamer_signals`.
- Optional: integrate a small open-source NLP (e.g., spaCy) to extract **PERSON** entities.
- **Explainability:** store short **evidence snippets** and counts.

---

## 🔎 Search Functionality

Implement naive search over `messages.jsonl`:

- Filter by `--by user|channel` and `--value`.
- Time range filters `--since` / `--until` (ISO8601).
- Text contains `--contains`.
- `--limit` to cap output.

Output pretty JSON to stdout.

---

## 🧱 Project Layout (suggested)

```
app/
  __init__.py
  cli.py                 # entrypoint (Typer/Click)
  models.py              # pydantic models (Subject, Message, Profile)
  io_jsonl.py            # append/read helpers (idempotent appends)
  providers/
    base.py
    gravatar_like.py
    handle_presence.py
  chat/
    runner.py            # orchestrates live/offline
    twitch_live.py       # IRC client or twitchio wrapper
    replay.py            # fixtures replayer
  analysis/
    signals.py           # regex/NLP heuristics
    rollups.py           # build/update profiles
data/                    # created at runtime
fixtures/
  handles.json
  chat/
    example_channel.jsonl
subjects.csv
tests/
  test_parsing.py
  test_rollups.py
  test_providers.py
README.md
```

---

## 📦 Fixtures (include in your repo)

**`subjects.csv`**
```csv
type,value
email,alice@example.com
username,someuser
phone,+12025550123
username,mod123
```

**`fixtures/handles.json`**
```json
{
  "someuser": ["twitch","twitter"],
  "mod123": ["twitch","github"],
  "ghost": []
}
```

**`fixtures/chat/example_channel.jsonl`**
```json
{"ts":"2025-09-02T12:00:00Z","channel":"example_channel","user_name":"someuser","text":"hey @mod is he still dating sara?"}
{"ts":"2025-09-02T12:00:03Z","channel":"example_channel","user_name":"mod123","text":"@someuser lol idk"}
{"ts":"2025-09-02T12:00:05Z","channel":"example_channel","user_name":"fan88","text":"link pls https://example.com"}
```

---

## 🧪 Tests (minimum)

- **Parsers:** mentions/URLs/emotes extraction.
- **Rollups:** user/channel profile aggregation from a small message set.
- **Providers:** enrichment logic with mocked data (`fixtures/handles.json`).

---

## 🔐 Env Vars (live mode)

- `TWITCH_OAUTH_TOKEN` (format: `oauth:xxxxxxx`)
- `TWITCH_NICK` (bot username)
- (Optional) `TWITCH_CLIENT_ID`

Document in your README how to obtain these, and provide an **offline flow** requiring no keys.

---

## 🧭 Quick Start Examples

```bash
# Offline flow
python -m app.cli subjects load --path subjects.csv
python -m app.cli chat run --channels example_channel --duration-seconds 15 --offline
python -m app.cli search messages --by user --value someuser --contains dating

# Live flow (requires env tokens)
export TWITCH_OAUTH_TOKEN="oauth:xxxxxxxx"
export TWITCH_NICK="yourbotname"
python -m app.cli chat run --channels myfavoritestreamer --duration-seconds 600
```

---

## 📋 Evaluation Rubric (100 pts)

| Area | Points | What we look for |
|---|---:|---|
| Architecture & Code Quality | 25 | Modularity, typing, clarity, small functions, comments/docstrings |
| Chat Ingestion | 20 | Stable live/offline modes, correct parsing, no dupes, resilience |
| Data Modeling & Files | 15 | Clean JSON/JSONL, consistent schemas, normalization, idempotent appends |
| Search UX | 10 | Correct filters, readable output, reasonable performance (~10k lines) |
| Subject Enrichment | 10 | Provider abstraction + ≥2 providers working (mock OK) |
| NLP/Signals | 10 | Useful simple rules; evidence captured; low false positives |
| Tests | 5 | Clear unit tests; easy to run locally |
| Docs | 5 | Setup, run instructions, design notes, limitations |

**Bonus (up to +10):**
- Tiny web API (FastAPI) exposing `/search` and `/profiles/*`
- Optional DB backend (SQLite/Postgres) with identical outputs
- Rate-limit handling & reconnection for live Twitch

---

## ⚖️ Legal / Ethics Guardrails

- Use **official APIs** or the **offline fixtures**.  
- Only ingest **public chat** or chats you’re authorized to join with your bot account.  
- Do **not** bypass access controls or violate ToS.  
- Redact obvious PII if it appears accidentally; keep logs easy to delete (per user/channel).

---

## 📝 Submission

- GitHub repo link with full source, fixtures, and tests.
- **README** explaining:
  - How to run (offline & live)
  - Design decisions & trade-offs (files vs DB, batching, search)
  - Known limitations & next steps

> Tip: Treat this like a mini-product—opt for clarity, deterministic behavior, and small, well-named modules.
