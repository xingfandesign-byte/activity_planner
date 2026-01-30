// Weekend Planner Frontend - Multi-Step Onboarding
const API_BASE = 'http://localhost:5001/v1';

// State
let currentUser = null;
let currentDigest = null;
let currentStep = 1;
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

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeAuth();
    setupEventListeners();
    checkSavedLocation();
});

async function initializeAuth() {
    try {
        const response = await fetch(`${API_BASE}/auth/session`);
        if (response.ok) {
            const data = await response.json();
            currentUser = data.authenticated ? data.user_id : 'demo_user';
        } else {
            currentUser = 'demo_user';
        }
    } catch (error) {
        console.error('Auth error:', error);
        currentUser = 'demo_user';
    }
}

function checkSavedLocation() {
    const saved = localStorage.getItem('weekend_planner_location');
    if (saved) {
        try {
            onboardingData.home_location = JSON.parse(saved);
            console.log('Loaded saved location:', onboardingData.home_location);
        } catch (e) {
            console.error('Error loading saved location:', e);
        }
    }
}

function setupEventListeners() {
    // Step 1: Group type selection
    document.querySelectorAll('#step-1 .selection-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('#step-1 .selection-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            onboardingData.group_type = card.dataset.value;
            
            // Auto-advance after selection
            setTimeout(() => goToStep(2), 300);
        });
    });
    
    // Step 2a: Location buttons
    document.getElementById('use-location-btn').addEventListener('click', requestCurrentLocation);
    document.getElementById('manual-location-btn').addEventListener('click', () => showSubstep('2b'));
    
    // Step 2b: Location type selection
    document.getElementById('select-zip').addEventListener('click', () => {
        document.getElementById('select-zip').classList.add('selected');
        document.getElementById('select-address').classList.remove('selected');
        document.getElementById('zip-input-group').classList.remove('hidden');
        document.getElementById('address-input-group').classList.add('hidden');
    });
    
    document.getElementById('select-address').addEventListener('click', () => {
        document.getElementById('select-address').classList.add('selected');
        document.getElementById('select-zip').classList.remove('selected');
        document.getElementById('address-input-group').classList.remove('hidden');
        document.getElementById('zip-input-group').classList.add('hidden');
    });
    
    // Step 2d: Multi-select cards for transportation
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
    
    // Step 4: Single-select groups (energy, time)
    document.querySelectorAll('#step-4 .selection-card[data-group]').forEach(card => {
        card.addEventListener('click', () => {
            const group = card.dataset.group;
            document.querySelectorAll(`#step-4 .selection-card[data-group="${group}"]`).forEach(c => {
                c.classList.remove('selected');
            });
            card.classList.add('selected');
            
            if (group === 'energy') {
                onboardingData.energy_level = card.dataset.value;
            } else if (group === 'time') {
                onboardingData.time_commitment = card.dataset.value;
            }
        });
    });
    
    // Step 5: Budget single-select and checkboxes
    document.querySelectorAll('#step-5 .selection-card[data-group="budget"]').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('#step-5 .selection-card[data-group="budget"]').forEach(c => {
                c.classList.remove('selected');
            });
            card.classList.add('selected');
            onboardingData.budget = card.dataset.value;
        });
    });
    
    // Planner screen listeners
    document.getElementById('refresh-btn')?.addEventListener('click', loadDigest);
    document.getElementById('settings-btn')?.addEventListener('click', () => {
        alert('Settings coming soon!');
    });
    
    // Modal close
    const modal = document.getElementById('detail-modal');
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    }
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.remove('active');
        });
    }
}

