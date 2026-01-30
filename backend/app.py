"""
Weekend Planner Backend API
Calendar-first V1 implementation
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# In-memory storage (replace with database in production)
users_db = {}
preferences_db = {}
visited_history_db = {}
recent_recommendations_db = {}
feedback_db = {}

# Mock places data (replace with Places API in production)
MOCK_PLACES = [
    {
        "place_id": "p_001",
        "name": "Golden Gate Park",
        "category": "parks",
        "address": "San Francisco, CA",
        "lat": 37.7694,
        "lng": -122.4862,
        "distance_miles": 2.5,
        "travel_time_min": 10,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.8
    },
    {
        "place_id": "p_002",
        "name": "Exploratorium",
        "category": "museums",
        "address": "Pier 15, San Francisco, CA",
        "lat": 37.8014,
        "lng": -122.3976,
        "distance_miles": 5.2,
        "travel_time_min": 18,
        "price_flag": "paid",
        "kid_friendly": True,
        "indoor_outdoor": "indoor",
        "rating": 4.7
    },
    {
        "place_id": "p_003",
        "name": "Alcatraz Island",
        "category": "attractions",
        "address": "San Francisco Bay, CA",
        "lat": 37.8267,
        "lng": -122.4230,
        "distance_miles": 3.8,
        "travel_time_min": 15,
        "price_flag": "paid",
        "kid_friendly": False,
        "indoor_outdoor": "outdoor",
        "rating": 4.6
    },
    {
        "place_id": "p_004",
        "name": "Lands End Trail",
        "category": "parks",
        "address": "San Francisco, CA",
        "lat": 37.7878,
        "lng": -122.5062,
        "distance_miles": 4.1,
        "travel_time_min": 12,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.9
    },
    {
        "place_id": "p_005",
        "name": "California Academy of Sciences",
        "category": "museums",
        "address": "Golden Gate Park, San Francisco, CA",
        "lat": 37.7699,
        "lng": -122.4661,
        "distance_miles": 2.8,
        "travel_time_min": 11,
        "price_flag": "paid",
        "kid_friendly": True,
        "indoor_outdoor": "indoor",
        "rating": 4.8
    },
    {
        "place_id": "p_006",
        "name": "Fisherman's Wharf",
        "category": "attractions",
        "address": "San Francisco, CA",
        "lat": 37.8080,
        "lng": -122.4177,
        "distance_miles": 5.5,
        "travel_time_min": 20,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.5
    },
    {
        "place_id": "p_007",
        "name": "Twin Peaks",
        "category": "parks",
        "address": "San Francisco, CA",
        "lat": 37.7544,
        "lng": -122.4477,
        "distance_miles": 3.2,
        "travel_time_min": 14,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.7
    },
    {
        "place_id": "p_008",
        "name": "SFMOMA",
        "category": "museums",
        "address": "151 3rd St, San Francisco, CA",
        "lat": 37.7857,
        "lng": -122.4011,
        "distance_miles": 4.8,
        "travel_time_min": 16,
        "price_flag": "paid",
        "kid_friendly": False,
        "indoor_outdoor": "indoor",
        "rating": 4.6
    },
    {
        "place_id": "p_009",
        "name": "Baker Beach",
        "category": "parks",
        "address": "San Francisco, CA",
        "lat": 37.7936,
        "lng": -122.4833,
        "distance_miles": 3.9,
        "travel_time_min": 13,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.6
    },
    {
        "place_id": "p_010",
        "name": "Japanese Tea Garden",
        "category": "parks",
        "address": "Golden Gate Park, San Francisco, CA",
        "lat": 37.7702,
        "lng": -122.4701,
        "distance_miles": 2.6,
        "travel_time_min": 10,
        "price_flag": "paid",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.7
    }
]

def get_user_id():
    """Get current user ID from session or header"""
    # Try session first (for cookie-based auth)
    user_id = session.get('user_id')
    if user_id:
        return user_id
    # Try header (for API-based auth)
    user_id = request.headers.get('X-User-Id')
    if user_id:
        return user_id
    # Default to demo user for development
    return 'demo_user'

def require_auth(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For demo, always allow - in production, check auth properly
        return f(*args, **kwargs)
    return decorated_function

# ========== PREFERENCES ==========

@app.route('/v1/preferences', methods=['GET'])
@require_auth
def get_preferences():
    """Get user preferences"""
    user_id = get_user_id()
    prefs = preferences_db.get(user_id)
    if not prefs:
        # Return defaults if no preferences set
        prefs = {
            "home_location": {"type": "city", "value": "San Francisco, CA"},
            "radius_miles": 10,
            "categories": ["parks", "museums", "attractions"],
            "kid_friendly": True,
            "budget": {"min": 0, "max": 50},
            "time_windows": ["SAT_AM", "SAT_PM", "SUN_AM", "SUN_PM"],
            "notification_time_local": "16:00",
            "dedup_window_days": 365,
            "calendar_dedup_opt_in": False
        }
    return jsonify(prefs)

@app.route('/v1/preferences', methods=['PUT'])
@require_auth
def update_preferences():
    """Update user preferences"""
    user_id = get_user_id()
    data = request.json
    print(f"[DEBUG] Updating preferences for user {user_id}: {data}")
    preferences_db[user_id] = data
    print(f"[DEBUG] Preferences saved. Categories: {data.get('categories', [])}")
    return jsonify({"status": "updated", "preferences": data})

# ========== RECOMMENDATIONS ==========

def should_dedup(place_id, user_id, prefs):
    """Check if a place should be deduplicated"""
    # Check explicit "already been"
    visited = visited_history_db.get(user_id, [])
    for visit in visited:
        if visit['place_id'] == place_id:
            visited_at = datetime.fromisoformat(visit['visited_at'])
            dedup_window = timedelta(days=prefs.get('dedup_window_days', 365))
            if datetime.now() - visited_at < dedup_window:
                return True
    
    # Check recently recommended (last 4 weeks)
    recent = recent_recommendations_db.get(user_id, [])
    four_weeks_ago = datetime.now() - timedelta(weeks=4)
    for rec in recent:
        if rec.get('place_id') == place_id:
            rec_at = datetime.fromisoformat(rec['recommended_at'])
            if rec_at > four_weeks_ago:
                return True
    
    return False

def filter_places(prefs, user_id):
    """Filter and rank places based on preferences"""
    filtered = []
    categories = prefs.get('categories', [])
    # If no categories specified, show all
    show_all_categories = len(categories) == 0
    
    print(f"[DEBUG] Filtering places - categories: {categories}, show_all: {show_all_categories}")
    print(f"[DEBUG] Total places to filter: {len(MOCK_PLACES)}")
    
    for place in MOCK_PLACES:
        # Hard filters
        if place['distance_miles'] > prefs.get('radius_miles', 10):
            print(f"[DEBUG] Filtered out {place['name']}: distance {place['distance_miles']} > {prefs.get('radius_miles', 10)}")
            continue
        
        # Category filter - only apply if categories are specified
        if not show_all_categories and place['category'] not in categories:
            print(f"[DEBUG] Filtered out {place['name']}: category {place['category']} not in {categories}")
            continue
        
        # Kid-friendly filter - only apply if explicitly requested
        if prefs.get('kid_friendly') is True and not place.get('kid_friendly'):
            print(f"[DEBUG] Filtered out {place['name']}: not kid-friendly")
            continue
        
        # Dedup check
        if should_dedup(place['place_id'], user_id, prefs):
            print(f"[DEBUG] Filtered out {place['name']}: already visited/recommended")
            continue
        
        filtered.append(place)
        print(f"[DEBUG] Included {place['name']} ({place['category']})")
    
    # Sort by rating and distance
    filtered.sort(key=lambda x: (x['rating'], -x['distance_miles']), reverse=True)
    
    # Diversity: max 2 per category
    result = []
    category_counts = {}
    for place in filtered:
        cat = place['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if category_counts[cat] <= 2:
            result.append(place)
        if len(result) >= 8:
            break
    
    # If no results and we have categories, try relaxing filters
    if len(result) == 0 and len(categories) > 0:
        print(f"[DEBUG] No results with strict filters, trying relaxed filters...")
        # Try without category filter
        for place in MOCK_PLACES:
            if place['distance_miles'] > prefs.get('radius_miles', 10) * 1.5:  # Increase radius
                continue
            if prefs.get('kid_friendly') is True and not place.get('kid_friendly'):
                continue
            if should_dedup(place['place_id'], user_id, prefs):
                continue
            if place not in result:
                result.append(place)
            if len(result) >= 8:
                break
    
    print(f"[DEBUG] Final result count: {len(result)}")
    return result

@app.route('/v1/digest', methods=['GET'])
@require_auth
def get_digest():
    """Get weekend digest for current week"""
    user_id = get_user_id()
    prefs = preferences_db.get(user_id, {})
    
    # Use defaults if no preferences set
    if not prefs:
        prefs = {
            "home_location": {"type": "city", "value": "San Francisco, CA"},
            "radius_miles": 10,
            "categories": ["parks", "museums", "attractions"],
            "kid_friendly": True,
            "budget": {"min": 0, "max": 50},
            "time_windows": ["SAT_AM", "SAT_PM", "SUN_AM", "SUN_PM"],
            "notification_time_local": "16:00",
            "dedup_window_days": 365,
            "calendar_dedup_opt_in": False
        }
    
    # Debug logging
    print(f"[DEBUG] User ID: {user_id}")
    print(f"[DEBUG] Preferences: {prefs}")
    print(f"[DEBUG] Categories: {prefs.get('categories', [])}")
    
    # Get current week
    now = datetime.now()
    week = f"{now.year}-{now.isocalendar()[1]:02d}"
    
    # Filter and rank places
    places = filter_places(prefs, user_id)
    print(f"[DEBUG] Filtered places count: {len(places)}")
    
    # Format recommendations
    items = []
    for i, place in enumerate(places):
        rec_id = f"r_{user_id}_{week}_{i}"
        items.append({
            "rec_id": rec_id,
            "type": "place",
            "place_id": place['place_id'],
            "title": place['name'],
            "category": place['category'],
            "distance_miles": place['distance_miles'],
            "travel_time_min": place['travel_time_min'],
            "price_flag": place['price_flag'],
            "kid_friendly": place['kid_friendly'],
            "indoor_outdoor": place['indoor_outdoor'],
            "explanation": f"Because you like {place['category']} and it's {place['travel_time_min']} min away",
            "source_url": f"https://maps.google.com/?q={place['lat']},{place['lng']}",
            "address": place['address'],
            "rating": place['rating']
        })
        
        # Track as recently recommended
        if user_id not in recent_recommendations_db:
            recent_recommendations_db[user_id] = []
        recent_recommendations_db[user_id].append({
            "place_id": place['place_id'],
            "rec_id": rec_id,
            "recommended_at": datetime.now().isoformat(),
            "week": week
        })
    
    response_data = {
        "week": week,
        "generated_at": datetime.now().isoformat(),
        "items": items
    }
    
    print(f"[DEBUG] Returning {len(items)} items")
    if len(items) == 0:
        print(f"[DEBUG] WARNING: No items to return!")
        print(f"[DEBUG] Available categories in MOCK_PLACES: {set(p['category'] for p in MOCK_PLACES)}")
        print(f"[DEBUG] Requested categories: {prefs.get('categories', [])}")
    
    return jsonify(response_data)

@app.route('/v1/feedback', methods=['POST'])
@require_auth
def submit_feedback():
    """Submit feedback on a recommendation"""
    user_id = get_user_id()
    data = request.json
    rec_id = data.get('rec_id')
    action = data.get('action')
    
    if not rec_id or not action:
        return jsonify({"error": "Missing rec_id or action"}), 400
    
    # Store feedback
    if user_id not in feedback_db:
        feedback_db[user_id] = []
    feedback_db[user_id].append({
        "rec_id": rec_id,
        "action": action,
        "created_at": datetime.now().isoformat(),
        "metadata": data.get('metadata', {})
    })
    
    # Handle "already_been" action
    if action == "already_been":
        # Find the place_id from the recommendation
        week = data.get('metadata', {}).get('week', '')
        for rec in recent_recommendations_db.get(user_id, []):
            if rec['rec_id'] == rec_id:
                place_id = rec['place_id']
                if user_id not in visited_history_db:
                    visited_history_db[user_id] = []
                visited_history_db[user_id].append({
                    "place_id": place_id,
                    "visited_at": datetime.now().isoformat(),
                    "signal_type": "manual",
                    "confidence": 1.0
                })
                break
    
    return jsonify({"status": "recorded"})

# ========== VISITED HISTORY ==========

@app.route('/v1/visited', methods=['GET'])
@require_auth
def get_visited():
    """Get visited places"""
    user_id = get_user_id()
    visited = visited_history_db.get(user_id, [])
    return jsonify({"visited": visited})

@app.route('/v1/visited', methods=['POST'])
@require_auth
def add_visited():
    """Manually add a visited place"""
    user_id = get_user_id()
    data = request.json
    place_id = data.get('place_id')
    
    if not place_id:
        return jsonify({"error": "Missing place_id"}), 400
    
    if user_id not in visited_history_db:
        visited_history_db[user_id] = []
    
    visited_history_db[user_id].append({
        "place_id": place_id,
        "visited_at": data.get('visited_at', datetime.now().isoformat()),
        "signal_type": data.get('signal_type', 'manual'),
        "confidence": data.get('confidence', 1.0)
    })
    
    return jsonify({"status": "added"})

@app.route('/v1/visited/<place_id>', methods=['DELETE'])
@require_auth
def remove_visited(place_id):
    """Remove a visited place"""
    user_id = get_user_id()
    if user_id in visited_history_db:
        visited_history_db[user_id] = [
            v for v in visited_history_db[user_id]
            if v['place_id'] != place_id
        ]
    return jsonify({"status": "removed"})

# ========== CALENDAR HELPERS ==========

@app.route('/v1/calendar/event_template', methods=['POST'])
@require_auth
def get_event_template():
    """Generate calendar event template"""
    user_id = get_user_id()
    data = request.json
    rec_id = data.get('rec_id')
    slot = data.get('slot', 'SAT_AM')
    timezone = data.get('timezone', 'America/Los_Angeles')
    
    # Find the recommendation
    place = None
    for p in MOCK_PLACES:
        # In real implementation, look up by rec_id
        if rec_id:
            place = p  # Simplified: use first match
            break
    
    if not place:
        return jsonify({"error": "Recommendation not found"}), 404
    
    # Calculate time based on slot
    now = datetime.now()
    # Find next Saturday
    days_until_saturday = (5 - now.weekday()) % 7
    if days_until_saturday == 0 and now.hour >= 12:
        days_until_saturday = 7
    saturday = now + timedelta(days=days_until_saturday)
    saturday = saturday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if slot == "SAT_AM":
        start_time = saturday.replace(hour=10, minute=0)
        end_time = saturday.replace(hour=12, minute=0)
    elif slot == "SAT_PM":
        start_time = saturday.replace(hour=14, minute=0)
        end_time = saturday.replace(hour=16, minute=0)
    elif slot == "SUN_AM":
        sunday = saturday + timedelta(days=1)
        start_time = sunday.replace(hour=10, minute=0)
        end_time = sunday.replace(hour=12, minute=0)
    elif slot == "SUN_PM":
        sunday = saturday + timedelta(days=1)
        start_time = sunday.replace(hour=14, minute=0)
        end_time = sunday.replace(hour=16, minute=0)
    else:
        # Default to SAT_AM
        start_time = saturday.replace(hour=10, minute=0)
        end_time = saturday.replace(hour=12, minute=0)
    
    event = {
        "summary": f"{place['name']} — Weekend Plan",
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": timezone
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": timezone
        },
        "location": place['address'],
        "description": f"{place['name']} - {place.get('category', 'activity')}\n\n"
                      f"Recommended because: {place.get('explanation', 'Weekend activity')}\n"
                      f"Distance: {place['distance_miles']} miles ({place['travel_time_min']} min)\n"
                      f"Price: {place['price_flag']}\n"
                      f"Kid-friendly: {'Yes' if place.get('kid_friendly') else 'No'}\n\n"
                      f"View on map: {place.get('source_url', '')}"
    }
    
    return jsonify(event)

# ========== NOTIFICATIONS ==========

@app.route('/v1/notifications/test', methods=['POST'])
@require_auth
def send_test_notification():
    """Send a test digest preview"""
    # In production, this would send an email
    return jsonify({"status": "test_sent", "message": "Test notification would be sent here"})

@app.route('/v1/notifications/pause', methods=['POST'])
@require_auth
def pause_notifications():
    """Pause or resume weekly digests"""
    user_id = get_user_id()
    data = request.json
    paused = data.get('paused', False)
    # Store pause state (in production, store in user preferences)
    return jsonify({"status": "paused" if paused else "resumed"})

# ========== AUTH ==========

# Simple token storage (use proper JWT in production)
auth_tokens = {}

@app.route('/v1/auth/signup', methods=['POST'])
def signup():
    """Create a new user account"""
    data = request.json
    method = data.get('method', 'email')
    
    if method == 'email':
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        
        # Check if user exists
        if email in users_db:
            return jsonify({"error": "User already exists"}), 409
        
        # Create user
        user_id = f"user_{len(users_db) + 1}_{datetime.now().timestamp()}"
        users_db[email] = {
            "user_id": user_id,
            "email": email,
            "password": password,  # In production, hash this!
            "created_at": datetime.now().isoformat(),
            "email_digest": data.get('email_digest', True)
        }
        
        # Create token
        token = f"token_{user_id}_{datetime.now().timestamp()}"
        auth_tokens[token] = user_id
        
        return jsonify({
            "user_id": user_id,
            "token": token,
            "status": "created"
        })
    
    return jsonify({"error": "Invalid auth method"}), 400

@app.route('/v1/auth/login', methods=['POST'])
def login():
    """Login with email/password"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    # Check credentials
    user = users_db.get(email)
    if not user or user.get('password') != password:
        return jsonify({"error": "Invalid credentials"}), 401
    
    user_id = user['user_id']
    
    # Create token
    token = f"token_{user_id}_{datetime.now().timestamp()}"
    auth_tokens[token] = user_id
    
    # Get preferences
    prefs = preferences_db.get(user_id)
    
    return jsonify({
        "user_id": user_id,
        "token": token,
        "preferences": prefs,
        "status": "authenticated"
    })

