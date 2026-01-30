# Onboarding Flow Recommendations

## Current State Assessment

The current onboarding asks for:
- Planning mode (family/individual)
- Home location
- Search radius
- Categories (checkboxes)
- Kid-friendly toggle
- Notification time

**Issues:**
- Too many fields upfront creates friction
- Checkboxes are less engaging than visual selection
- Missing key personalization signals (budget, energy level, timing)
- Notification time isn't essential for first experience

---

## Recommended Onboarding Flow

### Design Principles

1. **Progressive Disclosure** - Ask only what's needed, when it's needed
2. **Visual Selection** - Cards with images > checkboxes
3. **Smart Defaults** - Reduce required inputs
4. **Immediate Value** - Show recommendations quickly

---

### Screen 1: Welcome & Group Type

**Purpose:** Understand who the user is planning for (this affects all recommendations)

```
┌────────────────────────────────────────────┐
│                                            │
│         🎉 Weekend Planner                 │
│                                            │
│    Who are you planning weekends for?      │
│                                            │
│    ┌──────────┐  ┌──────────┐              │
│    │   👤     │  │   👫     │              │
│    │  Just    │  │  With    │              │
│    │   Me     │  │ Partner  │              │
│    └──────────┘  └──────────┘              │
│                                            │
│    ┌──────────┐  ┌──────────┐              │
│    │  👨‍👩‍👧‍👦   │  │   👥     │              │
│    │  Family  │  │  With    │              │
│    │ with Kids│  │ Friends  │              │
│    └──────────┘  └──────────┘              │
│                                            │
└────────────────────────────────────────────┘
```

**Data captured:** `group_type: "solo" | "couple" | "family" | "friends"`

---

### Screen 2: Location & Travel Preferences

**Purpose:** Establish location and real-time travel constraints via Maps integration

