# GeoVision — Satellite Imagery Crop & Disaster Change Detector

Built for **HackPreneur '26**, Problem Statement 8.2 (Space).

GeoVision is a full-stack MVP that performs rapid, near-real-time satellite change detection for disaster and crop-stress scenarios. A user selects an area of interest and a before/after date range; Sentinel-2 imagery is pulled via Google Earth Engine, a mode-selectable spectral index is computed and differenced, the result is cleaned and thresholded, and a small classifier refines the change mask. The output is quantified (hectares + % of AOI, severity rating) and served to a React/Leaflet frontend with a before/after toggle and change-mask overlay.

## Features

- **Three detection modes** — NDVI (crop stress), NDWI (flood), NBR (burn scar)
- **Adaptive Otsu thresholding** converts the change-signal distribution into a binary change mask
- **Random Forest fusion classifier** refines the mask using auto-bootstrapped labels from independent signals (index change, cloud flag, water, brightness)
- **SCL-based cloud/shadow/snow masking** + JRC permanent-water subtraction (flood mode)
- **Custom AOI** support via map click/draw, or bounding box / GeoJSON
- **3 validated reference presets**, served from cache for instant, reproducible demo results:
  - Bihar / Nepal border floods (2017)
  - Gospers Mountain bushfire, NSW, Australia
  - Po Valley drought, Italy
- Severity rating (mild / moderate / severe) with an alert summary and recommended actions

## Architecture

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

## Tech stack

| Layer | Stack |
|---|---|
| Imagery & analysis | Sentinel-2 via Google Earth Engine, NumPy, pandas, scikit-learn, scikit-image |
| Backend | FastAPI (Python), Uvicorn |
| Frontend | React + Vite, Leaflet / react-leaflet, Phosphor Icons |
| Deployment | Backend on Render, frontend on Vercel |

## Project structure

```
.
├── backend/
│   ├── main.py           # FastAPI app: /health, /analyze, /watchlist
│   ├── gee_client.py      # Earth Engine auth/init
│   ├── pipeline/          # ingestion → indices → masking → change detection → fusion → quantify
│   ├── models/             # Pydantic request/response schemas
│   ├── cache/              # Cached results for the 3 validated presets
│   └── requirements.txt
├── frontend/
│   ├── src/                # React app (map, AOI picker, results panel)
│   └── package.json
├── sample_events/           # Reference event write-ups used for preset validation
└── media/                   # Demo capture
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness + Earth Engine connectivity probe |
| `/analyze` | POST | Runs the change-detection pipeline for an AOI, date range, and mode; serves from cache for the 3 validated presets |
| `/watchlist` | GET | Ranked list of analyzed results (presets + current session's custom runs) |

## Running locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
earthengine authenticate   # one-time personal Google Earth Engine login
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

The frontend expects the backend at `http://localhost:8000` by default (`VITE_API_BASE`).

## Deployment

- **Backend (Render):** root directory left at repo root; build `pip install -r backend/requirements.txt`; start `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. Earth Engine auth is supplied via the `EE_CREDENTIALS_JSON` environment variable (personal OAuth credentials, not a service-account key) and `FRONTEND_ORIGIN` sets the allowed CORS origin.
- **Frontend (Vercel):** root directory `frontend`; framework preset Vite; `VITE_API_BASE` points at the deployed Render backend URL.

## Validation

Pipeline results were validated against three real, documented events (see `sample_events/`) before being locked in as cached presets, ensuring reproducible, judge-facing demo output independent of live Earth Engine latency.

## Team / Hackathon

Built for HackPreneur '26 — Problem Statement 8.2 (Space track).
