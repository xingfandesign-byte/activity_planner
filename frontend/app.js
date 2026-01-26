// Weekend Planner Frontend
const API_BASE = 'http://localhost:5001/v1';

let currentUser = null;
let currentDigest = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeAuth();
    setupEventListeners();
});

async function initializeAuth() {
    try {
        const response = await fetch(`${API_BASE}/auth/session`);
        if (!response.ok) {
            throw new Error('Backend not responding');
        }
        const data = await response.json();
        if (data.authenticated) {
            currentUser = data.user_id;
        } else {
            // Create demo session
            await fetch(`${API_BASE}/auth/session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: 'demo_user' })
            });
            currentUser = 'demo_user';
        }
        // Always show onboarding first
        checkOnboarding();
    } catch (error) {
        console.error('Auth error:', error);
        // Show error message but still show onboarding
        currentUser = 'demo_user';
        checkOnboarding();
    }
}

async function checkOnboarding() {
    // Always show onboarding first - don't auto-skip
    // User must complete onboarding to see results
    console.log('Showing onboarding screen');
    // Onboarding is already visible by default (class="screen active")
}

function setupEventListeners() {
    // Onboarding form
    const form = document.getElementById('onboarding-form');
    form.addEventListener('submit', handleOnboarding);
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadDigest);
    
    // Settings button
    document.getElementById('settings-btn').addEventListener('click', () => {
        alert('Settings coming soon!');
    });
    
    // Modal close
    const modal = document.getElementById('detail-modal');
    const closeBtn = document.querySelector('.close');
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

async function handleOnboarding(e) {
    e.preventDefault();
    
    const selectedCategories = Array.from(document.querySelectorAll('input[name="categories"]:checked'))
        .map(cb => cb.value);
    
    // Ensure at least one category is selected
    if (selectedCategories.length === 0) {
        alert('Please select at least one category.');
        return;
    }
    
    const formData = {
        home_location: {
            type: 'city',
            value: document.getElementById('home-location').value
        },
        radius_miles: parseInt(document.getElementById('radius').value),
        categories: selectedCategories,
        kid_friendly: document.getElementById('kid-friendly').checked,
        budget: { min: 0, max: 50 },
        time_windows: ['SAT_AM', 'SAT_PM', 'SUN_AM', 'SUN_PM'],
        notification_time_local: document.getElementById('notification-time').value,
        dedup_window_days: 365,
        calendar_dedup_opt_in: false
    };
    
    console.log('Saving preferences:', formData);
    
    try {
        const response = await fetch(`${API_BASE}/preferences`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to save preferences: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log('Preferences saved:', result);
        
        // Show loading state on submit button
        const submitButton = document.querySelector('#onboarding-form button[type="submit"]');
        if (submitButton) {
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Loading recommendations...';
            submitButton.disabled = true;
        }
        
        // Switch to planner screen
        showPlanner();
        
        // Load digest
        loadDigest().then(() => {
            // Reset button state (in case needed)
            if (submitButton) {
                submitButton.textContent = 'Get Started';
                submitButton.disabled = false;
            }
        });
    } catch (error) {
        console.error('Onboarding error:', error);
        alert(`Error saving preferences: ${error.message}\n\nMake sure the backend server is running on port 5001.`);
    }
}

function showPlanner() {
    // Hide onboarding
    const onboarding = document.getElementById('onboarding');
    const planner = document.getElementById('planner');
    
    if (onboarding) {
        onboarding.classList.remove('active');
    }
    if (planner) {
        planner.classList.add('active');
    }
    
    console.log('Switched to planner screen');
}

async function loadDigest() {
    const loading = document.getElementById('loading');
    const itemsContainer = document.getElementById('digest-items');
    
    loading.style.display = 'block';
    itemsContainer.innerHTML = '';
    
    try {
        console.log('Loading digest from:', `${API_BASE}/digest`);
        const response = await fetch(`${API_BASE}/digest`);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Digest loaded:', data);
        currentDigest = data;
        
        if (data.items && data.items.length > 0) {
            console.log(`Rendering ${data.items.length} recommendations`);
            renderDigestItems(data.items);
        } else {
            console.warn('No items in digest response');
            itemsContainer.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #666;">
                    <p><strong>No recommendations available</strong></p>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem;">This might be because:</p>
                    <ul style="text-align: left; display: inline-block; margin-top: 0.5rem;">
                        <li>All places are filtered out by your preferences</li>
                        <li>Selected categories don't match available places</li>
                        <li>All places are marked as "already been"</li>
                    </ul>
                    <p style="font-size: 0.85rem; margin-top: 1rem;">Try adjusting your preferences or click "Skip & Use Defaults" to see all recommendations.</p>
                    <button class="btn btn-secondary" onclick="skipOnboarding()" style="margin-top: 1rem;">Use Defaults</button>
                    <button class="btn btn-primary" onclick="loadDigest()" style="margin-top: 1rem; margin-left: 0.5rem;">Retry</button>
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
                <button class="btn btn-primary" onclick="loadDigest()" style="margin-top: 1rem;">Retry</button>
            </div>
        `;
    } finally {
        loading.style.display = 'none';
    }
}

function showBackendError() {
    // Show a banner if backend is not available
    const planner = document.getElementById('planner');
    if (planner && planner.classList.contains('active')) {
        const container = planner.querySelector('.container');
        if (container && !container.querySelector('.backend-error')) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'backend-error';
            errorDiv.style.cssText = 'background: #fee; border: 2px solid #fcc; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; color: #c33;';
            errorDiv.innerHTML = '<strong>⚠️ Backend Connection Issue:</strong> Make sure the backend server is running on <code>http://localhost:5001</code>';
            container.insertBefore(errorDiv, container.firstChild);
        }
    }
}

function renderDigestItems(items) {
    const container = document.getElementById('digest-items');
    container.innerHTML = '';
    
    if (!items || items.length === 0) {
        console.warn('No items to render');
        container.innerHTML = '<p style="text-align: center; padding: 2rem; color: #666;">No recommendations available.</p>';
        return;
    }
    
    console.log(`Rendering ${items.length} items`);
    items.forEach((item, index) => {
        console.log(`Rendering item ${index + 1}:`, item.title);
        const card = createRecommendationCard(item);
        container.appendChild(card);
    });
}

function createRecommendationCard(item) {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    
    card.innerHTML = `
        <div class="card-header">
            <div>
                <div class="card-title">${item.title}</div>
                <span class="card-category">${item.category}</span>
            </div>
        </div>
        <div class="card-info">
            <span class="info-badge">📍 ${item.distance_miles} mi</span>
            <span class="info-badge">⏱️ ${item.travel_time_min} min</span>
            <span class="info-badge">💰 ${item.price_flag}</span>
            ${item.kid_friendly ? '<span class="info-badge">👶 Kid-friendly</span>' : ''}
            <span class="info-badge">${item.indoor_outdoor === 'outdoor' ? '☀️ Outdoor' : '🏠 Indoor'}</span>
        </div>
        <div class="card-explanation">${item.explanation}</div>
        <div class="card-actions">
            <button class="btn btn-primary" onclick="showDetail('${item.rec_id}')">View Details</button>
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
    window.selectedRecId = recId;
}

function selectSlot(slot, recId) {
    // Remove previous selection
    document.querySelectorAll('.slot-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // Mark selected
    event.target.classList.add('selected');
    window.selectedSlot = slot;
    window.selectedRecId = recId;
    
    // Enable add to calendar button
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
        
        // Create Google Calendar link
        const start = new Date(event.start.dateTime).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        const end = new Date(event.end.dateTime).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        const details = encodeURIComponent(event.description);
        const location = encodeURIComponent(event.location);
        const title = encodeURIComponent(event.summary);
        
        const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${start}/${end}&details=${details}&location=${location}`;
        
        // Open in new window
        window.open(googleCalendarUrl, '_blank');
        
        // Record feedback
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
                metadata: {
                    week: currentDigest?.week || ''
                }
            })
        });
        
        if (action === 'like') {
            event.target.textContent = '👍 Liked!';
            setTimeout(() => {
                event.target.textContent = '👍';
            }, 2000);
        } else if (action === 'save') {
            event.target.textContent = '⭐ Saved!';
            setTimeout(() => {
                event.target.textContent = '⭐';
            }, 2000);
        } else if (action === 'already_been') {
            alert('Marked as visited. This place won\'t be recommended again.');
            loadDigest(); // Refresh to remove from list
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
    }
}

function skipOnboarding() {
    // Use default preferences and proceed to results
    const defaultPrefs = {
        home_location: {
            type: 'city',
            value: 'San Francisco, CA'
        },
        radius_miles: 10,
        categories: ['parks', 'museums', 'attractions'],
        kid_friendly: true,
        budget: { min: 0, max: 50 },
        time_windows: ['SAT_AM', 'SAT_PM', 'SUN_AM', 'SUN_PM'],
        notification_time_local: '16:00',
        dedup_window_days: 365,
        calendar_dedup_opt_in: false
    };
    
    // Save defaults and show results
    fetch(`${API_BASE}/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(defaultPrefs)
    }).then(() => {
        showPlanner();
        loadDigest();
    }).catch(error => {
        console.error('Error saving default preferences:', error);
        // Still show planner even if save fails
        showPlanner();
        loadDigest();
    });
}

// Make functions available globally
window.showDetail = showDetail;
window.selectSlot = selectSlot;
window.addToCalendar = addToCalendar;
window.handleFeedback = handleFeedback;
window.skipOnboarding = skipOnboarding;