**Flow: Location Input (3 steps)**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STEP 2a: Auto-prompt for current location (Happy Path)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│                                            │
│         Where are you based?               │
│                                            │
│    ┌────────────────────────────────┐      │
│    │                                │      │
│    │   📍 Use My Current Location   │      │  ← Primary CTA
│    │                                │      │
│    │   For accurate travel times    │      │
│    │                                │      │
│    └────────────────────────────────┘      │
│                                            │
│    [No thanks, I'll enter manually]        │  ← Secondary link
│                                            │
└────────────────────────────────────────────┘

        ↓ User clicks "Use My Current Location"
        
┌────────────────────────────────────────────┐
│                                            │
│    ┌────────────────────────────────┐      │
│    │  🌐 Browser Location Prompt    │      │
│    │                                │      │
│    │  "Weekend Planner wants to     │      │
│    │   know your location"          │      │
│    │                                │      │
│    │   [Block]      [Allow]         │      │
│    │                                │      │
│    └────────────────────────────────┘      │
│                                            │
└────────────────────────────────────────────┘

        ↓ User ALLOWS → Go to Step 2c (Save prompt)
        ↓ User BLOCKS or clicks "No thanks" → Go to Step 2b
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STEP 2b: Manual entry fallback (if location declined)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│                                            │
│    No problem! How would you like to       │
│    enter your location?                    │
│                                            │
│    ┌──────────────┐  ┌──────────────┐      │
│    │              │  │              │      │
│    │   🏠 ZIP     │  │   📍 Full    │      │
│    │    Code      │  │   Address    │      │
│    │              │  │              │      │
│    │  (faster     │  │  (exact      │      │
│    │   entry)     │  │   times) ✓   │      │
│    │              │  │              │      │
│    └──────────────┘  └──────────────┘      │
│                                            │
└────────────────────────────────────────────┘

        ↓ User selects ZIP Code

┌────────────────────────────────────────────┐
│                                            │
│    Enter your ZIP code:                    │
│                                            │
│    ┌────────────────────────────────┐      │
│    │ 94102                          │      │
│    └────────────────────────────────┘      │
│                                            │
│    🔒 We only use this for travel times    │
│                                            │
│                          [Continue →]      │
│                                            │
└────────────────────────────────────────────┘

        ↓ OR User selects Full Address

┌────────────────────────────────────────────┐
│                                            │
│    Enter your address:                     │
│                                            │
│    ┌────────────────────────────────┐      │
│    │ 123 Main St, San Francisco, CA │      │
│    └────────────────────────────────┘      │
│       ↳ Autocomplete suggestions...        │
│                                            │
│    🔒 We only use this for travel times    │
│                                            │
│                          [Continue →]      │
│                                            │
└────────────────────────────────────────────┘

        ↓ After entry → Go to Step 2c
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STEP 2c: Save location prompt (optional)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│                                            │
│    ✓ Location set!                         │
│                                            │
│    📍 San Francisco, CA 94102              │
│                                            │
│    ┌────────────────────────────────┐      │
│    │  ☐  Save as my home location   │      │
│    │     (skip this step next time) │      │
│    └────────────────────────────────┘      │
│                                            │
│              [Continue →]                  │
│                                            │
└────────────────────────────────────────────┘

  • Checkbox is unchecked by default
  • User can simply click Continue without saving
  • No need for a separate "session only" option
```

**Location Flow State Machine:**

```
                    ┌─────────────┐
                    │   Start     │
                    └──────┬──────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Prompt: "Use current  │
              │  location?"            │
              └────────────┬───────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       ┌─────────┐   ┌──────────┐   ┌──────────┐
       │ ALLOW   │   │  BLOCK   │   │ "No      │
       │         │   │          │   │ thanks"  │
       └────┬────┘   └────┬─────┘   └────┬─────┘
            │             │              │
            │             └──────┬───────┘
            │                    │
            │                    ▼
            │         ┌───────────────────┐
            │         │ Show: ZIP or Full │
            │         │ Address options   │
            │         └─────────┬─────────┘
            │                   │
            │                   ▼
            │         ┌───────────────────┐
            │         │ User enters       │
            │         │ location manually │
            │         └─────────┬─────────┘
            │                   │
            └─────────┬─────────┘
                      │
                      ▼
            ┌───────────────────┐
            │ Geocode & verify  │
            └─────────┬─────────┘
                      │
                      ▼
            ┌───────────────────┐
            │ Show: "Save as    │
            │ home?" checkbox   │
            │ (optional)        │
            └─────────┬─────────┘
                      │
                      ▼
            ┌───────────────────┐
            │ User clicks       │
            │ [Continue →]      │
            └─────────┬─────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
           ▼                     ▼
    ┌─────────────┐      ┌─────────────┐
    │ ☑ Checked:  │      │ ☐ Unchecked:│
    │ Save to     │      │ Session     │
    │ localStorage│      │ only        │
    └──────┬──────┘      └──────┬──────┘
           │                    │
           └─────────┬──────────┘
                     │
                     ▼
            ┌───────────────────┐
            │ Continue to       │
            │ travel prefs...   │
            └───────────────────┘
```
│                                            │
│    How do you get around? (select all)     │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │   🚶     │ │   🚇     │ │   🚗     │  │
│    │ Walking/ │ │  Public  │ │   Car    │  │
│    │  Biking  │ │  Transit │ │          │  │
│    │    ☑     │ │    ☑     │ │    ☑     │  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    When do you usually head out on         │
│    weekends? (for traffic estimates)       │
│                                            │
│    Saturday departure times:               │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │ Morning  │ │ Midday   │ │ Afternoon│  │
│    │ 8-10 AM  │ │ 11-1 PM  │ │  2-5 PM  │  │
│    │    ☑     │ │    ☑     │ │    ☐     │  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    Sunday departure times:                 │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │ Morning  │ │ Midday   │ │ Afternoon│  │
│    │ 8-10 AM  │ │ 11-1 PM  │ │  2-5 PM  │  │
│    │    ☑     │ │    ☐     │ │    ☐     │  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    Max travel time you're comfortable      │
│    with? (select all that apply)           │
│                                            │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │  < 15    │ │  15-30   │ │  30-60   │  │
│    │ minutes  │ │ minutes  │ │ minutes  │  │
│    │ (nearby) │ │(moderate)│ │(worth it)│  │
│    │    ☑     │ │    ☑     │ │    ☐     │  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    ┌──────────┐                            │
│    │   60+    │  ← For special day trips   │
│    │ minutes  │                            │
│    │    ☐     │                            │
│    └──────────┘                            │
│                                            │
│    ┌────────────────────────────────────┐  │
│    │ 🗺️ Connect to Google Maps / Waze   │  │
│    │    for real-time traffic estimates │  │
│    └────────────────────────────────────┘  │
│                                            │
│                            [Continue →]    │
└────────────────────────────────────────────┘
```

**Why departure time matters:**
- Saturday 9 AM vs 2 PM = very different traffic
- Real-time estimates are much more accurate than static distances
- "30 minutes away" on Sunday morning ≠ "30 minutes away" on Saturday afternoon

**Data captured:**
- `home_location: { type, input, lat, lng, formatted_address }`
- `transportation: string[]` (multi-select: walking, transit, car)
- `departure_times: { saturday: string[], sunday: string[] }` (multi-select time windows)
- `travel_time_ranges: string[]` (multi-select: "0-15", "15-30", "30-60", "60+")
- `maps_connected: boolean` (Google Maps or Waze linked)

**Location Input Types:**

| Type | Example Input | Use Case |
|------|---------------|----------|
| ZIP Code | `94102` | Quick entry, privacy-conscious users |
| Full Address | `123 Main St, San Francisco, CA 94102` | Precise travel times from exact location |
| Current Location | (browser geolocation) | Fastest entry, most accurate |

**Location Input Validation & Geocoding:**

```javascript
// Detect input type and validate
function detectLocationType(input) {
  const trimmed = input.trim();
  
  // US ZIP code (5 digits or 5+4 format)
  if (/^\d{5}(-\d{4})?$/.test(trimmed)) {
    return 'zip';
  }
  
  // Has street number + name = likely full address
  if (/^\d+\s+\w+/.test(trimmed) && trimmed.length > 10) {
    return 'address';
  }
  
  // City, State format
  if (/^[a-zA-Z\s]+,\s*[A-Z]{2}$/i.test(trimmed)) {
    return 'city';
  }
  
  return 'unknown';
}

// Geocode the input to get lat/lng
async function geocodeLocation(input, type) {
  const response = await fetch(
    `https://maps.googleapis.com/maps/api/geocode/json?` +
    `address=${encodeURIComponent(input)}&` +
    `key=${GOOGLE_MAPS_API_KEY}`
  );
  
  const data = await response.json();
  
  if (data.status !== 'OK' || !data.results.length) {
    throw new Error('Could not find this location. Please check and try again.');
  }
  
  const result = data.results[0];
  
  return {
    type: type,
    input: input,
    lat: result.geometry.location.lat,
    lng: result.geometry.location.lng,
    formatted_address: result.formatted_address,
    // For ZIP codes, use the center point
    // For addresses, use exact location
    precision: type === 'zip' ? 'approximate' : 'exact'
  };
}

