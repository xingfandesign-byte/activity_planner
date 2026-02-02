"""
Weekend Planner Backend API
Calendar-first V1 implementation
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import requests
import hashlib
import secrets
from functools import wraps


def hash_password(password, salt=None):
    """Hash a password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(password, stored_hash):
    """Verify a password against stored hash"""
    try:
        salt, hash_value = stored_hash.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return new_hash.hex() == hash_value
    except:
        # Fallback for plain text passwords (migration)
        return password == stored_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# Google Places API Configuration
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
GOOGLE_PLACES_BASE_URL = 'https://maps.googleapis.com/maps/api/place'

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5001/v1/auth/google/callback')

# Cache for API responses (simple in-memory cache)
places_cache = {}

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

def get_user_id_from_token(token):
    """Extract user ID from auth token"""
    token_data = auth_tokens.get(token)
    if token_data is None:
        return None
    # Handle both old format (string) and new format (dict)
    if isinstance(token_data, dict):
        return token_data.get('user_id')
    return token_data  # Old format: token_data is the user_id string


def get_user_id():
    """Get current user ID from session or header"""
    # Try session first (for cookie-based auth)
    user_id = session.get('user_id')
    if user_id:
        return user_id
    # Try Authorization header with Bearer token
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user_id = get_user_id_from_token(token)
        if user_id:
            return user_id
    # Try X-User-Id header (for API-based auth)
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

# ========== GOOGLE PLACES API INTEGRATION ==========

def search_google_places(location, category, radius_meters=10000):
    """Search for places using Google Places API"""
    if not GOOGLE_PLACES_API_KEY:
        print("[PLACES API] No API key configured, using mock data")
        return None
    
    # Map our categories to Google Places types
    category_to_type = {
        'parks': 'park',
        'museums': 'museum',
        'food': 'restaurant',
        'attractions': 'tourist_attraction',
        'events': 'event_venue',
        'shopping': 'shopping_mall',
        'entertainment': 'movie_theater',
        'nature': 'natural_feature'
    }
    
    place_type = category_to_type.get(category, 'point_of_interest')
    
    # Create cache key
    cache_key = f"{location.get('lat', 0)}_{location.get('lng', 0)}_{category}_{radius_meters}"
    
    # Check cache (expires after 1 hour)
    if cache_key in places_cache:
        cached = places_cache[cache_key]
        if (datetime.now() - cached['timestamp']).seconds < 3600:
            print(f"[PLACES API] Cache hit for {category}")
            return cached['data']
    
    try:
        # Nearby Search request
        url = f"{GOOGLE_PLACES_BASE_URL}/nearbysearch/json"
        params = {
            'location': f"{location.get('lat', 37.7749)},{location.get('lng', -122.4194)}",
            'radius': radius_meters,
            'type': place_type,
            'key': GOOGLE_PLACES_API_KEY
        }
        
        print(f"[PLACES API] Searching for {category} near {params['location']}")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK':
            places = data.get('results', [])
            print(f"[PLACES API] Found {len(places)} {category} places")
            
            # Cache the result
            places_cache[cache_key] = {
                'data': places,
                'timestamp': datetime.now()
            }
            
            return places
        else:
            print(f"[PLACES API] Error: {data.get('status')} - {data.get('error_message', '')}")
            return None
            
    except Exception as e:
        print(f"[PLACES API] Exception: {str(e)}")
        return None


def get_place_details(place_id):
    """Get detailed information about a place"""
    if not GOOGLE_PLACES_API_KEY:
        return None
    
    # Check cache
    cache_key = f"detail_{place_id}"
    if cache_key in places_cache:
        cached = places_cache[cache_key]
        if (datetime.now() - cached['timestamp']).seconds < 86400:  # 24 hour cache
            return cached['data']
    
    try:
        url = f"{GOOGLE_PLACES_BASE_URL}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry,rating,price_level,opening_hours,photos,types,user_ratings_total,website,formatted_phone_number',
            'key': GOOGLE_PLACES_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK':
            result = data.get('result', {})
            places_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            return result
        
        return None
        
    except Exception as e:
        print(f"[PLACES API] Details exception: {str(e)}")
        return None


