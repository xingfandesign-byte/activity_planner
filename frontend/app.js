// Weekend Planner Frontend - User Account Flow
const API_BASE = 'http://localhost:5001/v1';

// State
let currentUser = null;
let authToken = null;
let currentStep = 1;
let currentSubstep = '2a';
let editingPreference = null;

let onboardingData = {
    group_type: null,
    home_location: null,
    transportation: ['transit', 'car'],
    departure_times: {
        saturday: ['morning'],
        sunday: ['morning']
    },
    travel_time_ranges: ['0-15', '15-30'],
    interests: [],
    energy_level: 'moderate',
    time_commitment: 'half_day',
    budget: 'moderate',
    accessibility: [],
    avoid: []
};

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

async function initApp() {
    // Check for existing session
    authToken = localStorage.getItem('auth_token');
    const userId = localStorage.getItem('user_id');
    
    // Check for saved preferences (even without account)
    const savedPrefs = localStorage.getItem('weekend_planner_preferences');
    
    if (authToken && userId) {
        // Returning user with account - validate and load
        try {
            const response = await fetch(`${API_BASE}/user/preferences`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                currentUser = { id: userId, ...data.user };
                
                if (data.preferences && Object.keys(data.preferences).length > 0) {
                    onboardingData = { ...onboardingData, ...data.preferences };
                    showDashboard();
                    return;
                }
            } else if (response.status === 401) {
                // Token expired
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_id');
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }
    
    // Check local preferences (guest or failed auth)
    if (savedPrefs) {
        onboardingData = JSON.parse(savedPrefs);
        currentUser = { id: 'guest', isGuest: true };
        showDashboard();
        return;
    }
    
    // First-time user - go directly to onboarding (guest path)
    currentUser = { id: 'guest_' + Date.now(), isGuest: true };
    showOnboarding();
}

function setupEventListeners() {
    // Step 1: Group type selection
    document.querySelectorAll('#step-1 .selection-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('#step-1 .selection-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            onboardingData.group_type = card.dataset.value;
            setTimeout(() => goToStep(2), 300);
        });
    });
    
    // Step 2a: Location buttons
    document.getElementById('use-location-btn')?.addEventListener('click', requestCurrentLocation);
    document.getElementById('manual-location-btn')?.addEventListener('click', () => showSubstep('2b'));
    
    // Step 2b: Location type selection
    document.getElementById('select-zip')?.addEventListener('click', () => {
        document.getElementById('select-zip').classList.add('selected');
        document.getElementById('select-address').classList.remove('selected');
        document.getElementById('zip-input-group').classList.remove('hidden');
        document.getElementById('address-input-group').classList.add('hidden');
    });
    
    document.getElementById('select-address')?.addEventListener('click', () => {
        document.getElementById('select-address').classList.add('selected');
        document.getElementById('select-zip').classList.remove('selected');
        document.getElementById('address-input-group').classList.remove('hidden');
        document.getElementById('zip-input-group').classList.add('hidden');
    });
    
    // Step 2d: Multi-select cards
    document.querySelectorAll('#step-2d .selection-card.selectable').forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('selected');
            updateTransportationPrefs();
            updateDepartureTimePrefs();
            updateTravelTimePrefs();
        });
    });
    
    // Step 3: Interests multi-select
    document.querySelectorAll('#interests-grid .selection-card').forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('selected');
            updateInterests();
        });
    });
    
    // Step 4: Single-select groups
    document.querySelectorAll('#step-4 .selection-card[data-group]').forEach(card => {
        card.addEventListener('click', () => {
            const group = card.dataset.group;
            document.querySelectorAll(`#step-4 .selection-card[data-group="${group}"]`).forEach(c => {
                c.classList.remove('selected');
            });
            card.classList.add('selected');
            if (group === 'energy') onboardingData.energy_level = card.dataset.value;
            else if (group === 'time') onboardingData.time_commitment = card.dataset.value;
        });
    });
    
    // Step 5: Budget and checkboxes
    document.querySelectorAll('#step-5 .selection-card[data-group="budget"]').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('#step-5 .selection-card[data-group="budget"]').forEach(c => {
                c.classList.remove('selected');
            });
            card.classList.add('selected');
            onboardingData.budget = card.dataset.value;
        });
    });
    
    // Quick toggle buttons on dashboard
    document.querySelectorAll('.quick-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.parentElement;
            // For single-select groups
            if (btn.dataset.value === 'solo' || btn.dataset.value === 'couple' || 
                btn.dataset.value === 'family' || btn.dataset.value === 'friends') {
                group.querySelectorAll('.quick-toggle').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            } else {
                // Multi-select for travel time
                btn.classList.toggle('active');
            }
        });
    });
    
    // Modal close buttons
    document.querySelectorAll('.modal .close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').classList.remove('active');
        });
    });
    
    // Close modal on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.remove('active');
        });
    });
}


// ==================== SCREEN MANAGEMENT ====================

function showScreen(screenId) {
    // Hide loading state
    document.getElementById('app-loading')?.classList.add('hidden');
    
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId)?.classList.add('active');
}

function showAuthScreen() {
    showScreen('auth-screen');
    showLoginForm();
}

function showAuthFromOnboarding(type) {
    showScreen('auth-screen');
    if (type === 'signup') {
        showSignupForm();
    } else {
        showLoginForm();
    }
}

function showOnboarding() {
    showScreen('onboarding');
    initializeOnboarding();
}

function showDashboard() {
    showScreen('dashboard');
    populateDashboard();
    // Auto-load recommendations
    loadDashboardRecommendations();
}

function showPlanner() {
    showScreen('planner');
    loadDigest();
}

function showRecommendations() {
    // Gather quick adjustments before showing
    gatherQuickAdjustments();
    showPlanner();
}

function refreshRecommendations() {
    gatherQuickAdjustments();
    loadDashboardRecommendations();
}

