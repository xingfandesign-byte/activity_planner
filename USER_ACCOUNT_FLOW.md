# User Account & Onboarding Flow

This document separates the experience between **first-time users** (full onboarding) and **recurring users** (quick start with saved preferences).

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    App Launch                                                   │
│        │                                                        │
│        ▼                                                        │
│    ┌─────────────────┐                                          │
│    │ Check for saved │                                          │
│    │ account/session │                                          │
│    └────────┬────────┘                                          │
│             │                                                   │
│    ┌────────┴────────┐                                          │
│    │                 │                                          │
│    ▼                 ▼                                          │
│  No Account      Has Account                                    │
│    │                 │                                          │
│    ▼                 ▼                                          │
│  FIRST-TIME      RECURRING                                      │
│  ONBOARDING      USER VIEW                                      │
│  (Multi-step)    (One-page)                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: First-Time User Onboarding

### Step 1: Welcome & Account Creation

**Purpose:** Create account for saving preferences and personalization

```
┌────────────────────────────────────────────┐
│                                            │
│         🎉 Weekend Planner                 │
│                                            │
│    Get personalized weekend ideas          │
│    delivered every Friday                  │
│                                            │
│    ─────────────────────────────────────   │
│                                            │
│    Create your account:                    │
│                                            │
│    ○ Continue with Email                   │
│    ○ Continue with Phone                   │
│                                            │
│    ┌────────────────────────────────┐      │
│    │ 📧 Email or 📱 Phone number   │      │
│    └────────────────────────────────┘      │
│                                            │
│    ┌────────────────────────────────┐      │
│    │                                │      │
│    │        Continue →              │      │
│    │                                │      │
│    └────────────────────────────────┘      │
│                                            │
│    ─────────────────────────────────────   │
│                                            │
│    Or continue with:                       │
│                                            │
│    [G] Google    [A] Apple    [F] Facebook │
│                                            │
│    ─────────────────────────────────────   │
│                                            │
│    [Skip for now - use as guest]           │
│                                            │
│    By continuing, you agree to our         │
│    Terms of Service and Privacy Policy     │
│                                            │
└────────────────────────────────────────────┘
```

**Email Flow:**
```
┌────────────────────────────────────────────┐
│                                            │
│    Enter your email:                       │
│                                            │
│    ┌────────────────────────────────┐      │
│    │ hello@example.com              │      │
│    └────────────────────────────────┘      │
│                                            │
│    Create a password:                      │
│                                            │
│    ┌────────────────────────────────┐      │
│    │ ••••••••••                     │      │
│    └────────────────────────────────┘      │
│    ✓ At least 8 characters                 │
│                                            │
│    ☐ Send me weekly digest emails          │
│                                            │
│              [Create Account]              │
│                                            │
│    Already have an account? [Sign in]      │
│                                            │
└────────────────────────────────────────────┘
```

**Phone Flow:**
```
┌────────────────────────────────────────────┐
│                                            │
│    Enter your phone number:                │
│                                            │
│    ┌──────┐ ┌──────────────────────┐       │
│    │ +1 ▼ │ │ (555) 123-4567       │       │
│    └──────┘ └──────────────────────┘       │
│                                            │
│              [Send Code]                   │
│                                            │
└────────────────────────────────────────────┘

        ↓ After sending code

┌────────────────────────────────────────────┐
│                                            │
│    Enter the 6-digit code sent to          │
│    +1 (555) 123-4567                        │
│                                            │
│    ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│    │  1 │ │  2 │ │  3 │ │  4 │ │  5 │ │  6 │
│    └────┘ └────┘ └────┘ └────┘ └────┘ └────┘
│                                            │
│    Didn't receive it? [Resend code]        │
│                                            │
│              [Verify]                      │
│                                            │
└────────────────────────────────────────────┘
```

---

### Step 2: Who Are You Planning For?

```
┌────────────────────────────────────────────┐
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
│    💾 This will be saved to your account   │
│                                            │
└────────────────────────────────────────────┘
```

**Data saved:** `group_type`

---

### Step 3: Location & Travel Preferences

(Same as current flow - see ONBOARDING_RECOMMENDATIONS.md)

**Data saved:**
- `home_location`
- `transportation`
- `departure_times`
- `travel_time_ranges`

---