def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in miles (using Haversine formula)"""
    import math
    
    R = 3959  # Earth's radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def convert_google_place_to_item(place, user_location, index):
    """Convert Google Places API result to our recommendation format"""
    
    # Extract location
    geometry = place.get('geometry', {})
    location = geometry.get('location', {})
    place_lat = location.get('lat', 0)
    place_lng = location.get('lng', 0)
    
    # Calculate distance
    user_lat = user_location.get('lat', 37.7749)
    user_lng = user_location.get('lng', -122.4194)
    distance = calculate_distance(user_lat, user_lng, place_lat, place_lng)
    
    # Estimate travel time (rough: 2 min per mile for driving)
    travel_time = max(5, int(distance * 2))
    
    # Get price level
    price_level = place.get('price_level', 1)
    price_flags = {0: 'free', 1: '$', 2: '$$', 3: '$$$', 4: '$$$$'}
    price_flag = price_flags.get(price_level, '$')
    
    # Determine category from types
    types = place.get('types', [])
    category = 'attractions'
    if 'park' in types or 'natural_feature' in types:
        category = 'parks'
    elif 'museum' in types or 'art_gallery' in types:
        category = 'museums'
    elif 'restaurant' in types or 'food' in types or 'cafe' in types:
        category = 'food'
    elif 'shopping_mall' in types or 'store' in types:
        category = 'shopping'
    
    # Check if kid-friendly (heuristic based on types)
    kid_friendly = any(t in types for t in ['park', 'zoo', 'aquarium', 'amusement_park', 'museum'])
    
    # Indoor/outdoor
    outdoor_types = ['park', 'natural_feature', 'zoo', 'stadium', 'campground']
    indoor_outdoor = 'outdoor' if any(t in types for t in outdoor_types) else 'indoor'
    
    # Get photo URL if available
    photos = place.get('photos', [])
    photo_url = None
    if photos and GOOGLE_PLACES_API_KEY:
        photo_ref = photos[0].get('photo_reference')
        if photo_ref:
            photo_url = f"{GOOGLE_PLACES_BASE_URL}/photo?maxwidth=400&photo_reference={photo_ref}&key={GOOGLE_PLACES_API_KEY}"
    
    now = datetime.now()
    week = f"{now.year}-{now.isocalendar()[1]:02d}"
    
    return {
        "rec_id": f"gp_{week}_{index}",
        "type": "place",
        "place_id": place.get('place_id', ''),
        "title": place.get('name', 'Unknown Place'),
        "category": category,
        "distance_miles": round(distance, 1),
        "travel_time_min": travel_time,
        "price_flag": price_flag,
        "kid_friendly": kid_friendly,
        "indoor_outdoor": indoor_outdoor,
        "explanation": f"Highly rated {category} spot nearby",
        "source_url": f"https://maps.google.com/?q={place_lat},{place_lng}",
        "address": place.get('vicinity', place.get('formatted_address', '')),
        "rating": place.get('rating', 4.0),
        "total_ratings": place.get('user_ratings_total', 0),
        "photo_url": photo_url,
        "google_place": True
    }


@app.route('/v1/places/search', methods=['POST'])
def search_places():
    """Search for places using Google Places API"""
    data = request.json
    location = data.get('location', {'lat': 37.7749, 'lng': -122.4194})
    categories = data.get('categories', ['parks', 'museums', 'food'])
    radius = data.get('radius_meters', 10000)
    
    all_places = []
    
    for category in categories:
        places = search_google_places(location, category, radius)
        if places:
            for i, place in enumerate(places[:5]):  # Limit to 5 per category
                item = convert_google_place_to_item(place, location, len(all_places))
                all_places.append(item)
    
    # Sort by rating
    all_places.sort(key=lambda x: (x.get('rating', 0), -x.get('distance_miles', 100)), reverse=True)
    
    return jsonify({
        "places": all_places[:10],  # Return top 10
        "total": len(all_places),
        "source": "google_places" if GOOGLE_PLACES_API_KEY else "mock_data"
    })


# ========== AI-POWERED RECOMMENDATIONS ==========

@app.route('/v1/recommendations/ai', methods=['POST'])
def get_ai_recommendations():
    """Get AI-powered recommendations based on user profile"""
    data = request.json
    profile = data.get('profile', {})
    prompt = data.get('prompt', '')
    use_google_places = data.get('use_google_places', True)
    
    print(f"[AI] Received recommendation request")
    print(f"[AI] User profile: {json.dumps(profile, indent=2)}")
    print(f"[AI] Prompt length: {len(prompt)} chars")
    print(f"[AI] Use Google Places: {use_google_places}")
    
    items = []
    source = "mock_data"
    
    # Try Google Places API first if enabled and configured
    if use_google_places and GOOGLE_PLACES_API_KEY:
        print("[AI] Attempting to use Google Places API")
        items = generate_recommendations_from_google_places(profile)
        if items:
            source = "google_places"
            print(f"[AI] Got {len(items)} recommendations from Google Places")
    
    # Fall back to mock data if Google Places didn't work
    if not items:
        print("[AI] Using mock data for recommendations")
        items = generate_personalized_recommendations(profile)
        source = "mock_data"
    
    response_data = {
        "week": f"{datetime.now().year}-{datetime.now().isocalendar()[1]:02d}",
        "generated_at": datetime.now().isoformat(),
        "ai_powered": True,
        "source": source,
        "items": items
    }
    
    return jsonify(response_data)


def generate_recommendations_from_google_places(profile):
    """Generate recommendations using Google Places API"""
    
    location = profile.get('location', {})
    interests = profile.get('interests', [])
    travel_times = profile.get('travel_time_ranges', ['15-30'])
    kid_friendly = profile.get('kid_friendly', False)
    budget = profile.get('budget', 'moderate')
    
    # Map interests to Google Places categories
    interest_to_category = {
        'nature': 'parks',
        'arts_culture': 'museums',
        'food_drinks': 'food',
        'adventure': 'attractions',
        'learning': 'museums',
        'entertainment': 'entertainment',
        'relaxation': 'parks',
        'shopping': 'shopping',
        'events': 'attractions'
    }
    
    categories = list(set([interest_to_category.get(i, 'attractions') for i in interests]))
    if not categories:
        categories = ['parks', 'museums', 'food']
    
    # Determine search radius based on travel time
    max_travel = 30
    if '60+' in travel_times:
        max_travel = 90
    elif '30-60' in travel_times:
        max_travel = 60
    elif '15-30' in travel_times:
        max_travel = 30
    elif '0-15' in travel_times:
        max_travel = 15
    
    # Convert travel time to approximate radius in meters (assuming ~30 mph average)
    radius_meters = int(max_travel * 0.5 * 1609)  # half of max travel time at 30mph, converted to meters
    radius_meters = min(radius_meters, 50000)  # Max 50km radius
    
    all_places = []
    
    # Search for each category
    for category in categories[:3]:  # Limit to 3 categories
        places = search_google_places(location, category, radius_meters)
        if places:
            for place in places[:5]:  # Top 5 per category
                item = convert_google_place_to_item(place, location, len(all_places))
                
                # Apply filters
                if kid_friendly and not item.get('kid_friendly'):
                    continue
                
                # Budget filter
                if budget == 'free' and item.get('price_flag') != 'free':
                    continue
                
                # Add personalized explanation
                item['explanation'] = generate_explanation_for_google_place(item, profile)
                
                all_places.append(item)
    
    # Sort by relevance (rating + proximity)
    all_places.sort(key=lambda x: (x.get('rating', 0) * 2 - x.get('distance_miles', 10) * 0.1), reverse=True)
    
    return all_places[:5]  # Return top 5


def generate_explanation_for_google_place(place, profile):
    """Generate a personalized explanation for a Google Place"""
    
    group_type = profile.get('group_type', 'solo')
    
    group_phrases = {
        'solo': "Perfect for solo exploration",
        'couple': "Great spot for a date",
        'family': "Family-friendly destination",
        'friends': "Fun place to hang out"
    }
    
    parts = [group_phrases.get(group_type, "Recommended for you")]
    
    rating = place.get('rating', 0)
    if rating >= 4.5:
        parts.append(f"★ {rating} highly rated")
    elif rating >= 4.0:
        parts.append(f"★ {rating} well reviewed")
    
    distance = place.get('distance_miles', 0)
    if distance <= 5:
        parts.append(f"just {place.get('travel_time_min', 10)} min away")
    else:
        parts.append(f"{int(distance)} miles away")
    
    if place.get('price_flag') == 'free':
        parts.append("and it's free!")
    
    return " — ".join(parts)


def generate_personalized_recommendations(profile):
    """Generate recommendations based on user profile"""
    
    # Extract profile data with defaults
    location = profile.get('location', {})
    group_type = profile.get('group_type', 'solo')
    interests = profile.get('interests', [])
    energy_level = profile.get('energy_level', 'moderate')
    budget = profile.get('budget', 'moderate')
    travel_times = profile.get('travel_time_ranges', ['15-30'])
    kid_friendly = profile.get('kid_friendly', False)
    avoid = profile.get('avoid', [])
    
    # Map interests to categories
    interest_to_category = {
        'nature': 'parks',
        'arts_culture': 'museums',
        'food_drinks': 'food',
        'adventure': 'attractions',
        'learning': 'museums',
        'entertainment': 'attractions',
        'relaxation': 'parks',
        'shopping': 'attractions',
        'events': 'events'
    }
    
    target_categories = list(set([interest_to_category.get(i, 'attractions') for i in interests]))
    if not target_categories:
        target_categories = ['parks', 'museums', 'attractions']
    
    # Get max travel time
    max_travel = 30  # default
    if '60+' in travel_times:
        max_travel = 90
    elif '30-60' in travel_times:
        max_travel = 60
    elif '15-30' in travel_times:
        max_travel = 30
    elif '0-15' in travel_times:
        max_travel = 15
    
    # Budget filter
    budget_filters = {
        'free': ['free'],
        'low': ['free', 'paid'],
        'moderate': ['free', 'paid'],
        'any': ['free', 'paid']
    }
    allowed_prices = budget_filters.get(budget, ['free', 'paid'])
    
    # Filter places based on profile
    filtered_places = []
    for place in MOCK_PLACES:
        # Category match
        if place['category'] not in target_categories:
            continue
        
        # Travel time filter
        if place['travel_time_min'] > max_travel:
            continue
        
        # Budget filter
        if place['price_flag'] not in allowed_prices:
            continue
        
        # Kid-friendly filter
        if kid_friendly and not place.get('kid_friendly', False):
            continue
        
        # Avoid crowds filter
        if 'crowds' in avoid and place.get('crowded', False):
            continue
        
        filtered_places.append(place)
    
    # Sort by relevance (matching interests first, then by travel time)
    def relevance_score(p):
        score = 0
        # Interest match bonus
        if p['category'] in [interest_to_category.get(i) for i in interests]:
            score += 10
        # Closer is better
        score -= p['travel_time_min'] / 10
        # Rating bonus
        score += p.get('rating', 4) * 2
        return score
    
    filtered_places.sort(key=relevance_score, reverse=True)
    
    # Take top 5
    top_places = filtered_places[:5]
    
    # If not enough, add some fallbacks
    if len(top_places) < 5:
        for place in MOCK_PLACES:
            if place not in top_places:
                top_places.append(place)
            if len(top_places) >= 5:
                break
    
    # Generate personalized explanations
    items = []
    now = datetime.now()
    week = f"{now.year}-{now.isocalendar()[1]:02d}"
    
    for i, place in enumerate(top_places):
        explanation = generate_explanation(place, profile, interests)
        
        items.append({
            "rec_id": f"ai_{week}_{i}",
            "type": "place",
            "place_id": place['place_id'],
            "title": place['name'],
            "category": place['category'],
            "distance_miles": place['distance_miles'],
            "travel_time_min": place['travel_time_min'],
            "price_flag": place['price_flag'],
            "kid_friendly": place.get('kid_friendly', False),
            "indoor_outdoor": place.get('indoor_outdoor', 'outdoor'),
            "explanation": explanation,
            "source_url": f"https://maps.google.com/?q={place['lat']},{place['lng']}",
            "address": place['address'],
            "rating": place.get('rating', 4.0),
            "ai_matched": True
        })
    
    return items


def generate_explanation(place, profile, interests):
    """Generate a personalized explanation for why this place is recommended"""
    
    group_type = profile.get('group_type', 'solo')
    energy_level = profile.get('energy_level', 'moderate')
    
    # Group-specific language
    group_phrases = {
        'solo': "Perfect for a solo adventure",
        'couple': "Great for a romantic outing",
        'family': "Fun for the whole family",
        'friends': "Awesome spot to hang with friends"
    }
    
    # Energy-specific language
    energy_phrases = {
        'relaxing': "relaxed atmosphere",
        'moderate': "nice mix of exploration and downtime",
        'active': "plenty of activities to keep you moving"
    }
    
    # Category-specific benefits
    category_benefits = {
        'parks': "enjoy nature and fresh air",
        'museums': "discover something new and interesting",
        'food': "treat yourself to great food",
        'attractions': "have an exciting experience",
        'events': "join a fun local event"
    }
    
    # Build explanation
    parts = []
    
    # Group phrase
    if group_type in group_phrases:
        parts.append(group_phrases[group_type])
    
    # Travel time
    if place['travel_time_min'] <= 15:
        parts.append(f"just {place['travel_time_min']} minutes away")
    else:
        parts.append(f"only {place['travel_time_min']} min drive")
    
    # Category benefit
    cat = place['category']
    if cat in category_benefits:
        parts.append(category_benefits[cat])
    
    # Price mention
    if place['price_flag'] == 'free':
        parts.append("and it's free!")
    
    # Kid-friendly mention
    if place.get('kid_friendly') and group_type == 'family':
        parts.append("Kids will love it!")
    
    # Join parts
    if len(parts) >= 3:
        return f"{parts[0]} — {parts[1]}, {parts[2]}"
    elif len(parts) == 2:
        return f"{parts[0]} — {parts[1]}"
    else:
        return f"Recommended based on your preferences"


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
        
        # Create user with hashed password
        user_id = f"user_{len(users_db) + 1}_{datetime.now().timestamp()}"
        users_db[email] = {
            "user_id": user_id,
            "email": email,
            "password": hash_password(password),
            "created_at": datetime.now().isoformat(),
            "email_digest": data.get('email_digest', True)
        }
        
        # Create secure token
        token = secrets.token_urlsafe(32)
        auth_tokens[token] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        
        print(f"[AUTH] New user created: {email}")
        
        return jsonify({
            "user_id": user_id,
            "email": email,
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
    if not user or not verify_password(password, user.get('password', '')):
        return jsonify({"error": "Invalid email or password"}), 401
    
    user_id = user['user_id']
    
    # Create secure token
    token = secrets.token_urlsafe(32)
    auth_tokens[token] = {
        'user_id': user_id,
        'created_at': datetime.now().isoformat()
    }
    
    # Get preferences
    prefs = preferences_db.get(user_id)
    
    print(f"[AUTH] User logged in: {email}")
    
    return jsonify({
        "user_id": user_id,
        "email": email,
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
    
    # Create secure token
    token = secrets.token_urlsafe(32)
    auth_tokens[token] = {
        'user_id': user_id,
        'created_at': datetime.now().isoformat()
    }
    
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


# ========== GOOGLE OAUTH ==========

@app.route('/v1/auth/google/url', methods=['GET'])
def get_google_auth_url():
    """Get the Google OAuth authorization URL"""
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth not configured"}), 501
    
    # Generate a state token for CSRF protection
    import secrets
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build the Google OAuth URL
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + '&'.join(f'{k}={v}' for k, v in params.items())
    
    return jsonify({
        "url": auth_url,
        "configured": True
    })


@app.route('/v1/auth/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    from urllib.parse import urlencode
    
    error = request.args.get('error')
    if error:
        # Redirect to frontend with error
        return f'''
        <html><body>
        <script>
            window.opener.postMessage({{ type: 'oauth_error', error: '{error}' }}, '*');
            window.close();
        </script>
        </body></html>
        '''
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Verify state token
    stored_state = session.get('oauth_state')
    if not stored_state or state != stored_state:
        return f'''
        <html><body>
        <script>
            window.opener.postMessage({{ type: 'oauth_error', error: 'Invalid state token' }}, '*');
            window.close();
        </script>
        </body></html>
        '''
    
    # Exchange code for tokens
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        tokens = token_response.json()
        
        if 'error' in tokens:
            return f'''
            <html><body>
            <script>
                window.opener.postMessage({{ type: 'oauth_error', error: '{tokens.get("error_description", tokens["error"])}' }}, '*');
                window.close();
            </script>
            </body></html>
            '''
        
        access_token = tokens.get('access_token')
        
        # Get user info from Google
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        userinfo = userinfo_response.json()
        
        google_id = userinfo.get('id')
        email = userinfo.get('email')
        name = userinfo.get('name', '')
        picture = userinfo.get('picture', '')
        
        # Check if user exists, create if not
        user_id = f"google_{google_id}"
        
        if user_id not in users_db:
            users_db[user_id] = {
                'id': user_id,
                'email': email,
                'name': name,
                'picture': picture,
                'provider': 'google',
                'google_id': google_id,
                'created_at': datetime.now().isoformat()
            }
            print(f"[AUTH] Created new Google user: {email}")
        else:
            # Update user info
            users_db[user_id]['name'] = name
            users_db[user_id]['picture'] = picture
            print(f"[AUTH] Existing Google user logged in: {email}")
        
        # Generate auth token
        import secrets
        auth_token = secrets.token_urlsafe(32)
        auth_tokens[auth_token] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        
        # Store in session
        session['user_id'] = user_id
        
        # Send success message to opener window
        user_data = {
            'id': user_id,
            'email': email,
            'name': name,
            'picture': picture,
            'provider': 'google'
        }
        
        import json
        user_json = json.dumps(user_data).replace("'", "\\'")
        
        return f'''
        <html><body>
        <script>
            window.opener.postMessage({{
                type: 'oauth_success',
                token: '{auth_token}',
                user: {user_json}
            }}, '*');
            window.close();
        </script>
        </body></html>
        '''
        
    except Exception as e:
        print(f"[AUTH] Google OAuth error: {str(e)}")
        return f'''
        <html><body>
        <script>
            window.opener.postMessage({{ type: 'oauth_error', error: 'Authentication failed' }}, '*');
            window.close();
        </script>
        </body></html>
        '''


@app.route('/v1/auth/google/status', methods=['GET'])
def google_auth_status():
    """Check if Google OAuth is configured"""
    return jsonify({
        "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "client_id": GOOGLE_CLIENT_ID if GOOGLE_CLIENT_ID else None
    })


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
        user_id = get_user_id_from_token(token)
        
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