async function loadDashboardRecommendations() {
    const loading = document.getElementById('dashboard-loading');
    const container = document.getElementById('dashboard-digest-items');
    
    if (loading) loading.style.display = 'block';
    if (container) container.innerHTML = '<div class="loading" id="dashboard-loading">✨ Getting personalized recommendations...</div>';
    
    try {
        // Build user profile and prompt
        const userProfile = getUserProfile();
        const prompt = buildRecommendationPrompt();
        
        // Try AI-powered recommendations first
        const response = await fetch(`${API_BASE}/recommendations/ai`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': authToken ? `Bearer ${authToken}` : ''
            },
            body: JSON.stringify({ 
                profile: userProfile,
                prompt: prompt
            })
        });
        
        if (!response.ok) {
            // Fall back to regular digest if AI endpoint fails
            console.log('AI recommendations unavailable, falling back to digest');
            const fallbackResponse = await fetch(`${API_BASE}/digest`);
            if (!fallbackResponse.ok) throw new Error('Backend error');
            const data = await fallbackResponse.json();
            window.currentDigest = data;
            if (data.items?.length > 0) {
                renderDashboardItems(data.items);
            } else {
                throw new Error('No recommendations');
            }
            return;
        }
        
        const data = await response.json();
        window.currentDigest = data;
        
        if (data.items && data.items.length > 0) {
            renderDashboardItems(data.items);
        } else {
            if (container) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: #666;">
                        <p><strong>No recommendations yet</strong></p>
                        <button class="btn btn-primary" onclick="refreshRecommendations()" style="width: auto; margin-top: 1rem;">Retry</button>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #ef4444;">
                    <p><strong>Error loading recommendations</strong></p>
                    <p style="font-size: 0.85rem; margin-top: 0.5rem; color: #666;">Make sure the backend server is running</p>
                    <button class="btn btn-primary" onclick="refreshRecommendations()" style="width: auto; margin-top: 1rem;">Retry</button>
                </div>
            `;
        }
    }
}

function renderDashboardItems(items) {
    const container = document.getElementById('dashboard-digest-items');
    if (!container) return;
    
    container.innerHTML = '';
    items.forEach(item => {
        const card = createRecommendationCard(item);
        container.appendChild(card);
    });
}

// ==================== AUTH FORMS ====================

function showLoginForm() {
    document.getElementById('login-form').classList.add('active');
    document.getElementById('signup-form').classList.remove('active');
}

function showSignupForm() {
    document.getElementById('signup-form').classList.add('active');
    document.getElementById('login-form').classList.remove('active');
}

async function handleLogin() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    if (!email || !password) {
        alert('Please enter email and password');
        return;
    }
    
    await loginWithEmail(email, password);
}

async function loginWithEmail(email, password) {
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_email', email);
            localStorage.setItem('auth_provider', 'email');
            authToken = data.token;
            currentUser = { id: data.user_id, email };
            
            console.log('[Auth] Login successful:', email);
            
            if (data.preferences) {
                onboardingData = { ...onboardingData, ...data.preferences };
                showDashboard();
            } else {
                showOnboarding();
            }
        } else {
            // Show actual error from server
            alert(data.error || 'Invalid email or password');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Unable to connect to server. Please try again.');
    }
}


async function handleSignup() {
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    
    if (!email) {
        alert('Please enter your email');
        return;
    }
    
    if (password.length < 8) {
        alert('Password must be at least 8 characters');
        return;
    }
    
    await signupWithEmail(email, password);
}

async function signupWithEmail(email, password) {
    try {
        const response = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                method: 'email',
                email, 
                password,
                email_digest: document.getElementById('email-digest-optin')?.checked ?? true
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_email', email);
            localStorage.setItem('auth_provider', 'email');
            authToken = data.token;
            currentUser = { id: data.user_id, email, isGuest: false };
            
            console.log('[Auth] Signup successful:', email);
            
            // Check if we have preferences (coming from onboarding signup prompt)
            const savedPrefs = localStorage.getItem('weekend_planner_preferences');
            if (savedPrefs) {
                savePreferences();
                showDashboard();
            } else {
                showOnboarding();
            }
        } else {
            // Show actual error from server
            alert(data.error || 'Signup failed. Please try again.');
        }
    } catch (error) {
        console.error('Signup error:', error);
        alert('Unable to connect to server. Please try again.');
    }
}

function simulateLogin(identifier) {
    const userId = 'demo_' + Date.now();
    localStorage.setItem('auth_token', 'demo_token');
    localStorage.setItem('user_id', userId);
    authToken = 'demo_token';
    currentUser = { id: userId, email: identifier };
    
    // Check for saved preferences
    const savedPrefs = localStorage.getItem('weekend_planner_preferences');
    if (savedPrefs) {
        onboardingData = JSON.parse(savedPrefs);
        showDashboard();
    } else {
        showOnboarding();
    }
}

function simulateSignup(identifier) {
    const userId = 'demo_' + Date.now();
    localStorage.setItem('auth_token', 'demo_token');
    localStorage.setItem('user_id', userId);
    authToken = 'demo_token';
    currentUser = { id: userId, email: identifier, isGuest: false };
    
    // Check if we have preferences (coming from onboarding signup prompt)
    const savedPrefs = localStorage.getItem('weekend_planner_preferences');
    if (savedPrefs) {
        // Save to server and go to dashboard
        savePreferences();
        showDashboard();
    } else {
        // Fresh signup - go to onboarding
        showOnboarding();
    }
}

function continueAsGuest() {
    const guestId = 'guest_' + Date.now();
    sessionStorage.setItem('guest_id', guestId);
    currentUser = { id: guestId, isGuest: true };
    showOnboarding();
}

async function signInWithOAuth(provider) {
    if (provider === 'google') {
        try {
            // Check if Google OAuth is configured
            const statusResponse = await fetch(`${API_BASE}/auth/google/status`);
            const statusData = await statusResponse.json();
            
            if (!statusData.configured) {
                // Fall back to demo mode if not configured
                alert('Google OAuth not configured. Using demo mode.');
                simulateLogin('demo@google.com');
                return;
            }
            
            // Get the Google auth URL
            const urlResponse = await fetch(`${API_BASE}/auth/google/url`);
            const urlData = await urlResponse.json();
            
            if (urlData.url) {
                // Open Google OAuth in a popup
                const width = 500;
                const height = 600;
                const left = (window.innerWidth - width) / 2 + window.screenX;
                const top = (window.innerHeight - height) / 2 + window.screenY;
                
                const popup = window.open(
                    urlData.url,
                    'Google Sign In',
                    `width=${width},height=${height},left=${left},top=${top},popup=yes`
                );
                
                // Listen for message from popup
                window.addEventListener('message', function handleOAuthMessage(event) {
                    if (event.data.type === 'oauth_success') {
                        // Store auth token and user info
                        authToken = event.data.token;
                        currentUser = event.data.user;
                        localStorage.setItem('auth_token', authToken);
                        localStorage.setItem('user_id', currentUser.id);
                        localStorage.setItem('user_email', currentUser.email);
                        localStorage.setItem('user_name', currentUser.name || '');
                        localStorage.setItem('user_picture', currentUser.picture || '');
                        localStorage.setItem('auth_provider', 'google');
                        
                        console.log('[Auth] Google sign-in successful:', currentUser.email);
                        
                        // Check if user has preferences
                        checkUserPreferencesAndRedirect();
                        
                        window.removeEventListener('message', handleOAuthMessage);
                    } else if (event.data.type === 'oauth_error') {
                        console.error('[Auth] Google sign-in error:', event.data.error);
                        alert('Sign-in failed: ' + event.data.error);
                        window.removeEventListener('message', handleOAuthMessage);
                    }
                });
            }
        } catch (error) {
            console.error('[Auth] Google OAuth error:', error);
            alert('Failed to sign in with Google. Please try again.');
        }
    } else if (provider === 'apple') {
        // Apple Sign-In not implemented yet
        alert('Apple Sign-In coming soon! Please use Google or email.');
    }
}

async function checkUserPreferencesAndRedirect() {
    try {
        const response = await fetch(`${API_BASE}/user/preferences`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.preferences && Object.keys(data.preferences).length > 0) {
                // User has preferences, go to dashboard
                console.log('[Auth] User has saved preferences, going to dashboard');
                Object.assign(onboardingData, data.preferences);
                showDashboard();
            } else {
                // New user, start onboarding
                console.log('[Auth] New user, starting onboarding');
                showOnboarding();
            }
        } else {
            // No preferences, start onboarding
            showOnboarding();
        }
    } catch (error) {
        console.error('[Auth] Error checking preferences:', error);
        showOnboarding();
    }
}

function handleSignOut() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_id');
    authToken = null;
    currentUser = null;
    showAuthScreen();
}

// ==================== ONBOARDING ====================

function initializeOnboarding() {
    document.querySelectorAll('.onboarding-step').forEach(step => {
        step.classList.remove('active');
        step.style.display = 'none';
    });
    
    const step1 = document.getElementById('step-1');
    if (step1) {
        step1.classList.add('active');
        step1.style.display = 'block';
    }
    
    document.querySelectorAll('.substep').forEach(substep => {
        substep.classList.remove('active');
        substep.style.display = 'none';
    });
    
    const step2a = document.getElementById('step-2a');
    if (step2a) {
        step2a.classList.add('active');
        step2a.style.display = 'block';
    }
    
    document.querySelectorAll('.progress-step').forEach((el, index) => {
        el.classList.remove('active', 'completed');
        if (index === 0) el.classList.add('active');
    });
    
    currentStep = 1;
    currentSubstep = '2a';
    updateBackButton();
}

function goToStep(step) {
    if (step === 2 && !onboardingData.group_type) {
        alert('Please select who you\'re planning for.');
        return;
    }
    
    if (step === 3 && !onboardingData.home_location) {
        alert('Please set your location first.');
        return;
    }
    
    document.querySelectorAll('.progress-step').forEach((el, index) => {
        el.classList.remove('active', 'completed');
        if (index + 1 < step) el.classList.add('completed');
        if (index + 1 === step) el.classList.add('active');
    });
    
    document.querySelectorAll('.onboarding-step').forEach(el => {
        el.classList.remove('active');
        el.style.display = 'none';
    });
    
    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.classList.add('active');
        targetStep.style.display = 'block';
    }
    
    if (step === 2) {
        if (onboardingData.home_location) {
            showSubstep('2d');
        } else {
            showSubstep('2a');
        }
    }
    
    currentStep = step;
    updateBackButton();
    document.querySelector('.onboarding-container')?.scrollTo(0, 0);
}

function showSubstep(substep) {
    document.querySelectorAll('#step-2 .substep').forEach(el => {
        el.classList.remove('active');
        el.style.display = 'none';
    });
    
    const target = document.getElementById(`step-${substep}`);
    if (target) {
        target.classList.add('active');
        target.style.display = 'block';
    }
    
    currentSubstep = substep;
    updateBackButton();
}

// Global back navigation
function goBack() {
    if (currentStep === 1) {
        // First step - no back action (or could go to auth)
        return;
    }
    
    if (currentStep === 2) {
        // Handle substep navigation within step 2
        if (currentSubstep === '2a') {
            goToStep(1);
        } else if (currentSubstep === '2b') {
            showSubstep('2a');
        } else if (currentSubstep === '2c') {
            // Go back based on how user entered location
            if (onboardingData.home_location?.type === 'geolocation') {
                showSubstep('2a');
            } else {
                showSubstep('2b');
            }
            onboardingData.home_location = null;
        } else if (currentSubstep === '2d') {
            showSubstep('2c');
        }
    } else if (currentStep === 3) {
        goToStep(2);
    } else if (currentStep === 4) {
        goToStep(3);
    } else if (currentStep === 5) {
        goToStep(4);
    }
}

function updateBackButton() {
    const backBtn = document.getElementById('onboarding-back-btn');
    if (!backBtn) return;
    
    // Hide back button on step 1
    if (currentStep === 1) {
        backBtn.classList.add('hidden');
    } else {
        backBtn.classList.remove('hidden');
    }
}

// Location handling
async function requestCurrentLocation() {
    const btn = document.getElementById('use-location-btn');
    btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Getting location...</span>';
    btn.disabled = true;
    
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        resetLocationButton();
        showSubstep('2b');
        return;
    }
    
    try {
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000
            });
        });
        
        const { latitude, longitude } = position.coords;
        
        onboardingData.home_location = {
            type: 'geolocation',
            input: 'Current location',
            lat: latitude,
            lng: longitude,
            formatted_address: `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
            precision: 'exact'
        };
        
        document.getElementById('location-display').textContent = 
            `📍 ${onboardingData.home_location.formatted_address}`;
        
        showSubstep('2c');
        
    } catch (error) {
        console.error('Geolocation error:', error);
        resetLocationButton();
        showSubstep('2b');
    }
}