// Example outputs:
// ZIP: { type: 'zip', input: '94102', lat: 37.7786, lng: -122.4193, 
//        formatted_address: 'San Francisco, CA 94102, USA', precision: 'approximate' }
//
// Address: { type: 'address', input: '123 Main St, SF', lat: 37.7912, lng: -122.3965,
//            formatted_address: '123 Main St, San Francisco, CA 94105', precision: 'exact' }
```

**Privacy Note for Users:**

```
┌─────────────────────────────────────────────────────────┐
│  🔒 Privacy: Your location is only used to calculate    │
│     travel times. We never share your address.          │
│                                                         │
│     • ZIP code: ~1 mile accuracy (faster entry)         │
│     • Full address: Exact travel times (recommended)    │
└─────────────────────────────────────────────────────────┘
```

**Location Flow Implementation:**

```javascript
// Location state
const locationState = {
  source: null,        // 'geolocation', 'zip', 'address'
  data: null,          // geocoded location data
  saved: false,        // saved for future use
  sessionOnly: false   // only use for this session
};

// Step 2a: Request current location (happy path)
async function requestCurrentLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'));
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        // Reverse geocode to get address
        const { latitude, longitude } = position.coords;
        const locationData = await reverseGeocode(latitude, longitude);
        
        locationState.source = 'geolocation';
        locationState.data = {
          type: 'geolocation',
          input: 'Current location',
          lat: latitude,
          lng: longitude,
          formatted_address: locationData.formatted_address,
          precision: 'exact'
        };
        
        resolve(locationState.data);
      },
      (error) => {
        // User denied or error occurred
        reject(error);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
}