### Step 4: What Do You Enjoy?

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
│    ... (full grid)                         │
│                                            │
│    💾 This will be saved to your account   │
│                                            │
└────────────────────────────────────────────┘
```

**Data saved:** `interests[]`

---

### Step 5: Ideal Weekend Vibe

```
┌────────────────────────────────────────────┐
│                                            │
│    What's your ideal weekend vibe?         │
│                                            │
│    Energy Level:                           │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │   🧘     │ │   🚶     │ │   🏃     │  │
│    │ Relaxing │ │ Moderate │ │  Active  │  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    Time per activity:                      │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│    │  1-2 hr  │ │  3-4 hr  │ │ Full Day │  │
│    └──────────┘ └──────────┘ └──────────┘  │
│                                            │
│    💾 This will be saved to your account   │
│                                            │
└────────────────────────────────────────────┘
```

**Data saved:**
- `energy_level`
- `time_commitment`

---

### Step 6: Constraints (Optional)

```
┌────────────────────────────────────────────┐
│                                            │
│    A few more details (optional)           │
│                                            │
│    Budget:  [Free] [<$25] [<$50] [Any]     │
│                                            │
│    Accessibility:                          │
│    ☐ Wheelchair accessible                 │
│    ☐ Stroller friendly                     │
│                                            │
│    Prefer to avoid:                        │
│    ☐ Crowds  ☐ Tourist spots  ☐ Long waits │
│                                            │
│    [Skip]            [Save & Continue →]   │
│                                            │
└────────────────────────────────────────────┘
```

**Data saved:**
- `budget`
- `accessibility[]`
- `avoid[]`

---

### Step 7: Onboarding Complete

```
┌────────────────────────────────────────────┐
│                                            │
│         🎉 You're all set!                 │
│                                            │
│    Your preferences have been saved.       │
│    Here's a summary:                       │
│                                            │
│    ┌────────────────────────────────────┐  │
│    │ 📍 San Francisco, CA 94102         │  │
│    │ 👨‍👩‍👧‍👦 Planning for: Family with Kids  │  │
│    │ 🚗 Travel: Car, Transit            │  │
│    │ ⏱️ Max travel: 30 min              │  │
│    │ 🎯 Interests: Nature, Arts, Food   │  │
│    │ 🧘 Vibe: Moderate energy           │  │
│    │ 💰 Budget: Under $50               │  │
│    └────────────────────────────────────┘  │
│                                            │
│    You can update these anytime in         │
│    Settings.                               │
│                                            │
│         [🎉 Show My Recommendations]       │
│                                            │
└────────────────────────────────────────────┘
```

---

## Part 2: Recurring User Experience

### Quick Login

```
┌────────────────────────────────────────────┐
│                                            │
│         🎉 Weekend Planner                 │
│                                            │
│    Welcome back!                           │
│                                            │
│    ┌────────────────────────────────┐      │
│    │ 📧 Email or 📱 Phone number   │      │
│    └────────────────────────────────┘      │
│                                            │
│    ┌────────────────────────────────┐      │
│    │ 🔒 Password                    │      │
│    └────────────────────────────────┘      │
│                                            │
│    ☐ Remember me                           │
│                                            │
│              [Sign In]                     │
│                                            │
│    [Forgot password?]                      │
│                                            │
│    ─────────────────────────────────────   │
│                                            │
│    Or sign in with:                        │
│                                            │
│    [G] Google    [A] Apple    [F] Facebook │
│                                            │
│    ─────────────────────────────────────   │
│                                            │
│    Don't have an account? [Sign up]        │
│                                            │
└────────────────────────────────────────────┘
```

---

### Returning User Dashboard (One-Page View)

**Purpose:** Show saved preferences at a glance with ability to quickly adjust before viewing recommendations

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Weekend Planner                        [Settings] [Sign Out]   │
│                                                                 │
│  Welcome back, Sarah! 👋                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  YOUR SAVED PREFERENCES                              [Edit All] │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  📍 LOCATION                                    [Edit]  │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  San Francisco, CA 94102                                │    │
│  │  Saved home location                                    │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  👨‍👩‍👧‍👦 PLANNING FOR                                 [Edit]  │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  Family with Kids                                       │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  🚗 TRAVEL PREFERENCES                          [Edit]  │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  Transportation: Car, Transit                           │    │
│  │  Max travel time: 15-30 min                             │    │
│  │  Typical departure: Saturday morning, Sunday morning    │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  🎯 INTERESTS                                   [Edit]  │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  🌲 Nature & Parks                                      │    │
│  │  🎨 Arts & Culture                                      │    │
│  │  🍽️ Food & Drinks                                       │    │
│  │  📚 Learning & Science                                  │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  🧘 IDEAL VIBE                                  [Edit]  │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  Energy: Moderate (walking, exploring)                  │    │
│  │  Time: Half-day (3-4 hours)                             │    │
│  │  Budget: Under $50 per person                           │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  ⚙️ OTHER PREFERENCES                           [Edit]  │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  ✓ Kid-friendly activities                              │    │
│  │  ✓ Stroller friendly                                    │    │
│  │  Avoiding: Crowds, Long waits                           │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │           🎉 Show This Weekend's Recommendations        │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  QUICK ADJUSTMENTS FOR THIS WEEKEND:                            │
│                                                                 │
│  Different location?  ┌─────────────────────────────┐           │
│                       │ Use saved location ▼        │           │
│                       └─────────────────────────────┘           │
│                                                                 │
│  Planning for someone else?                                     │
│  [👤 Solo] [👫 Couple] [👨‍👩‍👧‍👦 Family] [👥 Friends]               │
│                                                                 │
│  More time this weekend?                                        │
│  [< 15 min] [15-30 min] [30-60 min] [60+ min day trip]          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Inline Edit Modal

When user clicks [Edit] on any section:

```
┌────────────────────────────────────────────┐
│                                        ✕   │
│                                            │
│  Edit: Interests                           │
│                                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │  🌲🏕️   │ │  🎨🖼️   │ │  🍽️🍷   │       │
│  │ Nature  │ │ Arts &  │ │ Food &  │       │
│  │    ✓    │ │    ✓    │ │    ✓    │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│  ... (full grid with current selections)   │
│                                            │
│  [Cancel]                    [Save Changes]│
│                                            │
└────────────────────────────────────────────┘
```

---

## Data Model

### User Account

```javascript
{
  "user_id": "usr_abc123",
  "created_at": "2026-01-20T10:00:00Z",
  "last_login": "2026-01-30T08:30:00Z",
  
  // Authentication
  "auth": {
    "method": "email",           // email, phone, google, apple, facebook
    "email": "sarah@example.com",
    "phone": null,
    "email_verified": true,
    "phone_verified": false
  },
  
  // Profile
  "profile": {
    "name": "Sarah",
    "avatar_url": null
  },
  
  // Notification preferences
  "notifications": {
    "email_digest": true,
    "sms_digest": false,
    "digest_day": "friday",
    "digest_time": "16:00"
  }
}
```

### Saved Preferences

```javascript
{
  "user_id": "usr_abc123",
  "updated_at": "2026-01-25T14:30:00Z",
  
  // Who
  "group_type": "family",
  
  // Where
  "home_location": {
    "type": "address",
    "input": "123 Main St, San Francisco, CA",
    "lat": 37.7749,
    "lng": -122.4194,
    "formatted_address": "123 Main St, San Francisco, CA 94102",
    "precision": "exact"
  },
  
  // Travel
  "transportation": ["car", "transit"],
  "departure_times": {
    "saturday": ["morning"],
    "sunday": ["morning"]
  },
  "travel_time_ranges": ["0-15", "15-30"],
  
  // Interests
  "interests": ["nature", "arts_culture", "food_drinks", "learning"],
  
  // Vibe
  "energy_level": "moderate",
  "time_commitment": "half_day",
  
  // Constraints
  "budget": "moderate",
  "accessibility": ["stroller"],
  "avoid": ["crowds", "waits"],
  
  // Derived
  "kid_friendly": true  // derived from group_type === "family"
}
```

---

## Authentication Implementation

### Email/Password

```javascript
// Sign up
async function signUpWithEmail(email, password) {
  const response = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      method: 'email',
      email, 
      password 
    })
  });
  
  if (response.ok) {
    const { user_id, token } = await response.json();
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_id', user_id);
    return { success: true, user_id };
  }
  
  return { success: false, error: await response.text() };
}