function resetLocationButton() {
    const btn = document.getElementById('use-location-btn');
    btn.innerHTML = '<span class="btn-icon">📍</span><span class="btn-text">Use My Current Location</span><span class="btn-subtext">For accurate travel times</span>';
    btn.disabled = false;
}

function submitLocation(type) {
    let input;
    
    if (type === 'zip') {
        input = document.getElementById('zip-input').value.trim();
        if (!/^\d{5}(-\d{4})?$/.test(input)) {
            alert('Please enter a valid ZIP code');
            return;
        }
    } else {
        input = document.getElementById('address-input').value.trim();
        if (input.length < 5) {
            alert('Please enter a valid address');
            return;
        }
    }
    
    onboardingData.home_location = {
        type: type,
        input: input,
        lat: 37.7749,
        lng: -122.4194,
        formatted_address: input,
        precision: type === 'zip' ? 'approximate' : 'exact'
    };
    
    document.getElementById('location-display').textContent = `📍 ${input}`;
    showSubstep('2c');
}

function completeLocationStep() {
    const saveCheckbox = document.getElementById('save-location-checkbox');
    
    if (saveCheckbox?.checked) {
        localStorage.setItem('weekend_planner_location', JSON.stringify({
            ...onboardingData.home_location,
            savedAt: new Date().toISOString()
        }));
    }
    
    showSubstep('2d');
}

