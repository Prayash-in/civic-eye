# Civic Eye — AI-Powered Civic Issue Reporting

> **See a problem. Report it. Let AI do the rest.**

Civic Eye is a crowdsourced civic issue reporting platform that turns raw citizen submissions (photo + description + location) into **structured, actionable civic intelligence** — classified, severity-scored, mapped, and routed to the responsible authority in seconds.

The MVP is built around an already-working **local vision model** (Qwen3-VL 4B via LM Studio) and deliberately keeps AI as a decision-support layer — authorities remain in control.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Issue Taxonomy](#issue-taxonomy)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Frontend Routes](#frontend-routes)
- [AI Pipeline](#ai-pipeline)
- [Data Model](#data-model)
- [Jurisdiction & Authority Routing](#jurisdiction--authority-routing)
- [Image Upload & Security](#image-upload--security)
- [Evaluation & Testing](#evaluation--testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

Citizens often report problems as an unstructured photo and a one-line description. Civic authorities need that noise converted into:

1. **What** is the issue? (classification)
2. **How bad** is it? (severity)
3. **How confident** is the prediction?
4. **Where** is it? (geolocation + jurisdiction)
5. **Who** should fix it? (department / authority)
6. **Should it notify** someone? (demo email, threshold-gated)

**Citizen flow:** `Open /report` → upload image + description + location → `Analyzing your report…` → AI result (issue type / severity / confidence / explanation) → persisted → visible on dashboard & map.

**Authority flow:** `Open /dashboard` → totals, breakdowns by issue type / severity / status, recent reports, map with markers, filters (issue type, severity, status), and per-report detail with image + jurisdiction + authority + notification log.

Design philosophy from `ai_problem_definition.md:566`: *Convert noisy crowdsourced observations into structured, explainable, and actionable civic intelligence.*

---

## Key Features

- **Local AI analysis** — `backend/ai/analyzer.py:547` calls Qwen3-VL through LM Studio OpenAI-compatible API; never fakes a result, returns `503`-style failure when unavailable.
- **8-way classification** with calibrated severity (`low` / `medium` / `high` / `critical`) and confidence.
- **Deterministic jurisdiction** — GPS → Assembly & Lok Sabha constituency + MLA/MP lookup via static GIS data in `backend/data/` (`backend/services/jurisdiction_service.py:82`).
- **Rule-based authority routing** — issue type → department/authority from `backend/data/authorities.json` (`backend/services/authority_service.py:57`), localized by district.
- **Threshold-gated demo notifications** — SMTP email only when `confidence > 0.5` (`backend/config.py:72`), status tracked per-recipient in `notifications` table.
- **Leaflet + OpenStreetMap** — free map with severity-colored pins, popups, and report linking (`frontend/src/components/ReportMap.jsx`).
- **Dashboard analytics** — totals, `by_issue_type` / `by_severity` / `by_status`, civic-response rollups, recent notifications (`backend/api/reports.py:154`).
- **Mobile-responsive, accessible UI** with loading skeletons, image preview, and graceful geolocation fallback.

---

## Issue Taxonomy

Exactly 8 issue types (MVP scope, `OPENCODE_MVP_PROMPT.md:87`):

| Category | Issue Types |
|---|---|
| **Road** | `pothole`, `damaged_road` |
| **Waste Management** | `garbage_overflow`, `illegal_dumping` |
| **Electricity** | `broken_streetlight` |
| **Water** | `water_leakage` |
| **Drainage** | `blocked_drain`, `open_drain` |

Severity levels: `low` → `medium` → `high` → `critical` (see `annotation_guidelines.md:208` for definitions).

Detailed prompt boundaries (pothole vs damaged_road, open vs blocked drain, garbage overflow vs illegal dumping) live in `backend/ai/analyzer.py:95`.

---

## Architecture

```
Citizen (React/Vite) ──► FastAPI (/api/reports) ──► report_service.py:204
                                │                          │
                                │                    save_image() → data/uploads/<uuid>.ext
                                │                    create_report() → SQLite (reports)
                                │                          │
                                │                    ai_service.py:10 → analyzer.py:547
                                │                          │  LM Studio http://localhost:1234/v1/chat/completions
                                │                          │  model: qwen/qwen3-vl-4b
                                │                          ▼
                                │                    CivicIssueAnalysis (issue_type, severity, confidence, explanation)
                                │                    update_analysis() → SQLite
                                │                          │
                                │                    jurisdiction_service.py:82 (GPS → constituency)
                                │                    authority_service.py:57 (issue → authority)
                                │                    notification_service (SMTP, threshold-gated)
                                │                    record_notification() → SQLite
                                ▼
                         Dashboard / Map / Detail (React Router + Leaflet)
```

Clean separation enforced: `API route → AI service → analyze_report() → CivicIssueAnalysis` — no AI logic in the API layer (`OPENCODE_MVP_PROMPT.md:176`).

---

## Tech Stack

| Layer | Technology |
|---|---|
| **AI** | Qwen3-VL 4B, LM Studio (OpenAI-compatible `/v1/chat/completions`), `requests`, `pydantic` |
| **Backend** | FastAPI `>=0.115`, Uvicorn `>=0.30`, SQLite, `python-multipart`, `python-dotenv` |
| **Frontend** | React `18.3`, React Router `6.26`, Vite `5.4`, Leaflet `1.9` |
| **Tooling** | `uv` (Python package manager), `pytest` (tests) |
| **Python** | `>=3.11` (`pyproject.toml:9`) |

---

## Project Structure

```
civic-ai/
├── backend/
│   ├── ai/
│   │   ├── analyzer.py          # Qwen3-VL analyzer — DO NOT replace (P0)
│   │   ├── vision_analyzer.py
│   │   ├── severity_engine.py
│   │   └── schema.py
│   ├── api/
│   │   ├── app.py               # FastAPI app, static /uploads mount, error handlers
│   │   └── reports.py           # POST /api/reports, GET /api/reports, /stats, /{id}
│   ├── models/
│   │   └── report.py            # Report + ReportStatus pydantic models
│   ├── services/
│   │   ├── report_service.py    # Validation, persistence, AI orchestration, routing
│   │   ├── ai_service.py        # Thin wrapper around analyzer.analyze_report
│   │   ├── jurisdiction_service.py
│   │   ├── authority_service.py
│   │   └── notification_service.py
│   ├── database/
│   │   └── database.py          # SQLite schema, migrations, CRUD
│   ├── data/
│   │   ├── constituencies.json
│   │   ├── representatives.json
│   │   └── authorities.json
│   └── config.py                # Env-driven config, upload limits, SMTP
├── frontend/
│   ├── src/
│   │   ├── pages/               # Landing, ReportPage, ReportsList, ReportDetail, Dashboard, MapPage
│   │   ├── components/          # Layout, Badge, ReportMap, Loading, Skeleton, etc.
│   │   ├── api.js               # fetch wrappers for /api/*
│   │   ├── App.jsx              # Route definitions
│   │   └── theme.js / styles.css
│   ├── vite.config.js           # Dev proxy: /api & /uploads → localhost:8000
│   └── package.json
├── src/                         # AI research modules (classification, severity, routing, etc.)
├── data/
│   ├── civic.db                 # SQLite DB (gitignored, auto-created)
│   ├── uploads/                 # User uploads (gitignored, unique filenames)
│   ├── development/ & evaluation/  # AI evaluation datasets — do not use as app data
├── tests/                       # pytest suite (analyzer, API, DB, jurisdiction, etc.)
├── notebooks/
├── pyproject.toml
├── uv.lock
└── .env                         # Local env (gitignored)
```

---

## Prerequisites

- **Python 3.11+** and [`uv`](https://docs.astral.sh/uv/)
- **Node.js 18+** and `npm`
- **LM Studio** with `qwen/qwen3-vl-4b` loaded and server running on `http://localhost:1234`

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo-url> civic-ai
cd civic-ai

# Backend deps
uv sync

# Frontend deps
cd frontend
npm install
cd ..
```

### 2. Configure environment

Create `.env` in the project root (see [Environment Variables](#environment-variables)):

```env
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
LM_STUDIO_MODEL=qwen/qwen3-vl-4b

# Optional: demo authority notifications (threshold-gated, >50% confidence)
DEMO_NOTIFICATION_EMAIL_1=team@example.com
DEMO_NOTIFICATION_EMAIL_2=team2@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=you@gmail.com
APP_BASE_URL=http://localhost:5173
```

> The `.env` file is gitignored. Never commit secrets. The app never exposes env vars to the frontend (`backend/config.py:44`).

### 3. Start LM Studio

- Open LM Studio → Load `qwen/qwen3-vl-4b` → Start local server (default `http://localhost:1234`).
- Verify: `curl http://localhost:1234/v1/models` should list the model.

### 4. Start the backend

```bash
uv run uvicorn backend.api.app:app --reload --port 8000
```

- Health check: `http://localhost:8000/api/health` → `{"status":"ok"}` (`backend/api/app.py:44`)
- Uploads served at `http://localhost:8000/uploads/<filename>`
- DB auto-initializes at `data/civic.db` on first request (`backend/database/database.py:84`).

### 5. Start the frontend

```bash
cd frontend
npm run dev
```

- App: `http://localhost:5173`
- Vite proxies `/api` and `/uploads` to `http://localhost:8000` (`frontend/vite.config.js:8`).

### 6. Verify end-to-end

1. Open `http://localhost:5173/report`
2. Upload a civic image (jpg/jpeg/png/webp, ≤10 MB), add description, allow or manually set location.
3. Submit → see `Analyzing your report…` → AI result (issue type, severity, confidence, explanation) → confirmation.
4. Check `http://localhost:5173/dashboard` and `http://localhost:5173/map`.

---

## Environment Variables

All config is centralized in `backend/config.py:1` and loaded via `python-dotenv`.

| Variable | Default | Description |
|---|---|---|
| `LM_STUDIO_URL` | `http://localhost:1234/v1/chat/completions` | LM Studio OpenAI-compatible endpoint |
| `LM_STUDIO_MODEL` | `qwen/qwen3-vl-4b` | Model name passed to LM Studio |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max image size in MB (`backend/config.py:26`) |
| `NOTIFICATION_ENABLED` | `true` | Set `false` to disable demo emails |
| `NOTIFICATION_MIN_CONFIDENCE` | `0.5` | Emails only sent when `confidence >` this value |
| `DEMO_NOTIFICATION_EMAIL_1/2/3` | — | Team-controlled demo recipients (comma-separated also supported) |
| `SMTP_HOST` / `SMTP_PORT` | — | SMTP relay (e.g. `smtp.gmail.com:587`) |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | — | SMTP credentials |
| `SMTP_FROM_EMAIL` | `SMTP_USERNAME` | Sender address |
| `APP_BASE_URL` | `http://localhost:5173` | Base URL used in notification links |

> Override `LM_STUDIO_URL` / `LM_STUDIO_MODEL` without changing code — the analyzer reads them at import time (`backend/ai/analyzer.py:16`).

---

## API Reference

Base URL (dev): `http://localhost:8000`

### `GET /api/health`

```json
{ "status": "ok" }
```

### `POST /api/reports`

Multipart form submission — `backend/api/reports.py:101`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `image` | file | yes | `jpg`/`jpeg`/`png`/`webp`, validated by extension + MIME + size |
| `description` | string | yes | Non-empty after trim; 422 if missing |
| `latitude` | float | no | Geolocation fallback handled gracefully |
| `longitude` | float | no | — |
| `category` | string | no | Legacy field, stored as-is |

**Success `200`:**

```json
{
  "id": 12,
  "image_path": "data/uploads/a1b2c3d4....jpg",
  "image_url": "/uploads/a1b2c3d4....jpg",
  "description": "Large pothole near the gate",
  "category": "",
  "issue_type": "pothole",
  "severity": "high",
  "confidence": 0.94,
  "explanation": "Distinct deep pothole visible...",
  "latitude": 26.14,
  "longitude": 91.73,
  "status": "submitted",
  "analysis_status": "completed",
  "jurisdiction": {
    "status": "resolved",
    "method": "polygon",
    "assembly_constituency": { "id": "AS-042", "name": "Dispur", "district": "Kamrup Metropolitan" },
    "lok_sabha_constituency": { "id": "GUWAHATI", "name": "Guwahati" }
  },
  "representatives": {
    "mla": { "name": "...", "party": "..." },
    "mp": { "name": "...", "party": "..." }
  },
  "authority": {
    "name": "Guwahati Municipal Corporation",
    "department": "roads_transport",
    "reason": "Pothole reports are routed to..."
  },
  "notification": {
    "status": "sent",
    "channel": "email",
    "sent_at": "2026-03-10T12:34:56+00:00"
  }
}
```

**Error cases:**

- `400` — unsupported type / oversized image (`backend/services/report_service.py:44`)
- `422` — missing description
- AI unavailable → report still persisted with `analysis_status: "failed"` and `issue_type: null`; response contains routed jurisdiction but no authority notification (`backend/services/report_service.py:230`)

### `GET /api/reports`

Query params: `issue_type`, `severity`, `status`, `analysis_status`, `limit` (1–500, default 100), `offset` (`backend/api/reports.py:135`).

### `GET /api/reports/stats`

Aggregated counts + recent reports + civic-response rollups (`backend/api/reports.py:154`):

```json
{
  "total": 42,
  "by_issue_type": { "pothole": 12, "garbage_overflow": 8 },
  "by_severity": { "high": 10, "medium": 20 },
  "by_status": { "submitted": 42 },
  "recent": [ ... ],
  "civic_response": {
    "routed": 38,
    "unrouted": 4,
    "by_authority": { "Guwahati Municipal Corporation": 20 },
    "notifications": { "sent": 18, "not_sent": 24 },
    "jurisdiction": { "resolved": 35, "outside_supported_area": 5 },
    "recent_notifications": [ ... ]
  }
}
```

### `GET /api/reports/{id}`

Single report with per-recipient notification log (`backend/api/reports.py:210`).

### `GET /uploads/{filename}`

Static file serving for uploaded images (`backend/api/app.py:17`).

---

## Frontend Routes

| Path | Component | Description |
|---|---|---|
| `/` | `Landing.jsx` | Hero, live stats, how-it-works, issue showcase, severity guide |
| `/report` | `ReportPage.jsx` | Image upload + preview, description, location (geolocation / map pick / manual), submit + AI result |
| `/reports` | `ReportsList.jsx` | Paginated list with filters (issue type, severity, status) |
| `/reports/:id` | `ReportDetail.jsx` | Full report, image, AI explanation, jurisdiction, authority, notification log |
| `/dashboard` | `Dashboard.jsx` | Totals, breakdowns, recent reports table, map, notification feed |
| `/map` | `MapPage.jsx` | Leaflet map with severity-colored pins, click → detail |

All routes are wrapped in `Layout.jsx` with theme support (`frontend/src/theme.js`).

---

## AI Pipeline

The analyzer is intentionally **not** replaced — treat `backend/ai/analyzer.py:547` as a dependency.

```
image_path + description
        │
        ▼
encode_image() → base64 data URL
        │
        ▼
SYSTEM_PROMPT (issue definitions + severity calibration) + user prompt
        │
        ▼
POST LM_STUDIO_URL  { model, messages, temperature: 0.1, max_tokens: 400 }
        │
        ▼
extract_json() → normalize_result() → CivicIssueAnalysis (pydantic)
```

- **Model:** `qwen/qwen3-vl-4b` (`backend/config.py:21`)
- **Timeout:** 180s (`backend/ai/analyzer.py:25`)
- **Service boundary:** `backend/services/ai_service.py:10` wraps `analyze_report()` and maps any exception to `AIServiceError("AI analysis is temporarily unavailable…")` — never fabricates `issue_type`/`severity` (`OPENCODE_MVP_PROMPT.md:422`).
- **Allowed values** validated in `normalize_result()` (`backend/ai/analyzer.py:478`).

---

## Data Model

`backend/models/report.py:24` and `backend/database/database.py:10`:

| Field | Type | Notes |
|---|---|---|
| `id` | int (PK) | Autoincrement |
| `image_path` | string | Relative to project root, e.g. `data/uploads/<uuid>.jpg` |
| `description` | string | Citizen text |
| `category` | string | Legacy, default `""` |
| `issue_type` | string \| null | One of 8 types, null when `analysis_status=failed` |
| `severity` | string \| null | `low`/`medium`/`high`/`critical` |
| `confidence` | float \| null | 0–1 |
| `explanation` | string \| null | AI rationale |
| `latitude` / `longitude` | float \| null | Optional |
| `status` | enum | `submitted` (default) / `reviewed` / `resolved` |
| `analysis_status` | enum | `pending` / `completed` / `failed` |
| `authority_name` / `department` / `routing_reason` | string \| null | Added via `update_routing()` |
| `assembly_constituency_id` / `name`, `lok_sabha_constituency_id` | string \| null | Jurisdiction |
| `mla_name` / `mla_party`, `mp_name` / `mp_party` | string \| null | Representatives |
| `notification_status` / `channel` / `sent_at` | string \| null | Roll-up from `notifications` table |

`notifications` table (`backend/database/database.py:48`) stores one row per recipient with `channel`, `recipient`, `status`, `error`, `sent_at`.

---

## Jurisdiction & Authority Routing

- **Jurisdiction** (`backend/services/jurisdiction_service.py:82`) — ray-casting point-in-polygon against `backend/data/constituencies.json`; falls back to Darrang bounding-box for Mangaldai demo; returns `resolved` / `outside_supported_area` / `unavailable`.
- **Authority** (`backend/services/authority_service.py:57`) — deterministic lookup in `backend/data/authorities.json` by `issue_type`, localized by district (e.g. Darrang → Mangaldai Municipal Board, water issues → district water authority). Unknown types fall back to `default_authority`.
- Both are **rule-based** — the AI never selects authorities or representatives.

---

## Image Upload & Security

- Allowed extensions: `.jpg` `.jpeg` `.png` `.webp` (`backend/config.py:30`)
- Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`
- Max size: `10 MB` default, configurable via `MAX_UPLOAD_SIZE_MB`
- Unique filenames via `uuid4().hex` + original extension (`backend/services/report_service.py:70`) — never overwrites, never uses user-supplied names
- Uploads stored outside source tree at `data/uploads/` (`OPENCODE_MVP_PROMPT.md:249`)
- Path traversal prevented via `Path(filename).name` (`backend/services/report_service.py:49`)
- Stack traces never exposed — `ReportServiceError` → `400`, unhandled → generic `500` (`backend/api/app.py:20`)

---

## Evaluation & Testing

Preserved AI evaluation assets (do not delete):

- `tests/test_analyzer.py`, `tests/test_vision_analyzer.py`, `tests/test_structured_severity.py`
- `tests/run_dev_benchmark.py`, `tests/run_evaluation_benchmark.py`
- `data/development/` and `data/evaluation/` datasets

Run tests with `uv`:

```bash
# All tests
uv run pytest -v

# API + DB + service tests only (no LM Studio needed)
uv run pytest tests/test_api.py tests/test_database.py tests/test_report_service.py -v

# AI analyzer tests (require LM Studio running)
uv run pytest tests/test_analyzer.py tests/test_vision_analyzer.py -v
```

Additional suites: `test_jurisdiction.py`, `test_authority.py`, `test_notification.py`, `test_civic_flow.py`, `test_severity_engine.py`.

---

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `Could not connect to LM Studio` | LM Studio server not running. Start it on `http://localhost:1234` and load `qwen/qwen3-vl-4b`. Check `LM_STUDIO_URL` in `.env`. |
| `AI analysis is temporarily unavailable` | Model timeout or invalid JSON. Retry; check LM Studio logs. Report is still saved with `analysis_status=failed`. |
| `Unsupported image type` | Use jpg/jpeg/png/webp only. |
| `Image exceeds maximum size` | Reduce file size or raise `MAX_UPLOAD_SIZE_MB`. |
| Frontend shows `Live statistics are temporarily unavailable` | Backend not running on `:8000` or proxy misconfigured. Check `vite.config.js:8` and backend health. |
| Map shows no pins | Reports without `latitude`/`longitude` are not mappable — submit with location. |
| `outside_supported_area` | Coordinates outside current GIS polygons (Kamrup Metropolitan + Darrang). Report still stored and routable via fallback authority. |

---

## Scripts

| Command | Description |
|---|---|
| `uv run uvicorn backend.api.app:app --reload --port 8000` | Start backend (auto-creates DB) |
| `uv run pytest` | Run test suite |
| `cd frontend && npm run dev` | Start frontend dev server |
| `cd frontend && npm run build` | Production build to `frontend/dist/` |
| `cd frontend && npm run preview` | Preview production build |

---

## License

This project is for hackathon / educational use. No license file is currently included — add one if you intend to distribute.

---

*Built with local AI, free maps, and a focus on shipping the smallest complete MVP that works end-to-end.*