// Sign in
async function signInWithEmail(email, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (response.ok) {
    const { user_id, token, preferences } = await response.json();
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_id', user_id);
    
    // Load saved preferences
    if (preferences) {
      loadSavedPreferences(preferences);
    }
    
    return { success: true, user_id, hasPreferences: !!preferences };
  }
  
  return { success: false, error: await response.text() };
}
```

### Phone (SMS OTP)

```javascript
// Request OTP
async function requestPhoneOTP(phoneNumber) {
  const response = await fetch(`${API_BASE}/auth/phone/request-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phoneNumber })
  });
  
  return response.ok;
}

// Verify OTP
async function verifyPhoneOTP(phoneNumber, code) {
  const response = await fetch(`${API_BASE}/auth/phone/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phoneNumber, code })
  });
  
  if (response.ok) {
    const { user_id, token, is_new_user, preferences } = await response.json();
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_id', user_id);
    
    return { 
      success: true, 
      user_id, 
      isNewUser: is_new_user,
      hasPreferences: !!preferences 
    };
  }
  
  return { success: false, error: await response.text() };
}
```

### OAuth (Google/Apple/Facebook)

```javascript
// OAuth sign in
async function signInWithOAuth(provider) {
  // Redirect to OAuth provider
  const redirectUrl = `${API_BASE}/auth/oauth/${provider}?redirect=${window.location.origin}/auth/callback`;
  window.location.href = redirectUrl;
}

