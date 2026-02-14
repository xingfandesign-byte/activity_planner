# Activity Planner - Calendar-first V1

An activity planning tool that sends Friday digests with personalized activity recommendations and integrates with Google Calendar.

## Features

- **Friday Digest**: Receive personalized activity recommendations
- **Calendar Integration**: One-click "Add to Calendar" functionality
- **Deduplication**: Prevents recommending places you've already visited
- **Preferences**: Customize location, radius, categories, and more
- **Feedback Loop**: Like, save, or mark places as "already been"

## Project Structure

```
activity-planner/
├── backend/          # Flask API server
│   ├── app.py       # Main API endpoints
│   └── requirements.txt
├── frontend/         # Web application
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd activity-planner/backend
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
python app.py
```

The API will be available at `http://localhost:5001`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd activity-planner/frontend
```

2. Serve the frontend using a simple HTTP server:

**Option 1: Python HTTP Server**
```bash
python3 -m http.server 8000
```

**Option 2: Node.js http-server**
```bash
npx http-server -p 8000
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

1. **Onboarding**: 
   - Select your planning mode (Family/Individual)
   - Set your home location
   - Choose search radius and categories
   - Configure notification preferences

2. **View Recommendations**:
   - Browse the activity digest with 8 personalized recommendations
   - Each card shows distance, travel time, price, and other details

3. **Add to Calendar**:
   - Click "View Details" on any recommendation
   - Select a time slot (Saturday/Sunday, Morning/Afternoon)
   - Click "Add to Calendar" to create a Google Calendar event

4. **Provide Feedback**:
   - Like recommendations (👍)
   - Save for later (⭐)
   - Mark as "Already Been" to prevent future recommendations

## API Endpoints

### Preferences
- `GET /v1/preferences` - Get user preferences
- `PUT /v1/preferences` - Update user preferences

### Recommendations
- `GET /v1/digest` - Get activity digest
- `POST /v1/feedback` - Submit feedback on recommendations

### Visited History
- `GET /v1/visited` - Get visited places
- `POST /v1/visited` - Add visited place
- `DELETE /v1/visited/<place_id>` - Remove visited place

### Calendar
- `POST /v1/calendar/event_template` - Generate calendar event template

### Notifications
- `POST /v1/notifications/test` - Send test notification
- `POST /v1/notifications/pause` - Pause/resume notifications

## Current Implementation Status

### ✅ Implemented
- User onboarding flow
- Preferences management
- Recommendation engine with deduplication
- Digest generation
- Feedback system
- Calendar event template generation
- Basic UI/UX

### 🚧 Future Enhancements
- Google OAuth integration (currently using demo session)
- Real Places API integration (currently using mock data)
- Email notification system
- Calendar history parsing for deduplication
- Weather-aware filtering
- Shared planning (partner collaboration)
- Assistant conversation mode (V2)

## Development Notes

- The current implementation uses in-memory storage. For production, replace with a proper database (PostgreSQL, MongoDB, etc.)
- Mock places data is used for demonstration. Integrate with Google Places API for real data
- Google Calendar integration currently generates calendar links. Full OAuth integration needed for direct event creation
- Email notifications are stubbed. Integrate with SendGrid, Mailgun, or similar service

## Configuration

### Environment Variables (for production)

```bash
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
PLACES_API_KEY=your-google-places-api-key
EMAIL_API_KEY=your-email-service-api-key
```

## License

This is a demo implementation based on the Activity Planner specification.