@app.route('/v1/auth/phone/request-otp', methods=['POST'])
def request_phone_otp():
    """Request OTP for phone authentication"""
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    # In production, send actual SMS
    # For demo, just return success
    return jsonify({"status": "otp_sent", "message": "Verification code sent"})

@app.route('/v1/auth/phone/verify-otp', methods=['POST'])
def verify_phone_otp():
    """Verify OTP and authenticate"""
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    
    if not phone or not code:
        return jsonify({"error": "Phone and code required"}), 400
    
    # For demo, accept any 6-digit code or '123456'
    if code != '123456' and len(code) != 6:
        return jsonify({"error": "Invalid code"}), 401
    
    # Find or create user
    is_new_user = phone not in users_db
    
    if is_new_user:
        user_id = f"user_phone_{len(users_db) + 1}_{datetime.now().timestamp()}"
        users_db[phone] = {
            "user_id": user_id,
            "phone": phone,
            "created_at": datetime.now().isoformat()
        }
    else:
        user_id = users_db[phone]['user_id']
    
    # Create token
    token = f"token_{user_id}_{datetime.now().timestamp()}"
    auth_tokens[token] = user_id
    
    # Get preferences
    prefs = preferences_db.get(user_id)
    
    return jsonify({
        "user_id": user_id,
        "token": token,
        "is_new_user": is_new_user,
        "preferences": prefs,
        "status": "authenticated"
    })