function handleSaveLocationCheckbox(checkbox) {
    if (!checkbox.checked) return;
    
    const existingLocation = localStorage.getItem('weekend_planner_location');
    
    if (existingLocation) {
        const parsed = JSON.parse(existingLocation);
        const confirmed = confirm(
            `Home location is already set to "${parsed.formatted_address || parsed.input}".\n\nDo you want to update to this new location?`
        );
        
        if (!confirmed) {
            checkbox.checked = false;
        }
    }
}

function goBackFromLocationConfirm() {
    // Go back based on how user entered location
    if (onboardingData.home_location?.type === 'geolocation') {
        showSubstep('2a');
    } else {
        showSubstep('2b');
    }
    // Clear the location so user can re-enter
    onboardingData.home_location = null;
}

// Preference updates
function updateTransportationPrefs() {
    const selected = document.querySelectorAll('#step-2d .selection-card.selectable.selected[data-value="walking"], #step-2d .selection-card.selectable.selected[data-value="transit"], #step-2d .selection-card.selectable.selected[data-value="car"]');
    onboardingData.transportation = Array.from(selected)
        .filter(card => ['walking', 'transit', 'car'].includes(card.dataset.value))
        .map(card => card.dataset.value);
}

function updateDepartureTimePrefs() {
    onboardingData.departure_times = { saturday: [], sunday: [] };
    
    document.querySelectorAll('#step-2d .selection-card.selectable.selected[data-day]').forEach(card => {
        const day = card.dataset.day;
        const value = card.dataset.value;
        if (!onboardingData.departure_times[day].includes(value)) {
            onboardingData.departure_times[day].push(value);
        }
    });
}

function updateTravelTimePrefs() {
    const selected = document.querySelectorAll('#step-2d .selection-card.selectable.selected[data-value="0-15"], #step-2d .selection-card.selectable.selected[data-value="15-30"], #step-2d .selection-card.selectable.selected[data-value="30-60"], #step-2d .selection-card.selectable.selected[data-value="60+"]');
    onboardingData.travel_time_ranges = Array.from(selected)
        .filter(card => ['0-15', '15-30', '30-60', '60+'].includes(card.dataset.value))
        .map(card => card.dataset.value);
}

function updateInterests() {
    const selected = document.querySelectorAll('#interests-grid .selection-card.selected');
    onboardingData.interests = Array.from(selected).map(card => card.dataset.value);
    
    const count = onboardingData.interests.length;
    const countEl = document.getElementById('interests-count');
    const continueBtn = document.getElementById('step3-continue');
    
    if (countEl) {
        countEl.textContent = `${count} selected (minimum 3)`;
        countEl.style.color = count >= 3 ? '#10b981' : '#666';
    }
    
    if (continueBtn) {
        continueBtn.disabled = count < 3;
    }
}

// Complete onboarding
async function completeOnboarding() {
    onboardingData.accessibility = Array.from(document.querySelectorAll('input[name="accessibility"]:checked'))
        .map(cb => cb.value);
    onboardingData.avoid = Array.from(document.querySelectorAll('input[name="avoid"]:checked'))
        .map(cb => cb.value);
    
    // Save preferences locally first
    await savePreferences();
    
    // If guest user, prompt to sign up
    if (!authToken || currentUser?.isGuest) {
        showSignupPrompt();
    } else {
        showDashboard();
    }
}

function skipAndComplete() {
    onboardingData.interests = ['nature', 'arts_culture', 'entertainment'];
    completeOnboarding();
}

function showSignupPrompt() {
    document.getElementById('signup-prompt-modal').classList.add('active');
}

function closeSignupPrompt() {
    document.getElementById('signup-prompt-modal').classList.remove('active');
}

function skipSignupAndContinue() {
    closeSignupPrompt();
    showDashboard();
}

function signupFromPrompt() {
    closeSignupPrompt();
    showScreen('auth-screen');
    showSignupForm();
}

async function savePreferences() {
    const categoryMapping = {
        'nature': ['parks'],
        'arts_culture': ['museums'],
        'food_drinks': ['food'],
        'adventure': ['attractions'],
        'learning': ['museums'],
        'entertainment': ['attractions'],
        'relaxation': ['parks'],
        'shopping': ['attractions'],
        'events': ['events']
    };
    
    const categories = [...new Set(
        onboardingData.interests.flatMap(interest => categoryMapping[interest] || [])
    )];
    
    const preferences = {
        ...onboardingData,
        categories: categories.length > 0 ? categories : ['parks', 'museums', 'attractions'],
        kid_friendly: onboardingData.group_type === 'family',
        radius_miles: getRadiusFromTravelTime()
    };
    
    // Save to localStorage for demo
    localStorage.setItem('weekend_planner_preferences', JSON.stringify(preferences));
    
    // Try to save to backend
    try {
        await fetch(`${API_BASE}/preferences`, {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(preferences)
        });
    } catch (error) {
        console.log('Backend save failed, using local storage');
    }
}

