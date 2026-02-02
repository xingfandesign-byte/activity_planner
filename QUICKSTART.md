# Quick Start Guide

## Running the Weekend Planner

### Option 1: Use the startup script (Recommended)

```bash
cd weekend-planner
./run.sh
```

This will:
- Start the backend API server on port 5001
- Start the frontend web server on port 8000
- Open your browser to http://localhost:8000

### Option 2: Manual startup

**Terminal 1 - Backend:**
```bash
cd weekend-planner/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd weekend-planner/frontend
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## Environment Setup (Optional)

### Google Places API

To get real location data instead of mock data, set up a Google Places API key:

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

## First Time Setup

1. **Complete Onboarding**:
   - Select planning mode (Family/Individual)
   - Enter your location (default: San Francisco, CA)
   - Choose categories and preferences
   - Set notification time

2. **View Recommendations**:
   - Browse the weekend digest
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
✅ Weekend digest with 8 personalized recommendations
✅ Deduplication (prevents showing places you've visited)
✅ Calendar event creation (Google Calendar links)
✅ Feedback system (like, save, already been)
✅ Responsive web UI

## Next Steps for Production

- Integrate Google OAuth for authentication
- Connect to Google Places API for real location data
- Implement email notifications for Friday digests
- Add database persistence (currently in-memory)
- Calendar history parsing for automatic deduplication