// Step 2b: Manual entry fallback
async function handleManualEntry(type, input) {
  const locationData = await geocodeLocation(input, type);
  
  locationState.source = type;
  locationState.data = locationData;
  
  return locationData;
}

// Step 2c: Handle continue with optional save checkbox
function handleLocationContinue(saveCheckboxChecked) {
  if (saveCheckboxChecked) {
    // User opted to save - store in localStorage
    localStorage.setItem('weekend_planner_location', JSON.stringify({
      ...locationState.data,
      savedAt: new Date().toISOString()
    }));
    locationState.saved = true;
  } else {
    // User skipped save - session only (default)
    sessionStorage.setItem('weekend_planner_location', JSON.stringify(locationState.data));
    locationState.saved = false;
  }
  
  // Continue to next step either way
  proceedToTravelPreferences();
}

// Check for saved location on app start
function checkSavedLocation() {
  const saved = localStorage.getItem('weekend_planner_location');
  if (saved) {
    const data = JSON.parse(saved);
    return {
      exists: true,
      data: data,
      // Optionally verify it's not too old
      isStale: daysSince(data.savedAt) > 30
    };
  }
  return { exists: false };
}

// Returning user flow
async function initLocationFlow() {
  const saved = checkSavedLocation();
  
  if (saved.exists && !saved.isStale) {
    // Show confirmation for returning users
    return showSavedLocationConfirmation(saved.data);
  }
  
  // New user or stale location - start fresh flow
  return showLocationRequestPrompt();
}
```

**Returning User Experience:**

```
┌────────────────────────────────────────────┐
│                                            │
│    Welcome back! 👋                        │
│                                            │
│    Use your saved location?                │
│                                            │
│    📍 San Francisco, CA 94102              │
│       Saved 5 days ago                     │
│                                            │
│    ┌────────────────────────────────┐      │
│    │      ✓ Yes, use this           │      │
│    └────────────────────────────────┘      │
│                                            │
│    [Update my location]                    │
│                                            │
└────────────────────────────────────────────┘
```

---

### Maps API Integration

**Supported Providers:**

| Provider | API | Best For |
|----------|-----|----------|
| Google Maps | Directions API + Distance Matrix API | Comprehensive, all transport modes |
| Waze | Waze Transport SDK | Real-time traffic, driving only |
| Apple Maps | MapKit JS | iOS users, privacy-focused |

**How it works:**

```
┌─────────────────────────────────────────────────────────────┐
│                      RECOMMENDATION FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User selects departure window: "Saturday 9-10 AM"       │
│                         ↓                                   │
│  2. Backend queries candidate places within max radius      │
│                         ↓                                   │
│  3. For each place, call Maps API:                          │
│     GET /directions?origin={user_home}                      │
│                     &destination={place}                    │
│                     &departure_time={sat_9am}               │
│                     &mode={driving|transit|walking}         │
│                         ↓                                   │
│  4. Get real travel time with traffic:                      │
│     { duration_in_traffic: "23 mins",                       │
│       duration: "18 mins",        ← without traffic         │
│       distance: "8.2 mi" }                                  │
│                         ↓                                   │
│  5. Filter places where travel_time fits user's ranges      │
│                         ↓                                   │
│  6. Show recommendations with accurate travel times         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**API Integration Code:**