@app.route('/v1/auth/logout', methods=['POST'])
def logout():
    """Logout and invalidate token"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token in auth_tokens:
            del auth_tokens[token]
    
    session.clear()
    return jsonify({"status": "logged_out"})

@app.route('/v1/auth/session', methods=['POST'])
def create_session():
    """Create a demo session (replace with OAuth in production)"""
    data = request.json
    user_id = data.get('user_id', 'demo_user')
    session['user_id'] = user_id
    return jsonify({"user_id": user_id, "status": "authenticated"})

@app.route('/v1/auth/session', methods=['GET'])
def get_session():
    """Get current session"""
    user_id = get_user_id()
    return jsonify({"user_id": user_id, "authenticated": bool(user_id)})

# ========== USER PROFILE & PREFERENCES ==========

@app.route('/v1/user/preferences', methods=['GET'])
def get_user_preferences():
    """Get user profile and preferences (for returning users)"""
    auth_header = request.headers.get('Authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user_id = auth_tokens.get(token)
        
        if not user_id:
            return jsonify({"error": "Invalid token"}), 401
        
        # Get user info
        user_info = None
        for identifier, user in users_db.items():
            if user.get('user_id') == user_id:
                user_info = {
                    "id": user_id,
                    "email": user.get('email'),
                    "phone": user.get('phone')
                }
                break
        
        # Get preferences
        prefs = preferences_db.get(user_id, {})
        
        return jsonify({
            "user": user_info,
            "preferences": prefs
        })
    
    return jsonify({"error": "Authorization required"}), 401

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "weekend-planner-api"})

if __name__ == '__main__':
    print("=" * 50)
    print("Weekend Planner Backend API")
    print("=" * 50)
    print("Server starting on http://localhost:5001")
    print("API endpoints available at http://localhost:5001/v1")
    print("Health check: http://localhost:5001/health")
    print("=" * 50)
    app.run(debug=True, port=5001, host='0.0.0.0')
