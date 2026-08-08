# GeoVision AI 🛰️

> AI-powered satellite change detection — analyze any region on Earth across any time window using Google Earth Engine.

GeoVision AI is a full-stack geospatial intelligence platform built for **HackPreneur '26** (Problem Statement 8.2 — Space). It detects and visualises land-cover changes (flooding, deforestation, burn scars, crop stress) from multispectral satellite imagery. Draw an area of interest on the map, pick two date windows, and the pipeline returns spectral-difference maps, change statistics, and an AI-generated narrative — in seconds.

---

## Features

- 🗺️ **Interactive AOI Selection** — Draw or paste any polygon / bounding-box on a Leaflet map; the backend validates size and fetches optimal imagery automatically.
- 📡 **Google Earth Engine Integration** — Fetches Sentinel-2 composites via GEE, computes NDVI / NDWI / NBR indices, and returns SCL cloud-masked mosaics.
- 🔬 **Three Detection Modes** — NDVI (crop stress), NDWI (flood), NBR (burn scar); adaptive Otsu thresholding converts the change signal into a binary change mask.
- 🌲 **Random Forest Fusion Classifier** — Refines the mask using auto-bootstrapped labels from independent signals (index change, cloud flag, water, brightness).
- 💧 **Advanced Masking** — SCL-based cloud/shadow/snow masking + JRC permanent-water subtraction (flood mode).
- ⚡ **Smart Caching** — Two-tier cache (in-memory session cache + on-disk preset cache) eliminates redundant GEE calls for repeated or preset requests.
- 🤖 **AI Narrative Generation** — GPT-powered natural-language summaries explain detected changes in plain English, with severity rating and recommended actions.
- 📊 **Change Statistics** — Pixel-level change magnitude, affected area (hectares + % of AOI), severity rating, and per-class breakdowns.
- 📋 **Watchlist** — Save and monitor named AOIs; re-run analysis with one click and compare results over time.
- 🏷️ **3 Validated Reference Presets** — Served from cache for instant, reproducible demo results:
  - Bihar / Nepal border floods (2017)
  - Gospers Mountain bushfire, NSW, Australia
  - Po Valley drought, Italy
- 🌙 **Dark-mode UI** — Space Grotesk / JetBrains Mono typography, fully responsive React + Vite frontend with before/after toggle and change-mask overlay.

---

## Demo

![GeoVision AI demo screenshot](./media/image.png)

[![Watch the demo](./media/image.png)](./media/video.mp4)

### 🎥 Demo Video

[Watch the full walkthrough](./media/video.mp4)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Vite + React)            │
│  Leaflet map · AOI drawing · Results overlay · Watchlist│
└───────────────────────┬─────────────────────────────────┘
                        │  HTTP / REST  (port 5173 → 8000)
┌───────────────────────▼─────────────────────────────────┐
│                FastAPI Backend  (Uvicorn)                │
│                                                         │
│  POST /analyze ──► pipeline/                            │
│    ├── gee_client.py   (GEE auth & connectivity check)  │
│    ├── pipeline/       (fetch → mask → diff → stats)    │
│    ├── cache.py        (disk preset + session LRU)      │
│    ├── geocoder.py     (place-name → bbox resolution)   │
│    ├── messages.py     (AI narrative generation)        │
│    └── watchlist.py    (saved AOI persistence)          │
│                                                         │
│  External: Google Earth Engine API · OpenAI API         │
└─────────────────────────────────────────────────────────┘
```

### Pipeline Flow

```
AOI (GeoJSON/bbox) + before/after dates + mode
        │
        ▼
[ingestion]   Sentinel-2 median composites over adaptive windows
              (SCL cloud-masked; widens from ±6d up to ±14d in poor clear-sky coverage)
        ▼
[indices]     NDVI / NDWI / NBR (mode-selectable)
        ▼
[masking]     SCL cloud/shadow/snow mask + JRC permanent water mask (flood mode)
        ▼
[change_detection]   after − before diff → adaptive Otsu threshold → binary mask
        ▼
[fusion_classifier]  Random Forest refines the mask using auto-bootstrapped
                      labels from independent signals
        ▼
[quantify]    hectares, % of AOI, severity, alert object
        ▼
[FastAPI POST /analyze]  →  JSON + before/after/mask thumbnails
        ▼
[React frontend]  AOI picker, date ranges, mode selector, Leaflet map with
                   before/after toggle + change-mask overlay, alert card
```

Each pipeline stage is a pure function in `backend/pipeline/`; `backend/main.py` orchestrates them.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Leaflet / react-leaflet, Phosphor Icons |
| Fonts | Space Grotesk (variable), JetBrains Mono (variable) |
| Backend | FastAPI (Python), Uvicorn, Pydantic v2 |
| Geospatial | Sentinel-2 via Google Earth Engine API (`earthengine-api`), geemap |
| Analysis | NumPy, Pandas, scikit-learn, scikit-image, Pillow |
| AI | OpenAI GPT (narrative generation) |
| Deployment | Backend on Render, frontend on Vercel |

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness + Earth Engine connectivity probe |
| `/analyze` | POST | Runs the change-detection pipeline for an AOI, date range, and mode; serves from cache for the 3 validated presets |
| `/watchlist` | GET | Ranked list of analyzed results (presets + current session's custom runs) |

---

## Getting Started

### Prerequisites

- Python ≥ 3.10
- Node.js ≥ 18
- A Google Earth Engine account (personal OAuth or service-account credentials)
- (Optional) OpenAI API key for AI narratives

### Backend

```bash
cd backend
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt

# Authenticate GEE (first run)
earthengine authenticate

uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # starts Vite dev server on http://localhost:5173
```

The frontend expects the backend at `http://localhost:8000` by default (`VITE_API_BASE`).

---

## Project Structure

```
Geovision-AI/
├── backend/
│   ├── main.py              # FastAPI app: /health, /analyze, /watchlist
│   ├── pipeline/            # ingestion → indices → masking → change detection → fusion → quantify
│   ├── models/              # Pydantic request/response schemas
│   ├── gee_client.py        # GEE init & connectivity helpers
│   ├── cache.py             # Two-tier caching layer
│   ├── geocoder.py          # Place → bbox resolution
│   ├── messages.py          # AI narrative generation
│   └── watchlist.py         # Saved AOI management
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/      # Map, sidebar, results, watchlist UI
│       ├── api/             # API wrappers
│       └── styles/
├── media/
│   ├── image.png            # Demo screenshot
│   └── video.mp4            # Full walkthrough video
├── sample_events/           # Reference event write-ups used for preset validation
└── backend/requirements.txt
```

---

## Deployment

- **Backend (Render):** root directory left at repo root; build command `pip install -r backend/requirements.txt`; start `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. Earth Engine auth is supplied via the `EE_CREDENTIALS_JSON` environment variable (personal OAuth credentials) and `FRONTEND_ORIGIN` sets the allowed CORS origin.
- **Frontend (Vercel):** root directory `frontend`; framework preset Vite; `VITE_API_BASE` points at the deployed Render backend URL.

---

## Validation

Pipeline results were validated against three real, documented events (see `sample_events/`) before being locked in as cached presets, ensuring reproducible, judge-facing demo output independent of live Earth Engine latency.

---

## Team / Hackathon

Built for **HackPreneur '26** — Problem Statement 8.2 (Space track).

---

## License

MIT © 2026 GeoVision AI contributors