// Navigation
function goToStep(step) {
    // Validation
    if (step === 2 && !onboardingData.group_type) {
        alert('Please select who you\'re planning for.');
        return;
    }
    
    if (step === 3 && !onboardingData.home_location) {
        alert('Please set your location first.');
        return;
    }
    
    // Update progress bar
    document.querySelectorAll('.progress-step').forEach((el, index) => {
        el.classList.remove('active', 'completed');
        if (index + 1 < step) el.classList.add('completed');
        if (index + 1 === step) el.classList.add('active');
    });
    
    // Show step
    document.querySelectorAll('.onboarding-step').forEach(el => el.classList.remove('active'));
    document.getElementById(`step-${step}`).classList.add('active');
    
    // Reset substeps for step 2
    if (step === 2) {
        if (onboardingData.home_location) {
            showSubstep('2d'); // Skip to travel prefs if location already set
        } else {
            showSubstep('2a');
        }
    }
    
    currentStep = step;
}

function showSubstep(substep) {
    document.querySelectorAll('#step-2 .substep').forEach(el => el.classList.remove('active'));
    document.getElementById(`step-${substep}`).classList.add('active');
}

// Location handling
async function requestCurrentLocation() {
    const btn = document.getElementById('use-location-btn');
    btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Getting location...</span>';
    btn.disabled = true;
    
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        btn.innerHTML = '<span class="btn-icon">📍</span><span class="btn-text">Use My Current Location</span><span class="btn-subtext">For accurate travel times</span>';
        btn.disabled = false;
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
        
        // Reverse geocode (simplified - in production use Google Maps API)
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
        btn.innerHTML = '<span class="btn-icon">📍</span><span class="btn-text">Use My Current Location</span><span class="btn-subtext">For accurate travel times</span>';
        btn.disabled = false;
        
        if (error.code === 1) {
            // Permission denied
            showSubstep('2b');
        } else {
            alert('Could not get your location. Please enter it manually.');
            showSubstep('2b');
        }
    }
}

function submitLocation(type) {
    let input, address;
    
    if (type === 'zip') {
        input = document.getElementById('zip-input').value.trim();
        if (!/^\d{5}(-\d{4})?$/.test(input)) {
            alert('Please enter a valid ZIP code (e.g., 94102)');
            return;
        }
        address = input;
    } else {
        input = document.getElementById('address-input').value.trim();
        if (input.length < 5) {
            alert('Please enter a valid address');
            return;
        }
        address = input;
    }
    
    // In production, geocode the address using Google Maps API
    onboardingData.home_location = {
        type: type,
        input: input,
        lat: 37.7749, // Default SF coords - would be geocoded in production
        lng: -122.4194,
        formatted_address: address,
        precision: type === 'zip' ? 'approximate' : 'exact'
    };
    
    document.getElementById('location-display').textContent = `📍 ${address}`;
    showSubstep('2c');
}

function completeLocationStep() {
    const saveCheckbox = document.getElementById('save-location-checkbox');
    
    if (saveCheckbox.checked) {
        localStorage.setItem('weekend_planner_location', JSON.stringify({
            ...onboardingData.home_location,
            savedAt: new Date().toISOString()
        }));
    }
    
    showSubstep('2d');
}

// Update preferences from multi-select cards
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
    
    countEl.textContent = `${count} selected (minimum 3)`;
    countEl.style.color = count >= 3 ? '#10b981' : '#666';
    
    continueBtn.disabled = count < 3;
}

// Complete onboarding
async function completeOnboarding() {
    // Gather all checkbox data
    onboardingData.accessibility = Array.from(document.querySelectorAll('input[name="accessibility"]:checked'))
        .map(cb => cb.value);
    onboardingData.avoid = Array.from(document.querySelectorAll('input[name="avoid"]:checked'))
        .map(cb => cb.value);
    
    // Map interests to backend categories
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
    
    // Build preferences for API
    const preferences = {
        home_location: onboardingData.home_location,
        radius_miles: getRadiusFromTravelTime(),
        categories: categories.length > 0 ? categories : ['parks', 'museums', 'attractions'],
        kid_friendly: onboardingData.group_type === 'family',
        budget: { min: 0, max: getBudgetMax() },
        time_windows: getTimeWindows(),
        notification_time_local: '16:00',
        dedup_window_days: 365,
        calendar_dedup_opt_in: false,
        // Extended preferences
        group_type: onboardingData.group_type,
        transportation: onboardingData.transportation,
        travel_time_ranges: onboardingData.travel_time_ranges,
        energy_level: onboardingData.energy_level,
        time_commitment: onboardingData.time_commitment,
        accessibility: onboardingData.accessibility,
        avoid: onboardingData.avoid
    };
    
    console.log('Saving preferences:', preferences);
    
    try {
        const response = await fetch(`${API_BASE}/preferences`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(preferences)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save preferences');
        }
        
        showPlanner();
        loadDigest();
        
    } catch (error) {
        console.error('Error saving preferences:', error);
        alert('Error saving preferences. Please try again.');
    }
}

