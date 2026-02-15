# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Activity Planner is a weekend activity recommendation app. Flask backend API + vanilla JS frontend (no framework, no build step). SQLite database. Deployed on Render.

## Development Commands

### Run locally (both servers)
```bash
./run.sh
# Backend: http://localhost:5001, Frontend: http://localhost:8000
```

### Run backend manually
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Run frontend manually
```bash
cd frontend
python3 -m http.server 8000
```

### Test backend
```bash
bash test_backend.sh
# Runs curl-based health checks against /health, /v1/digest, /v1/preferences
```

### Build frontend for production
```bash
bash scripts/build-frontend.sh
# Injects API_URL into frontend/config.js
```

There is no linter, formatter, or unit test framework configured.

## Architecture

### Backend (`backend/`)

Monolithic Flask REST API. All routes defined in `app.py` (~2,600 lines) under `/v1` prefix. CORS enabled for all origins.

- **app.py** — All API endpoints: auth (email/phone OTP/Google OAuth), preferences, recommendations/digest, feedback, calendar, geolocation, image search, feeds, notifications
- **db.py** — SQLite persistence layer. Tables: `users`, `preferences`, `visited_history`, `saved_places`, `recent_recommendations`, `auth_tokens`, `password_reset_tokens`, `verification_tokens`. Auto-creates tables on startup via `db.init_db()`
- **local_feeds.py** — RSS/Atom feed parsing, Facebook Graph API, Eventbrite API, Manus AI personalization. Uses ThreadPoolExecutor for concurrent fetching.
- **send_friday_digest.py** — Email digest scheduler

Auth uses Bearer tokens in `Authorization` header. Falls back to demo user if no token provided. Passwords hashed with PBKDF2-SHA256.

### Frontend (`frontend/`)

Single-page app in vanilla HTML/CSS/JS — no build framework.

- **index.html** — All screens in one file (auth, onboarding, digest, settings)
- **app.js** — State management, API calls, UI rendering (~3,100 lines)
- **styles.css** — Custom gradient UI, responsive design
- **config.js** — Sets `window.API_BASE` (injected by build script for production)

Frontend communicates with backend via `fetch()` using `window.API_BASE + endpoint`.

### Key data flow

User onboarding (7 steps) → preferences saved to SQLite → `/v1/digest` generates recommendations using Google Places API (or mock fallback) + optional Manus AI → results displayed in feed with images from Google CSE/Pexels/Unsplash.

## Environment Variables

**Required for production:** `SECRET_KEY`, `FRONTEND_URL`, `GOOGLE_REDIRECT_URI`

**Optional — auth:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

**Optional — recommendations:** `MANUS_API_KEY`, `GOOGLE_PLACES_API_KEY` (falls back to mock data)

**Optional — images:** `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_CX`, `PEXELS_API_KEY`, `UNSPLASH_ACCESS_KEY`

**Optional — email:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`

**Optional — feeds:** `LOCAL_FEED_URLS`, `LOCAL_FEED_LABELS`, `FACEBOOK_ACCESS_TOKEN`, `EVENTBRITE_TOKEN`

## Deployment

Render Blueprint via `render.yaml`. Backend runs with gunicorn. Frontend is a static site built by `scripts/build-frontend.sh`. SQLite data is ephemeral on Render free tier (lost on redeploy).