```javascript
// Google Maps Distance Matrix API
async function getTravelTime(origin, destination, departureTime, mode) {
  const response = await fetch(
    `https://maps.googleapis.com/maps/api/distancematrix/json?` +
    `origins=${encodeURIComponent(origin)}&` +
    `destinations=${encodeURIComponent(destination)}&` +
    `departure_time=${departureTime.getTime() / 1000}&` +
    `mode=${mode}&` +  // driving, transit, walking, bicycling
    `traffic_model=best_guess&` +
    `key=${GOOGLE_MAPS_API_KEY}`
  );
  
  const data = await response.json();
  const element = data.rows[0].elements[0];
  
  return {
    duration_seconds: element.duration.value,
    duration_in_traffic_seconds: element.duration_in_traffic?.value,
    duration_text: element.duration_in_traffic?.text || element.duration.text,
    distance_meters: element.distance.value,
    distance_text: element.distance.text
  };
}

// Waze API (via Waze Transport SDK)
async function getWazeTravelTime(origin, destination, departureTime) {
  // Waze provides real-time traffic data
  const response = await waze.routes({
    from: origin,
    to: destination,
    arriveAt: departureTime,  // or departAt
    vehicleType: 'PRIVATE'
  });
  
  return {
    duration_seconds: response.routes[0].duration,
    duration_text: formatDuration(response.routes[0].duration),
    has_traffic_jam: response.routes[0].jamLevel > 2
  };
}
```

**Caching Strategy:**

```javascript
// Cache travel times to reduce API calls
const travelTimeCache = new Map();

function getCacheKey(origin, destination, departureWindow, mode) {
  // Round departure to 30-min windows for caching
  const windowKey = Math.floor(departureWindow.getTime() / (30 * 60 * 1000));
  return `${origin}|${destination}|${windowKey}|${mode}`;
}

async function getCachedTravelTime(origin, destination, departureTime, mode) {
  const key = getCacheKey(origin, destination, departureTime, mode);
  
  if (travelTimeCache.has(key)) {
    const cached = travelTimeCache.get(key);
    // Cache valid for 1 hour
    if (Date.now() - cached.timestamp < 60 * 60 * 1000) {
      return cached.data;
    }
  }
  
  const data = await getTravelTime(origin, destination, departureTime, mode);
  travelTimeCache.set(key, { data, timestamp: Date.now() });
  return data;
}
```

**Traffic Level Definitions:**

| Level | Meaning | Example |
|-------|---------|---------|
| 🟢 Light | < 10% slower than no traffic | "18 min now vs 17 min with no traffic" |
| 🟡 Moderate | 10-30% slower than no traffic | "23 min now vs 18 min with no traffic (+5 min)" |
| 🔴 Heavy | > 30% slower than no traffic | "35 min now vs 20 min with no traffic (+15 min)" |
| ⚫ Severe | > 60% slower than no traffic | "50 min now vs 25 min with no traffic (+25 min)" |

```javascript
function getTrafficLevel(durationWithTraffic, durationNoTraffic) {
  const ratio = durationWithTraffic / durationNoTraffic;
  
  if (ratio < 1.10) return { level: 'light', emoji: '🟢', label: 'Light traffic' };
  if (ratio < 1.30) return { level: 'moderate', emoji: '🟡', label: 'Moderate traffic' };
  if (ratio < 1.60) return { level: 'heavy', emoji: '🔴', label: 'Heavy traffic' };
  return { level: 'severe', emoji: '⚫', label: 'Severe traffic' };
}
```

**Recommendation Card with Real-Time Travel:**

```
┌─────────────────────────────────────────────┐
│  🌲 Golden Gate Park                        │
│  Parks • ⭐ 4.8                              │
├─────────────────────────────────────────────┤
│                                             │
│  🚗 23 min by car (Saturday 9 AM)           │
│     └─ 🟡 Moderate traffic (+5 min)         │
│        (18 min without traffic)             │
│                                             │
│  🚇 35 min by transit                       │
│     └─ Take MUNI N → walk 5 min             │
│                                             │
│  [View on Waze]  [View on Google Maps]      │
│                                             │
├─────────────────────────────────────────────┤
│  [Add to Calendar]  [👍]  [Already Been]    │
└─────────────────────────────────────────────┘
```

**More Examples:**

```
🟢 Light traffic (+2 min)
   "22 min — basically normal, good time to go"