// ==================== DASHBOARD ====================

function populateDashboard() {
    // User name
    const userName = currentUser?.email?.split('@')[0] || 'there';
    document.getElementById('user-name').textContent = userName;
    
    // Location
    document.getElementById('pref-location').textContent = 
        onboardingData.home_location?.formatted_address || 'Not set';
    
    // Group type
    const groupLabels = {
        'solo': 'Just Me',
        'couple': 'With Partner',
        'family': 'Family with Kids',
        'friends': 'With Friends'
    };
    document.getElementById('pref-group').textContent = 
        groupLabels[onboardingData.group_type] || 'Not set';
    
    // Update group icon
    const groupIcons = { 'solo': '👤', 'couple': '👫', 'family': '👨‍👩‍👧‍👦', 'friends': '👥' };
    const groupCard = document.querySelector('.pref-card:nth-child(2) .pref-icon');
    if (groupCard) groupCard.textContent = groupIcons[onboardingData.group_type] || '👤';
    
    // Transportation
    document.getElementById('pref-transport').textContent = 
        onboardingData.transportation.map(t => t.charAt(0).toUpperCase() + t.slice(1)).join(', ') || 'Not set';
    
    // Travel time
    document.getElementById('pref-travel-time').textContent = 
        onboardingData.travel_time_ranges.join(', ').replace(/-/g, '-') + ' min' || 'Not set';
    
    // Departure times
    const departures = [];
    if (onboardingData.departure_times.saturday?.length) {
        departures.push('Saturday ' + onboardingData.departure_times.saturday.join(', '));
    }
    if (onboardingData.departure_times.sunday?.length) {
        departures.push('Sunday ' + onboardingData.departure_times.sunday.join(', '));
    }
    document.getElementById('pref-departure').textContent = departures.join('; ') || 'Not set';
    
    // Interests
    const interestLabels = {
        'nature': '🌲 Nature & Parks',
        'arts_culture': '🎨 Arts & Culture',
        'food_drinks': '🍽️ Food & Drinks',
        'adventure': '🎢 Adventure',
        'learning': '📚 Learning',
        'entertainment': '🎵 Entertainment',
        'relaxation': '🧘 Relaxation',
        'shopping': '🛍️ Shopping',
        'events': '🎪 Events'
    };
    const interestsContainer = document.getElementById('pref-interests');
    if (interestsContainer) {
        interestsContainer.innerHTML = onboardingData.interests
            .map(i => `<span class="tag">${interestLabels[i] || i}</span>`)
            .join('') || '<span>Not set</span>';
    }
    
    // Energy level
    const energyLabels = {
        'relaxing': 'Relaxing (sit, view, chill)',
        'moderate': 'Moderate (walking, exploring)',
        'active': 'Active (adventure, sports)'
    };
    document.getElementById('pref-energy').textContent = 
        energyLabels[onboardingData.energy_level] || 'Not set';
    
    // Time commitment
    const timeLabels = {
        'quick': '1-2 hours',
        'half_day': 'Half-day (3-4 hours)',
        'full_day': 'Full day (5+ hours)'
    };
    document.getElementById('pref-time-commit').textContent = 
        timeLabels[onboardingData.time_commitment] || 'Not set';
    
    // Budget
    const budgetLabels = {
        'free': 'Free only',
        'low': 'Under $25 per person',
        'moderate': 'Under $50 per person',
        'any': 'No limit'
    };
    document.getElementById('pref-budget').textContent = 
        budgetLabels[onboardingData.budget] || 'Not set';
    
    // Other preferences
    const otherPrefs = [];
    if (onboardingData.group_type === 'family') otherPrefs.push('✓ Kid-friendly activities');
    onboardingData.accessibility?.forEach(a => {
        const labels = { 'wheelchair': '✓ Wheelchair accessible', 'stroller': '✓ Stroller friendly', 'limited_walking': '✓ Limited walking' };
        otherPrefs.push(labels[a] || a);
    });
    if (onboardingData.avoid?.length) {
        otherPrefs.push('Avoiding: ' + onboardingData.avoid.join(', '));
    }
    document.getElementById('pref-other').innerHTML = 
        otherPrefs.map(p => `<p>${p}</p>`).join('') || '<p>None set</p>';
    
    // Set quick toggle states
    document.querySelectorAll('.quick-toggle[data-value]').forEach(btn => {
        const value = btn.dataset.value;
        if (value === onboardingData.group_type) {
            btn.classList.add('active');
        } else if (['solo', 'couple', 'family', 'friends'].includes(value)) {
            btn.classList.remove('active');
        }
        
        if (onboardingData.travel_time_ranges?.includes(value)) {
            btn.classList.add('active');
        } else if (['0-15', '15-30', '30-60', '60+'].includes(value)) {
            btn.classList.remove('active');
        }
    });
}

function gatherQuickAdjustments() {
    // Gather any quick adjustments made on dashboard
    const activeGroup = document.querySelector('.quick-toggle-group .quick-toggle.active[data-value="solo"], .quick-toggle-group .quick-toggle.active[data-value="couple"], .quick-toggle-group .quick-toggle.active[data-value="family"], .quick-toggle-group .quick-toggle.active[data-value="friends"]');
    if (activeGroup) {
        onboardingData.group_type = activeGroup.dataset.value;
    }
    
    const activeTimes = document.querySelectorAll('.quick-toggle-group .quick-toggle.active[data-value="0-15"], .quick-toggle-group .quick-toggle.active[data-value="15-30"], .quick-toggle-group .quick-toggle.active[data-value="30-60"], .quick-toggle-group .quick-toggle.active[data-value="60+"]');
    if (activeTimes.length > 0) {
        onboardingData.travel_time_ranges = Array.from(activeTimes).map(b => b.dataset.value);
    }
}

