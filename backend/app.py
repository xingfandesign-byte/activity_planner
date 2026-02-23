"""
Activity Planner Backend API
Calendar-first V1 implementation
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import requests
import hashlib
import hmac
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
# CORS: allow frontend origin for OAuth (credentials required for session cookie)
_cors_origins = ['http://localhost:8000', 'http://0.0.0.0:8000']
_furl = os.environ.get('FRONTEND_URL', '').rstrip('/')
if _furl:
    _cors_origins.append(_furl)
CORS(app, supports_credentials=True, origins=_cors_origins)

# Google Places API Configuration
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
GOOGLE_PLACES_BASE_URL = 'https://maps.googleapis.com/maps/api/place'

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5001/v1/auth/google/callback')

# Cache for API responses (simple in-memory cache)
places_cache = {}
# Cache for geocoding (ZIP/address -> lat,lng) to avoid repeated lookups
geocode_cache = {}
# Cache for image search (query -> url) to avoid hitting API limits
image_search_cache = {}
# In-memory warm cache for recommendations (key -> {items, sources, timestamp})
_warm_cache = {}
_warm_cache_lock = None  # Lazy-initialized threading lock
_background_refresh_in_progress = set()  # Track in-flight background refreshes

# Circuit breaker pattern for external APIs
_circuit_breakers = {}  # {source: {failures: int, last_failure: datetime, total_calls: int}}

# Image search: Google Custom Search, Pexels, Unsplash (keywords from title + event detail)
GOOGLE_CSE_API_KEY = os.environ.get('GOOGLE_CSE_API_KEY', '')
GOOGLE_CSE_CX = os.environ.get('GOOGLE_CSE_CX', '')  # Custom Search Engine ID with Image search enabled
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY', '')
UNSPLASH_ACCESS_KEY = os.environ.get('UNSPLASH_ACCESS_KEY', '')

# Database persistence (backend/db.py uses SQLite)
import db as _db
db = _db
db.init_db()

# Clean expired cache entries on startup
try:
    db.clean_expired_cache()
    print("[CACHE] Cleaned expired cache entries")
except Exception as e:
    print(f"[CACHE] Error cleaning cache: {e}")

# Local feeds (RSS, Facebook, Eventbrite) to complement Google Places
try:
    import local_feeds
except ImportError:
    local_feeds = None

# Mock places data (replace with Places API in production)
MOCK_PLACES = [
    {
        "place_id": "ChIJ51cu8IcfmogRW07iZizUBrE",
        "name": "Golden Gate Park",
        "category": "parks",
        "address": "San Francisco, CA 94122",
        "lat": 37.7694,
        "lng": -122.4862,
        "distance_miles": 2.5,
        "travel_time_min": 10,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.8,
        "total_ratings": 45892,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Golden_Gate_Park_1.jpg/1280px-Golden_Gate_Park_1.jpg",
        "google_maps_url": "https://www.google.com/maps/place/Golden+Gate+Park/@37.7694208,-122.4862138,15z"
    },
    {
        "place_id": "ChIJNYvRwcKAhYARPJzfNJeTHvM",
        "name": "Exploratorium",
        "category": "museums",
        "address": "Pier 15, The Embarcadero, San Francisco, CA 94111",
        "lat": 37.8014,
        "lng": -122.3976,
        "distance_miles": 5.2,
        "travel_time_min": 18,
        "price_flag": "$$",
        "kid_friendly": True,
        "indoor_outdoor": "indoor",
        "rating": 4.7,
        "total_ratings": 12543,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Exploratorium_2010.jpg/1280px-Exploratorium_2010.jpg",
        "google_maps_url": "https://www.google.com/maps/place/Exploratorium/@37.8016519,-122.3990694,17z"
    },
    {
        "place_id": "ChIJfzjKxsV_j4ARmeNKVsXLDlk",
        "name": "Alcatraz Island",
        "category": "attractions",
        "address": "San Francisco, CA 94133",
        "lat": 37.8267,
        "lng": -122.4230,
        "distance_miles": 3.8,
        "travel_time_min": 15,
        "price_flag": "$$",
        "kid_friendly": False,
        "indoor_outdoor": "outdoor",
        "rating": 4.7,
        "total_ratings": 34521,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Alcatraz_Island_as_seen_from_the_East.jpg/1280px-Alcatraz_Island_as_seen_from_the_East.jpg",
        "google_maps_url": "https://www.google.com/maps/place/Alcatraz+Island/@37.8269775,-122.4229555,17z"
    },
    {
        "place_id": "ChIJEfkMgcCAhYARyE0sMEfQ1Zs",
        "name": "Lands End Trail",
        "category": "parks",
        "address": "Lands End Trail, San Francisco, CA 94121",
        "lat": 37.7878,
        "lng": -122.5062,
        "distance_miles": 4.1,
        "travel_time_min": 12,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.9,
        "total_ratings": 8934,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Lands_End_%28San_Francisco%29_2020.jpg/1280px-Lands_End_%28San_Francisco%29_2020.jpg",
        "google_maps_url": "https://www.google.com/maps/place/Lands+End/@37.7877636,-122.5063379,16z"
    },
    {
        "place_id": "ChIJddqAct-AhYARt4T4C1GGblI",
        "name": "California Academy of Sciences",
        "category": "museums",
        "address": "55 Music Concourse Dr, San Francisco, CA 94118",
        "lat": 37.7699,
        "lng": -122.4661,
        "distance_miles": 2.8,
        "travel_time_min": 11,
        "price_flag": "$$$",
        "kid_friendly": True,
        "indoor_outdoor": "indoor",
        "rating": 4.6,
        "total_ratings": 21567,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/California_Academy_of_Sciences_2.jpg/1280px-California_Academy_of_Sciences_2.jpg",
        "google_maps_url": "https://www.google.com/maps/place/California+Academy+of+Sciences/@37.7699066,-122.4660944,17z"
    },
    {
        "place_id": "ChIJiQSq3jeAhYARdAv5PJxLQks",
        "name": "Fisherman's Wharf",
        "category": "attractions",
        "address": "Beach St & The Embarcadero, San Francisco, CA 94133",
        "lat": 37.8080,
        "lng": -122.4177,
        "distance_miles": 5.5,
        "travel_time_min": 20,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.5,
        "total_ratings": 67823,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Fishermans_Wharf_Sign%2C_SF%2C_CA%2C_jjron_25.03.2012.jpg/1280px-Fishermans_Wharf_Sign%2C_SF%2C_CA%2C_jjron_25.03.2012.jpg",
        "google_maps_url": "https://www.google.com/maps/place/Fisherman's+Wharf/@37.808,-122.4177,16z"
    },
    {
        "place_id": "ChIJSV0E3nKAhYARYIGT3rE-7j0",
        "name": "Twin Peaks",
        "category": "parks",
        "address": "501 Twin Peaks Blvd, San Francisco, CA 94114",
        "lat": 37.7544,
        "lng": -122.4477,
        "distance_miles": 3.2,
        "travel_time_min": 14,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.7,
        "total_ratings": 15678,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Sf_twinpeaks.jpg/1280px-Sf_twinpeaks.jpg",
        "google_maps_url": "https://www.google.com/maps/place/Twin+Peaks/@37.7544,-122.4477,16z"
    },
    {
        "place_id": "ChIJU1Ysd32AhYARY0rBWTEnQIA",
        "name": "SFMOMA",
        "category": "museums",
        "address": "151 3rd St, San Francisco, CA 94103",
        "lat": 37.7857,
        "lng": -122.4011,
        "distance_miles": 4.8,
        "travel_time_min": 16,
        "price_flag": "$$",
        "kid_friendly": True,
        "indoor_outdoor": "indoor",
        "rating": 4.5,
        "total_ratings": 18234,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/SFMOMA_2016.jpg/1280px-SFMOMA_2016.jpg",
        "google_maps_url": "https://www.google.com/maps/place/San+Francisco+Museum+of+Modern+Art/@37.7857107,-122.4010984,17z"
    },
    {
        "place_id": "ChIJWZaXYvaAhYAR3ztA1L1HzrI",
        "name": "Baker Beach",
        "category": "parks",
        "address": "1504 Pershing Dr, San Francisco, CA 94129",
        "lat": 37.7936,
        "lng": -122.4833,
        "distance_miles": 3.9,
        "travel_time_min": 13,
        "price_flag": "free",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.7,
        "total_ratings": 9876,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Baker_Beach_panorama.jpg/1280px-Baker_Beach_panorama.jpg",
        "google_maps_url": "https://www.google.com/maps/place/Baker+Beach/@37.7936364,-122.4833083,16z"
    },
    {
        "place_id": "ChIJLw5uvt-AhYARVDlQd2P40C4",
        "name": "Japanese Tea Garden",
        "category": "parks",
        "address": "75 Hagiwara Tea Garden Dr, San Francisco, CA 94118",
        "lat": 37.7702,
        "lng": -122.4701,
        "distance_miles": 2.6,
        "travel_time_min": 10,
        "price_flag": "$",
        "kid_friendly": True,
        "indoor_outdoor": "outdoor",
        "rating": 4.6,
        "total_ratings": 11234,
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Japanese_Tea_Garden_%28San_Francisco%29.JPG/1280px-Japanese_Tea_Garden_%28San_Francisco%29.JPG",
        "google_maps_url": "https://www.google.com/maps/place/Japanese+Tea+Garden/@37.7701656,-122.4700706,17z"
    }
]

def get_user_id_from_token(token):
    """Extract user ID from auth token"""
    return db.get_user_id_from_token(token)


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
    prefs = db.get_preferences(user_id)
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
    db.set_preferences(user_id, data)
    print(f"[DEBUG] Preferences saved. Categories: {data.get('categories', [])}")
    return jsonify({"status": "updated", "preferences": data})


# ========== GEOCODING ==========

@app.route('/v1/geocode', methods=['GET'])
def geocode_address():
    """Geocode an address or ZIP code to lat/lng"""
    address = request.args.get('address', '').strip()
    if not address:
        return jsonify({"error": "Address parameter required"}), 400
    
    result = geocode_to_lat_lng(address)
    if result:
        lat, lng = result
        return jsonify({
            "lat": lat,
            "lng": lng,
            "formatted_address": address
        })
    else:
        return jsonify({"error": "Could not geocode address"}), 404


@app.route('/v1/reverse-geocode', methods=['GET'])
def reverse_geocode():
    """Reverse geocode lat/lng to address"""
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Valid lat and lng parameters required"}), 400
    
    if lat == 0 and lng == 0:
        return jsonify({"error": "Valid lat and lng parameters required"}), 400
    
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        r = requests.get(
            url, 
            params={"lat": lat, "lon": lng, "format": "json"},
            headers={"User-Agent": "ActivityPlanner/1.0"},
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            address = data.get('address', {})
            
            # Build formatted address
            parts = []
            if address.get('city'):
                parts.append(address['city'])
            elif address.get('town'):
                parts.append(address['town'])
            elif address.get('village'):
                parts.append(address['village'])
            elif address.get('county'):
                parts.append(address['county'])
            
            if address.get('state'):
                parts.append(address['state'])
            
            formatted = ", ".join(parts) if parts else data.get('display_name', 'Unknown location')
            
            return jsonify({
                "lat": lat,
                "lng": lng,
                "formatted_address": formatted,
                "display_name": data.get('display_name', '')
            })
        else:
            return jsonify({"error": "Reverse geocoding failed"}), 500
            
    except Exception as e:
        print(f"[REVERSE_GEOCODE] Error: {e}")
        return jsonify({"error": "Reverse geocoding failed"}), 500


@app.route('/v1/image-search', methods=['GET'])
def image_search():
    """
    Search for an image by query (keywords from title + event detail + location).
    Uses Google Custom Search API (Google Images) if configured, else Pexels, else Unsplash.
    Returns first relevant image URL for the location/event.
    """
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({"url": None, "source": None}), 200

    cache_key = f"img:{query[:100]}"
    if cache_key in image_search_cache:
        cached = image_search_cache[cache_key]
        return jsonify({"url": cached.get("url"), "source": cached.get("source")}), 200

    url = None
    source = None

    # 1. Try Google Custom Search (Google Images)
    if GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX:
        try:
            gurl = "https://www.googleapis.com/customsearch/v1"
            r = requests.get(
                gurl,
                params={
                    "key": GOOGLE_CSE_API_KEY,
                    "cx": GOOGLE_CSE_CX,
                    "q": query,
                    "searchType": "image",
                    "num": 3,
                    "safe": "active",
                },
                timeout=8,
            )
            if r.status_code == 200:
                data = r.json()
                items = data.get("items", [])
                if items:
                    url = items[0].get("link")
                    source = "google"
        except Exception as e:
            print(f"[IMAGE_SEARCH] Google CSE error: {e}")

    # 2. Fallback: Pexels API
    if not url and PEXELS_API_KEY:
        try:
            pexels_url = "https://api.pexels.com/v1/search"
            r = requests.get(
                pexels_url,
                params={"query": query, "per_page": 3},
                headers={"Authorization": PEXELS_API_KEY},
                timeout=8,
            )
            if r.status_code == 200:
                data = r.json()
                photos = data.get("photos", [])
                if photos:
                    # Prefer medium size for good quality without huge files
                    src = photos[0].get("src", {})
                    url = src.get("medium") or src.get("large") or src.get("original")
                    source = "pexels"
        except Exception as e:
            print(f"[IMAGE_SEARCH] Pexels error: {e}")

    # 3. Fallback: Unsplash API (keywords from title + event detail)
    if not url and UNSPLASH_ACCESS_KEY:
        try:
            unsplash_url = "https://api.unsplash.com/search/photos"
            r = requests.get(
                unsplash_url,
                params={"query": query, "per_page": 3},
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                timeout=8,
            )
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                if results:
                    urls = results[0].get("urls", {})
                    url = urls.get("regular") or urls.get("small") or urls.get("full")
                    source = "unsplash"
        except Exception as e:
            print(f"[IMAGE_SEARCH] Unsplash error: {e}")

    image_search_cache[cache_key] = {"url": url, "source": source}
    return jsonify({"url": url, "source": source}), 200


# ========== RECOMMENDATIONS ==========

# ========== CIRCUIT BREAKER PATTERN ==========

def is_circuit_open(source):
    """Check if circuit breaker is open for a source (too many recent failures)."""
    if source not in _circuit_breakers:
        return False
    
    cb = _circuit_breakers[source]
    failures = cb.get('failures', 0)
    last_failure = cb.get('last_failure')
    
    # Open circuit if 3+ failures in last 10 minutes
    if failures >= 3 and last_failure:
        from datetime import datetime, timedelta
        if datetime.now() - last_failure < timedelta(minutes=10):
            return True
        # Reset after 10 minutes
        cb['failures'] = 0
    
    return False


def record_success(source):
    """Record successful API call for circuit breaker."""
    if source in _circuit_breakers:
        _circuit_breakers[source]['failures'] = 0
        _circuit_breakers[source]['total_calls'] = _circuit_breakers[source].get('total_calls', 0) + 1


def record_failure(source):
    """Record failed API call for circuit breaker."""
    from datetime import datetime
    
    if source not in _circuit_breakers:
        _circuit_breakers[source] = {'failures': 0, 'total_calls': 0}
    
    cb = _circuit_breakers[source]
    cb['failures'] = cb.get('failures', 0) + 1
    cb['last_failure'] = datetime.now()
    cb['total_calls'] = cb.get('total_calls', 0) + 1
    
    print(f"[CIRCUIT_BREAKER] {source}: {cb['failures']} failures, last: {cb['last_failure']}")


# ========== RECOMMENDATION ENGINE ==========

def _get_warm_cache_key(user_id, prefs):
    """Generate a stable cache key for warm cache lookups."""
    import hashlib
    home_location = prefs.get('home_location', {})
    categories = prefs.get('categories', [])
    location_str = home_location.get('formatted_address') or home_location.get('input') or ''
    kid_friendly = prefs.get('kid_friendly', False)
    travel_time_ranges = prefs.get('travel_time_ranges', [])
    cache_key_data = f"{user_id}|{location_str}|{','.join(sorted(categories))}|{kid_friendly}|{','.join(sorted(travel_time_ranges))}"
    return hashlib.md5(cache_key_data.encode()).hexdigest()[:16]


def _refresh_recommendations_background(user_id, prefs, cache_key):
    """Background thread to refresh recommendations and update warm cache."""
    global _warm_cache, _background_refresh_in_progress
    try:
        items, sources = _fetch_recommendations_live(user_id, prefs, cache_key)
        if items:
            _warm_cache[cache_key] = {
                'items': items,
                'sources': sources,
                'timestamp': datetime.now()
            }
            print(f"[WARM_CACHE] Background refresh done: {len(items)} items for key {cache_key}")
    except Exception as e:
        print(f"[WARM_CACHE] Background refresh error: {e}")
    finally:
        _background_refresh_in_progress.discard(cache_key)


# Warm cache TTL: serve from cache if < 15 min old, trigger background refresh if > 5 min old
WARM_CACHE_FRESH_SECONDS = 300   # 5 min: fully fresh, no refresh needed
WARM_CACHE_STALE_SECONDS = 900   # 15 min: stale but serveable, trigger background refresh


def get_recommendations(user_id, prefs):
    """
    Main recommendation engine with stale-while-revalidate pattern:
    1. Check in-memory warm cache — serve immediately if available
    2. If cache is stale (>5min), trigger background refresh
    3. If no cache, fetch live (blocking)
    4. Fallback chain: Google Places -> Local feeds -> DB cache -> Mock data
    """
    import hashlib
    import threading
    global _warm_cache_lock
    if _warm_cache_lock is None:
        _warm_cache_lock = threading.Lock()
    
    cache_key = _get_warm_cache_key(user_id, prefs)
    print(f"[RECOMMENDATIONS] Getting recommendations for user {user_id}, cache_key: {cache_key}")
    
    # Step 0: Check warm cache (stale-while-revalidate)
    cached = _warm_cache.get(cache_key)
    if cached:
        age_seconds = (datetime.now() - cached['timestamp']).total_seconds()
        if age_seconds < WARM_CACHE_STALE_SECONDS:
            print(f"[WARM_CACHE] Hit! age={age_seconds:.0f}s, items={len(cached['items'])}")
            # If stale (>5min), trigger background refresh
            if age_seconds > WARM_CACHE_FRESH_SECONDS and cache_key not in _background_refresh_in_progress:
                _background_refresh_in_progress.add(cache_key)
                t = threading.Thread(
                    target=_refresh_recommendations_background,
                    args=(user_id, prefs, cache_key),
                    daemon=True
                )
                t.start()
                print(f"[WARM_CACHE] Triggered background refresh (stale)")
            return cached['items'], cached['sources']
    
    # No warm cache — fetch live (blocking)
    items, sources = _fetch_recommendations_live(user_id, prefs, cache_key)
    
    # Store in warm cache
    if items:
        _warm_cache[cache_key] = {
            'items': items,
            'sources': sources,
            'timestamp': datetime.now()
        }
    
    return items, sources


def _fetch_recommendations_live(user_id, prefs, cache_key):
    """
    Live fetch from all sources with fallback chain:
    1. Try Google Places API (if key configured)
    2. Try local feeds (parallel fetch, 5s timeout)
    3. Merge and rank results
    4. Cache successful results
    5. If all live sources fail, return cached results
    6. If no cache, return enriched mock data
    """
    from datetime import datetime, timedelta
    
    # Resolve user location
    home_location = prefs.get('home_location', {})
    user_lat, user_lng = resolve_user_location(home_location)
    categories = prefs.get('categories', [])
    kid_friendly = prefs.get('kid_friendly', False)
    travel_time_ranges = prefs.get('travel_time_ranges', [])
    
    # Step 1: Try to get from cache first
    cached = db.get_cached_recommendations(user_id, cache_key)
    cached_items = cached['items'] if cached else None
    
    # Initialize result tracking
    all_items = []
    sources_tried = []
    sources_succeeded = []
    sources_failed = []
    
    # Step 2: Try Google Places API (if key configured and not circuit broken)
    if GOOGLE_PLACES_API_KEY and not is_circuit_open('google_places'):
        print("[RECOMMENDATIONS] Trying Google Places API...")
        sources_tried.append('google_places')
        
        try:
            places_items = get_google_places_recommendations(prefs, user_id, user_lat, user_lng)
            if places_items:
                all_items.extend(places_items)
                sources_succeeded.append('google_places')
                record_success('google_places')
                print(f"[RECOMMENDATIONS] Google Places: {len(places_items)} items")
            else:
                record_failure('google_places')
                sources_failed.append('google_places')
        except Exception as e:
            print(f"[RECOMMENDATIONS] Google Places error: {e}")
            record_failure('google_places')
            sources_failed.append('google_places')
    else:
        if not GOOGLE_PLACES_API_KEY:
            print("[RECOMMENDATIONS] Google Places API key not configured")
        if is_circuit_open('google_places'):
            print("[RECOMMENDATIONS] Google Places circuit breaker open, skipping")
    
    # Step 3: Try local feeds (if not circuit broken)
    if local_feeds and not is_circuit_open('local_feeds'):
        print("[RECOMMENDATIONS] Trying local feeds...")
        sources_tried.append('local_feeds')
        
        try:
            # Build profile for local feeds
            profile = {
                'location': home_location,
                'group_type': prefs.get('group_type'),
                'interests': prefs.get('interests', []),
                'energy_level': prefs.get('energy_level'),
                'budget': prefs.get('budget'),
                'travel_time_ranges': travel_time_ranges,
                'kid_friendly': kid_friendly
            }
            
            max_travel_min = get_max_travel_time(travel_time_ranges)
            max_radius_miles = get_max_radius_miles(travel_time_ranges)
            week_str = f"{datetime.now().year}-{datetime.now().isocalendar()[1]:02d}"
            
            local_items = local_feeds.get_local_feed_recommendations(
                profile=profile,
                user_lat=user_lat,
                user_lng=user_lng,
                geocode_fn=geocode_to_lat_lng,
                max_items=20,
                max_travel_min=max_travel_min,
                max_radius_miles=max_radius_miles,
                week_str=week_str
            )
            
            if local_items:
                all_items.extend(local_items)
                sources_succeeded.append('local_feeds')
                record_success('local_feeds')
                print(f"[RECOMMENDATIONS] Local feeds: {len(local_items)} items")
            else:
                record_failure('local_feeds')
                sources_failed.append('local_feeds')
        except Exception as e:
            print(f"[RECOMMENDATIONS] Local feeds error: {e}")
            record_failure('local_feeds')
            sources_failed.append('local_feeds')
    else:
        if not local_feeds:
            print("[RECOMMENDATIONS] Local feeds module not available")
        if is_circuit_open('local_feeds'):
            print("[RECOMMENDATIONS] Local feeds circuit breaker open, skipping")
    
    # Step 4: Merge, deduplicate and rank results
    if all_items:
        print(f"[RECOMMENDATIONS] Merging {len(all_items)} items from {len(sources_succeeded)} sources")
        
        # Filter by user preferences
        filtered_items = []
        print(f"[RECOMMENDATIONS] Filtering {len(all_items)} items, max_travel={get_max_travel_time(travel_time_ranges)}, max_radius={get_max_radius_miles(travel_time_ranges)}")
        for item in all_items:
            # Apply travel time filter
            travel_time = item.get('travel_time_min')
            if travel_time and isinstance(travel_time, (int, float)):
                max_travel = get_max_travel_time(travel_time_ranges)
                if travel_time > max_travel:
                    continue
            
            # Apply distance filter  
            distance = item.get('distance_miles')
            if distance and isinstance(distance, (int, float)):
                max_radius = get_max_radius_miles(travel_time_ranges) 
                if distance > max_radius:
                    continue
            
            # Apply deduplication
            place_id = item.get('place_id')
            if place_id and should_dedup(place_id, user_id, prefs):
                continue
            
            filtered_items.append(item)
        
        print(f"[RECOMMENDATIONS] After filtering: {len(filtered_items)} items (from {len(all_items)})")
        
        # Score and rank all items together
        def _item_score(item):
            score = 0
            # Strong bonus for items with distance data
            if item.get('distance_miles') is not None:
                score += 30
                # Closer items score higher
                d = item.get('distance_miles', 50)
                if d <= 5:
                    score += 15
                elif d <= 10:
                    score += 10
                elif d <= 20:
                    score += 5
            # Rating bonus
            score += (item.get('rating', 0) or 0) * 5
            # Events with dates are more actionable
            if item.get('event_date'):
                score += 5
            # Kid-friendly bonus if applicable
            if kid_friendly and item.get('kid_friendly'):
                score += 10
            # Free is a plus
            if (item.get('price_flag') or '').lower() == 'free':
                score += 3
            return score
        
        filtered_items.sort(key=_item_score, reverse=True)
        
        # Take top 15 items with source diversity
        final_items = []
        source_counts = {}
        max_per_source = 6
        
        for item in filtered_items:
            src = item.get('feed_source') or item.get('type', 'unknown')
            if source_counts.get(src, 0) >= max_per_source:
                continue
            source_counts[src] = source_counts.get(src, 0) + 1
            final_items.append(item)
            if len(final_items) >= 15:
                break
        
        # Fill remaining if needed
        if len(final_items) < 15:
            for item in filtered_items:
                if item not in final_items:
                    final_items.append(item)
                    if len(final_items) >= 15:
                        break
        
        # Cache successful results
        if final_items:
            cache_expiry = datetime.now() + timedelta(hours=1)
            db.cache_recommendations(user_id, cache_key, final_items, cache_expiry.isoformat())
            print(f"[RECOMMENDATIONS] Cached {len(final_items)} items")
        
        return final_items, sources_succeeded
    
    # Step 5: If all live sources failed, try cached results
    if cached_items:
        print(f"[RECOMMENDATIONS] All live sources failed, returning {len(cached_items)} cached items")
        return cached_items, ['cache']
    
    # Step 6: Last resort - return enriched mock data
    print("[RECOMMENDATIONS] No live sources or cache, falling back to mock data")
    mock_items = get_enriched_mock_data(prefs, user_id, user_lat, user_lng)
    return mock_items, ['mock']


def get_google_places_recommendations(prefs, user_id, user_lat, user_lng):
    """Get recommendations from Google Places API based on user preferences."""
    if not GOOGLE_PLACES_API_KEY:
        return []
    
    items = []
    categories = prefs.get('categories', ['parks', 'museums', 'attractions'])
    travel_time_ranges = prefs.get('travel_time_ranges', ['15-30'])
    max_radius_miles = get_max_radius_miles(travel_time_ranges)
    radius_meters = min(int(max_radius_miles * 1609), 50000)  # Convert to meters, max 50km
    
    location = {'lat': user_lat, 'lng': user_lng}
    
    # Search each category
    for category in categories[:3]:  # Limit to 3 categories to avoid rate limits
        places = search_google_places(location, category, radius_meters)
        if places:
            for i, place in enumerate(places[:3]):  # Top 3 per category
                item = convert_google_place_to_item(place, location, len(items))
                
                # Apply kid_friendly filter if needed
                if prefs.get('kid_friendly') and not item.get('kid_friendly'):
                    continue
                
                # Apply budget filter
                budget = prefs.get('budget', 'moderate')
                if budget == 'free' and item.get('price_flag') != 'free':
                    continue
                
                items.append(item)
    
    return items


def get_enriched_mock_data(prefs, user_id, user_lat, user_lng):
    """Return mock data enriched with correct distances/travel times from user location."""
    mock_items = []
    categories = prefs.get('categories', ['parks', 'museums', 'attractions'])
    travel_time_ranges = prefs.get('travel_time_ranges', ['15-30'])
    max_travel = get_max_travel_time(travel_time_ranges)
    max_radius = get_max_radius_miles(travel_time_ranges)
    
    week = f"{datetime.now().year}-{datetime.now().isocalendar()[1]:02d}"
    
    for i, place in enumerate(MOCK_PLACES):
        # Apply category filter
        if categories and place['category'] not in categories:
            continue
        
        # Apply deduplication 
        if should_dedup(place['place_id'], user_id, prefs):
            continue
        
        # Compute actual distance and travel time from user location
        enriched_place = _place_with_distance_from_user(place, user_lat, user_lng)
        
        # Apply distance/time filters
        if enriched_place['distance_miles'] > max_radius:
            continue
        if enriched_place.get('travel_time_min', 0) > max_travel:
            continue
        
        # Apply kid_friendly filter
        if prefs.get('kid_friendly') and not enriched_place.get('kid_friendly'):
            continue
        
        # Convert to recommendation format
        rec_id = f"mock_{user_id}_{week}_{len(mock_items)}"
        google_maps_url = enriched_place.get('google_maps_url') or f"https://www.google.com/maps/search/?api=1&query={enriched_place['lat']},{enriched_place['lng']}"
        
        item = {
            "rec_id": rec_id,
            "type": "place",
            "place_id": enriched_place['place_id'],
            "title": enriched_place['name'],
            "category": enriched_place['category'],
            "distance_miles": enriched_place['distance_miles'],
            "travel_time_min": enriched_place['travel_time_min'],
            "price_flag": enriched_place['price_flag'],
            "kid_friendly": enriched_place.get('kid_friendly', False),
            "indoor_outdoor": enriched_place.get('indoor_outdoor', 'outdoor'),
            "explanation": f"Because you like {enriched_place['category']} and it's {enriched_place['travel_time_min']} min away",
            "source_url": google_maps_url,
            "google_maps_url": google_maps_url,
            "address": enriched_place['address'],
            "rating": enriched_place.get('rating', 4.0),
            "total_ratings": enriched_place.get('total_ratings', 0),
            "photo_url": enriched_place.get('photo_url')
        }
        
        mock_items.append(item)
        
        if len(mock_items) >= 8:
            break
    
    # Track as recently recommended
    for item in mock_items:
        db.add_recent_recommendation(user_id, item['place_id'], item['rec_id'], week)
    
    return mock_items


def should_dedup(place_id, user_id, prefs):
    """Check if a place should be deduplicated"""
    # Check explicit "already been"
    visited = db.get_visited_list(user_id)
    for visit in visited:
        if visit['place_id'] == place_id:
            visited_at = datetime.fromisoformat(visit['visited_at'])
            dedup_window = timedelta(days=prefs.get('dedup_window_days', 365))
            if datetime.now() - visited_at < dedup_window:
                return True
    
    # Check recently recommended (last 4 weeks)
    recent = db.get_recent_recommendations_list(user_id)
    four_weeks_ago = datetime.now() - timedelta(weeks=4)
    for rec in recent:
        if rec.get('place_id') == place_id:
            rec_at = datetime.fromisoformat(rec['recommended_at'])
            if rec_at > four_weeks_ago:
                return True
    
    return False

# Average speed (mph) for deriving max distance from max travel time
AVG_SPEED_MPH = 25

def get_max_travel_time(travel_time_ranges):
    """Get max travel time in minutes from travel_time_ranges list"""
    if not travel_time_ranges:
        return 30  # default
    
    max_time = 0
    for range_str in travel_time_ranges:
        if range_str == '60+':
            return 90  # Cap at 90 min for 60+
        elif range_str == '30-60':
            max_time = max(max_time, 60)
        elif range_str == '15-30':
            max_time = max(max_time, 30)
        elif range_str == '0-15':
            max_time = max(max_time, 15)
    
    return max_time if max_time > 0 else 30

def get_max_radius_miles(travel_time_ranges):
    """Get max distance in miles from travel_time_ranges (aligned with travel time).
    Uses average speed so distance and time filters are consistent."""
    max_min = get_max_travel_time(travel_time_ranges)
    # distance = (minutes / 60) * speed_mph
    return max(3, int((max_min / 60) * AVG_SPEED_MPH))

def _place_with_distance_from_user(place, user_lat, user_lng):
    """Return a copy of place with distance_miles and travel_time_min computed from user location."""
    import copy
    p = copy.deepcopy(place)
    dist = calculate_distance(user_lat, user_lng, place['lat'], place['lng'])
    p['distance_miles'] = round(dist, 1)
    p['travel_time_min'] = estimate_travel_time_minutes(dist)
    return p


def filter_places(prefs, user_id, user_lat=None, user_lng=None):
    """Filter and rank places based on preferences. If user_lat/lng are provided,
    distance and travel_time are computed from the user's location (so they match ZIP/address)."""
    filtered = []
    categories = prefs.get('categories', [])
    show_all_categories = len(categories) == 0
    
    travel_time_ranges = prefs.get('travel_time_ranges', ['15-30'])
    max_travel_time = get_max_travel_time(travel_time_ranges)
    radius_limit = get_max_radius_miles(travel_time_ranges)
    
    # If user location provided, we'll compute distance/time per place; else use mock values
    use_user_location = user_lat is not None and user_lng is not None
    
    print(f"[DEBUG] Filtering places - categories: {categories}, user_location: {use_user_location}")
    print(f"[DEBUG] Travel time ranges: {travel_time_ranges}, max_travel_time: {max_travel_time} min, max_radius: {radius_limit} mi")
    
    for place in MOCK_PLACES:
        if use_user_location:
            place = _place_with_distance_from_user(place, user_lat, user_lng)
        
        if place['distance_miles'] > radius_limit:
            continue
        if place.get('travel_time_min', 0) > max_travel_time:
            continue
        if not show_all_categories and place['category'] not in categories:
            continue
        if prefs.get('kid_friendly') is True and not place.get('kid_friendly'):
            continue
        if should_dedup(place['place_id'], user_id, prefs):
            continue
        
        filtered.append(place)
    
    filtered.sort(key=lambda x: (x['rating'], -x['distance_miles']), reverse=True)
    
    result = []
    category_counts = {}
    for place in filtered:
        cat = place['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if category_counts[cat] <= 2:
            result.append(place)
        if len(result) >= 8:
            break
    
    if len(result) == 0 and len(categories) > 0:
        relaxed_max_time = int(max_travel_time * 1.5)
        relaxed_radius = int(radius_limit * 1.5)
        for place in MOCK_PLACES:
            if use_user_location:
                place = _place_with_distance_from_user(place, user_lat, user_lng)
            if place['distance_miles'] > relaxed_radius or place.get('travel_time_min', 0) > relaxed_max_time:
                continue
            if prefs.get('kid_friendly') is True and not place.get('kid_friendly'):
                continue
            if should_dedup(place['place_id'], user_id, prefs):
                continue
            if place not in result:
                result.append(place)
            if len(result) >= 8:
                break

    # Last resort: return closest places regardless of radius/category filters
    if len(result) == 0:
        print(f"[DEBUG] No results after relaxed filter, returning closest places")
        all_places = []
        for place in MOCK_PLACES:
            if use_user_location:
                place = _place_with_distance_from_user(place, user_lat, user_lng)
            if should_dedup(place['place_id'], user_id, prefs):
                continue
            all_places.append(place)
        all_places.sort(key=lambda x: x['distance_miles'])
        result = all_places[:8]

    print(f"[DEBUG] Final result count: {len(result)}")
    return result

@app.route('/v1/digest', methods=['GET'])
@require_auth
def get_digest():
    """Get activity digest for current week using new recommendation engine with fallback chain"""
    import time as _time
    _request_start = _time.time()
    user_id = get_user_id()
    prefs = db.get_preferences(user_id) or {}
    
    # Use defaults if no preferences set
    if not prefs:
        prefs = {
            "home_location": {"type": "city", "value": "San Francisco, CA"},
            "radius_miles": 10,
            "categories": ["parks", "museums", "attractions"],
            "kid_friendly": True,
            "budget": {"min": 0, "max": 50},
            "time_windows": ["SAT_AM", "SAT_PM", "SUN_AM", "SUN_PM"],
            "travel_time_ranges": ["15-30"],
            "notification_time_local": "16:00",
            "dedup_window_days": 365,
            "calendar_dedup_opt_in": False
        }
    
    # Debug logging
    print(f"[DIGEST] User ID: {user_id}")
    print(f"[DIGEST] Categories: {prefs.get('categories', [])}")
    
    # Get current week
    now = datetime.now()
    week = f"{now.year}-{now.isocalendar()[1]:02d}"
    
    # Get recommendations using new engine with fallback chain
    try:
        items, sources = get_recommendations(user_id, prefs)
        
        elapsed_ms = int((_time.time() - _request_start) * 1000)
        response_data = {
            "week": week,
            "generated_at": datetime.now().isoformat(),
            "items": items,
            "sources": sources,  # Show which sources were used
            "from_cache": 'cache' in sources,
            "response_time_ms": elapsed_ms
        }
        
        print(f"[DIGEST] Returning {len(items)} items from sources: {', '.join(sources)} in {elapsed_ms}ms")
        resp = jsonify(response_data)
        resp.headers['X-Response-Time'] = f"{elapsed_ms}ms"
        return resp
        
    except Exception as e:
        import traceback
        print(f"[DIGEST] Error in recommendation engine: {e}")
        traceback.print_exc()
        # Emergency fallback - return empty result with error info
        return jsonify({
            "week": week,
            "generated_at": datetime.now().isoformat(),
            "items": [],
            "sources": ['error'],
            "error": str(e),
            "from_cache": False
        })

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


_nominatim_rate_limited = False  # Skip Nominatim when rate-limited

def geocode_to_lat_lng(query):
    """Resolve ZIP code or address to lat/lng using OpenStreetMap Nominatim (no API key)."""
    global _nominatim_rate_limited
    import re
    query = (query or "").strip()
    if not query:
        return None
    # Detect raw lat/lng coordinates (e.g. "37.7922, -122.4583")
    coord_match = re.match(r'^(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)$', query)
    if coord_match:
        lat, lng = float(coord_match.group(1)), float(coord_match.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            print(f"[GEOCODE] Detected coordinates: ({lat}, {lng})")
            geocode_cache[query.lower()] = (lat, lng)
            return (lat, lng)

    cache_key = query.lower()
    if cache_key in geocode_cache:
        cached = geocode_cache[cache_key]
        print(f"[GEOCODE] Cache hit for '{query}' -> {cached}")
        return cached
    try:
        # Determine the search query
        if query.isdigit() and len(query) == 5:
            # US ZIP code
            q = f"{query}, USA"
        elif re.search(r',\s*[A-Z]{2}\s*(\d{5})?$', query.upper()):
            # Has US state abbreviation (e.g., "Palo Alto, CA" or "123 Main St, City, CA 94301")
            # Append USA for better results
            q = f"{query}, USA"
        else:
            q = query
        
        # Fast path: common Bay Area cities (avoids Nominatim entirely)
        _KNOWN_LOCATIONS = {
            "san francisco": (37.7749, -122.4194),
            "san francisco, california": (37.7749, -122.4194),
            "san francisco, ca": (37.7749, -122.4194),
            "sf": (37.7749, -122.4194),
            "sf, ca": (37.7749, -122.4194),
            "oakland": (37.8044, -122.2712),
            "oakland, ca": (37.8044, -122.2712),
            "berkeley": (37.8716, -122.2727),
            "berkeley, ca": (37.8716, -122.2727),
            "fremont": (37.5485, -121.9886),
            "fremont, ca": (37.5485, -121.9886),
            "newark": (37.5316, -122.0392),
            "newark, ca": (37.5316, -122.0392),
            "san jose": (37.3382, -121.8863),
            "san jose, ca": (37.3382, -121.8863),
            "palo alto": (37.4419, -122.1430),
            "palo alto, ca": (37.4419, -122.1430),
            "mountain view": (37.3861, -122.0839),
            "mountain view, ca": (37.3861, -122.0839),
            "sunnyvale": (37.3688, -122.0363),
            "sunnyvale, ca": (37.3688, -122.0363),
            "hayward": (37.6688, -122.0808),
            "hayward, ca": (37.6688, -122.0808),
            "union city": (37.5934, -122.0438),
            "union city, ca": (37.5934, -122.0438),
            "castro valley": (37.6941, -122.0864),
            "castro valley, ca": (37.6941, -122.0864),
            "pleasanton": (37.6624, -121.8747),
            "pleasanton, ca": (37.6624, -121.8747),
            "livermore": (37.6819, -121.7680),
            "livermore, ca": (37.6819, -121.7680),
            "dublin": (37.7022, -121.9358),
            "dublin, ca": (37.7022, -121.9358),
            "san mateo": (37.5630, -122.3255),
            "san mateo, ca": (37.5630, -122.3255),
            "redwood city": (37.4852, -122.2364),
            "redwood city, ca": (37.4852, -122.2364),
            "santa clara": (37.3541, -121.9552),
            "santa clara, ca": (37.3541, -121.9552),
            "cupertino": (37.3230, -122.0322),
            "cupertino, ca": (37.3230, -122.0322),
            "milpitas": (37.4323, -121.8996),
            "milpitas, ca": (37.4323, -121.8996),
            "san leandro": (37.7249, -122.1561),
            "san leandro, ca": (37.7249, -122.1561),
            "walnut creek": (37.9101, -122.0652),
            "walnut creek, ca": (37.9101, -122.0652),
            "concord": (37.9780, -122.0311),
            "concord, ca": (37.9780, -122.0311),
            "richmond": (37.9358, -122.3478),
            "richmond, ca": (37.9358, -122.3478),
            "daly city": (37.6879, -122.4702),
            "daly city, ca": (37.6879, -122.4702),
            "south san francisco": (37.6547, -122.4077),
            "south san francisco, ca": (37.6547, -122.4077),
            "alameda": (37.7652, -122.2416),
            "alameda, ca": (37.7652, -122.2416),
            "kensington": (37.9107, -122.2802),
            "kensington, ca": (37.9107, -122.2802),
            "emeryville": (37.8313, -122.2852),
            "emeryville, ca": (37.8313, -122.2852),
            "east bay": (37.7749, -122.2000),
            "east bay, ca": (37.7749, -122.2000),
            "bay area": (37.6000, -122.1000),
        }
        known_key = cache_key.replace(", usa", "").replace(",usa", "").strip()
        if known_key in _KNOWN_LOCATIONS:
            result = _KNOWN_LOCATIONS[known_key]
            geocode_cache[cache_key] = result
            print(f"[GEOCODE] Known location: '{query}' -> {result}")
            return result

        if _nominatim_rate_limited:
            print(f"[GEOCODE] Skipping Nominatim (rate-limited) for '{q}'")
            geocode_cache[cache_key] = None
            return None

        print(f"[GEOCODE] Searching for: '{q}'")
        url = "https://nominatim.openstreetmap.org/search"
        r = requests.get(url, params={"q": q, "format": "json", "limit": 1}, headers={"User-Agent": "ActivityPlanner/1.0"}, timeout=4)
        
        if r.status_code == 429:
            print(f"[GEOCODE] Rate limited for '{q}' - skipping Nominatim for remaining items")
            _nominatim_rate_limited = True
            geocode_cache[cache_key] = None
            return None
        if r.status_code != 200:
            print(f"[GEOCODE] HTTP {r.status_code} for '{q}'")
            geocode_cache[cache_key] = None
            return None
        
        data = r.json()
        if not data:
            print(f"[GEOCODE] No results for '{q}'")
            geocode_cache[cache_key] = None
            return None
        
        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        geocode_cache[cache_key] = (lat, lng)
        print(f"[GEOCODE] Found: '{q}' -> ({lat}, {lng})")
        return (lat, lng)
    except Exception as e:
        print(f"[GEOCODE] Error for '{query}': {e}")
        return None


def resolve_user_location(location):
    """
    Get (lat, lng) from user's saved location (ZIP, address, or geolocation).
    Prefer geocoding from address/ZIP when present so distance/travel time are correct.
    Returns (lat, lng) or (37.7749, -122.4194) as fallback (SF).
    """
    if not location:
        return (37.7749, -122.4194)
    if isinstance(location, dict):
        query = location.get("formatted_address") or location.get("input") or location.get("value") or ""
        if query and str(query).strip():
            coords = geocode_to_lat_lng(str(query).strip())
            if coords:
                return coords
        if "lat" in location and "lng" in location:
            return (float(location["lat"]), float(location["lng"]))
    if isinstance(location, str):
        coords = geocode_to_lat_lng(location)
        if coords:
            return coords
    return (37.7749, -122.4194)


def estimate_travel_time_minutes(distance_miles, avg_mph=25):
    """Estimate travel time in minutes from distance (miles)."""
    if distance_miles <= 0:
        return 5
    return max(5, int(round((distance_miles / avg_mph) * 60)))


def convert_google_place_to_item(place, user_location, index):
    """Convert Google Places API result to our recommendation format"""
    
    # Extract location
    geometry = place.get('geometry', {})
    location = geometry.get('location', {})
    place_lat = location.get('lat', 0)
    place_lng = location.get('lng', 0)
    
    # Calculate distance and travel time from user location (must have lat/lng)
    user_lat = user_location.get('lat', 37.7749)
    user_lng = user_location.get('lng', -122.4194)
    distance = calculate_distance(user_lat, user_lng, place_lat, place_lng)
    travel_time = estimate_travel_time_minutes(distance)
    
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
    """Search for places using Google Places API. Location can be {lat, lng} or {formatted_address/input} (geocoded)."""
    data = request.json
    raw_location = data.get('location', {'lat': 37.7749, 'lng': -122.4194})
    if 'lat' in raw_location and 'lng' in raw_location:
        location = {'lat': float(raw_location['lat']), 'lng': float(raw_location['lng'])}
    else:
        user_lat, user_lng = resolve_user_location(raw_location)
        location = {'lat': user_lat, 'lng': user_lng}
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


# ========== LOCAL FEEDS (complement to Google Places) ==========

@app.route('/v1/feeds/config', methods=['GET'])
def get_feeds_config():
    """Return which local feed sources are configured (no secrets)."""
    if not local_feeds:
        return jsonify({"enabled": False, "sources": []})
    config = local_feeds.get_local_feed_config()
    sources = []
    for c in config["feed_configs"]:
        sources.append({"type": "rss", "label": c.get("label") or c.get("url", "")[:50], "url": c.get("url", "")})
    if config.get("facebook_token"):
        sources.append({"type": "facebook", "label": "Facebook Local"})
    if config.get("eventbrite_token"):
        sources.append({"type": "eventbrite", "label": "Eventbrite"})
    return jsonify({"enabled": True, "sources": sources})


# ========== AI-POWERED RECOMMENDATIONS ==========

@app.route('/v1/recommendations/ai', methods=['POST'])
def get_ai_recommendations():
    """Get AI-powered recommendations with caching and fallback support."""
    import time as _time
    _request_start = _time.time()
    data = request.json
    profile = data.get('profile', {})
    prompt = data.get('prompt', '')
    
    # Get user_id for deduplication and caching
    user_id = get_user_id()
    
    print(f"[AI] Received recommendation request for user: {user_id}")
    print(f"[AI] User profile: {json.dumps(profile, indent=2)}")
    
    # Convert profile to preferences format for compatibility with main engine
    prefs = {
        'home_location': profile.get('location', {}),
        'categories': [],  # Will be derived from interests
        'group_type': profile.get('group_type'),
        'interests': profile.get('interests', []),
        'energy_level': profile.get('energy_level'),
        'budget': profile.get('budget'),
        'travel_time_ranges': profile.get('travel_time_ranges', ['15-30']),
        'kid_friendly': profile.get('kid_friendly', False)
    }
    
    # Map interests to categories for filtering
    interest_to_category = {
        'nature': ['parks'],
        'arts_culture': ['museums'],
        'food_drinks': ['food'],
        'adventure': ['attractions'],
        'learning': ['museums'],
        'entertainment': ['attractions'],
        'relaxation': ['parks'],
        'shopping': ['attractions'],
        'events': ['events']
    }
    
    categories = []
    for interest in prefs.get('interests', []):
        categories.extend(interest_to_category.get(interest, []))
    prefs['categories'] = list(set(categories)) or ['parks', 'museums', 'attractions']
    
    try:
        # Use the same recommendation engine with fallback chain
        items, sources = get_recommendations(user_id, prefs)
        
        elapsed_ms = int((_time.time() - _request_start) * 1000)
        response_data = {
            "week": f"{datetime.now().year}-{datetime.now().isocalendar()[1]:02d}",
            "generated_at": datetime.now().isoformat(),
            "ai_powered": True,
            "sources": sources,
            "items": items,
            "from_cache": 'cache' in sources,
            "response_time_ms": elapsed_ms
        }
        
        print(f"[AI] Returning {len(items)} recommendations from sources: {', '.join(sources)} in {elapsed_ms}ms")
        resp = jsonify(response_data)
        resp.headers['X-Response-Time'] = f"{elapsed_ms}ms"
        return resp
        
    except Exception as e:
        print(f"[AI] Error in AI recommendations: {e}")
        return jsonify({
            "error": "Failed to generate AI recommendations", 
            "details": str(e),
            "week": f"{datetime.now().year}-{datetime.now().isocalendar()[1]:02d}",
            "generated_at": datetime.now().isoformat(),
            "ai_powered": True,
            "sources": ['error'],
            "items": []
        }), 500


def generate_recommendations_from_google_places(profile, user_id=None):
    """Generate recommendations using Google Places API.
    User location (ZIP/address) is resolved to lat/lng so distance and travel_time match."""
    
    raw_location = profile.get('location', {})
    user_lat, user_lng = resolve_user_location(raw_location)
    location = {'lat': user_lat, 'lng': user_lng}
    interests = profile.get('interests', [])
    travel_times = profile.get('travel_time_ranges', ['15-30'])
    kid_friendly = profile.get('kid_friendly', False)
    budget = profile.get('budget', 'moderate')
    
    # Get visited places for deduplication
    visited_place_ids = set()
    if user_id:
        visited = db.get_visited_list(user_id)
        visited_place_ids = {v['place_id'] for v in visited}
    
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
    
    # Use shared helpers so travel time and distance are aligned
    max_travel = get_max_travel_time(travel_times)
    max_radius_miles = get_max_radius_miles(travel_times)
    # Convert to meters for Places API (1 mile ≈ 1609 m)
    radius_meters = min(int(max_radius_miles * 1609), 50000)  # Max 50km
    
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
                
                # Travel time and distance filter (aligned with user selection)
                if item.get('travel_time_min', 0) > max_travel or item.get('distance_miles', 0) > max_radius_miles:
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


def generate_personalized_recommendations(profile, user_id=None):
    """Generate recommendations based on user profile. Distance and travel_time
    are computed from the user's saved location (ZIP/address) so they match."""
    
    location = profile.get('location', {})
    user_lat, user_lng = resolve_user_location(location)
    
    group_type = profile.get('group_type', 'solo')
    interests = profile.get('interests', [])
    energy_level = profile.get('energy_level', 'moderate')
    budget = profile.get('budget', 'moderate')
    travel_times = profile.get('travel_time_ranges', ['15-30'])
    kid_friendly = profile.get('kid_friendly', False)
    avoid = profile.get('avoid', [])
    
    visited_place_ids = set()
    if user_id:
        visited = db.get_visited_list(user_id)
        visited_place_ids = {v['place_id'] for v in visited}
    
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
    
    max_travel = get_max_travel_time(travel_times)
    max_radius_miles = get_max_radius_miles(travel_times)
    
    budget_filters = {
        'free': ['free'],
        'low': ['free', '$'],
        'moderate': ['free', '$', '$$'],
        'any': ['free', '$', '$$', '$$$', '$$$$', 'paid']
    }
    allowed_prices = budget_filters.get(budget, ['free', '$', '$$', '$$$'])
    
    # Filter places: compute distance/time from user location for each place
    filtered_places = []
    for place in MOCK_PLACES:
        if place['place_id'] in visited_place_ids:
            continue
        if place['category'] not in target_categories:
            continue
        
        place = _place_with_distance_from_user(place, user_lat, user_lng)
        
        if place.get('distance_miles', 0) > max_radius_miles:
            continue
        if place['travel_time_min'] > max_travel:
            continue
        if place['price_flag'] not in allowed_prices:
            continue
        if kid_friendly and not place.get('kid_friendly', False):
            continue
        if 'crowds' in avoid and place.get('crowded', False):
            continue
        
        filtered_places.append(place)
    
    def relevance_score(p):
        score = 0
        if p['category'] in [interest_to_category.get(i) for i in interests]:
            score += 10
        score -= p['travel_time_min'] / 10
        score += p.get('rating', 4) * 2
        return score
    
    filtered_places.sort(key=relevance_score, reverse=True)
    
    top_places = filtered_places[:5]
    
    if len(top_places) < 5:
        top_ids = {p['place_id'] for p in top_places}
        for place in MOCK_PLACES:
            if place['place_id'] in visited_place_ids or place['place_id'] in top_ids:
                continue
            place = _place_with_distance_from_user(place, user_lat, user_lng)
            if place.get('distance_miles', 0) > max_radius_miles or place['travel_time_min'] > max_travel:
                continue
            top_places.append(place)
            top_ids.add(place['place_id'])
            if len(top_places) >= 5:
                break
    
    # Generate personalized explanations
    items = []
    now = datetime.now()
    week = f"{now.year}-{now.isocalendar()[1]:02d}"
    
    for i, place in enumerate(top_places):
        explanation = generate_explanation(place, profile, interests)
        
        # Use Google Maps URL from mock data, or build from coordinates
        google_maps_url = place.get('google_maps_url') or f"https://www.google.com/maps/search/?api=1&query={place['lat']},{place['lng']}"
        
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
            "source_url": google_maps_url,
            "google_maps_url": google_maps_url,
            "address": place['address'],
            "rating": place.get('rating', 4.0),
            "total_ratings": place.get('total_ratings', 0),
            "photo_url": place.get('photo_url'),
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
    place_id = data.get('place_id')
    
    if not rec_id or not action:
        return jsonify({"error": "Missing rec_id or action"}), 400
    
    # Find place_id from recommendation if not provided
    if not place_id:
        for rec in db.get_recent_recommendations_list(user_id):
            if rec['rec_id'] == rec_id:
                place_id = rec['place_id']
                break
    
    # Handle "already_been" action - add to visited list
    if action == "already_been" and place_id:
        if not db.visited_contains(user_id, place_id):
            db.add_visited(user_id, place_id, signal_type="manual", confidence=1.0)
            print(f"[FEEDBACK] User {user_id} marked {place_id} as been")
    
    # Handle "unbeen" action - remove from visited list
    elif action == "unbeen" and place_id:
        db.remove_visited(user_id, place_id)
        print(f"[FEEDBACK] User {user_id} unmarked {place_id} as been")
    
    # Handle "favorite" action - add to saved list
    elif action == "favorite" and place_id:
        if not db.saved_contains(user_id, place_id):
            db.add_saved(user_id, place_id)
            print(f"[FEEDBACK] User {user_id} saved {place_id}")
    
    # Handle "unsave" action - remove from saved list
    elif action == "unsave" and place_id:
        db.remove_saved(user_id, place_id)
        print(f"[FEEDBACK] User {user_id} unsaved {place_id}")
    
    return jsonify({"status": "recorded", "action": action})

# ========== VISITED HISTORY ==========

def get_place_details_by_id(place_id):
    """Helper to get place details from mock data by place_id"""
    for place in MOCK_PLACES:
        if place.get('place_id') == place_id:
            return {
                "place_id": place_id,
                "title": place.get('name', 'Unknown Place'),
                "category": place.get('category', 'general'),
                "address": place.get('address', ''),
                "photo_url": place.get('photo_url', ''),
                "google_maps_url": place.get('google_maps_url', ''),
                "rating": place.get('rating', 0),
                "total_ratings": place.get('total_ratings', 0),
                "price_level": place.get('price_level', 1)
            }
    # Return basic info if not found in mock data
    return {
        "place_id": place_id,
        "title": place_id.replace('_', ' ').title(),
        "category": "general"
    }

@app.route('/v1/visited', methods=['GET'])
@require_auth
def get_visited():
    """Get visited places with full details"""
    user_id = get_user_id()
    visited = db.get_visited_list(user_id)
    
    # Enrich with place details
    enriched = []
    for v in visited:
        place_details = get_place_details_by_id(v['place_id'])
        enriched.append({
            **place_details,
            "visited_at": v.get('visited_at'),
            "signal_type": v.get('signal_type', 'manual')
        })
    
    return jsonify({"visited": enriched})

@app.route('/v1/visited', methods=['POST'])
@require_auth
def add_visited():
    """Manually add a visited place"""
    user_id = get_user_id()
    data = request.json
    place_id = data.get('place_id')
    
    if not place_id:
        return jsonify({"error": "Missing place_id"}), 400
    
    db.add_visited(
        user_id, place_id,
        visited_at=data.get('visited_at', datetime.now().isoformat()),
        signal_type=data.get('signal_type', 'manual'),
        confidence=data.get('confidence', 1.0)
    )
    return jsonify({"status": "added"})

@app.route('/v1/visited/<place_id>', methods=['DELETE'])
@require_auth
def remove_visited(place_id):
    """Remove a visited place"""
    user_id = get_user_id()
    db.remove_visited(user_id, place_id)
    return jsonify({"status": "removed"})

# ========== SAVED PLACES ==========

@app.route('/v1/saved', methods=['GET'])
@require_auth
def get_saved():
    """Get saved/favorited places with full details"""
    user_id = get_user_id()
    saved = db.get_saved_list(user_id)
    
    # Enrich with place details
    enriched = []
    for s in saved:
        place_details = get_place_details_by_id(s['place_id'])
        enriched.append({
            **place_details,
            "saved_at": s.get('saved_at')
        })
    
    return jsonify({"saved": enriched})

@app.route('/v1/saved/<place_id>', methods=['DELETE'])
@require_auth
def remove_saved(place_id):
    """Remove a saved place"""
    user_id = get_user_id()
    db.remove_saved(user_id, place_id)
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
        "summary": f"{place['name']} — Activity Plan",
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
                      f"Recommended because: {place.get('explanation', 'Recommended activity')}\n"
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

RESET_TOKEN_EXPIRY_HOURS = 1

# Optional SMTP for password reset emails
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '') or os.environ.get('SMTP_PASS', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', SMTP_USER or 'noreply@activityplanner.local')
FRONTEND_URL = os.environ.get('FRONTEND_URL', '').rstrip('/')  # e.g. https://app.example.com


def send_password_reset_email(to_email, reset_link):
    """Send password reset email via SMTP. Returns True on success, False otherwise."""
    if not SMTP_HOST or not SMTP_USER:
        print("[EMAIL] SMTP not configured (set SMTP_HOST, SMTP_USER, SMTP_PASSWORD)")
        return False
    subject = "Reset your Activity Planner password"
    text = f"""Hi,

You requested a password reset for your Activity Planner account.

Click the link below to set a new password (valid for 1 hour):

{reset_link}

If you didn't request this, you can ignore this email.

— Activity Planner
"""
    html = f"""<p>Hi,</p>
<p>You requested a password reset for your Activity Planner account.</p>
<p><a href="{reset_link}">Click here to set a new password</a> (valid for 1 hour).</p>
<p>If you didn't request this, you can ignore this email.</p>
<p>— Activity Planner</p>"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())
        print(f"[EMAIL] Password reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send to {to_email}: {e}")
        return False


def send_verification_email(to_email, verify_link):
    """Send email verification link via SMTP. Returns True on success."""
    if not SMTP_HOST or not SMTP_USER:
        print("[EMAIL] SMTP not configured (set SMTP_HOST, SMTP_USER, SMTP_PASSWORD)")
        return False
    subject = "Verify your Activity Planner email"
    text = f"""Hi,

Thanks for signing up for Activity Planner.

Click the link below to verify your email (valid for 24 hours):

{verify_link}

If you didn't create an account, you can ignore this email.

— Activity Planner
"""
    html = f"""<p>Hi,</p>
<p>Thanks for signing up for Activity Planner.</p>
<p><a href="{verify_link}">Click here to verify your email</a> (valid for 24 hours).</p>
<p>If you didn't create an account, you can ignore this email.</p>
<p>— Activity Planner</p>"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())
        print(f"[EMAIL] Verification email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send verification to {to_email}: {e}")
        return False


def send_friday_digest_email(to_email, user_name, recommendations, frontend_url):
    """Send Friday digest email with personalized recommendations. Returns True on success."""
    if not SMTP_HOST or not SMTP_USER:
        print("[EMAIL] SMTP not configured (set SMTP_HOST, SMTP_USER, SMTP_PASSWORD)")
        return False
    
    if not recommendations:
        print(f"[EMAIL] No recommendations for {to_email}, skipping digest")
        return False
    
    greeting = f"Hi {user_name}," if user_name else "Hi,"
    subject = "🎉 Your Activity Planner Digest - Top Picks for You!"
    
    # Build recommendation list for plain text
    rec_text_list = []
    for i, rec in enumerate(recommendations[:5], 1):
        title = rec.get('title', 'Event')
        distance = rec.get('distance_display', 'n/a')
        address = rec.get('address', '')
        event_date = rec.get('event_date', '')
        rec_text_list.append(f"{i}. {title}\n   📍 {address or 'Location TBD'}\n   🚗 {distance}")
    
    rec_text = "\n\n".join(rec_text_list)
    
    text = f"""{greeting}

Here are your personalized activity recommendations! 🌟

{rec_text}

Ready to plan? Visit Activity Planner to see more details and add events to your calendar.

{frontend_url or 'https://activityplanner.local'}

Happy exploring!
— The Activity Planner Team

---
You're receiving this because you signed up for Activity Planner digests.
"""

    # Build HTML version
    rec_html_items = []
    for rec in recommendations[:5]:
        title = rec.get('title', 'Event')
        distance = rec.get('distance_display', 'n/a')
        address = rec.get('address', '')
        event_date = rec.get('event_date', '')
        description = (rec.get('description') or rec.get('explanation') or '')[:150]
        event_link = rec.get('event_link', '')
        
        # Format date if present
        date_html = ''
        if event_date:
            try:
                from datetime import datetime as dt
                date_obj = dt.fromisoformat(event_date.replace('Z', '+00:00'))
                date_html = f'<span style="color: #6366f1; font-size: 14px;">📅 {date_obj.strftime("%a, %b %d at %I:%M %p")}</span><br>'
            except:
                date_html = f'<span style="color: #6366f1; font-size: 14px;">📅 {event_date}</span><br>'
        
        rec_html_items.append(f'''
        <div style="background: #f9fafb; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <h3 style="margin: 0 0 8px 0; color: #111; font-size: 18px;">{title}</h3>
            {date_html}
            <p style="margin: 8px 0; color: #555; font-size: 14px;">{description}</p>
            <p style="margin: 8px 0; color: #666; font-size: 13px;">📍 {address or 'Location TBD'} &nbsp;|&nbsp; 🚗 {distance}</p>
            {f'<a href="{event_link}" style="color: #6366f1; text-decoration: none; font-size: 14px;">View event →</a>' if event_link else ''}
        </div>
        ''')
    
    rec_html = "".join(rec_html_items)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #6366f1; margin: 0;">🎉 Activity Planner</h1>
            <p style="color: #666; margin: 8px 0 0 0;">Your personalized activity digest</p>
        </div>
        
        <p style="font-size: 16px;">{greeting}</p>
        <p style="font-size: 16px;">Here are your top activity picks! 🌟</p>
        
        {rec_html}
        
        <div style="text-align: center; margin-top: 24px;">
            <a href="{frontend_url or 'https://activityplanner.local'}" style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 500;">View All Recommendations</a>
        </div>
        
        <p style="margin-top: 32px; font-size: 16px;">Happy exploring!<br>— The Activity Planner Team</p>
        
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 32px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            You're receiving this because you signed up for Activity Planner digests.
        </p>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())
        print(f"[EMAIL] Friday digest sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send digest to {to_email}: {e}")
        return False


def send_all_friday_digests():
    """Send Friday digest emails to all users with preferences. Returns count of emails sent."""
    from local_feeds import get_local_feed_recommendations
    
    users = db.get_all_users_with_preferences()
    sent_count = 0
    
    print(f"[DIGEST] Starting Friday digest for {len(users)} users")
    
    for user in users:
        try:
            user_id = user.get('id')
            email = user.get('email')
            name = user.get('name', '')
            preferences = user.get('preferences', {})
            
            if not email or not preferences:
                continue
            
            # Get personalized recommendations - use default location if not set
            user_location = preferences.get('location') or {}
            user_lat = user_location.get('lat') or 37.5485  # Default: Fremont, CA
            user_lng = user_location.get('lng') or -121.9886
            
            recommendations = get_local_feed_recommendations(
                profile=preferences,
                user_lat=user_lat,
                user_lng=user_lng,
                geocode_fn=geocode_to_lat_lng,
                max_items=5
            )
            
            if recommendations:
                if send_friday_digest_email(email, name, recommendations, FRONTEND_URL):
                    sent_count += 1
                    
        except Exception as e:
            print(f"[DIGEST] Error processing user {user.get('email', 'unknown')}: {e}")
    
    print(f"[DIGEST] Completed. Sent {sent_count} digest emails.")
    return sent_count


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
        if db.user_exists_by_identifier(email.lower()):
            return jsonify({"error": "User already exists"}), 409
        
        # Create user with hashed password
        user_id = f"user_{db.count_users() + 1}_{datetime.now().timestamp()}"
        db.create_user_email(
            email.lower(), user_id, hash_password(password),
            email_digest=data.get('email_digest', True)
        )
        
        # Create secure token
        token = secrets.token_urlsafe(32)
        db.set_auth_token(token, user_id)
        
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
    
    # Check that account exists and password matches
    user = db.get_user_by_identifier(email.lower())
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    if user.get('identifier_type') == 'google' and not user.get('password'):
        return jsonify({"error": "This account uses Google sign-in. Please log in with Google, or use 'Forgot password' to set a password."}), 401
    if not verify_password(password, user.get('password', '')):
        return jsonify({"error": "Invalid email or password"}), 401
    
    user_id = user['user_id']
    
    # Create secure token
    token = secrets.token_urlsafe(32)
    db.set_auth_token(token, user_id)
    
    # Get preferences
    prefs = db.get_preferences(user_id)
    
    print(f"[AUTH] User logged in: {email}")
    
    return jsonify({
        "user_id": user_id,
        "email": email,
        "token": token,
        "email_verified": user.get('email_verified', False),
        "preferences": prefs,
        "status": "authenticated"
    })


@app.route('/v1/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Request a password reset link. Sends email if SMTP is configured; else returns token for dev."""
    data = request.json
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({"error": "Email required"}), 400

    reset_token = None
    email_sent = False
    if db.user_exists_by_email_for_reset(email):
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
        db.set_reset_token(token, email, expires_at)
        reset_token = token
        # Build reset link for email or for dev response
        base = FRONTEND_URL or request.host_url.rstrip('/')
        reset_link = f"{base}/index.html?reset_token={token}" if base else None
        if reset_link and SMTP_HOST and SMTP_USER:
            email_sent = send_password_reset_email(email, reset_link)
        if not email_sent and reset_link:
            print(f"[AUTH] Email not sent (SMTP not configured). Reset link: {reset_link[:50]}...")
        print(f"[AUTH] Password reset requested for {email}, token expires {expires_at.isoformat()}")

    payload = {
        "message": "If an account exists with this email, you will receive a link to reset your password."
    }
    # Only return token in response when email was NOT sent (dev/testing)
    if reset_token and not email_sent:
        payload["reset_token"] = reset_token
    return jsonify(payload)


@app.route('/v1/auth/reset-password', methods=['POST'])
def reset_password():
    """Set new password using a valid reset token."""
    data = request.json
    token = (data.get('token') or '').strip()
    new_password = data.get('new_password')

    if not token:
        return jsonify({"error": "Reset token required"}), 400
    if not new_password or len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    record = db.get_reset_token(token)
    if not record:
        return jsonify({"error": "Invalid or expired reset link"}), 400

    try:
        expires_at = datetime.fromisoformat(record["expires_at"])
    except (ValueError, KeyError):
        db.delete_reset_token(token)
        return jsonify({"error": "Invalid or expired reset link"}), 400

    if datetime.now() > expires_at:
        db.delete_reset_token(token)
        return jsonify({"error": "Reset link has expired"}), 400

    email = record["email"]
    user = db.get_user_by_identifier(email)
    if not user:
        db.delete_reset_token(token)
        return jsonify({"error": "Invalid or expired reset link"}), 400

    # Update password (user row: we need an update function)
    db.update_user_password(email, hash_password(new_password))
    db.delete_reset_token(token)
    print(f"[AUTH] Password reset completed for {email}")
    return jsonify({"message": "Password updated. You can sign in with your new password."})


@app.route('/v1/auth/verify-email', methods=['POST'])
def verify_email():
    """Verify email using token from verification link."""
    data = request.json
    token = (data.get('token') or '').strip()
    if not token:
        return jsonify({"error": "Verification token required"}), 400

    record = db.get_verification_token(token)
    if not record:
        return jsonify({"error": "Invalid or expired verification link"}), 400

    try:
        expires_at = datetime.fromisoformat(record["expires_at"])
    except (ValueError, KeyError):
        db.delete_verification_token(token)
        return jsonify({"error": "Invalid or expired verification link"}), 400

    if datetime.now() > expires_at:
        db.delete_verification_token(token)
        return jsonify({"error": "Verification link has expired"}), 400

    email = record["email"]
    user = db.get_user_by_identifier(email)
    if not user:
        db.delete_verification_token(token)
        return jsonify({"error": "Account not found"}), 400

    db.set_user_email_verified(email)
    db.delete_verification_token(token)
    print(f"[AUTH] Email verified for {email}")
    return jsonify({"message": "Email verified. You can sign in with your account.", "email": email})


@app.route('/v1/auth/resend-verification', methods=['POST'])
def resend_verification():
    """Send a new verification email. Body: { email } or use authenticated user's email."""
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    if not email:
        # Optional: use current user from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            t = auth_header[7:]
            user_id = db.get_user_id_from_token(t)
            if user_id:
                user = db.get_user_by_user_id(user_id)
                if user:
                    email = (user.get('email') or user.get('identifier') or '').strip().lower()
        if not email:
            return jsonify({"error": "Email required"}), 400

    user = db.get_user_by_identifier(email)
    if not user:
        return jsonify({"error": "No account found with this email"}), 404
    if user.get('email_verified'):
        return jsonify({"message": "Email is already verified"}), 200

    verify_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=getattr(db, 'VERIFICATION_TOKEN_EXPIRY_HOURS', 24))
    db.set_verification_token(verify_token, email, expires_at)
    base = FRONTEND_URL or request.host_url.rstrip('/')
    verify_link = f"{base}/index.html?verify_token={verify_token}" if base else None
    sent = False
    if verify_link and SMTP_HOST and SMTP_USER:
        sent = send_verification_email(email, verify_link)
    if not sent and verify_link:
        print(f"[AUTH] Resend verification: email not sent. Link: {verify_link[:50]}...")

    payload = {"message": "If your account exists and is unverified, a new verification link was sent."}
    if verify_token and not sent:
        payload["verification_token"] = verify_token
    return jsonify(payload)


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
    is_new_user = not db.user_exists_by_identifier(phone)
    
    if is_new_user:
        user_id = f"user_phone_{db.count_users() + 1}_{datetime.now().timestamp()}"
        db.create_user_phone(phone, user_id)
    else:
        user_id = db.get_user_by_identifier(phone)['user_id']
    
    # Create secure token
    token = secrets.token_urlsafe(32)
    db.set_auth_token(token, user_id)
    
    # Get preferences
    prefs = db.get_preferences(user_id)
    
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
        if db.get_user_id_from_token(token):
            db.delete_auth_token(token)
    
    session.clear()
    return jsonify({"status": "logged_out"})


# ========== GOOGLE OAUTH ==========

@app.route('/v1/auth/google/url', methods=['GET'])
def get_google_auth_url():
    """Get the Google OAuth authorization URL"""
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth not configured"}), 501
    
    # Generate a signed state token for CSRF protection (no session dependency)
    nonce = secrets.token_urlsafe(32)
    sig = hmac.new(app.secret_key.encode(), f"auth:{nonce}".encode(), hashlib.sha256).hexdigest()[:16]
    state = f"auth:{nonce}:{sig}"

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
    
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + '&'.join(f'{k}={requests.utils.quote(str(v))}' for k, v in params.items())
    
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

    # Verify signed state token (no session dependency)
    state_valid = False
    oauth_type = 'auth'
    if state and ':' in state:
        parts = state.split(':', 2)
        if len(parts) == 3:
            oauth_type = parts[0]
            nonce = parts[1]
            sig = parts[2]
            expected_sig = hmac.new(app.secret_key.encode(), f"{oauth_type}:{nonce}".encode(), hashlib.sha256).hexdigest()[:16]
            state_valid = hmac.compare_digest(sig, expected_sig)
    if not state_valid:
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
        
        # Check if an account with this email already exists (e.g. from email signup)
        existing_user = db.get_user_by_identifier(email.lower())
        if existing_user:
            user_id = existing_user['user_id']
            db.update_user_google_link(user_id, name, picture)
        else:
            user_id = f"google_{google_id}"
            db.upsert_user_google(user_id, email, name=name, picture=picture)
        print(f"[AUTH] Google user logged in: {email}")
        
        # Generate auth token
        auth_token = secrets.token_urlsafe(32)
        db.set_auth_token(auth_token, user_id)
        
        # Store in session
        session['user_id'] = user_id
        
        # Check if this is a calendar auth request
        if oauth_type == 'calendar':
            # Return calendar-specific success with access token for calendar API
            print(f"[AUTH] Calendar auth successful for: {email}")
            return f'''
            <html><body>
            <script>
                window.opener.postMessage({{
                    type: 'calendar_auth_success',
                    token: '{access_token}',
                    auth_token: '{auth_token}'
                }}, '*');
                window.close();
            </script>
            </body></html>
            '''
        
        # Send success message to opener window (normal auth)
        user_data = {
            'id': user_id,
            'email': email,
            'name': name,
            'picture': picture,
            'provider': 'google'
        }
        
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


# ========== GOOGLE CALENDAR API ==========

@app.route('/v1/auth/google/calendar/url', methods=['GET'])
def get_google_calendar_auth_url():
    """Get the Google OAuth URL with Calendar scope"""
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth not configured"}), 501
    
    nonce = secrets.token_urlsafe(32)
    sig = hmac.new(app.secret_key.encode(), f"calendar:{nonce}".encode(), hashlib.sha256).hexdigest()[:16]
    state = f"calendar:{nonce}:{sig}"

    # Include calendar scope
    scopes = 'openid email profile https://www.googleapis.com/auth/calendar.events'
    
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': scopes,
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + '&'.join(f'{k}={requests.utils.quote(str(v))}' for k, v in params.items())
    
    return jsonify({
        "url": auth_url,
        "configured": True
    })


@app.route('/v1/calendar/event', methods=['POST'])
def create_calendar_event():
    """Create a Google Calendar event"""
    data = request.json
    calendar_token = data.get('calendar_token')
    event_data = data.get('event', {})
    
    if not calendar_token:
        return jsonify({"error": "No calendar token provided"}), 400
    
    try:
        # Build event payload for Google Calendar API
        event = {
            'summary': event_data.get('title', 'Activity Plan'),
            'location': event_data.get('location', ''),
            'description': event_data.get('description', ''),
        }
        
        event_date = event_data.get('date')
        
        if event_data.get('isAllDay', True):
            # All-day event
            event['start'] = {'date': event_date}
            event['end'] = {'date': event_date}
        else:
            # Timed event
            start_time = event_data.get('startTime', '10:00')
            end_time = event_data.get('endTime', '12:00')
            event['start'] = {
                'dateTime': f"{event_date}T{start_time}:00",
                'timeZone': 'America/Los_Angeles'
            }
            event['end'] = {
                'dateTime': f"{event_date}T{end_time}:00",
                'timeZone': 'America/Los_Angeles'
            }
        
        # Add reminder if requested
        if event_data.get('reminder'):
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': event_data['reminder']}
                ]
            }
        
        # Call Google Calendar API
        response = requests.post(
            'https://www.googleapis.com/calendar/v3/calendars/primary/events',
            headers={
                'Authorization': f'Bearer {calendar_token}',
                'Content-Type': 'application/json'
            },
            json=event,
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            print(f"[CALENDAR] Event created: {result.get('id')}")
            return jsonify({
                "status": "created",
                "event_id": result.get('id'),
                "event_link": result.get('htmlLink')
            })
        else:
            error_data = response.json()
            print(f"[CALENDAR] Error: {error_data}")
            return jsonify({
                "error": error_data.get('error', {}).get('message', 'Failed to create event')
            }), response.status_code
            
    except Exception as e:
        print(f"[CALENDAR] Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500


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
        user = db.get_user_by_user_id(user_id)
        user_info = None
        if user:
            user_info = {
                "id": user_id,
                "email": user.get('email'),
                "phone": user.get('phone'),
                "email_verified": user.get('email_verified', False)
            }
        
        # Get preferences
        prefs = db.get_preferences(user_id) or {}
        
        return jsonify({
            "user": user_info,
            "preferences": prefs
        })
    
    return jsonify({"error": "Authorization required"}), 401

@app.route('/v1/debug/check-email', methods=['GET'])
def debug_check_email():
    """Dev only: check if an email is registered (database)."""
    email = (request.args.get('email') or '').strip().lower()
    if not email:
        return jsonify({"error": "Query param 'email' required"}), 400
    exists = db.user_exists_by_identifier(email)
    return jsonify({"email": email, "exists": exists})


# ==================== FRIDAY DIGEST ENDPOINTS ====================

@app.route('/v1/digest/send-all', methods=['POST'])
def trigger_all_digests():
    """
    Trigger sending Friday digest emails to all users.
    Should be called by a cron job on Fridays.
    Requires admin_key query param for security.
    """
    admin_key = request.args.get('admin_key', '')
    expected_key = os.environ.get('ADMIN_API_KEY', 'dev-admin-key')
    
    if admin_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 401
    
    sent_count = send_all_friday_digests()
    return jsonify({
        "message": f"Digest emails sent",
        "sent_count": sent_count
    })


@app.route('/v1/digest/send-test', methods=['POST'])
def send_test_digest():
    """
    Send a test digest email to a specific email address.
    Body: { "email": "user@example.com" }
    Requires admin_key query param.
    """
    admin_key = request.args.get('admin_key', '')
    expected_key = os.environ.get('ADMIN_API_KEY', 'dev-admin-key')
    
    if admin_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    # Find user by email
    user = db.get_user_by_identifier(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get user preferences
    prefs = db.get_preferences(user['user_id'])
    if not prefs:
        return jsonify({"error": "User has no preferences set"}), 400
    
    # Get recommendations - use default Bay Area location if user has no location set
    from local_feeds import get_local_feed_recommendations
    user_location = prefs.get('location') or {}
    user_lat = user_location.get('lat') or 37.5485  # Default: Fremont, CA
    user_lng = user_location.get('lng') or -121.9886
    
    recommendations = get_local_feed_recommendations(
        profile=prefs,
        user_lat=user_lat,
        user_lng=user_lng,
        geocode_fn=geocode_to_lat_lng,
        max_items=5
    )
    
    if not recommendations:
        return jsonify({"error": "No recommendations available"}), 400
    
    # Send digest
    success = send_friday_digest_email(
        email, 
        user.get('name', ''), 
        recommendations, 
        FRONTEND_URL
    )
    
    if success:
        return jsonify({"message": f"Test digest sent to {email}"})
    else:
        return jsonify({"error": "Failed to send email. Check SMTP configuration."}), 500


@app.route('/v1/user/digest-preferences', methods=['GET', 'POST'])
def user_digest_preferences():
    """
    GET: Check if user has digest emails enabled.
    POST: Enable/disable digest emails. Body: { "enabled": true/false }
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = db.get_user_id_from_token(token) if token else None
    
    if not user_id:
        return jsonify({"error": "Authorization required"}), 401
    
    user = db.get_user_by_user_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if request.method == 'GET':
        # email_digest is 1 (enabled) by default, 0 means disabled
        enabled = user.get('email_digest', 1) != 0
        return jsonify({"digest_enabled": enabled})
    
    # POST - update preference
    data = request.json or {}
    enabled = data.get('enabled', True)
    
    with db.get_conn() as c:
        c.execute(
            "UPDATE users SET email_digest = ? WHERE user_id = ?",
            (1 if enabled else 0, user_id)
        )
    
    return jsonify({
        "message": f"Digest emails {'enabled' if enabled else 'disabled'}",
        "digest_enabled": enabled
    })


@app.route('/v1/status', methods=['GET'])
def api_status():
    """API status endpoint with circuit breaker information"""
    from datetime import datetime
    
    status = {
        "status": "ok", 
        "service": "activity-planner-api",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "google_places": bool(GOOGLE_PLACES_API_KEY),
            "local_feeds": bool(local_feeds),
            "caching": True
        },
        "circuit_breakers": {}
    }
    
    # Add circuit breaker status
    for source, cb_data in _circuit_breakers.items():
        status["circuit_breakers"][source] = {
            "failures": cb_data.get('failures', 0),
            "total_calls": cb_data.get('total_calls', 0),
            "last_failure": cb_data.get('last_failure').isoformat() if cb_data.get('last_failure') else None,
            "circuit_open": is_circuit_open(source)
        }
    
    return jsonify(status)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "activity-planner-api"})

def _warm_cache_on_startup():
    """Pre-fetch recommendations for known users on startup (background thread)."""
    import threading
    import time
    
    def _do_warm():
        time.sleep(2)  # Let the server start first
        try:
            users_with_prefs = db.get_all_users_with_preferences()
            if not users_with_prefs:
                # Warm cache for demo user with default prefs
                users_with_prefs = [{'id': 'demo_user', 'preferences': {
                    'home_location': {'value': 'San Francisco, CA'},
                    'categories': ['parks', 'museums', 'attractions'],
                    'kid_friendly': True,
                    'travel_time_ranges': ['15-30'],
                }}]
            
            for user in users_with_prefs[:3]:  # Warm top 3 users max
                user_id = user.get('id', 'demo_user')
                prefs = user.get('preferences', {})
                if not prefs:
                    continue
                cache_key = _get_warm_cache_key(user_id, prefs)
                if cache_key in _warm_cache:
                    continue
                print(f"[WARM_CACHE] Pre-warming for user {user_id}...")
                try:
                    items, sources = _fetch_recommendations_live(user_id, prefs, cache_key)
                    if items:
                        _warm_cache[cache_key] = {
                            'items': items,
                            'sources': sources,
                            'timestamp': datetime.now()
                        }
                        print(f"[WARM_CACHE] Warmed {len(items)} items for {user_id}")
                except Exception as e:
                    print(f"[WARM_CACHE] Error warming for {user_id}: {e}")
        except Exception as e:
            print(f"[WARM_CACHE] Startup warming error: {e}")
    
    t = threading.Thread(target=_do_warm, daemon=True)
    t.start()
    print("[WARM_CACHE] Background cache warming started")


# Warm cache on startup (non-blocking)
_warm_cache_on_startup()


if __name__ == '__main__':
    print("=" * 50)
    print("Activity Planner Backend API")
    print("=" * 50)
    print("Server starting on http://localhost:5001")
    print("API endpoints available at http://localhost:5001/v1")
    print("Health check: http://localhost:5001/health")
    print("=" * 50)
    app.run(debug=True, port=5001, host='0.0.0.0')