function skipAndComplete() {
    // Use defaults and complete
    onboardingData.interests = ['nature', 'arts_culture', 'entertainment'];
    completeOnboarding();
}

// Helper functions
function getRadiusFromTravelTime() {
    if (onboardingData.travel_time_ranges.includes('60+')) return 50;
    if (onboardingData.travel_time_ranges.includes('30-60')) return 30;
    if (onboardingData.travel_time_ranges.includes('15-30')) return 15;
    return 10;
}

function getBudgetMax() {
    const budgetMap = { 'free': 0, 'low': 25, 'moderate': 50, 'any': 1000 };
    return budgetMap[onboardingData.budget] || 50;
}

function getTimeWindows() {
    const windows = [];
    const dayMap = { saturday: 'SAT', sunday: 'SUN' };
    const timeMap = { morning: 'AM', midday: 'PM', afternoon: 'PM' };
    
    Object.entries(onboardingData.departure_times).forEach(([day, times]) => {
        times.forEach(time => {
            windows.push(`${dayMap[day]}_${timeMap[time]}`);
        });
    });
    
    return [...new Set(windows)];
}

function showPlanner() {
    document.getElementById('onboarding').classList.remove('active');
    document.getElementById('planner').classList.add('active');
}

// Load digest
async function loadDigest() {
    const loading = document.getElementById('loading');
    const itemsContainer = document.getElementById('digest-items');
    
    loading.style.display = 'block';
    itemsContainer.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE}/digest`);
        
        if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Digest loaded:', data);
        currentDigest = data;
        
        if (data.items && data.items.length > 0) {
            renderDigestItems(data.items);
        } else {
            itemsContainer.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #666;">
                    <p><strong>No recommendations available</strong></p>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem;">Try adjusting your preferences.</p>
                    <button class="btn btn-primary" onclick="loadDigest()" style="margin-top: 1rem; width: auto;">Retry</button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading digest:', error);
        itemsContainer.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #ef4444;">
                <p><strong>Error loading recommendations</strong></p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">${error.message}</p>
                <p style="font-size: 0.85rem; margin-top: 1rem; color: #666;">Make sure the backend server is running on port 5001</p>
                <button class="btn btn-primary" onclick="loadDigest()" style="margin-top: 1rem; width: auto;">Retry</button>
            </div>
        `;
    } finally {
        loading.style.display = 'none';
    }
}

function renderDigestItems(items) {
    const container = document.getElementById('digest-items');
    container.innerHTML = '';
    
    items.forEach(item => {
        const card = createRecommendationCard(item);
        container.appendChild(card);
    });
}