// Edit preferences
function editPreference(section) {
    editingPreference = section;
    const modal = document.getElementById('edit-modal');
    const title = document.getElementById('edit-modal-title');
    const content = document.getElementById('edit-modal-content');
    
    switch(section) {
        case 'location':
            title.textContent = 'Edit Location';
            content.innerHTML = `
                <div class="form-group">
                    <label>Enter your location:</label>
                    <input type="text" id="edit-location-input" value="${onboardingData.home_location?.formatted_address || ''}" placeholder="ZIP code or address">
                </div>
            `;
            break;
        case 'group':
            title.textContent = 'Edit: Planning For';
            content.innerHTML = `
                <div class="selection-grid">
                    ${['solo', 'couple', 'family', 'friends'].map(g => `
                        <div class="selection-card ${onboardingData.group_type === g ? 'selected' : ''}" data-value="${g}" onclick="selectEditOption(this, 'group')">
                            <div class="card-emoji">${{solo: '👤', couple: '👫', family: '👨‍👩‍👧‍👦', friends: '👥'}[g]}</div>
                            <div class="card-label">${{solo: 'Just Me', couple: 'With Partner', family: 'Family with Kids', friends: 'With Friends'}[g]}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            break;
        case 'interests':
            title.textContent = 'Edit: Interests';
            const interestOptions = ['nature', 'arts_culture', 'food_drinks', 'adventure', 'learning', 'entertainment', 'relaxation', 'shopping', 'events'];
            const interestLabels = {
                'nature': '🌲🏕️ Nature & Parks',
                'arts_culture': '🎨🖼️ Arts & Culture',
                'food_drinks': '🍽️🍷 Food & Drinks',
                'adventure': '🎢🎯 Adventure',
                'learning': '📚🔬 Learning',
                'entertainment': '🎵🎭 Entertainment',
                'relaxation': '🧘☕ Relaxation',
                'shopping': '🛍️🏪 Shopping',
                'events': '🎪🎠 Events'
            };
            content.innerHTML = `
                <div class="selection-grid three-col">
                    ${interestOptions.map(i => `
                        <div class="selection-card selectable ${onboardingData.interests?.includes(i) ? 'selected' : ''}" data-value="${i}" onclick="toggleEditOption(this, 'interests')">
                            <div class="card-label">${interestLabels[i]}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            break;
        default:
            title.textContent = 'Edit Preference';
            content.innerHTML = '<p>Edit form coming soon...</p>';
    }
    
    modal.classList.add('active');
}

function selectEditOption(el, type) {
    el.parentElement.querySelectorAll('.selection-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
}

function toggleEditOption(el, type) {
    el.classList.toggle('selected');
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.remove('active');
    editingPreference = null;
}

function savePreferenceEdit() {
    switch(editingPreference) {
        case 'location':
            const locationInput = document.getElementById('edit-location-input').value;
            if (locationInput) {
                onboardingData.home_location = {
                    type: 'manual',
                    input: locationInput,
                    formatted_address: locationInput,
                    lat: 37.7749,
                    lng: -122.4194
                };
            }
            break;
        case 'group':
            const selectedGroup = document.querySelector('#edit-modal-content .selection-card.selected');
            if (selectedGroup) {
                onboardingData.group_type = selectedGroup.dataset.value;
            }
            break;
        case 'interests':
            const selectedInterests = document.querySelectorAll('#edit-modal-content .selection-card.selected');
            onboardingData.interests = Array.from(selectedInterests).map(c => c.dataset.value);
            break;
    }
    
    savePreferences();
    populateDashboard();
    closeEditModal();
}

function editAllPreferences() {
    closeSettings();
    showOnboarding();
}

// ==================== SETTINGS ====================

function openSettings() {
    populateSettings();
    document.getElementById('settings-modal').classList.add('active');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.remove('active');
}

function showSettingsTab(tab) {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`.settings-tab[onclick*="${tab}"]`)?.classList.add('active');
    document.getElementById(`settings-${tab}`)?.classList.add('active');
}

function populateSettings() {
    // Populate account info
    const email = currentUser?.email || 'user@example.com';
    document.getElementById('account-email').textContent = email;
    document.getElementById('account-since').textContent = 'January 2026';
    
    // Preferences are already populated by populateDashboard
}

function changePassword() {
    alert('Password change feature coming soon!');
}

function deleteAccount() {
    if (confirm('Are you sure you want to delete your account? This cannot be undone.')) {
        localStorage.clear();
        sessionStorage.clear();
        showAuthScreen();
    }
}

function saveNotificationSettings() {
    const settings = {
        weekly: document.getElementById('notif-weekly')?.checked,
        events: document.getElementById('notif-events')?.checked,
        deals: document.getElementById('notif-deals')?.checked
    };
    localStorage.setItem('notification_settings', JSON.stringify(settings));
    alert('Notification preferences saved!');
}

// ==================== QUICK ADJUSTMENTS ====================

function selectQuickGroup(btn) {
    btn.parentElement.querySelectorAll('.quick-toggle').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    onQuickAdjustmentChange();
}

function toggleQuickTravelTime(btn) {
    btn.classList.toggle('active');
    onQuickAdjustmentChange();
}

function onQuickAdjustmentChange() {
    // Auto-refresh recommendations when adjustments change
    clearTimeout(window.quickAdjustmentTimeout);
    window.quickAdjustmentTimeout = setTimeout(() => {
        gatherQuickAdjustments();
        loadDashboardRecommendations();
    }, 500);
}

// ==================== RECOMMENDATIONS ====================

function getRadiusFromTravelTime() {
    if (onboardingData.travel_time_ranges?.includes('60+')) return 50;
    if (onboardingData.travel_time_ranges?.includes('30-60')) return 30;
    if (onboardingData.travel_time_ranges?.includes('15-30')) return 15;
    return 10;
}

