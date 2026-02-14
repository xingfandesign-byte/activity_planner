# Quick Start Guide

## Running the Activity Planner

### Option 1: Use the startup script (Recommended)

```bash
cd activity-planner
./run.sh
```

This will:
- Start the backend API server on port 5001
- Start the frontend web server on port 8000
- Open your browser to http://localhost:8000

### Option 2: Manual startup

**Terminal 1 - Backend:**
```bash
cd activity-planner/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd activity-planner/frontend
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## Environment Setup (Optional)

### Google Places API

To get real location data instead of mock data, set up a Google Places API key:

**Note:** Recommendations are currently **Manus-only**. The Google Places integration is no longer used by `/v1/recommendations/ai` unless you re-enable it in code.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Places API**
4. Create an API key under Credentials
5. Set the environment variable:

```bash
export GOOGLE_PLACES_API_KEY="your-api-key-here"
```

Or add to your `.env` file:
```
GOOGLE_PLACES_API_KEY=your-api-key-here
```

**Note:** The app works without an API key using mock data for development.

### Google OAuth (Sign in with Google)

To enable "Sign in with Google":

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Click **Create Credentials > OAuth client ID**
4. Select **Web application**
5. Add authorized JavaScript origins:
   - `http://localhost:8000` (development)
   - Your production domain
6. Add authorized redirect URIs:
   - `http://localhost:5001/v1/auth/google/callback`
7. Copy the **Client ID** and **Client Secret**
8. Set environment variables:

```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

**Note:** The app works without OAuth using email/password authentication.

### Password reset email (SMTP)

To send real password reset emails (instead of showing the reset link only in the app):

1. **Gmail:** Use an [App Password](https://support.google.com/accounts/answer/185833) (not your normal password). Enable 2FA first, then create an app password for "Mail".
2. **Other providers:** Use your provider’s SMTP host, port (usually 587), and credentials.

Set these environment variables (or add to `.env`):

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export EMAIL_FROM="Activity Planner <your-email@gmail.com>"
export FRONTEND_URL="http://localhost:8000"
```

- **SMTP_HOST** – e.g. `smtp.gmail.com`, `smtp.office365.com`
- **SMTP_PORT** – usually `587` (TLS)
- **SMTP_USER** / **SMTP_PASSWORD** – SMTP login (for Gmail, use an app password)
- **EMAIL_FROM** – From address (and optional display name)
- **FRONTEND_URL** – Base URL of the app (used in the reset link). Use your real URL in production.

If SMTP is **not** set, the app still works: after "Forgot password?" the reset link is shown in the UI for testing.

### Local feeds (RSS, Facebook, Eventbrite, Manus)

Recommendations can be complemented with local events and news. Set any of:

- **LOCAL_FEED_URLS** – Comma-separated RSS/Atom URLs (e.g. Axios, city event calendars). **LOCAL_FEED_LABELS** – Optional labels (same order).
- **FACEBOOK_ACCESS_TOKEN** – Optional; Facebook Graph API token for events near the user.
- **EVENTBRITE_TOKEN** – Optional; [Eventbrite API](https://www.eventbrite.com/platform/api) token.
- **MANUS_API_KEY** – Optional; [Manus API](https://open.manus.ai/docs) key. User preferences are converted to a prompt and sent to Manus; the agent returns personalized local activity recommendations (events, places, activities), which are merged with Google Places and other feeds.

Example:

```bash
export MANUS_API_KEY="your-manus-api-key"
```

To see which sources are configured: `GET /v1/feeds/config` (returns enabled sources, no secrets).

### Detail page images (location-specific)

The detail page shows images that match the event/location using keywords from the title and event detail. Configure one of (tried in order):

- **GOOGLE_CSE_API_KEY** + **GOOGLE_CSE_CX** – [Google Custom Search](https://programmablesearchengine.google.com/) with Image search enabled (100 free queries/day).
- **PEXELS_API_KEY** – [Pexels API](https://www.pexels.com/api/) (free, 200 req/hr).
- **UNSPLASH_ACCESS_KEY** – [Unsplash API](https://unsplash.com/developers) (free, 50 req/hr).

If none are set, the app uses category-based placeholder images.

## First Time Setup

1. **Complete Onboarding**:
   - Select planning mode (Family/Individual)
   - Enter your location (default: San Francisco, CA)
   - Choose categories and preferences
   - Set notification time

2. **View Recommendations**:
   - Browse the activity digest
   - Each card shows distance, travel time, price, and details

3. **Add to Calendar**:
   - Click "View Details" on any recommendation
   - Select a time slot
   - Click "Add to Calendar" to create a Google Calendar event

4. **Provide Feedback**:
   - Like (👍) or Save (⭐) recommendations
   - Mark as "Already Been" to prevent future recommendations

## Features Implemented

✅ User onboarding and preferences
✅ Activity digest with 8 personalized recommendations
✅ Deduplication (prevents showing places you've visited)
✅ Calendar event creation (Google Calendar links)
✅ Feedback system (like, save, already been)
✅ Responsive web UI
✅ Google Places API integration (real location data)
✅ Google OAuth authentication (Sign in with Google)
✅ Email/password authentication
✅ AI-powered personalized recommendations
✅ Database persistence (SQLite: users, preferences, saved/visited, auth)
✅ Local feeds (RSS/Atom, Facebook Local, Eventbrite, Manus) to complement Google Places
✅ Manus: user preference → prompt → personalized local feed (optional)

## Next Steps for Production

- Implement email notifications for Friday digests
- Calendar history parsing for automatic deduplication
- Add Apple Sign-In support