🟡 Moderate traffic (+8 min)  
   "28 min — some slowdowns, expect minor delays"

🔴 Heavy traffic (+15 min)
   "35 min — significant delays, consider leaving earlier or later"

⚫ Severe traffic (+25 min)
   "45 min — major delays, maybe pick a closer destination"
```

**Deep Links to Navigation Apps:**

```javascript
function getNavigationLinks(destination, userLocation) {
  const destEncoded = encodeURIComponent(destination.address);
  const coords = `${destination.lat},${destination.lng}`;
  
  return {
    google_maps: `https://www.google.com/maps/dir/?api=1&destination=${destEncoded}`,
    waze: `https://waze.com/ul?ll=${coords}&navigate=yes`,
    apple_maps: `http://maps.apple.com/?daddr=${destEncoded}`
  };
}
```

---

### Screen 3: Interests (Pick 3+)

**Purpose:** Understand activity preferences through visual selection

```
┌────────────────────────────────────────────┐
│                                            │
│    What do you enjoy? (pick at least 3)    │
│                                            │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│    │  🌲🏕️   │ │  🎨🖼️   │ │  🍽️🍷   │     │
│    │ Nature  │ │ Arts &  │ │ Food &  │     │
│    │ & Parks │ │ Culture │ │ Drinks  │     │
│    └─────────┘ └─────────┘ └─────────┘     │
│                                            │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│    │  🎢🎯   │ │  📚🔬   │ │  🎵🎭   │     │
│    │Adventure│ │Learning │ │ Enter-  │     │
│    │& Sports │ │& Science│ │tainment │     │
│    └─────────┘ └─────────┘ └─────────┘     │
│                                            │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│    │  🧘☕   │ │  🛍️🏪   │ │  🎪🎠   │     │
│    │Relaxa-  │ │Shopping │ │ Local   │     │
│    │  tion   │ │& Markets│ │ Events  │     │
│    └─────────┘ └─────────┘ └─────────┘     │
│                                            │
│                            [Continue →]    │
└────────────────────────────────────────────┘
```

**Category mappings:**
| Visual | Backend Categories |
|--------|-------------------|
| Nature & Parks | parks, trails, beaches, gardens |
| Arts & Culture | museums, galleries, historic_sites |
| Food & Drinks | restaurants, cafes, breweries, food_tours |
| Adventure & Sports | hiking, sports, adventure, outdoor_activities |
| Learning & Science | science_centers, workshops, classes |
| Entertainment | movies, arcades, bowling, escape_rooms |
| Relaxation | spas, scenic_views, picnic_spots |
| Shopping & Markets | farmers_markets, shopping_districts |
| Local Events | festivals, concerts, community_events |

**Data captured:** `interests: string[]` (minimum 3)

---

### Screen 4: Activity Style

**Purpose:** Understand energy level and time preferences

```
┌────────────────────────────────────────────┐
│                                            │
│    What's your ideal weekend vibe?         │
│                                            │
│    Energy Level:                           │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │   🧘     │ │   🚶     │ │   🏃     │  │
│    │ Relaxing │ │ Moderate │ │  Active  │  │
│    │(sit,view)│ │(walking) │ │(adventure│  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    How much time per activity?             │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │  1-2 hr  │ │  3-4 hr  │ │ Full Day │  │
│    │  Quick   │ │ Half-day │ │  Outing  │  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    When do you prefer activities?          │
│    □ Morning (before noon)                 │
│    □ Afternoon (noon - 5pm)                │
│    □ Evening (after 5pm)                   │
│                                            │
│                            [Continue →]    │
└────────────────────────────────────────────┘
```

**Data captured:**
- `energy_level: "relaxing" | "moderate" | "active"`
- `time_commitment: "quick" | "half_day" | "full_day"`
- `preferred_times: string[]`

---

### Screen 5: Constraints (Optional - Can Skip)

**Purpose:** Capture budget and accessibility needs

```
┌────────────────────────────────────────────┐
│                                            │
│    A few more details (optional)           │
│                                            │
│    Budget per outing:                      │
│    ○ Free activities only                  │
│    ○ Under $25 per person                  │
│    ○ Under $50 per person                  │
│    ○ No budget limit                       │
│                                            │
│    Accessibility needs:                    │
│    □ Wheelchair accessible                 │
│    □ Stroller friendly                     │
│    □ Limited walking                       │
│                                            │
│    Prefer to avoid:                        │
│    □ Crowded places                        │
│    □ Tourist spots                         │
│    □ Requires reservations                 │
│    □ Long wait times                       │
│                                            │
│    [Skip]              [Finish Setup →]    │
└────────────────────────────────────────────┘
```

**Data captured:**
- `budget: "free" | "low" | "moderate" | "any"`
- `accessibility: string[]`
- `avoid: string[]`

---

## Complete Data Model

```javascript
{
  // Screen 1
  "group_type": "family",        // solo, couple, family, friends
  
  // Screen 2
  "home_location": {
    "type": "geolocation",                      // geolocation, zip, address
    "input": "Current location",                // user's original input
    "lat": 37.7786,
    "lng": -122.4193,
    "formatted_address": "San Francisco, CA 94102, USA",
    "precision": "exact",                       // approximate (zip) or exact (address/geolocation)
    "saved": true,                              // saved for future use
    "saved_at": "2026-01-25T10:30:00Z"          // when location was saved
  },
  "transportation": ["walking", "transit", "car"],  // multi-select
  "departure_times": {
    "saturday": ["morning", "midday"],    // morning (8-10), midday (11-1), afternoon (2-5)
    "sunday": ["morning"]
  },
  "travel_time_ranges": ["0-15", "15-30"],          // multi-select: 0-15, 15-30, 30-60, 60+
  "maps_provider": "google",                        // google, waze, apple
  "maps_connected": true
  
  // Screen 3
  "interests": [
    "nature",
    "arts_culture", 
    "food_drinks"
  ],
  
  // Screen 4
  "energy_level": "moderate",    // relaxing, moderate, active
  "time_commitment": "half_day", // quick, half_day, full_day
  "preferred_times": ["morning", "afternoon"],
  
  // Screen 5 (optional)
  "budget": "moderate",          // free, low, moderate, any
  "accessibility": [],
  "avoid": ["crowds"],
  
  // Settings (moved from onboarding)
  "notification_time_local": "16:00",
  "notification_day": "friday",
  "dedup_window_days": 365,
  "calendar_dedup_opt_in": false
}
```

---

## Derived Preferences

Based on user selections, automatically set:

| User Selection | Auto-set Preferences |
|----------------|---------------------|
| Group: Family with Kids | `kid_friendly: true`, suggest parks, museums, zoos |
| Group: Couple | Include romantic spots, nicer restaurants |
| Energy: Relaxing | Filter out hikes, active sports |
| Energy: Active | Prioritize outdoor adventures, sports |
| Transport: [walking] only | Show walking directions, query walking times |
| Transport: [transit] included | Show transit routes, query transit times |
| Transport: [car] included | Show driving with traffic, parking info |
| Departure: Sat morning | Query traffic for ~9 AM Saturday |
| Departure: Sat afternoon | Query traffic for ~3 PM Saturday |
| Time range: [0-15] only | Badge: "Quick trip", prioritize nearby |
| Time range: includes [60+] | Include "Day trip worthy" destinations |
| Budget: Free | Filter to free activities only |

### Real-Time Travel Filtering with Maps API

```javascript
// Parse range string like "15-30" into [15, 30]
function parseRange(rangeStr) {
  if (rangeStr.endsWith('+')) {
    return [parseInt(rangeStr), Infinity];
  }
  const [min, max] = rangeStr.split('-').map(Number);
  return [min, max];
}

// Convert departure time window to actual datetime
function getDepartureTime(day, window) {
  const today = new Date();
  const daysUntilTarget = day === 'saturday' 
    ? (6 - today.getDay() + 7) % 7 || 7
    : (7 - today.getDay() + 7) % 7 || 7;
  
  const targetDate = new Date(today);
  targetDate.setDate(today.getDate() + daysUntilTarget);
  
  const hours = {
    'morning': 9,    // 9 AM
    'midday': 12,    // 12 PM
    'afternoon': 15  // 3 PM
  };
  
  targetDate.setHours(hours[window], 0, 0, 0);
  return targetDate;
}

// Main filtering function with real-time travel times
async function filterPlacesWithRealTravelTime(places, userPrefs) {
  const results = [];
  
  // Get user's preferred departure time for traffic estimates
  const primaryDeparture = getDepartureTime(
    userPrefs.departure_times.saturday?.length ? 'saturday' : 'sunday',
    userPrefs.departure_times.saturday?.[0] || userPrefs.departure_times.sunday?.[0]
  );
  
  for (const place of places) {
    // Get real travel time from Maps API
    const travelTimes = {};
    
    for (const mode of userPrefs.transportation) {
      const apiMode = mode === 'car' ? 'driving' : mode;
      const travelData = await getCachedTravelTime(
        `${userPrefs.home_location.lat},${userPrefs.home_location.lng}`,
        `${place.lat},${place.lng}`,
        primaryDeparture,
        apiMode
      );
      
      travelTimes[mode] = {
        duration_min: Math.ceil(travelData.duration_in_traffic_seconds / 60),
        duration_text: travelData.duration_text,
        has_traffic: travelData.duration_in_traffic_seconds > travelData.duration_seconds * 1.2
      };
    }
    
    // Find best travel option
    const bestMode = Object.entries(travelTimes)
      .sort((a, b) => a[1].duration_min - b[1].duration_min)[0];
    
    const bestTravelTime = bestMode[1].duration_min;
    
    // Check if travel time fits user's acceptable ranges
    const timeMatch = userPrefs.travel_time_ranges.some(range => {
      const [min, max] = parseRange(range);
      return bestTravelTime >= min && bestTravelTime < max;
    });
    
    if (timeMatch) {
      results.push({
        ...place,
        travel_times: travelTimes,
        best_travel_mode: bestMode[0],
        best_travel_time_min: bestTravelTime,
        departure_context: primaryDeparture.toLocaleString()
      });
    }
  }
  
  // Sort by travel time (closest first)
  return results.sort((a, b) => a.best_travel_time_min - b.best_travel_time_min);
}

// Example output for a place:
// {
//   name: "Golden Gate Park",
//   travel_times: {
//     car: { duration_min: 23, duration_text: "23 mins", has_traffic: true },
//     transit: { duration_min: 35, duration_text: "35 mins", has_traffic: false },
//     walking: { duration_min: 85, duration_text: "1 hr 25 mins", has_traffic: false }
//   },
//   best_travel_mode: "car",
//   best_travel_time_min: 23,
//   departure_context: "Saturday, 9:00 AM"
// }
```

---

## Migration from Current Flow

### Quick Wins (Minimal Code Changes)

1. **Add energy level** - New dropdown/radio in current form
2. **Add budget range** - New dropdown in current form
3. **Replace "kid-friendly" checkbox** with "Who's joining?" dropdown
4. **Move notification time** to a Settings screen
5. **Add "Prefer to avoid"** multi-select

### Full Redesign

1. Split form into multi-step wizard
2. Replace checkboxes with visual card selection
3. Add progress indicator
4. Implement auto-location detection
5. Add "Skip" option for optional screens

---

## Success Metrics

Track these to measure onboarding effectiveness:

| Metric | Target |
|--------|--------|
| Onboarding completion rate | > 80% |
| Time to complete | < 90 seconds |
| First recommendation click | > 60% |
| Return visit (week 2) | > 40% |
| Preferences updated later | < 20% (means initial capture was good) |

---

## A/B Test Ideas

1. **Short vs Long**: 3 screens vs 5 screens
2. **Visual vs List**: Card selection vs checkboxes
3. **Required vs Optional**: Make Screen 5 required or skippable
4. **Defaults**: Pre-select popular options vs start blank