// Build recommendation prompt from user profile
function buildRecommendationPrompt() {
    const groupLabels = {
        'solo': 'myself (solo)',
        'couple': 'me and my partner (couple)',
        'family': 'my family with kids',
        'friends': 'me and my friends'
    };
    
    const interestLabels = {
        'nature': 'nature, parks, and outdoor activities',
        'arts_culture': 'arts, culture, and museums',
        'food_drinks': 'food, restaurants, and drinks',
        'adventure': 'adventure and sports',
        'learning': 'learning and science',
        'entertainment': 'entertainment and shows',
        'relaxation': 'relaxation and wellness',
        'shopping': 'shopping and markets',
        'events': 'local events and festivals'
    };
    
    const energyLabels = {
        'relaxing': 'relaxing (prefer sitting, viewing, minimal walking)',
        'moderate': 'moderate (comfortable with walking and light exploring)',
        'active': 'active (enjoy sports, hiking, and physical activities)'
    };
    
    const timeLabels = {
        'quick': '1-2 hours per activity',
        'half_day': '3-4 hours (half-day activities)',
        'full_day': '5+ hours (full-day experiences)'
    };
    
    const budgetLabels = {
        'free': 'free activities only',
        'low': 'budget-friendly (under $25 per person)',
        'moderate': 'moderate budget (under $50 per person)',
        'any': 'no budget restrictions'
    };
    
    // Build the prompt
    const location = onboardingData.home_location?.formatted_address || 'San Francisco, CA';
    const group = groupLabels[onboardingData.group_type] || 'myself';
    const interests = onboardingData.interests?.map(i => interestLabels[i]).filter(Boolean).join(', ') || 'various activities';
    const energy = energyLabels[onboardingData.energy_level] || 'moderate activity level';
    const timeCommit = timeLabels[onboardingData.time_commitment] || 'flexible time';
    const budget = budgetLabels[onboardingData.budget] || 'moderate budget';
    const travelTime = onboardingData.travel_time_ranges?.join(', ').replace(/-/g, '-') + ' minutes' || '30 minutes';
    const transportation = onboardingData.transportation?.join(', ') || 'car';
    
    // Build constraints
    const constraints = [];
    if (onboardingData.group_type === 'family') {
        constraints.push('must be kid-friendly');
    }
    if (onboardingData.accessibility?.length) {
        constraints.push(`accessibility needs: ${onboardingData.accessibility.join(', ')}`);
    }
    if (onboardingData.avoid?.length) {
        constraints.push(`avoid: ${onboardingData.avoid.join(', ')}`);
    }
    
    const prompt = `Generate 5 weekend activity recommendations for someone with this profile:

**Location:** ${location}
**Planning for:** ${group}
**Interests:** ${interests}
**Activity level:** ${energy}
**Time commitment:** ${timeCommit}
**Budget:** ${budget}
**Max travel time:** ${travelTime}
**Transportation:** ${transportation}
${constraints.length ? `**Constraints:** ${constraints.join('; ')}` : ''}

For each recommendation, provide:
1. Name of place/activity
2. Category (e.g., Park, Museum, Restaurant, Event)
3. Why it's a good match for this profile
4. Estimated distance and travel time from their location
5. Price range (Free, $, $$, $$$)
6. Best time to visit
7. Kid-friendly: Yes/No
8. Indoor/Outdoor

Format as JSON array with these fields: title, category, explanation, distance_miles, travel_time_min, price_flag, best_time, kid_friendly, indoor_outdoor, address`;

    return prompt;
}

// Get user profile for API
function getUserProfile() {
    return {
        location: onboardingData.home_location,
        group_type: onboardingData.group_type,
        interests: onboardingData.interests,
        energy_level: onboardingData.energy_level,
        time_commitment: onboardingData.time_commitment,
        budget: onboardingData.budget,
        travel_time_ranges: onboardingData.travel_time_ranges,
        transportation: onboardingData.transportation,
        accessibility: onboardingData.accessibility,
        avoid: onboardingData.avoid,
        kid_friendly: onboardingData.group_type === 'family'
    };
}

async function loadDigest() {
    const loading = document.getElementById('loading');
    const itemsContainer = document.getElementById('digest-items');
    
    if (loading) loading.style.display = 'block';
    if (itemsContainer) itemsContainer.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE}/digest`);
        
        if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`);
        }
        
        const data = await response.json();
        window.currentDigest = data;
        
        if (data.items && data.items.length > 0) {
            renderDigestItems(data.items);
        } else {
            if (itemsContainer) {
            itemsContainer.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #666;">
                    <p><strong>No recommendations available</strong></p>
                        <button class="btn btn-primary" onclick="loadDigest()" style="width: auto; margin-top: 1rem;">Retry</button>
                </div>
            `;
            }
        }
    } catch (error) {
        console.error('Error loading digest:', error);
        if (itemsContainer) {
        itemsContainer.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #ef4444;">
                <p><strong>Error loading recommendations</strong></p>
                <p style="font-size: 0.85rem; margin-top: 1rem; color: #666;">Make sure the backend server is running on port 5001</p>
                    <button class="btn btn-primary" onclick="loadDigest()" style="width: auto; margin-top: 1rem;">Retry</button>
            </div>
        `;
        }
    } finally {
        if (loading) loading.style.display = 'none';
    }
}

function renderDigestItems(items) {
    const container = document.getElementById('digest-items');
    if (!container) return;
    
    container.innerHTML = '';
    items.forEach(item => {
        const card = createRecommendationCard(item);
        container.appendChild(card);
    });
}

function createRecommendationCard(item) {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    
    const trafficClass = item.travel_time_min < 15 ? 'traffic-light' : 
                         item.travel_time_min < 30 ? 'traffic-moderate' : 'traffic-heavy';
    const trafficLabel = item.travel_time_min < 15 ? '🟢 Light' : 
                         item.travel_time_min < 30 ? '🟡 Moderate' : '🔴 Heavy';
    
    card.innerHTML = `
        <div class="card-header">
            <div>
                <div class="card-title">${item.title}</div>
                <span class="card-category">${item.category}</span>
            </div>
        </div>
        <div class="card-info">
            <span class="info-badge">📍 ${item.distance_miles} mi</span>
            <span class="info-badge ${trafficClass}">⏱️ ${item.travel_time_min} min (${trafficLabel})</span>
            <span class="info-badge">💰 ${item.price_flag}</span>
            ${item.kid_friendly ? '<span class="info-badge">👶 Kid-friendly</span>' : ''}
        </div>
        <div class="card-explanation">${item.explanation}</div>
        <div class="card-actions">
            <button class="btn btn-primary" onclick="showDetail('${item.rec_id}')" style="width: auto;">View Details</button>
            <button class="btn btn-secondary" onclick="handleFeedback('${item.rec_id}', 'like', event)">👍</button>
            <button class="btn btn-secondary" onclick="handleFeedback('${item.rec_id}', 'save', event)">⭐</button>
        </div>
    `;
    
    return card;
}