// Handle OAuth callback
async function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  const user_id = params.get('user_id');
  const is_new_user = params.get('is_new_user') === 'true';
  
  if (token && user_id) {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_id', user_id);
    
    if (is_new_user) {
      // New user - go to onboarding step 2
      window.location.href = '/onboarding?step=2';
    } else {
      // Existing user - go to dashboard
      window.location.href = '/dashboard';
    }
  }
}
```

---

## App Flow Logic

```javascript
// Main app initialization
async function initApp() {
  const token = localStorage.getItem('auth_token');
  const userId = localStorage.getItem('user_id');
  
  if (!token || !userId) {
    // No account - show first-time onboarding
    showFirstTimeOnboarding();
    return;
  }
  
  // Validate token and get preferences
  try {
    const response = await fetch(`${API_BASE}/user/preferences`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      const preferences = await response.json();
      
      if (preferences && Object.keys(preferences).length > 0) {
        // Has saved preferences - show returning user dashboard
        showReturningUserDashboard(preferences);
      } else {
        // Has account but no preferences - continue onboarding from step 2
        showOnboardingFromStep(2);
      }
    } else if (response.status === 401) {
      // Token expired - show login
      showLoginScreen();
    }
  } catch (error) {
    console.error('Error loading preferences:', error);
    showLoginScreen();
  }
}

function showFirstTimeOnboarding() {
  // Show step 1 (account creation)
  document.getElementById('first-time-onboarding').style.display = 'block';
  document.getElementById('returning-user-dashboard').style.display = 'none';
  goToStep(1);
}

function showReturningUserDashboard(preferences) {
  // Show one-page dashboard with saved preferences
  document.getElementById('first-time-onboarding').style.display = 'none';
  document.getElementById('returning-user-dashboard').style.display = 'block';
  populateDashboard(preferences);
}

function showLoginScreen() {
  // Show login form
  document.getElementById('login-screen').style.display = 'block';
  document.getElementById('first-time-onboarding').style.display = 'none';
  document.getElementById('returning-user-dashboard').style.display = 'none';
}
```

---

## API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/signup` | POST | Create account (email/password) |
| `/auth/login` | POST | Sign in (email/password) |
| `/auth/logout` | POST | Sign out |
| `/auth/phone/request-otp` | POST | Send SMS verification code |
| `/auth/phone/verify-otp` | POST | Verify SMS code |
| `/auth/oauth/{provider}` | GET | OAuth redirect |
| `/auth/oauth/callback` | GET | OAuth callback |
| `/auth/forgot-password` | POST | Request password reset |
| `/auth/reset-password` | POST | Reset password with token |

### User & Preferences

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/user/profile` | GET | Get user profile |
| `/user/profile` | PUT | Update user profile |
| `/user/preferences` | GET | Get saved preferences |
| `/user/preferences` | PUT | Update preferences |
| `/user/preferences/{section}` | PATCH | Update single section |
| `/user/delete` | DELETE | Delete account |

---

## Security Considerations

1. **Password Requirements:**
   - Minimum 8 characters
   - Hashed with bcrypt (cost factor 12)
   
2. **Phone OTP:**
   - 6-digit code
   - Expires in 10 minutes
   - Max 3 attempts before lockout
   - Rate limit: 1 OTP per minute

3. **Session Management:**
   - JWT tokens with 7-day expiry
   - Refresh tokens with 30-day expiry
   - Secure, HttpOnly cookies for web

4. **Data Privacy:**
   - Location data encrypted at rest
   - User can delete account and all data
   - GDPR/CCPA compliant data export

---

## Guest Mode

Users can skip account creation and use as guest:

```javascript
function continueAsGuest() {
  // Generate temporary guest ID
  const guestId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  sessionStorage.setItem('guest_id', guestId);
  
  // Show onboarding from step 2 (skip account creation)
  showOnboardingFromStep(2);
}
```

**Guest limitations:**
- Preferences saved to sessionStorage only
- Lost when browser closes
- No weekly digest emails
- Prompt to create account after 3 visits