function createRecommendationCard(item) {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    
    // Simulate traffic status
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
            <span class="info-badge">${item.indoor_outdoor === 'outdoor' ? '☀️ Outdoor' : '🏠 Indoor'}</span>
        </div>
        <div class="card-explanation">${item.explanation}</div>
        <div class="card-actions">
            <button class="btn btn-primary" onclick="showDetail('${item.rec_id}')" style="width: auto;">View Details</button>
            <button class="btn btn-secondary" onclick="handleFeedback('${item.rec_id}', 'like')">👍</button>
            <button class="btn btn-secondary" onclick="handleFeedback('${item.rec_id}', 'save')">⭐</button>
        </div>
    `;
    
    return card;
}

async function showDetail(recId) {
    const item = currentDigest.items.find(i => i.rec_id === recId);
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
                <div class="detail-info-value">${item.travel_time_min} minutes</div>
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
            <p style="margin-bottom: 1rem; color: #666;">Choose a time slot:</p>
            <div class="slot-buttons">
                <button class="slot-btn" onclick="selectSlot('SAT_AM', '${recId}')">Saturday Morning<br>10:00 AM - 12:00 PM</button>
                <button class="slot-btn" onclick="selectSlot('SAT_PM', '${recId}')">Saturday Afternoon<br>2:00 PM - 4:00 PM</button>
                <button class="slot-btn" onclick="selectSlot('SUN_AM', '${recId}')">Sunday Morning<br>10:00 AM - 12:00 PM</button>
                <button class="slot-btn" onclick="selectSlot('SUN_PM', '${recId}')">Sunday Afternoon<br>2:00 PM - 4:00 PM</button>
            </div>
        </div>
        <div style="margin-top: 1.5rem;">
            <button class="btn btn-success" id="add-to-calendar-btn" onclick="addToCalendar('${recId}')" disabled>Add to Calendar</button>
            <button class="btn btn-secondary" onclick="handleFeedback('${recId}', 'already_been')" style="margin-left: 0.5rem;">Already Been</button>
        </div>
    `;
    
    modal.classList.add('active');
    window.selectedSlot = null;
}

function selectSlot(slot, recId) {
    document.querySelectorAll('.slot-btn').forEach(btn => btn.classList.remove('selected'));
    event.target.classList.add('selected');
    window.selectedSlot = slot;
    document.getElementById('add-to-calendar-btn').disabled = false;
}

async function addToCalendar(recId) {
    if (!window.selectedSlot) {
        alert('Please select a time slot first');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/calendar/event_template`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rec_id: recId,
                slot: window.selectedSlot,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
            })
        });
        
        const event = await response.json();
        
        const start = new Date(event.start.dateTime).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        const end = new Date(event.end.dateTime).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        const details = encodeURIComponent(event.description);
        const location = encodeURIComponent(event.location);
        const title = encodeURIComponent(event.summary);
        
        const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${start}/${end}&details=${details}&location=${location}`;
        
        window.open(googleCalendarUrl, '_blank');
        
        await handleFeedback(recId, 'add_to_calendar');
        
        alert('Calendar event created! Check your Google Calendar.');
        document.getElementById('detail-modal').classList.remove('active');
    } catch (error) {
        console.error('Error adding to calendar:', error);
        alert('Error creating calendar event. Please try again.');
    }
}

async function handleFeedback(recId, action) {
    try {
        await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rec_id: recId,
                action: action,
                metadata: { week: currentDigest?.week || '' }
            })
        });
        
        if (action === 'like') {
            event.target.textContent = '👍 Liked!';
            setTimeout(() => { event.target.textContent = '👍'; }, 2000);
        } else if (action === 'save') {
            event.target.textContent = '⭐ Saved!';
            setTimeout(() => { event.target.textContent = '⭐'; }, 2000);
        } else if (action === 'already_been') {
            alert('Marked as visited. This place won\'t be recommended again.');
            document.getElementById('detail-modal').classList.remove('active');
            loadDigest();
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
    }
}

// Make functions globally available
window.goToStep = goToStep;
window.showSubstep = showSubstep;
window.submitLocation = submitLocation;
window.completeLocationStep = completeLocationStep;
window.completeOnboarding = completeOnboarding;
window.skipAndComplete = skipAndComplete;
window.showDetail = showDetail;
window.selectSlot = selectSlot;
window.addToCalendar = addToCalendar;
window.handleFeedback = handleFeedback;
window.loadDigest = loadDigest;