async function showDetail(recId) {
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    if (!item) return;
    
    const modal = document.getElementById('detail-modal');
    const content = document.getElementById('detail-content');
    
    content.innerHTML = `
        <div class="detail-header">
            <h2 class="detail-title">${item.title}</h2>
            <span class="card-category">${item.category}</span>
        </div>
        <div class="detail-info">
            <div class="detail-info-item">
                <div class="detail-info-label">Distance</div>
                <div class="detail-info-value">${item.distance_miles} miles</div>
            </div>
            <div class="detail-info-item">
                <div class="detail-info-label">Travel Time</div>
                <div class="detail-info-value">${item.travel_time_min} min</div>
            </div>
            <div class="detail-info-item">
                <div class="detail-info-label">Price</div>
                <div class="detail-info-value">${item.price_flag}</div>
            </div>
            <div class="detail-info-item">
                <div class="detail-info-label">Type</div>
                <div class="detail-info-value">${item.indoor_outdoor}</div>
            </div>
        </div>
        <div class="time-slots">
            <h3>Add to Calendar</h3>
            <div class="slot-buttons">
                <button class="slot-btn" onclick="selectSlot('SAT_AM')">Saturday Morning</button>
                <button class="slot-btn" onclick="selectSlot('SAT_PM')">Saturday Afternoon</button>
                <button class="slot-btn" onclick="selectSlot('SUN_AM')">Sunday Morning</button>
                <button class="slot-btn" onclick="selectSlot('SUN_PM')">Sunday Afternoon</button>
            </div>
        </div>
        <div style="margin-top: 1.5rem;">
            <button class="btn btn-success" id="add-to-calendar-btn" onclick="addToCalendar('${recId}')" disabled>Add to Calendar</button>
        </div>
    `;
    
    modal.classList.add('active');
    window.selectedSlot = null;
}

function selectSlot(slot) {
    document.querySelectorAll('.slot-btn').forEach(btn => btn.classList.remove('selected'));
    event.target.classList.add('selected');
    window.selectedSlot = slot;
    document.getElementById('add-to-calendar-btn').disabled = false;
}

async function addToCalendar(recId) {
    if (!window.selectedSlot) {
        alert('Please select a time slot');
        return;
    }
    
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    if (!item) return;
    
    // Create Google Calendar URL
    const now = new Date();
    const saturday = new Date(now);
    saturday.setDate(now.getDate() + (6 - now.getDay()));
    
    let start, end;
    if (window.selectedSlot === 'SAT_AM') {
        start = new Date(saturday); start.setHours(10, 0, 0);
        end = new Date(saturday); end.setHours(12, 0, 0);
    } else if (window.selectedSlot === 'SAT_PM') {
        start = new Date(saturday); start.setHours(14, 0, 0);
        end = new Date(saturday); end.setHours(16, 0, 0);
    } else if (window.selectedSlot === 'SUN_AM') {
        const sunday = new Date(saturday); sunday.setDate(saturday.getDate() + 1);
        start = new Date(sunday); start.setHours(10, 0, 0);
        end = new Date(sunday); end.setHours(12, 0, 0);
    } else {
        const sunday = new Date(saturday); sunday.setDate(saturday.getDate() + 1);
        start = new Date(sunday); start.setHours(14, 0, 0);
        end = new Date(sunday); end.setHours(16, 0, 0);
    }
    
    const formatDate = (d) => d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    
    const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(item.title)}&dates=${formatDate(start)}/${formatDate(end)}&details=${encodeURIComponent(item.explanation)}&location=${encodeURIComponent(item.address || '')}`;
    
    window.open(url, '_blank');
        document.getElementById('detail-modal').classList.remove('active');
}

async function handleFeedback(recId, action, event) {
    try {
        await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rec_id: recId, action })
        });
        
        if (event?.target) {
            const btn = event.target;
        if (action === 'like') {
                btn.textContent = '👍✓';
                setTimeout(() => { btn.textContent = '👍'; }, 2000);
        } else if (action === 'save') {
                btn.textContent = '⭐✓';
                setTimeout(() => { btn.textContent = '⭐'; }, 2000);
            }
        }
    } catch (error) {
        console.error('Feedback error:', error);
    }
}

// ==================== GLOBAL FUNCTIONS ====================

window.showLoginForm = showLoginForm;
window.showSignupForm = showSignupForm;
window.showAuthFromOnboarding = showAuthFromOnboarding;
window.handleLogin = handleLogin;
window.handleSignup = handleSignup;
window.continueAsGuest = continueAsGuest;
window.signInWithOAuth = signInWithOAuth;
window.handleSignOut = handleSignOut;
window.goToStep = goToStep;
window.showSubstep = showSubstep;
window.goBack = goBack;
window.submitLocation = submitLocation;
window.completeLocationStep = completeLocationStep;
window.goBackFromLocationConfirm = goBackFromLocationConfirm;
window.handleSaveLocationCheckbox = handleSaveLocationCheckbox;
window.completeOnboarding = completeOnboarding;
window.skipAndComplete = skipAndComplete;
window.showDashboard = showDashboard;
window.showRecommendations = showRecommendations;
window.refreshRecommendations = refreshRecommendations;
window.editPreference = editPreference;
window.selectEditOption = selectEditOption;
window.toggleEditOption = toggleEditOption;
window.closeEditModal = closeEditModal;
window.savePreferenceEdit = savePreferenceEdit;
window.editAllPreferences = editAllPreferences;
window.openSettings = openSettings;
window.closeSettings = closeSettings;
window.showSettingsTab = showSettingsTab;
window.changePassword = changePassword;
window.deleteAccount = deleteAccount;
window.saveNotificationSettings = saveNotificationSettings;
window.selectQuickGroup = selectQuickGroup;
window.toggleQuickTravelTime = toggleQuickTravelTime;
window.onQuickAdjustmentChange = onQuickAdjustmentChange;
window.showSignupPrompt = showSignupPrompt;
window.closeSignupPrompt = closeSignupPrompt;
window.skipSignupAndContinue = skipSignupAndContinue;
window.signupFromPrompt = signupFromPrompt;
window.loadDigest = loadDigest;
window.showDetail = showDetail;
window.selectSlot = selectSlot;
window.addToCalendar = addToCalendar;
window.handleFeedback = handleFeedback;
window.showForgotPassword = () => alert('Password reset coming soon!');
window.clearCache = clearCache;

function clearCache() {
    localStorage.clear();
    sessionStorage.clear();
    alert('Cache cleared! Refreshing...');
    window.location.reload();
}
