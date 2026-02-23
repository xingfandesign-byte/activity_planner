// Activity Planner Frontend - User Account Flow
const API_BASE = (typeof window !== 'undefined' && window.API_BASE) || 'http://localhost:5001/v1';

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

// Loading animation state
let loadingPhraseInterval = null;

// ==================== MOTIVATIONAL LOADING PHRASES ====================

const motivationalPhrases = {
    // Solo / Self - inspirational phrases for personal growth
    solo: [
        "✨ Your next adventure awaits...",
        "🌟 Finding moments just for you...",
        "💫 Discovering your perfect escape...",
        "🎯 Curating experiences that spark joy...",
        // Famous quotes for solo/self-discovery
        '"The only person you are destined to become is the person you decide to be." — Ralph Waldo Emerson',
        '"Life is either a daring adventure or nothing at all." — Helen Keller',
        '"Be yourself; everyone else is already taken." — Oscar Wilde',
        '"The journey of a thousand miles begins with a single step." — Lao Tzu',
        '"Do one thing every day that scares you." — Eleanor Roosevelt',
        '"Not all those who wander are lost." — J.R.R. Tolkien',
        '"The best time to plant a tree was 20 years ago. The second best time is now." — Chinese Proverb',
        '"You must be the change you wish to see in the world." — Mahatma Gandhi',
        '"In the middle of difficulty lies opportunity." — Albert Einstein',
        '"What lies behind us and what lies before us are tiny matters compared to what lies within us." — Ralph Waldo Emerson',
        '"The only way to do great work is to love what you do." — Steve Jobs',
        '"Believe you can and you\'re halfway there." — Theodore Roosevelt',
        '"It is never too late to be what you might have been." — George Eliot',
        '"The purpose of life is to live it, to taste experience to the utmost." — Eleanor Roosevelt',
        '"Your time is limited, don\'t waste it living someone else\'s life." — Steve Jobs',
    ],
    
    // Couple - romantic and connection phrases
    couple: [
        "💕 Finding romantic adventures for two...",
        "🌹 Curating special moments together...",
        "✨ Love is in the details...",
        "💫 Creating memories side by side...",
        // Famous quotes about love and togetherness
        '"The best thing to hold onto in life is each other." — Audrey Hepburn',
        '"Love is composed of a single soul inhabiting two bodies." — Aristotle',
        '"In all the world, there is no heart for me like yours." — Maya Angelou',
        '"Whatever our souls are made of, his and mine are the same." — Emily Brontë',
        '"The greatest thing you\'ll ever learn is just to love and be loved in return." — Eden Ahbez',
        '"We loved with a love that was more than love." — Edgar Allan Poe',
        '"You know you\'re in love when you can\'t fall asleep because reality is finally better than your dreams." — Dr. Seuss',
        '"Being deeply loved by someone gives you strength, while loving someone deeply gives you courage." — Lao Tzu',
        '"The best and most beautiful things in this world cannot be seen or even heard, but must be felt with the heart." — Helen Keller',
        '"Love recognizes no barriers." — Maya Angelou',
        '"A successful marriage requires falling in love many times, always with the same person." — Mignon McLaughlin',
        '"Where there is love there is life." — Mahatma Gandhi',
    ],
    
    // Family - warm, inclusive family phrases
    family: [
        "👨‍👩‍👧‍👦 Finding fun for the whole family...",
        "🏠 Home is where the heart is, adventure is where we go...",
        "🎈 Making memories that last a lifetime...",
        "🌈 Family time is the best time...",
        // Famous quotes about family
        '"Family is not an important thing. It\'s everything." — Michael J. Fox',
        '"The love of a family is life\'s greatest blessing." — Unknown',
        '"In family life, love is the oil that eases friction." — Friedrich Nietzsche',
        '"The family is one of nature\'s masterpieces." — George Santayana',
        '"Other things may change us, but we start and end with family." — Anthony Brandt',
        '"Family means no one gets left behind or forgotten." — David Ogden Stiers',
        '"The most important thing in the world is family and love." — John Wooden',
        '"Children are the anchors of a mother\'s life." — Sophocles',
        '"A happy family is but an earlier heaven." — George Bernard Shaw',
        '"The memories we make with our family is everything." — Candace Cameron Bure',
        '"Family is the most important thing in the world." — Princess Diana',
        '"To us, family means putting your arms around each other and being there." — Barbara Bush',
        '"There is no doubt that it is around the family that all the greatest virtues are created." — Winston Churchill',
        '"Call it a clan, call it a network, call it a tribe, call it a family: Whatever you call it, whoever you are, you need one." — Jane Howard',
    ],
    
    // Friends - fun, social phrases
    friends: [
        "🎉 Rally the crew, adventure awaits...",
        "🍻 Finding your squad's next hangout...",
        "✨ Good times with great friends incoming...",
        "🎊 The best stories start with 'Remember when...'",
        // Famous quotes about friendship
        '"A friend is someone who knows all about you and still loves you." — Elbert Hubbard',
        '"Friendship is born at that moment when one person says to another, \'What! You too?\'" — C.S. Lewis',
        '"There is nothing I would not do for those who are really my friends." — Jane Austen',
        '"A real friend is one who walks in when the rest of the world walks out." — Walter Winchell',
        '"Friends are the family you choose." — Jess C. Scott',
        '"Life was meant for good friends and great adventures." — Unknown',
        '"Good friends, good books, and a sleepy conscience: this is the ideal life." — Mark Twain',
        '"The only way to have a friend is to be one." — Ralph Waldo Emerson',
        '"True friends are never apart, maybe in distance but never in heart." — Helen Keller',
        '"Friendship is the only cement that will ever hold the world together." — Woodrow Wilson',
        '"A sweet friendship refreshes the soul." — Proverbs 27:9',
        '"Friends show their love in times of trouble, not in happiness." — Euripides',
        '"Lots of people want to ride with you in the limo, but what you want is someone who will take the bus with you." — Oprah Winfrey',
    ],
    
    // Default / fallback phrases
    default: [
        "✨ Getting personalized recommendations...",
        "🔍 Searching for the perfect activities...",
        "🌟 Curating your activity possibilities...",
        "💫 Finding what's happening near you...",
        '"The world is a book and those who do not travel read only one page." — Saint Augustine',
        '"Life is what happens when you\'re busy making other plans." — John Lennon',
        '"Twenty years from now you will be more disappointed by the things you didn\'t do." — Mark Twain',
        '"Adventure is worthwhile in itself." — Amelia Earhart',
        '"Take only memories, leave only footprints." — Chief Seattle',
        '"The real voyage of discovery consists not in seeking new landscapes, but in having new eyes." — Marcel Proust',
    ],
    
    // Interest-specific additions
    interests: {
        nature: [
            "🌲 Nature is calling...",
            '"In every walk with nature, one receives far more than he seeks." — John Muir',
            '"Look deep into nature, and then you will understand everything better." — Albert Einstein',
            '"The earth has music for those who listen." — Shakespeare',
            '"Adopt the pace of nature: her secret is patience." — Ralph Waldo Emerson',
        ],
        arts_culture: [
            "🎨 Culture and creativity await...",
            '"Every artist was first an amateur." — Ralph Waldo Emerson',
            '"Art washes away from the soul the dust of everyday life." — Pablo Picasso',
            '"The purpose of art is washing the dust of daily life off our souls." — Pablo Picasso',
            '"Creativity takes courage." — Henri Matisse',
        ],
        food_drink: [
            "🍽️ Delicious discoveries ahead...",
            '"One cannot think well, love well, sleep well, if one has not dined well." — Virginia Woolf',
            '"Life is uncertain. Eat dessert first." — Ernestine Ulmer',
            '"Food is symbolic of love when words are inadequate." — Alan D. Wolfelt',
            '"Cooking is love made visible." — Unknown',
        ],
        fitness: [
            "💪 Energizing activities incoming...",
            '"The only bad workout is the one that didn\'t happen." — Unknown',
            '"Take care of your body. It\'s the only place you have to live." — Jim Rohn',
            '"Physical fitness is the first requisite of happiness." — Joseph Pilates',
            '"The body achieves what the mind believes." — Napoleon Hill',
        ],
        nightlife: [
            "🌙 The night is young...",
            '"We are all in the gutter, but some of us are looking at the stars." — Oscar Wilde',
            '"The night is more alive and more richly colored than the day." — Vincent van Gogh',
            '"Music is the wine that fills the cup of silence." — Robert Fripp',
        ],
        learning: [
            "📚 Knowledge is an adventure...",
            '"Live as if you were to die tomorrow. Learn as if you were to live forever." — Mahatma Gandhi',
            '"Education is the most powerful weapon which you can use to change the world." — Nelson Mandela',
            '"The more that you read, the more things you will know." — Dr. Seuss',
            '"An investment in knowledge pays the best interest." — Benjamin Franklin',
        ],
        shopping: [
            "🛍️ Retail therapy incoming...",
            '"I have enough clothes and shoes. I never want to go shopping again. — said no one ever"',
            '"Whoever said money can\'t buy happiness didn\'t know where to shop." — Gertrude Stein',
            '"Shopping is my cardio." — Carrie Bradshaw',
        ],
    }
};

function getPersonalizedPhrases() {
    const groupType = onboardingData.group_type || 'default';
    const interests = onboardingData.interests || [];
    
    // Start with group-type phrases
    let phrases = [...(motivationalPhrases[groupType] || motivationalPhrases.default)];
    
    // Add interest-specific phrases
    interests.forEach(interest => {
        if (motivationalPhrases.interests[interest]) {
            phrases.push(...motivationalPhrases.interests[interest]);
        }
    });
    
    // Add some defaults for variety
    phrases.push(...motivationalPhrases.default.slice(0, 3));
    
    // Shuffle the phrases
    return phrases.sort(() => Math.random() - 0.5);
}

function startLoadingAnimation(container) {
    if (!container) return;
    
    const phrases = getPersonalizedPhrases();
    let currentIndex = 0;
    
    // Set initial phrase
    container.innerHTML = `<div class="loading-phrases" id="loading-phrase-container">
        <div class="loading-spinner"></div>
        <p class="loading-phrase" id="loading-phrase">${phrases[0]}</p>
        <p class="loading-subtext">This may take a moment...</p>
    </div>`;
    
    // Rotate phrases every 2.5 seconds
    loadingPhraseInterval = setInterval(() => {
        currentIndex = (currentIndex + 1) % phrases.length;
        const phraseEl = document.getElementById('loading-phrase');
        if (phraseEl) {
            phraseEl.style.opacity = '0';
            setTimeout(() => {
                phraseEl.textContent = phrases[currentIndex];
                phraseEl.style.opacity = '1';
            }, 300);
        }
    }, 2500);
}

function stopLoadingAnimation() {
    if (loadingPhraseInterval) {
        clearInterval(loadingPhraseInterval);
        loadingPhraseInterval = null;
    }
}

// ==================== NETWORK STATUS ====================

let isOffline = !navigator.onLine;
let retryCount = 0;
const MAX_RETRIES = 3;

window.addEventListener('online', () => {
    isOffline = false;
    retryCount = 0;
    const banner = document.getElementById('offline-banner');
    if (banner) banner.classList.add('hidden');
    // Auto-refresh if we were showing an error
    const container = document.getElementById('dashboard-digest-items');
    if (container && container.querySelector('.empty-state, [style*="color: #ef4444"]')) {
        loadDashboardRecommendations();
    }
});

window.addEventListener('offline', () => {
    isOffline = true;
    showOfflineBanner();
});

function showOfflineBanner() {
    let banner = document.getElementById('offline-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.setAttribute('role', 'alert');
        banner.innerHTML = `
            <span>📡 You're offline — showing cached results</span>
            <button onclick="this.parentElement.classList.add('hidden')" aria-label="Dismiss">✕</button>
        `;
        document.body.prepend(banner);
    }
    banner.classList.remove('hidden');
}

function getRetryDelay() {
    // Exponential backoff: 1s, 2s, 4s
    return Math.min(1000 * Math.pow(2, retryCount), 4000);
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

async function initApp() {
    const urlParams = new URLSearchParams(window.location.search);
    // Check for email verification link (URL has ?verify_token=...)
    const verifyToken = urlParams.get('verify_token');
    if (verifyToken) {
        showAuthScreen();
        await handleVerifyEmailLink(verifyToken);
        return;
    }
    // Check for password reset link (URL has ?reset_token=...)
    const resetToken = urlParams.get('reset_token');
    if (resetToken) {
        showAuthScreen();
        showResetPasswordForm(resetToken);
        return;
    }
    
    // Check for existing session
    authToken = localStorage.getItem('auth_token');
    const userId = localStorage.getItem('user_id');
    
    // Check for saved preferences (even without account)
    const savedPrefs = localStorage.getItem('activity_planner_preferences');
    
    if (authToken && userId) {
        // Returning user with account - validate and load
        try {
            const response = await fetch(`${API_BASE}/user/preferences`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                currentUser = { id: userId, ...data.user };
                if (data.user && typeof data.user.email_verified === 'boolean') {
                    currentUser.email_verified = data.user.email_verified;
                }
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
        btn.addEventListener('click', (e) => {
            const value = btn.dataset.value;
            // Travel time toggles: only handle via onclick="toggleQuickTravelTime(this)" to avoid double-toggle
            if (value === '0-15' || value === '15-30' || value === '30-60' || value === '60+') {
                return;
            }
            // Single-select for group (Planning for)
            const group = btn.parentElement;
            group.querySelectorAll('.quick-toggle').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            onQuickAdjustmentChange();
        });
    });
    
    // Enter key support for forms
    document.getElementById('login-password')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    document.getElementById('login-email')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') document.getElementById('login-password')?.focus();
    });
    document.getElementById('signup-password')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleSignup();
    });
    document.getElementById('signup-email')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') document.getElementById('signup-password')?.focus();
    });
    document.getElementById('zip-input')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitLocation('zip');
    });
    document.getElementById('address-input')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitLocation('address');
    });
    document.getElementById('forgot-email')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleForgotPassword();
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

    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                activeModal.classList.remove('active');
                e.preventDefault();
            }
        }
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
    
    // Show skeleton cards for perceived performance
    if (container) {
        container.innerHTML = `
            <div class="skeleton-cards">
                ${Array(4).fill('').map(() => `
                    <div class="recommendation-card skeleton-card">
                        <div class="skeleton-line skeleton-title"></div>
                        <div class="skeleton-line skeleton-short"></div>
                        <div class="skeleton-line skeleton-medium"></div>
                        <div class="skeleton-line skeleton-short"></div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Start personalized loading animation (overlay)
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loading-overlay';
    startLoadingAnimation(loadingOverlay);
    if (container) container.prepend(loadingOverlay);
    
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
            const fallbackResponse = await fetch(`${API_BASE}/digest`, {
                headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {}
            });
            if (!fallbackResponse.ok) throw new Error('Backend error');
            const data = await fallbackResponse.json();
            window.currentDigest = data;
            stopLoadingAnimation();
            if (data.items?.length > 0) {
                renderDashboardItems(data.items);
            } else {
                throw new Error('No recommendations');
            }
            return;
        }
        
        const data = await response.json();
        window.currentDigest = data;
        stopLoadingAnimation();
        
        if (data.items && data.items.length > 0) {
            // Save successful results for fallback use
            try {
                localStorage.setItem('last_successful_recommendations', JSON.stringify({
                    items: data.items,
                    timestamp: Date.now(),
                    sources: data.sources
                }));
            } catch (e) {
                // Ignore localStorage errors
            }
            
            renderDashboardItems(data.items, data.from_cache, data.sources);
        } else {
            if (container) {
                container.innerHTML = buildEmptyState();
            }
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        stopLoadingAnimation();
        
        // Try to show last successful results from localStorage as fallback
        const lastResults = localStorage.getItem('last_successful_recommendations');
        if (lastResults) {
            try {
                const data = JSON.parse(lastResults);
                if (data.items && data.items.length > 0) {
                    if (container) {
                        container.innerHTML = '';
                        // Show network error indicator with cached results
                        const errorIndicator = document.createElement('div');
                        errorIndicator.innerHTML = `
                            <div style="background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #dc2626;">
                                <span>⚠️</span>
                                <span>Network error - showing last successful results</span>
                                <button onclick="refreshRecommendations()" style="margin-left: auto; padding: 0.25rem 0.5rem; font-size: 0.75rem; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer;">Retry</button>
                            </div>
                        `;
                        container.appendChild(errorIndicator);
                        
                        // Show the cached items
                        data.items.forEach(item => {
                            const card = createRecommendationCard(item);
                            container.appendChild(card);
                        });
                    }
                    return;
                }
            } catch (e) {
                // Failed to parse cached data, continue to error display
            }
        }
        
        if (container) {
            const offline = !navigator.onLine;
            container.innerHTML = `
                <div class="empty-state" role="alert">
                    <div class="empty-state-icon">${offline ? '📡' : '⚠️'}</div>
                    <h3 class="empty-state-title">${offline ? "You're offline" : 'Error loading recommendations'}</h3>
                    <p class="empty-state-subtitle">${offline
                        ? 'Check your internet connection and try again.'
                        : 'Make sure the backend server is running, or try again in a moment.'}</p>
                    <button class="btn btn-primary" onclick="retryWithBackoff()" style="width: auto; margin-top: 1rem;" id="retry-btn">
                        Retry
                    </button>
                </div>
            `;
        }
    }
}

// Lazy load images using IntersectionObserver
const _imgObserver = ('IntersectionObserver' in window) ? new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
                img.src = img.dataset.src;
                delete img.dataset.src;
            }
            _imgObserver.unobserve(img);
        }
    });
}, { rootMargin: '200px' }) : null;

function observeLazyImages(container) {
    if (!container) return;
    container.querySelectorAll('img[data-src]').forEach(img => {
        if (_imgObserver) {
            _imgObserver.observe(img);
        } else {
            img.src = img.dataset.src;
            delete img.dataset.src;
        }
    });
}

function renderDashboardItems(items, fromCache = false, sources = []) {
    const container = document.getElementById('dashboard-digest-items');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Show response time if available
    const responseTime = window.currentDigest?.response_time_ms;
    if (responseTime !== undefined) {
        const timeIndicator = document.createElement('div');
        timeIndicator.className = 'response-time-indicator';
        timeIndicator.textContent = `Loaded in ${responseTime < 1000 ? responseTime + 'ms' : (responseTime / 1000).toFixed(1) + 's'}`;
        container.appendChild(timeIndicator);
    }
    
    // Add cache/source indicator if needed
    if (fromCache || sources.includes('cache')) {
        const cacheIndicator = document.createElement('div');
        cacheIndicator.className = 'cache-indicator';
        cacheIndicator.innerHTML = `
            <div style="background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #6b7280;">
                <span>💾</span>
                <span>Showing cached results - refresh to get latest recommendations</span>
                <button onclick="refreshRecommendations()" style="margin-left: auto; padding: 0.25rem 0.5rem; font-size: 0.75rem; background: #374151; color: white; border: none; border-radius: 4px; cursor: pointer;">Refresh</button>
            </div>
        `;
        container.appendChild(cacheIndicator);
    } else if (sources.includes('mock')) {
        const mockIndicator = document.createElement('div');
        mockIndicator.className = 'mock-indicator';
        mockIndicator.innerHTML = `
            <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #92400e;">
                <span>ℹ️</span>
                <span>Showing sample recommendations - try refreshing for live results</span>
                <button onclick="refreshRecommendations()" style="margin-left: auto; padding: 0.25rem 0.5rem; font-size: 0.75rem; background: #f59e0b; color: white; border: none; border-radius: 4px; cursor: pointer;">Refresh</button>
            </div>
        `;
        container.appendChild(mockIndicator);
    }
    
    // Add recommendation cards
    items.forEach(item => {
        const card = createRecommendationCard(item);
        container.appendChild(card);
    });
    
    // Start lazy loading images
    observeLazyImages(container);
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
            currentUser = { id: data.user_id, email, email_verified: data.email_verified === true };
            
            console.log('[Auth] Login successful:', email);
            
            if (data.preferences) {
                onboardingData = { ...onboardingData, ...data.preferences };
                showDashboard();
            } else {
                showOnboarding();
            }
        } else {
            // Show actual error from server (account may not exist or wrong password)
            alert(data.error || 'Invalid email or password');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Unable to connect to server. Please try again.');
    }
}

async function handleVerifyEmailLink(token) {
    const msgEl = document.getElementById('verify-email-message');
    if (!msgEl) return;
    msgEl.style.display = 'block';
    msgEl.classList.remove('success', 'error');
    msgEl.textContent = 'Verifying your email...';
    try {
        const response = await fetch(`${API_BASE}/auth/verify-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        const data = await response.json();
        if (response.ok) {
            msgEl.classList.add('success');
            msgEl.textContent = data.message || 'Email verified. You can sign in with your account.';
            window.history.replaceState({}, document.title, window.location.pathname || '/index.html');
        } else {
            msgEl.classList.add('error');
            msgEl.textContent = data.error || 'Invalid or expired verification link.';
        }
    } catch (e) {
        msgEl.classList.add('error');
        msgEl.textContent = 'Unable to verify. Please try again or request a new link.';
    }
}

function dismissVerifyBanner() {
    localStorage.setItem('verify_banner_dismissed', '1');
    const el = document.getElementById('verify-email-banner');
    if (el) el.classList.add('hidden');
}

async function resendVerificationEmail() {
    const email = localStorage.getItem('user_email') || currentUser?.email;
    if (!email) {
        alert('Email not found. Please sign in again.');
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/auth/resend-verification`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': authToken ? `Bearer ${authToken}` : '' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        if (response.ok) {
            if (data.verification_token) {
                const link = `${window.location.origin}${window.location.pathname || '/index.html'}?verify_token=${encodeURIComponent(data.verification_token)}`;
                alert('Verification email sent (or use this link for testing): ' + link);
            } else {
                alert(data.message || 'If your account is unverified, a new verification link was sent to your email.');
            }
        } else {
            alert(data.error || 'Could not send verification email.');
        }
    } catch (e) {
        console.error('Resend verification error:', e);
        alert('Unable to send. Please try again.');
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
            
            console.log('[Auth] Signup successful - new account created:', email);
            
            // NEW ACCOUNT: Always start fresh with onboarding
            // Clear any previous guest preferences to ensure clean onboarding experience
            localStorage.removeItem('activity_planner_preferences');
            onboardingData = {
                group_type: null,
                home_location: null,
                transportation: [],
                departure_times: { saturday: [], sunday: [] },
                travel_time_ranges: [],
                interests: [],
                energy_level: null,
                time_commitment: null,
                budget: null,
                accessibility: [],
                avoid: []
            };
            
            showOnboarding();
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
    const savedPrefs = localStorage.getItem('activity_planner_preferences');
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
    
    console.log('[Auth] Demo signup - new account created:', identifier);
    
    // NEW ACCOUNT: Always start fresh with onboarding
    // Clear any previous guest preferences to ensure clean onboarding experience
    localStorage.removeItem('activity_planner_preferences');
    onboardingData = {
        group_type: null,
        home_location: null,
        transportation: [],
        departure_times: { saturday: [], sunday: [] },
        travel_time_ranges: [],
        interests: [],
        energy_level: null,
        time_commitment: null,
        budget: null,
        accessibility: [],
        avoid: []
    };
    
    showOnboarding();
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
            const statusResponse = await fetch(`${API_BASE}/auth/google/status`, { credentials: 'include' });
            if (!statusResponse.ok) {
                console.error('[Auth] Google status check failed:', statusResponse.status, statusResponse.statusText);
                alert('Failed to sign in with Google. Server returned ' + statusResponse.status + '.');
                return;
            }
            const statusData = await statusResponse.json();

            if (!statusData.configured) {
                // Fall back to demo mode if not configured
                alert('Google OAuth not configured. Using demo mode.');
                simulateLogin('demo@google.com');
                return;
            }

            // Get the Google auth URL
            const urlResponse = await fetch(`${API_BASE}/auth/google/url`, { credentials: 'include' });
            if (!urlResponse.ok) {
                console.error('[Auth] Google URL fetch failed:', urlResponse.status, urlResponse.statusText);
                alert('Failed to sign in with Google. Server returned ' + urlResponse.status + '.');
                return;
            }
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

                if (!popup || popup.closed) {
                    alert('Popup was blocked. Please allow popups for this site and try again.');
                    return;
                }

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
                        alert('Sign-in failed: ' + (event.data.error || 'Unknown error'));
                        window.removeEventListener('message', handleOAuthMessage);
                    }
                });
            } else {
                console.error('[Auth] No URL returned from server:', urlData);
                alert('Failed to sign in with Google. Server did not return an auth URL.');
            }
        } catch (error) {
            console.error('[Auth] Google OAuth error:', error);
            alert('Failed to sign in with Google: ' + error.message);
        }
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
        formatted_address: input,
        precision: type === 'zip' ? 'approximate' : 'exact'
        // lat/lng omitted so backend geocodes from address for correct distance/travel time
    };
    
    document.getElementById('location-display').textContent = `📍 ${input}`;
    showSubstep('2c');
}

function completeLocationStep() {
    const saveCheckbox = document.getElementById('save-location-checkbox');
    
    if (saveCheckbox?.checked) {
        localStorage.setItem('activity_planner_location', JSON.stringify({
            ...onboardingData.home_location,
            savedAt: new Date().toISOString()
        }));
    }
    
    showSubstep('2d');
}

function handleSaveLocationCheckbox(checkbox) {
    if (!checkbox.checked) return;
    
    const existingLocation = localStorage.getItem('activity_planner_location');
    
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
    localStorage.setItem('activity_planner_preferences', JSON.stringify(preferences));
    
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
    
    // Email verification banner (show only for email signup users who haven't verified)
    const verifyBanner = document.getElementById('verify-email-banner');
    if (verifyBanner) {
        const showBanner = !currentUser?.isGuest && currentUser?.email &&
            currentUser.email_verified === false && localStorage.getItem('auth_provider') === 'email';
        if (showBanner && !localStorage.getItem('verify_banner_dismissed')) {
            verifyBanner.classList.remove('hidden');
        } else {
            verifyBanner.classList.add('hidden');
        }
    }
    
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
        onboardingData.travel_time_ranges?.join(', ').replace(/-/g, '-') + ' min' || 'Not set';
    
    // Sync Quick Adjustments travel time toggles to match saved preferences
    document.querySelectorAll('.travel-time-toggles .quick-toggle').forEach(btn => {
        const value = btn.dataset.value;
        if (onboardingData.travel_time_ranges?.includes(value)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
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
                    formatted_address: locationInput
                    // omit lat/lng so backend geocodes from address for correct distance/travel time
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
    
    // Load data for specific tabs
    if (tab === 'saved') {
        loadSavedPlaces();
    } else if (tab === 'been') {
        loadBeenPlaces();
    } else if (tab === 'interests') {
        loadAffinityScores();
    } else if (tab === 'interests') {
        loadInterestProfile();
    }
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

async function loadAffinityScores() {
    const loadingEl = document.getElementById('affinity-loading');
    const contentEl = document.getElementById('affinity-content');
    const listEl = document.getElementById('affinity-list');
    const statsEl = document.getElementById('affinity-stats');
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        listEl.innerHTML = '<div class="list-auth-needed">Sign in to see your learned preferences</div>';
        statsEl.innerHTML = '';
        return;
    }
    
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/user/affinity`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayAffinityScores(data);
        } else {
            listEl.innerHTML = '<div class="list-error">Failed to load preferences</div>';
            statsEl.innerHTML = '';
        }
    } catch (error) {
        console.error('Error loading affinity scores:', error);
        listEl.innerHTML = '<div class="list-error">Failed to load preferences</div>';
        statsEl.innerHTML = '';
    } finally {
        loadingEl.style.display = 'none';
        contentEl.style.display = 'block';
    }
}

function displayAffinityScores(data) {
    const listEl = document.getElementById('affinity-list');
    const statsEl = document.getElementById('affinity-stats');
    const { preferences = [], stats = {} } = data;
    
    if (preferences.length === 0) {
        listEl.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🎯</div>
                <p>No learned preferences yet</p>
                <p class="empty-hint">Use thumbs up/down, save places, and mark places as visited to build your preference profile</p>
            </div>
        `;
        statsEl.innerHTML = '';
        return;
    }
    
    // Display preference items
    listEl.innerHTML = preferences.map(pref => {
        const barWidth = Math.abs(pref.score) * 100; // score is [-1, 1]
        return `
            <div class="affinity-item ${pref.sentiment}">
                <div class="affinity-category">${pref.category}</div>
                <div class="affinity-score">
                    <div class="affinity-bar">
                        <div class="affinity-bar-fill ${pref.sentiment}" style="width: ${barWidth}%"></div>
                    </div>
                    <div class="affinity-value">${pref.score > 0 ? '+' : ''}${pref.score}</div>
                    <div class="affinity-level ${pref.level}">${pref.level}</div>
                </div>
            </div>
        `;
    }).join('');
    
    // Display stats
    statsEl.innerHTML = `
        <h4>📊 Your Activity Summary</h4>
        <div class="affinity-stats-grid">
            <div class="affinity-stat">
                <span class="affinity-stat-value">${stats.saved_places || 0}</span>
                <span class="affinity-stat-label">Saved</span>
            </div>
            <div class="affinity-stat">
                <span class="affinity-stat-value">${stats.visited_places || 0}</span>
                <span class="affinity-stat-label">Visited</span>
            </div>
            <div class="affinity-stat">
                <span class="affinity-stat-value">${stats.interactions || 0}</span>
                <span class="affinity-stat-label">Total</span>
            </div>
        </div>
    `;
}

async function resetAffinityScores() {
    if (!confirm('Are you sure you want to reset your learned preferences? This will clear your personalization data.')) {
        return;
    }
    
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE}/user/affinity/reset`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            alert('Your learned preferences have been reset successfully.');
            loadAffinityScores(); // Reload the display
        } else {
            alert('Failed to reset preferences. Please try again.');
        }
    } catch (error) {
        console.error('Error resetting affinity scores:', error);
        alert('Failed to reset preferences. Please try again.');
    }
}

async function loadSavedPlaces() {
    const listEl = document.getElementById('saved-places-list');
    const emptyEl = document.getElementById('saved-empty');
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        listEl.innerHTML = '<div class="list-auth-needed">Sign in to see your saved places</div>';
        emptyEl.style.display = 'none';
        return;
    }
    
    listEl.innerHTML = '<div class="list-loading">Loading...</div>';
    emptyEl.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/saved`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.saved && data.saved.length > 0) {
                listEl.innerHTML = data.saved.map(place => createPlaceListItem(place, 'saved')).join('');
            } else {
                listEl.innerHTML = '';
                emptyEl.style.display = 'block';
            }
        } else {
            listEl.innerHTML = '<div class="list-error">Failed to load saved places</div>';
        }
    } catch (error) {
        console.error('Error loading saved places:', error);
        listEl.innerHTML = '<div class="list-error">Failed to load saved places</div>';
    }
}

async function loadBeenPlaces() {
    const listEl = document.getElementById('been-places-list');
    const emptyEl = document.getElementById('been-empty');
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        listEl.innerHTML = '<div class="list-auth-needed">Sign in to see your visited places</div>';
        emptyEl.style.display = 'none';
        return;
    }
    
    listEl.innerHTML = '<div class="list-loading">Loading...</div>';
    emptyEl.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/visited`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.visited && data.visited.length > 0) {
                listEl.innerHTML = data.visited.map(place => createPlaceListItem(place, 'been')).join('');
            } else {
                listEl.innerHTML = '';
                emptyEl.style.display = 'block';
            }
        } else {
            listEl.innerHTML = '<div class="list-error">Failed to load visited places</div>';
        }
    } catch (error) {
        console.error('Error loading visited places:', error);
        listEl.innerHTML = '<div class="list-error">Failed to load visited places</div>';
    }
}

function createPlaceListItem(place, listType) {
    const dateStr = listType === 'saved' 
        ? (place.saved_at ? `Saved ${formatRelativeDate(place.saved_at)}` : '')
        : (place.visited_at ? `Marked ${formatRelativeDate(place.visited_at)}` : '');
    
    const removeAction = listType === 'saved' ? 'removeSavedPlace' : 'removeBeenPlace';
    
    return `
        <div class="place-list-item" data-place-id="${place.place_id}">
            <div class="place-list-image">
                ${place.photo_url 
                    ? `<img src="${place.photo_url}" alt="${place.title}" onerror="this.parentElement.innerHTML='📍'">`
                    : '<span class="place-list-icon">📍</span>'
                }
            </div>
            <div class="place-list-info">
                <div class="place-list-title">${place.title}</div>
                <div class="place-list-meta">
                    ${place.category ? `<span class="place-list-category">${place.category}</span>` : ''}
                    ${place.rating ? `<span class="place-list-rating">⭐ ${place.rating}</span>` : ''}
                </div>
                ${dateStr ? `<div class="place-list-date">${dateStr}</div>` : ''}
            </div>
            <button class="place-list-remove" onclick="${removeAction}('${place.place_id}')" title="Remove">×</button>
        </div>
    `;
}

function formatRelativeDate(isoDate) {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
}

async function removeSavedPlace(placeId) {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE}/saved/${placeId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Reload the list
            loadSavedPlaces();
        }
    } catch (error) {
        console.error('Error removing saved place:', error);
    }
}

async function removeBeenPlace(placeId) {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE}/visited/${placeId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Reload the list
            loadBeenPlaces();
        }
    } catch (error) {
        console.error('Error removing visited place:', error);
    }
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
    // Check if custom location is selected
    const locationSelect = document.getElementById('quick-location');
    const customLocationInput = document.getElementById('quick-location-custom');
    
    if (locationSelect && locationSelect.value === 'custom') {
        // Show custom location input if it doesn't exist
        if (!customLocationInput) {
            const inputHtml = `
                <div id="quick-location-custom-wrapper" class="form-group" style="margin-top: 0.5rem;">
                    <input type="text" id="quick-location-custom" placeholder="Enter ZIP code or address" style="width: 100%;">
                    <button class="btn btn-primary" onclick="applyCustomLocation()" style="margin-top: 0.5rem; width: 100%;">Apply Location</button>
                </div>
            `;
            locationSelect.parentElement.insertAdjacentHTML('beforeend', inputHtml);
        }
        return; // Don't auto-refresh until they click Apply
    } else {
        // Remove custom input if it exists and a different option is selected
        const wrapper = document.getElementById('quick-location-custom-wrapper');
        if (wrapper) wrapper.remove();
    }
    
    // Handle current location option
    if (locationSelect && locationSelect.value === 'current') {
        getCurrentLocationForQuickAdjust();
        return; // Will refresh after getting location
    }
    
    // Auto-refresh recommendations when adjustments change
    clearTimeout(window.quickAdjustmentTimeout);
    window.quickAdjustmentTimeout = setTimeout(() => {
        gatherQuickAdjustments();
        loadDashboardRecommendations();
    }, 500);
}

async function applyCustomLocation() {
    const input = document.getElementById('quick-location-custom');
    const locationSelect = document.getElementById('quick-location');
    
    if (!input || !input.value.trim()) {
        alert('Please enter a location');
        return;
    }
    
    const address = input.value.trim();
    
    try {
        // Geocode the address
        const response = await fetch(`${API_BASE}/geocode?address=${encodeURIComponent(address)}`);
        if (response.ok) {
            const data = await response.json();
            if (data.lat && data.lng) {
                // Update onboarding data with new location
                onboardingData.home_location = {
                    lat: data.lat,
                    lng: data.lng,
                    formatted_address: data.formatted_address || address,
                    input: address,
                    type: 'manual'
                };
                
                // Update the select to show the custom location
                locationSelect.innerHTML = `
                    <option value="">📍 Use saved location</option>
                    <option value="current">📍 Use current location</option>
                    <option value="custom">✏️ Enter new location...</option>
                    <option value="applied" selected>📍 ${data.formatted_address || address}</option>
                `;
                
                // Remove the input wrapper
                const wrapper = document.getElementById('quick-location-custom-wrapper');
                if (wrapper) wrapper.remove();
                
                // Refresh recommendations
                gatherQuickAdjustments();
                loadDashboardRecommendations();
            } else {
                alert('Could not find that location. Please try a different address.');
            }
        } else {
            alert('Error looking up location. Please try again.');
        }
    } catch (error) {
        console.error('Geocoding error:', error);
        alert('Error looking up location. Please try again.');
    }
}

function getCurrentLocationForQuickAdjust() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            // Reverse geocode to get address
            try {
                const response = await fetch(`${API_BASE}/reverse-geocode?lat=${lat}&lng=${lng}`);
                let formatted_address = 'Current Location';
                if (response.ok) {
                    const data = await response.json();
                    formatted_address = data.formatted_address || 'Current Location';
                }
                
                onboardingData.home_location = {
                    lat: lat,
                    lng: lng,
                    formatted_address: formatted_address,
                    type: 'geolocation'
                };
                
                // Update the select
                const locationSelect = document.getElementById('quick-location');
                if (locationSelect) {
                    locationSelect.innerHTML = `
                        <option value="">📍 Use saved location</option>
                        <option value="current">📍 Use current location</option>
                        <option value="custom">✏️ Enter new location...</option>
                        <option value="applied" selected>📍 ${formatted_address}</option>
                    `;
                }
                
                // Refresh recommendations
                gatherQuickAdjustments();
                loadDashboardRecommendations();
            } catch (error) {
                console.error('Reverse geocoding error:', error);
                onboardingData.home_location = {
                    lat: lat,
                    lng: lng,
                    formatted_address: 'Current Location',
                    type: 'geolocation'
                };
                gatherQuickAdjustments();
                loadDashboardRecommendations();
            }
        },
        (error) => {
            console.error('Geolocation error:', error);
            alert('Could not get your current location. Please enter an address instead.');
            // Reset to saved location
            const locationSelect = document.getElementById('quick-location');
            if (locationSelect) locationSelect.value = '';
        }
    );
}

// ==================== RECOMMENDATIONS ====================

// Align with backend: max radius (miles) derived from max travel time at ~25 mph avg
function getRadiusFromTravelTime() {
    const maxMin = getMaxTravelTimeMinutes();
    return Math.max(3, Math.round((maxMin / 60) * 25));
}

function getMaxTravelTimeMinutes() {
    const r = onboardingData.travel_time_ranges;
    if (!r?.length) return 30;
    if (r.includes('60+')) return 90;
    if (r.includes('30-60')) return 60;
    if (r.includes('15-30')) return 30;
    if (r.includes('0-15')) return 15;
    return 30;
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
    
    const prompt = `Generate 5 activity recommendations for someone with this profile:

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
            renderDigestItems(data.items, data.from_cache, data.sources);
            // Restore thumbs feedback button states
            loadFeedbackStatus();
        } else {
            if (itemsContainer) {
                itemsContainer.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: #666;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                        <p><strong>No recommendations available</strong></p>
                        <p style="margin: 0.5rem 0; font-size: 0.9rem;">Try adjusting your preferences or check back later</p>
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
                    <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
                    <p><strong>Error loading recommendations</strong></p>
                    <p style="font-size: 0.85rem; margin-top: 0.5rem; color: #666;">Make sure the backend server is running on port 5001</p>
                    <button class="btn btn-primary" onclick="loadDigest()" style="width: auto; margin-top: 1rem;">Retry</button>
                </div>
            `;
        }
    } finally {
        if (loading) loading.style.display = 'none';
    }
}

function renderDigestItems(items, fromCache = false, sources = []) {
    const container = document.getElementById('digest-items');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Add cache/source indicator if needed
    if (fromCache || sources.includes('cache')) {
        const cacheIndicator = document.createElement('div');
        cacheIndicator.innerHTML = `
            <div style="background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #6b7280;">
                <span>💾</span>
                <span>Showing cached results - refresh to get latest recommendations</span>
                <button onclick="loadDigest()" style="margin-left: auto; padding: 0.25rem 0.5rem; font-size: 0.75rem; background: #374151; color: white; border: none; border-radius: 4px; cursor: pointer;">Refresh</button>
            </div>
        `;
        container.appendChild(cacheIndicator);
    } else if (sources.includes('mock')) {
        const mockIndicator = document.createElement('div');
        mockIndicator.innerHTML = `
            <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #92400e;">
                <span>ℹ️</span>
                <span>Showing sample recommendations - try refreshing for live results</span>
                <button onclick="loadDigest()" style="margin-left: auto; padding: 0.25rem 0.5rem; font-size: 0.75rem; background: #f59e0b; color: white; border: none; border-radius: 4px; cursor: pointer;">Refresh</button>
            </div>
        `;
        container.appendChild(mockIndicator);
    }
    
    items.forEach(item => {
        const card = createRecommendationCard(item);
        container.appendChild(card);
    });
    
    observeLazyImages(container);
}

function createRecommendationCard(item) {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    card.style.cursor = 'pointer';
    card.setAttribute('role', 'article');
    card.setAttribute('aria-label', item.title);
    card.setAttribute('tabindex', '0');
    
    // Handle n/a and estimated distances
    const isDistanceNA = item.distance_is_na || item.distance_miles === null;
    const isEstimated = item.distance_is_estimated;
    
    let distanceDisplay, travelTimeDisplay, trafficClass, trafficLabel;
    
    if (isDistanceNA) {
        distanceDisplay = 'n/a';
        travelTimeDisplay = 'n/a';
        trafficClass = 'traffic-unknown';
        trafficLabel = '⚪ Unknown';
    } else if (isEstimated) {
        distanceDisplay = `~${item.distance_miles} mi`;
        travelTimeDisplay = `~${item.travel_time_min} min`;
        trafficClass = item.travel_time_min < 15 ? 'traffic-light' : 
                       item.travel_time_min < 30 ? 'traffic-moderate' : 'traffic-heavy';
        trafficLabel = 'Estimated';
    } else {
        distanceDisplay = `${item.distance_miles} mi`;
        travelTimeDisplay = `${item.travel_time_min} min`;
        trafficClass = item.travel_time_min < 15 ? 'traffic-light' : 
                       item.travel_time_min < 30 ? 'traffic-moderate' : 'traffic-heavy';
        trafficLabel = item.travel_time_min < 15 ? '🟢 Light' : 
                       item.travel_time_min < 30 ? '🟡 Moderate' : '🔴 Heavy';
    }
    
    // Format event date if available
    let eventDateDisplay = '';
    if (item.event_date) {
        try {
            const date = new Date(item.event_date);
            if (!isNaN(date.getTime())) {
                eventDateDisplay = date.toLocaleDateString('en-US', { 
                    weekday: 'short', 
                    month: 'short', 
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                });
            } else {
                eventDateDisplay = item.event_date;
            }
        } catch {
            eventDateDisplay = item.event_date;
        }
    }
    
    // Build location/distance badge
    let locationBadge;
    if (isDistanceNA) {
        // Show address snippet instead of n/a
        const addr = (item.address || '').trim();
        locationBadge = addr ? `<span class="info-badge">📍 ${addr.length > 30 ? addr.substring(0, 30) + '…' : addr}</span>` : '';
    } else {
        locationBadge = `<span class="info-badge">📍 ${distanceDisplay}</span>
            <span class="info-badge ${trafficClass}">⏱️ ${travelTimeDisplay}</span>`;
    }
    
    // Source badge
    const feedSource = item.feed_source || item.source || '';
    const sourceBadge = feedSource ? `<span class="info-badge" style="color:#9ca3af;font-size:0.8rem;">${feedSource}</span>` : '';
    
    // Clean explanation - truncate for card view
    let explanation = (item.explanation || item.description || '').replace(/<[^>]*>/g, ' ').replace(/&[^;]+;/g, ' ').replace(/^[^a-zA-Z0-9]+/, '').replace(/\s+/g, ' ').trim();
    if (explanation.length > 150) explanation = explanation.substring(0, 147) + '…';
    
    // Price badge
    const priceBadge = item.price_flag && item.price_flag.toLowerCase() === 'free' 
        ? '<span class="info-badge" style="color:#059669;font-weight:600;">Free</span>' 
        : (item.price_flag && item.price_flag !== '$' ? `<span class="info-badge">${item.price_flag}</span>` : '');
    
    // Card image
    const cardImageUrl = item.photo_url || getPlaceImageUrl(item.category, item.title);
    const categoryEmojis = {
        'parks': '🌲', 'museums': '🏛️', 'food': '🍽️', 'attractions': '🎢',
        'entertainment': '🎭', 'shopping': '🛍️', 'events': '🎪', 'nature': '🌿',
        'family': '👨‍👩‍👧‍👦', 'community': '🏘️'
    };
    const placeholderEmoji = categoryEmojis[item.category] || '📍';

    card.innerHTML = `
        <div class="card-image-container">
            <div class="card-image-placeholder">${placeholderEmoji}</div>
            <img class="card-image" data-src="${cardImageUrl}" alt="" loading="lazy"
                 onload="this.classList.add('loaded')"
                 onerror="this.remove()">
        </div>
        <div class="card-header">
            <div>
                <div class="card-title">${item.title}</div>
            </div>
        </div>
        ${eventDateDisplay ? `<div class="card-event-date">📅 ${eventDateDisplay}</div>` : ''}
        <div class="card-info">
            ${locationBadge}
            ${item.kid_friendly ? '<span class="info-badge">👶 Kid-friendly</span>' : ''}
            ${priceBadge}
            ${sourceBadge}
        </div>
        ${explanation ? `<div class="card-explanation">${explanation}</div>` : ''}
        <div class="card-actions">
            <button class="btn btn-primary" onclick="event.stopPropagation(); showDetail('${item.rec_id}')" style="width: auto;">View Details</button>
            ${item.event_link ? `<a href="${item.event_link}" target="_blank" rel="noopener" class="btn btn-secondary" onclick="event.stopPropagation();" title="Event Link">🔗</a>` : ''}
            <button class="btn btn-secondary feedback-btn" data-place-id="${item.place_id}" data-feedback="thumbs_up" onclick="event.stopPropagation(); handleThumbsFeedback('${item.rec_id}', '${item.place_id}', '${item.category || ''}', 'thumbs_up', event)" title="Like this">👍</button>
            <button class="btn btn-secondary feedback-btn" data-place-id="${item.place_id}" data-feedback="thumbs_down" onclick="event.stopPropagation(); handleThumbsFeedback('${item.rec_id}', '${item.place_id}', '${item.category || ''}', 'thumbs_down', event)" title="Not for me">👎</button>
            <button class="btn btn-secondary" onclick="event.stopPropagation(); handleFeedback('${item.rec_id}', 'favorite', event)" title="Favorite">⭐</button>
            <button class="btn btn-secondary" onclick="event.stopPropagation(); handleFeedback('${item.rec_id}', 'already_been', event)" title="Already been here">✅</button>
            <button class="btn btn-secondary" onclick="event.stopPropagation(); shareRecommendation('${item.rec_id}')" title="Share">📤</button>
        </div>
    `;
    
    // Make entire card clickable and keyboard-accessible
    card.addEventListener('click', () => {
        showDetail(item.rec_id);
    });
    card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            showDetail(item.rec_id);
        }
    });
    
    return card;
}

async function showDetail(recId) {
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    if (!item) return;

    // Track click for personalization
    try {
        fetch(`${API_BASE}/track/click`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ place_id: item.place_id, rec_id: recId, category: item.category })
        });
    } catch (e) { /* silent */ }
    
    const modal = document.getElementById('detail-modal');
    const content = document.getElementById('detail-content');
    
    // Build Google Maps search URL - use specific address if available, otherwise title + user's city/state
    let searchQuery;
    const address = (item.address || '').trim();
    const hasSpecificAddress = /^\d+\s/.test(address); // Starts with a street number
    const userLocation = onboardingData.home_location || {};
    const locationContext = userLocation.formatted_address || '';
    const cityStateMatch = locationContext.match(/([A-Za-z\s]+,\s*[A-Z]{2})/);
    const cityState = cityStateMatch ? cityStateMatch[1] : '';

    if (hasSpecificAddress) {
        searchQuery = address;
    } else {
        if (address) {
            searchQuery = cityState ? `${address}, ${cityState}` : address;
        } else {
            searchQuery = cityState ? `${item.title}, ${cityState}` : item.title;
        }
    }
    const googleMapsSearchUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(searchQuery)}`;

    // Build image search query from title + keywords from event detail + location (for Google/Pexels/Unsplash)
    const imageSearchQuery = buildImageSearchQuery(item, address, cityState);
    
    // Get image URL - use photo from API, else we'll fetch from image search (Google/Pexels), else category fallback
    const categoryFallbackUrl = getPlaceImageUrl(item.category, item.title);
    const genericFallbackUrl = 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&h=400&fit=crop';
    const imageUrl = item.photo_url || categoryFallbackUrl;
    
    // Build rating display with link to Google reviews
    const ratingDisplay = item.rating ? `
        <a href="${googleMapsSearchUrl}" target="_blank" rel="noopener" class="detail-rating-link">
            <div class="detail-rating">
                <span class="rating-stars">${'★'.repeat(Math.round(item.rating))}${'☆'.repeat(5 - Math.round(item.rating))}</span>
                <span class="rating-value">${item.rating}</span>
                ${item.total_ratings ? `<span class="rating-count">(${item.total_ratings.toLocaleString()} reviews)</span>` : ''}
                <span class="google-link-icon">↗</span>
            </div>
        </a>
    ` : '';
    
    // Build description - deduplicate time and location info
    let description = item.description || item.explanation || generatePlaceDescription(item);
    
    // Strip HTML tags from description
    if (description) {
        description = description.replace(/<[^>]*>/g, ' ').replace(/&[^;]+;/g, ' ');
    }
    let displayAddress = item.address || '';
    let extractedStreetAddress = '';
    
    // Clean up description to remove duplicated info
    if (description) {
        // Remove time/date patterns if event_date is already shown
        if (item.event_date) {
            description = description
                // Remove full pattern like "Sun February 8, 2026 - 2:00 pm - 4:00 pm" (anywhere in text)
                .replace(/(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.?,?\s*(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)[a-z]*\.?\s+\d{1,2}(st|nd|rd|th)?,?\s*(\d{4})?\s*[-–—]?\s*\d{1,2}(:\d{2})?\s*(am|pm)?\s*[-–—]?\s*\d{1,2}(:\d{2})?\s*(am|pm)?\s*[-–—:]?\s*/gi, '')
                // Remove day names at start
                .replace(/^(On\s+)?(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*/i, '')
                // Remove date patterns like "Jan 25, 2026 at 10:00 AM" or "January 25, 2026" with optional time range (anywhere)
                .replace(/(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)[a-z]*\.?\s+\d{1,2}(st|nd|rd|th)?,?\s*(\d{4})?\s*[-–—]?\s*(at\s+)?\d{1,2}(:\d{2})?\s*(am|pm)?\s*([-–—to]+\s*\d{1,2}(:\d{2})?\s*(am|pm)?)?\s*[-–—:]?\s*/gi, '')
                // Remove numeric date patterns like "1/25/2026"
                .replace(/\d{1,2}\/\d{1,2}(\/\d{2,4})?\s*(at\s+)?\d{1,2}(:\d{2})?\s*(am|pm)?\s*[-–—:]?\s*/gi, '')
                // Remove standalone time like "at 10:00 AM" or "8:00 AM"
                .replace(/^(at\s+)?\d{1,2}(:\d{2})?\s*(am|pm)\s*[-–—:]?\s*/gi, '')
                // Remove time ranges like "10:00 AM - 2:00 PM" or "8:00am-10:00am"
                .replace(/\d{1,2}(:\d{2})?\s*(am|pm)?\s*[-–—to]+\s*\d{1,2}(:\d{2})?\s*(am|pm)?\s*[-–—:]?\s*/gi, '');
        }
        
        // Extract street address from description (like "40000 Paseo Padre Pkwy")
        // Pattern: number + street name (+ optional suffix like St, Ave, Pkwy, Blvd, Dr, Rd, Way, Ln, Ct)
        const streetAddressMatch = description.match(/(\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Parkway|Pkwy|Boulevard|Blvd|Drive|Dr|Road|Rd|Way|Lane|Ln|Court|Ct|Place|Pl|Circle|Cir)\.?)(?:[,\s]+([A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?))?/i);
        if (streetAddressMatch) {
            extractedStreetAddress = streetAddressMatch[0].trim();
            // Remove the street address from description
            description = description.replace(streetAddressMatch[0], '').trim();
        }
        
        // Remove location/address if already shown in address UI
        if (item.address) {
            const addressParts = item.address.split(',').map(p => p.trim()).filter(p => p.length > 2);
            addressParts.forEach(part => {
                // Escape special regex characters
                const escaped = part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                // Remove the address part from description (case insensitive)
                description = description.replace(new RegExp(`(at\\s+|@\\s*|Location:\\s*|Address:\\s*)?${escaped}[,.]?\\s*`, 'gi'), '');
            });
            // Also try to remove the full address
            const fullAddressEscaped = item.address.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            description = description.replace(new RegExp(`(at\\s+|@\\s*|Location:\\s*|Address:\\s*)?${fullAddressEscaped}[,.]?\\s*`, 'gi'), '');
        }
        
        // Clean up any leftover artifacts
        description = description
            .replace(/^[^a-zA-Z0-9]+/, '')           // Remove any non-alphanumeric at start
            .replace(/[^a-zA-Z0-9.!?]+$/, '')       // Remove non-alphanumeric at end (keep sentence endings)
            .replace(/\s+/g, ' ')                    // Normalize whitespace
            .trim();
        
        // If description is effectively empty or too short after cleanup, set to empty string
        if (!description || description.length < 5) {
            description = '';
        }
    }
    
    // Build merged address display
    // If we have a venue name (no street number) and extracted a street address, combine them
    let hasTwoLineAddress = false;
    if (displayAddress && extractedStreetAddress) {
        // Check if displayAddress looks like a venue name (no street number at start)
        const hasStreetNumber = /^\d+\s/.test(displayAddress);
        if (!hasStreetNumber) {
            // displayAddress is likely a venue name, append street address below
            displayAddress = `<span class="detail-address-venue">${displayAddress}</span><span class="detail-address-street">${extractedStreetAddress}</span>`;
            hasTwoLineAddress = true;
        }
    } else if (extractedStreetAddress && !displayAddress) {
        displayAddress = extractedStreetAddress;
    }
    
    content.innerHTML = `
        <a href="${googleMapsSearchUrl}" target="_blank" rel="noopener" class="detail-image-link">
            <div class="detail-image-container">
                <img id="detail-modal-image" src="${imageUrl}" alt="${item.title}" class="detail-image" 
                    data-category-fallback="${categoryFallbackUrl}" 
                    data-generic-fallback="${genericFallbackUrl}"
                    onerror="handleDetailImageError(this)">
                <div class="image-overlay">
                    <span class="view-on-google">View on Google Maps ↗</span>
                </div>
            </div>
        </a>
        <div class="detail-header">
            <h2 class="detail-title">${item.title}</h2>
            ${ratingDisplay}
        </div>
        ${item.event_date ? `
        <div class="detail-event-date">${(() => {
            try {
                const date = new Date(item.event_date);
                if (!isNaN(date.getTime())) {
                    return date.toLocaleDateString('en-US', { 
                        weekday: 'short', 
                        month: 'short', 
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit'
                    });
                }
                return item.event_date;
            } catch { return item.event_date; }
        })()}</div>
        ` : ''}
        ${description ? `
        <div class="detail-description">
            <p>${description}</p>
        </div>
        ` : ''}
        ${item.event_link ? `
        <a href="${item.event_link}" target="_blank" rel="noopener" class="detail-event-link">View event →</a>
        ` : ''}
        ${displayAddress ? `
        <a href="${googleMapsSearchUrl}" target="_blank" rel="noopener" class="detail-address-link">
            <div class="detail-address">
                <span class="detail-address-content">${displayAddress}</span>
                <span class="google-link-icon">↗</span>
            </div>
        </a>
        ` : ''}
        <div class="detail-info">
            <div class="detail-info-item">
                <span class="detail-info-label">Distance</span>
                <span class="detail-info-value">${item.distance_is_na || item.distance_miles === null ? 'n/a' : (item.distance_is_estimated ? `~${item.distance_miles} mi` : `${item.distance_miles} mi`)}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">Travel</span>
                <span class="detail-info-value">${item.distance_is_na || item.travel_time_min === null ? 'n/a' : (item.distance_is_estimated ? `~${item.travel_time_min} min` : `${item.travel_time_min} min`)}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">Price</span>
                <span class="detail-info-value">${(() => {
                    const price = (item.price_flag || '').toLowerCase().trim();
                    if (price === 'free') return 'Free';
                    if (price === '$$' || price === '$$$' || price === '$$$$') return item.price_flag;
                    return 'n/a';
                })()}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">Setting</span>
                <span class="detail-info-value">${item.indoor_outdoor || 'n/a'}</span>
            </div>
            ${item.kid_friendly ? `
            <div class="detail-info-item">
                <span class="detail-info-label">Family</span>
                <span class="detail-info-value">Kid-friendly</span>
            </div>
            ` : ''}
        </div>
        ${item.best_time ? `<div class="detail-best-time">Best time to visit: ${item.best_time}</div>` : ''}
        <div class="time-slots">
            <h3>Add to Calendar</h3>
            <p class="time-slots-hint">Select a time slot</p>
            <div class="slot-buttons">
                <button class="slot-btn" onclick="selectSlot('SAT_AM')">Saturday Morning</button>
                <button class="slot-btn" onclick="selectSlot('SAT_PM')">Saturday Afternoon</button>
                <button class="slot-btn" onclick="selectSlot('SUN_AM')">Sunday Morning</button>
                <button class="slot-btn" onclick="selectSlot('SUN_PM')">Sunday Afternoon</button>
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <button class="btn btn-success" id="add-to-calendar-btn" onclick="addToCalendar('${recId}')" style="flex: 1;">Add to Calendar</button>
            <button class="btn btn-secondary" onclick="shareRecommendation('${recId}')" style="flex: 0 0 auto;">📤 Share</button>
        </div>
    `;
    
    modal.classList.add('active');
    window.selectedSlot = null;

    // If no photo from source, fetch location-specific image from Google/Pexels and update when ready
    if (!item.photo_url && imageSearchQuery) {
        fetch(`${API_BASE}/image-search?q=${encodeURIComponent(imageSearchQuery)}`)
            .then(r => r.json())
            .then(data => {
                const img = document.getElementById('detail-modal-image');
                if (img && data.url) {
                    img.src = data.url;
                    img.onerror = () => handleDetailImageError(img);
                }
            })
            .catch(() => {});
    }
}

function handleDetailImageError(imgEl) {
    if (!imgEl) return;
    const categoryFallback = imgEl.dataset.categoryFallback;
    const genericFallback = imgEl.dataset.genericFallback;
    if (imgEl.src !== categoryFallback && categoryFallback) {
        imgEl.src = categoryFallback;
        imgEl.onerror = () => { if (genericFallback) imgEl.src = genericFallback; };
    } else if (genericFallback) {
        imgEl.src = genericFallback;
        imgEl.onerror = null;
    }
}

function buildImageSearchQuery(item, address, cityState) {
    // Extract keywords from title and event detail for better image search (Google/Pexels/Unsplash)
    const title = (item.title || '').trim();
    const rawDesc = (item.description || item.explanation || '').trim();
    const desc = rawDesc.replace(/<[^>]*>/g, ' ').replace(/&[^;]+;/g, ' ');
    const category = (item.category || '').trim();
    const bestTime = (item.best_time || '').trim();

    const stopWords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'we', 'you', 'they', 'our', 'your', 'their', 'join', 'us', 'get', 'see', 'come', 'visit', 'enjoy', 'explore', 'discover', 'experience', 'local', 'free', 'event', 'events']);
    const extractKeywords = (text, maxWords = 8) => {
        if (!text || text.length < 3) return [];
        const words = text.toLowerCase()
            .replace(/[^\w\s'-]/g, ' ')
            .split(/\s+/)
            .filter(w => w.length >= 3 && !stopWords.has(w) && !/^\d+$/.test(w));
        const seen = new Set();
        return words.filter(w => {
            if (seen.has(w)) return false;
            seen.add(w);
            return true;
        }).slice(0, maxWords);
    };

    const titleKeywords = extractKeywords(title, 5);
    const descKeywords = extractKeywords(desc, 6);
    const categoryKeywords = category ? extractKeywords(category, 2) : [];
    const bestTimeKeywords = bestTime ? extractKeywords(bestTime, 2) : []; // e.g. "sunset", "morning"
    const combined = [...new Set([...titleKeywords, ...descKeywords, ...categoryKeywords, ...bestTimeKeywords])].join(' ');
    const location = [address, cityState].filter(Boolean).join(' ').trim();

    return [title, combined, location].filter(Boolean).join(' ').trim() || title;
}

function getPlaceImageUrl(category, title) {
    // Curated Unsplash images by category
    const categoryImages = {
        'parks': [
            'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=800&h=400&fit=crop'
        ],
        'museums': [
            'https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1566127444979-b3d2b654e3d7?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=800&h=400&fit=crop'
        ],
        'food': [
            'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=800&h=400&fit=crop'
        ],
        'attractions': [
            'https://images.unsplash.com/photo-1499002238440-d264f8f8a8d5?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=400&fit=crop'
        ],
        'entertainment': [
            'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=800&h=400&fit=crop'
        ],
        'shopping': [
            'https://images.unsplash.com/photo-1481437156560-3205f6a55735?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=800&h=400&fit=crop',
            'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&h=400&fit=crop'
        ]
    };
    
    const images = categoryImages[category] || categoryImages['attractions'];
    // Use title hash to consistently pick same image for same place
    const hash = title.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    return images[hash % images.length];
}

function generatePlaceDescription(item) {
    const descriptions = {
        'parks': `Escape to nature at ${item.title}. This beautiful outdoor space offers a perfect retreat from the busy city life. Whether you're looking to take a leisurely stroll, have a picnic, or simply relax surrounded by greenery, this is the ideal spot for a relaxing day.`,
        'museums': `Discover art, history, and culture at ${item.title}. This museum offers fascinating exhibits that will engage visitors of all ages. Plan to spend a few hours exploring the collections and learning something new.`,
        'food': `Treat yourself to a delicious dining experience at ${item.title}. Known for its excellent cuisine and welcoming atmosphere, this spot is perfect for a memorable meal with family or friends.`,
        'attractions': `Experience the excitement of ${item.title}. This popular destination offers unique experiences and entertainment that make it a must-visit spot for your next adventure.`,
        'entertainment': `Get ready for fun at ${item.title}! This entertainment venue promises an exciting time filled with memorable experiences. Perfect for creating lasting memories with your loved ones.`,
        'shopping': `Explore the shops and boutiques at ${item.title}. From unique finds to popular brands, this destination offers a great shopping experience for everyone.`
    };
    
    return descriptions[item.category] || `Visit ${item.title} for a wonderful experience. ${item.explanation || ''}`;
}

function selectSlot(slot) {
    const btn = event.target;
    
    // Toggle selection - click again to deselect
    if (btn.classList.contains('selected')) {
        btn.classList.remove('selected');
        window.selectedSlot = null;
    } else {
        document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        window.selectedSlot = slot;
    }
}

async function addToCalendar(recId) {
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    if (!item) return;
    
    // Helper to format date as YYYY-MM-DD in local timezone
    const formatLocalDate = (d) => {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    // Calculate next Saturday and Sunday
    const now = new Date();
    const dayOfWeek = now.getDay(); // 0 = Sunday, 6 = Saturday
    
    // Days until next Saturday (if today is Sunday, next Sat is in 6 days)
    // If today is Saturday (6), we use today; otherwise calculate days to Saturday
    let daysUntilSaturday;
    if (dayOfWeek === 6) {
        daysUntilSaturday = 0; // Today is Saturday
    } else if (dayOfWeek === 0) {
        daysUntilSaturday = 6; // Today is Sunday, next Saturday is in 6 days
    } else {
        daysUntilSaturday = 6 - dayOfWeek; // Weekday: days until Saturday
    }
    
    const saturday = new Date(now);
    saturday.setDate(now.getDate() + daysUntilSaturday);
    
    const sunday = new Date(saturday);
    sunday.setDate(saturday.getDate() + 1);
    
    let eventData = {
        title: item.title,
        location: item.address || '',
        description: item.explanation || '',
        isAllDay: true
    };
    
    // Time slots: Morning = 9am-12pm, Afternoon = 2pm-6pm
    if (window.selectedSlot) {
        eventData.isAllDay = false;
        
        if (window.selectedSlot === 'SAT_AM') {
            eventData.date = formatLocalDate(saturday);
            eventData.startTime = '09:00';
            eventData.endTime = '12:00';
        } else if (window.selectedSlot === 'SAT_PM') {
            eventData.date = formatLocalDate(saturday);
            eventData.startTime = '14:00';
            eventData.endTime = '18:00';
        } else if (window.selectedSlot === 'SUN_AM') {
            eventData.date = formatLocalDate(sunday);
            eventData.startTime = '09:00';
            eventData.endTime = '12:00';
        } else if (window.selectedSlot === 'SUN_PM') {
            eventData.date = formatLocalDate(sunday);
            eventData.startTime = '14:00';
            eventData.endTime = '18:00';
        }
    } else {
        // No slot selected - default to all-day Saturday
        eventData.date = formatLocalDate(saturday);
    }
    
    // Open Google Calendar with the event data
    addToCalendarManual(recId, eventData);
}

function showCalendarAuthPrompt(recId, item) {
    const modal = document.getElementById('detail-modal');
    const content = document.getElementById('detail-content');
    
    content.innerHTML = `
        <div class="calendar-auth-prompt">
            <h2>📅 Connect Google Calendar</h2>
            <p>To add "${item.title}" to your calendar, please sign in with Google.</p>
            
            <div class="calendar-auth-benefits">
                <div class="benefit-item">✓ Add events directly to your calendar</div>
                <div class="benefit-item">✓ Set reminders automatically</div>
                <div class="benefit-item">✓ Sync across all devices</div>
            </div>
            
            <button class="btn btn-oauth btn-oauth-full" onclick="connectGoogleCalendar('${recId}')">
                <span class="oauth-icon">G</span> Connect with Google
            </button>
            
            <div class="auth-divider"><span>or</span></div>
            
            <button class="btn btn-secondary" onclick="addToCalendarManual('${recId}')" style="width: 100%;">
                Open Google Calendar (manual)
            </button>
            
            <p class="auth-switch" style="margin-top: 1rem;">
                <a href="#" onclick="closeDetailModal(); return false;">Cancel</a>
            </p>
        </div>
    `;
}

async function connectGoogleCalendar(recId) {
    try {
        // Get Google OAuth URL with calendar scope
        const response = await fetch(`${API_BASE}/auth/google/calendar/url`, { credentials: 'include' });
        const data = await response.json();
        
        if (data.url) {
            // Store recId to continue after auth
            sessionStorage.setItem('pending_calendar_recId', recId);
            
            // Open OAuth popup
            const width = 500;
            const height = 600;
            const left = (window.innerWidth - width) / 2 + window.screenX;
            const top = (window.innerHeight - height) / 2 + window.screenY;
            
            const popup = window.open(
                data.url,
                'Google Calendar Auth',
                `width=${width},height=${height},left=${left},top=${top},popup=yes`
            );
            
            // Listen for OAuth completion
            window.addEventListener('message', function handleCalendarAuth(event) {
                if (event.data.type === 'calendar_auth_success') {
                    localStorage.setItem('google_calendar_token', event.data.token);
                    localStorage.setItem('auth_provider', 'google');
                    
                    // Continue with calendar event
                    const pendingRecId = sessionStorage.getItem('pending_calendar_recId');
                    if (pendingRecId) {
                        sessionStorage.removeItem('pending_calendar_recId');
                        const item = window.currentDigest?.items?.find(i => i.rec_id === pendingRecId);
                        if (item) {
                            showCalendarEventModal(pendingRecId, item);
                        }
                    }
                    
                    window.removeEventListener('message', handleCalendarAuth);
                } else if (event.data.type === 'oauth_error') {
                    alert('Failed to connect Google Calendar: ' + event.data.error);
                    window.removeEventListener('message', handleCalendarAuth);
                }
            });
        } else {
            // Fallback to manual add
            addToCalendarManual(recId);
        }
    } catch (error) {
        console.error('Calendar auth error:', error);
        addToCalendarManual(recId);
    }
}

function showCalendarEventModal(recId, item) {
    const modal = document.getElementById('detail-modal');
    const content = document.getElementById('detail-content');
    
    // Get next Saturday and Sunday
    const now = new Date();
    const saturday = new Date(now);
    saturday.setDate(now.getDate() + (6 - now.getDay()));
    const sunday = new Date(saturday);
    sunday.setDate(saturday.getDate() + 1);
    
    const formatDateForInput = (d) => d.toISOString().split('T')[0];
    
    content.innerHTML = `
        <div class="calendar-event-form">
            <h2>📅 Add to Calendar</h2>
            <h3>${item.title}</h3>
            <p class="event-location">📍 ${item.address || 'Location not specified'}</p>
            
            <div class="form-group">
                <label>Event Type</label>
                <div class="event-type-toggle">
                    <button class="event-type-btn active" onclick="selectEventType('day', this)" data-type="day">All Day Event</button>
                    <button class="event-type-btn" onclick="selectEventType('timed', this)" data-type="timed">Specific Time</button>
                </div>
            </div>
            
            <div class="form-group">
                <label>Date</label>
                <input type="date" id="event-date" value="${formatDateForInput(saturday)}" min="${formatDateForInput(now)}">
            </div>
            
            <div id="time-fields" style="display: none;">
                <div class="form-row">
                    <div class="form-group">
                        <label>Start Time</label>
                        <input type="time" id="event-start-time" value="10:00">
                    </div>
                    <div class="form-group">
                        <label>End Time</label>
                        <input type="time" id="event-end-time" value="12:00">
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>Add a note (optional)</label>
                <textarea id="event-notes" placeholder="Any notes for this event...">${item.explanation || ''}</textarea>
            </div>
            
            <div class="form-group">
                <label><input type="checkbox" id="event-reminder" checked> Remind me 1 hour before</label>
            </div>
            
            <div class="calendar-actions">
                <button class="btn btn-primary" onclick="saveToGoogleCalendar('${recId}')">Save to Calendar</button>
                <button class="btn btn-secondary" onclick="closeDetailModal()">Cancel</button>
            </div>
        </div>
    `;
    
    window.currentEventType = 'day';
}

function selectEventType(type, btn) {
    document.querySelectorAll('.event-type-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    window.currentEventType = type;
    
    const timeFields = document.getElementById('time-fields');
    timeFields.style.display = type === 'timed' ? 'block' : 'none';
}

async function saveToGoogleCalendar(recId) {
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    if (!item) return;
    
    const eventDate = document.getElementById('event-date').value;
    const eventNotes = document.getElementById('event-notes').value;
    const addReminder = document.getElementById('event-reminder').checked;
    
    let eventData = {
        title: item.title,
        location: item.address || '',
        description: eventNotes,
        date: eventDate,
        isAllDay: window.currentEventType === 'day',
        reminder: addReminder ? 60 : null // 60 minutes before
    };
    
    if (window.currentEventType === 'timed') {
        eventData.startTime = document.getElementById('event-start-time').value;
        eventData.endTime = document.getElementById('event-end-time').value;
    }
    
    const calendarToken = localStorage.getItem('google_calendar_token');
    
    if (calendarToken) {
        // Try to create event via API
        try {
            const response = await fetch(`${API_BASE}/calendar/event`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                },
                body: JSON.stringify({
                    calendar_token: calendarToken,
                    event: eventData
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showCalendarSuccess(result.event_link);
                return;
            }
        } catch (error) {
            console.error('Calendar API error:', error);
        }
    }
    
    // Fallback to manual URL method
    addToCalendarManual(recId, eventData);
}

function addToCalendarManual(recId, eventData = null) {
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    if (!item) return;
    
    // Helper to format date as YYYYMMDD
    const formatDateOnly = (dateStr) => dateStr.replace(/-/g, '');
    
    // Helper to format datetime as YYYYMMDDTHHMMSS (local time, no Z suffix)
    const formatDateTime = (dateStr, timeStr) => {
        return dateStr.replace(/-/g, '') + 'T' + timeStr.replace(/:/g, '') + '00';
    };
    
    // Helper to format local date as YYYY-MM-DD
    const formatLocalDate = (d) => {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    let url;
    
    if (eventData && eventData.isAllDay) {
        // All-day event - use date only format
        const date = formatDateOnly(eventData.date);
        url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(item.title)}&dates=${date}/${date}&details=${encodeURIComponent(eventData.description || item.explanation)}&location=${encodeURIComponent(item.address || '')}`;
    } else if (eventData && eventData.startTime) {
        // Timed event - use local datetime format (no Z suffix)
        const startDT = formatDateTime(eventData.date, eventData.startTime);
        const endDT = formatDateTime(eventData.date, eventData.endTime);
        url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(item.title)}&dates=${startDT}/${endDT}&details=${encodeURIComponent(eventData.description || item.explanation)}&location=${encodeURIComponent(item.address || '')}`;
    } else {
        // Default: next Saturday all-day
        const now = new Date();
        const dayOfWeek = now.getDay();
        let daysUntilSaturday = (dayOfWeek === 6) ? 0 : (dayOfWeek === 0) ? 6 : (6 - dayOfWeek);
        const saturday = new Date(now);
        saturday.setDate(now.getDate() + daysUntilSaturday);
        const date = formatDateOnly(formatLocalDate(saturday));
        url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(item.title)}&dates=${date}/${date}&details=${encodeURIComponent(item.explanation)}&location=${encodeURIComponent(item.address || '')}`;
    }
    
    window.open(url, '_blank');
    closeDetailModal();
}

function showCalendarSuccess(eventLink) {
    const content = document.getElementById('detail-content');
    content.innerHTML = `
        <div class="calendar-success">
            <div class="success-icon">✅</div>
            <h2>Added to Calendar!</h2>
            <p>Your event has been saved to Google Calendar.</p>
            ${eventLink ? `<a href="${eventLink}" target="_blank" class="btn btn-secondary">View in Calendar</a>` : ''}
            <button class="btn btn-primary" onclick="closeDetailModal()" style="margin-top: 1rem;">Done</button>
        </div>
    `;
}

function closeDetailModal() {
    document.getElementById('detail-modal').classList.remove('active');
}

async function loadInterestProfile() {
    const container = document.getElementById('interest-profile-content');
    if (!container) return;
    try {
        const resp = await fetch(`${API_BASE}/profile/interests`);
        if (!resp.ok) throw new Error('Failed to load');
        const data = await resp.json();
        const affinity = data.affinity_scores || {};
        const signals = data.signals || {};

        const categories = Object.entries(affinity).sort((a, b) => b[1] - a[1]);

        let html = '';
        if (categories.length === 0) {
            html = '<p style="color: #999;">No preferences learned yet. Like, save, or visit places to personalize your recommendations!</p>';
        } else {
            html += '<div style="margin-bottom: 1rem;">';
            for (const [cat, score] of categories) {
                const pct = Math.round((score + 1) / 2 * 100);
                const color = score > 0 ? '#22c55e' : score < 0 ? '#ef4444' : '#9ca3af';
                const emoji = { parks: '🌳', museums: '🏛️', food: '🍽️', attractions: '🎡', events: '🎪', shopping: '🛍️', entertainment: '🎭', nature: '🌿', arts: '🎨' }[cat] || '📍';
                html += `<div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="width: 120px; font-size: 0.9rem;">${emoji} ${cat}</span>
                    <div style="flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${pct}%; height: 100%; background: ${color}; border-radius: 4px;"></div>
                    </div>
                    <span style="width: 50px; text-align: right; font-size: 0.8rem; color: ${color};">${score > 0 ? '+' : ''}${score}</span>
                </div>`;
            }
            html += '</div>';
        }

        html += `<div style="font-size: 0.8rem; color: #999; margin-top: 0.5rem;">
            Signals: ${signals.thumbs_up || 0} 👍 · ${signals.thumbs_down || 0} 👎 · ${signals.saved || 0} ⭐ · ${signals.visited || 0} ✅ · ${signals.clicks || 0} clicks
        </div>`;

        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<p style="color: #ef4444;">Failed to load interest profile.</p>';
    }
}

async function resetInterestProfile(clearAll) {
    const msg = clearAll
        ? 'This will clear all your feedback and click data. Continue?'
        : 'This will reset personalized ranking (keeps your feedback data). Continue?';
    if (!confirm(msg)) return;
    try {
        await fetch(`${API_BASE}/profile/interests/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clear_feedback: !!clearAll })
        });
        loadInterestProfile();
    } catch (e) {
        alert('Failed to reset profile.');
    }
}

async function loadFeedbackStatus() {
    try {
        const resp = await fetch(`${API_BASE}/feedback/status`);
        if (!resp.ok) return;
        const data = await resp.json();
        const feedbackMap = data.feedback || {};
        document.querySelectorAll('.feedback-btn').forEach(btn => {
            const placeId = btn.dataset.placeId;
            const feedbackType = btn.dataset.feedback;
            if (feedbackMap[placeId] === feedbackType) {
                btn.classList.add('feedback-active');
                btn.style.background = feedbackType === 'thumbs_up' ? '#d4edda' : '#f8d7da';
            }
        });
    } catch (e) { /* silent */ }
}

async function handleThumbsFeedback(recId, placeId, category, action, event) {
    try {
        const btn = event?.target;
        const isActive = btn?.classList.contains('feedback-active');

        if (isActive) {
            // Remove feedback
            await fetch(`${API_BASE}/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rec_id: recId, action: 'remove_feedback', place_id: placeId })
            });
            btn.classList.remove('feedback-active');
            btn.style.background = '';
        } else {
            await fetch(`${API_BASE}/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rec_id: recId, action, place_id: placeId, category })
            });
            // Clear sibling feedback button state
            if (btn) {
                const parent = btn.parentElement;
                parent.querySelectorAll('.feedback-btn').forEach(b => {
                    b.classList.remove('feedback-active');
                    b.style.background = '';
                });
                btn.classList.add('feedback-active');
                btn.style.background = action === 'thumbs_up' ? '#d4edda' : '#f8d7da';
            }
        }
    } catch (error) {
        console.error('Thumbs feedback error:', error);
    }
}

async function handleFeedback(recId, action, event) {
    // Find the place_id from current digest
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    const placeId = item?.place_id;
    
    try {
        await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rec_id: recId, action, place_id: placeId })
        });
        
        if (event?.target) {
            const btn = event.target;
            
            // Toggle logic - check if already marked
            if (action === 'favorite') {
                if (btn.classList.contains('saved-marked')) {
                    // Unsave
                    btn.textContent = '⭐';
                    btn.classList.remove('saved-marked');
                    // Send unsave action
                    fetch(`${API_BASE}/feedback`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ rec_id: recId, action: 'unsave', place_id: placeId })
                    });
                } else {
                    // Save
                    btn.textContent = '⭐ Saved';
                    btn.classList.add('saved-marked');
                }
            } else if (action === 'already_been') {
                if (btn.classList.contains('been-marked')) {
                    // Unbeen
                    btn.textContent = '✅';
                    btn.classList.remove('been-marked');
                    // Send unbeen action
                    fetch(`${API_BASE}/feedback`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ rec_id: recId, action: 'unbeen', place_id: placeId })
                    });
                } else {
                    // Mark as been
                    btn.textContent = '✅ Been';
                    btn.classList.add('been-marked');
                }
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
window.resendVerificationEmail = resendVerificationEmail;
window.dismissVerifyBanner = dismissVerifyBanner;
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
window.applyCustomLocation = applyCustomLocation;
window.getCurrentLocationForQuickAdjust = getCurrentLocationForQuickAdjust;
window.showSignupPrompt = showSignupPrompt;
window.closeSignupPrompt = closeSignupPrompt;
window.skipSignupAndContinue = skipSignupAndContinue;
window.signupFromPrompt = signupFromPrompt;
window.loadDigest = loadDigest;
window.showDetail = showDetail;
window.selectSlot = selectSlot;
window.addToCalendar = addToCalendar;
window.connectGoogleCalendar = connectGoogleCalendar;
window.addToCalendarManual = addToCalendarManual;
window.selectEventType = selectEventType;
window.saveToGoogleCalendar = saveToGoogleCalendar;
window.closeDetailModal = closeDetailModal;
window.handleFeedback = handleFeedback;
window.resetInterestProfile = resetInterestProfile;
window.handleThumbsFeedback = handleThumbsFeedback;
window.loadAffinityScores = loadAffinityScores;
window.resetAffinityScores = resetAffinityScores;
window.showForgotPassword = showForgotPassword;
window.closeForgotPasswordModal = closeForgotPasswordModal;
window.handleForgotPassword = handleForgotPassword;
window.handleResetPassword = handleResetPassword;
window.showLoginFormFromReset = showLoginFormFromReset;
window.togglePasswordVisibility = togglePasswordVisibility;
window.clearCache = clearCache;
window.loadSavedPlaces = loadSavedPlaces;
window.loadBeenPlaces = loadBeenPlaces;
window.removeSavedPlace = removeSavedPlace;
window.removeBeenPlace = removeBeenPlace;

function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const eye = btn.querySelector('.icon-eye');
    const eyeOff = btn.querySelector('.icon-eye-off');
    if (input.type === 'password') {
        input.type = 'text';
        if (eye) eye.style.display = 'none';
        if (eyeOff) eyeOff.style.display = '';
        btn.setAttribute('title', 'Hide password');
        btn.setAttribute('aria-label', 'Hide password');
    } else {
        input.type = 'password';
        if (eye) eye.style.display = '';
        if (eyeOff) eyeOff.style.display = 'none';
        btn.setAttribute('title', 'Show password');
        btn.setAttribute('aria-label', 'Show password');
    }
}

// ==================== PASSWORD RESET ====================

function showForgotPassword() {
    const modal = document.getElementById('forgot-password-modal');
    const emailInput = document.getElementById('forgot-email');
    const loginEmail = document.getElementById('login-email');
    if (loginEmail && loginEmail.value) emailInput.value = loginEmail.value;
    document.getElementById('forgot-message').style.display = 'none';
    document.getElementById('forgot-error').style.display = 'none';
    if (modal) modal.classList.add('active');
}

function closeForgotPasswordModal() {
    const modal = document.getElementById('forgot-password-modal');
    if (modal) modal.classList.remove('active');
}

async function handleForgotPassword() {
    const email = document.getElementById('forgot-email').value.trim();
    const msgEl = document.getElementById('forgot-message');
    const errEl = document.getElementById('forgot-error');
    msgEl.style.display = 'none';
    errEl.style.display = 'none';
    
    if (!email) {
        errEl.textContent = 'Please enter your email';
        errEl.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json().catch(() => ({}));
        
        if (response.ok) {
            msgEl.innerHTML = data.message || "If an account exists with this email, you'll receive a link to reset your password.";
            if (data.reset_token) {
                const resetLink = `${window.location.origin}${window.location.pathname || '/index.html'}?reset_token=${encodeURIComponent(data.reset_token)}`;
                msgEl.innerHTML += `<br><br><strong>For testing:</strong> <a href="${resetLink}">Open this link</a> to set a new password.`;
            }
            msgEl.style.display = 'block';
            msgEl.style.color = '#059669';
        } else {
            errEl.textContent = data.error || 'Something went wrong. Please try again.';
            errEl.style.display = 'block';
        }
    } catch (error) {
        errEl.textContent = 'Unable to connect. Please try again.';
        errEl.style.display = 'block';
    }
}

function showResetPasswordForm(token) {
    document.getElementById('login-form').classList.remove('active');
    document.getElementById('signup-form').classList.remove('active');
    document.getElementById('reset-password-form').classList.add('active');
    document.getElementById('reset-token-input').value = token;
    document.getElementById('reset-new-password').value = '';
    document.getElementById('reset-confirm-password').value = '';
    document.getElementById('reset-error').style.display = 'none';
}

function showLoginFormFromReset() {
    document.getElementById('reset-password-form').classList.remove('active');
    document.getElementById('login-form').classList.add('active');
    document.getElementById('signup-form').classList.remove('active');
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
}

async function handleResetPassword() {
    const token = document.getElementById('reset-token-input').value.trim();
    const newPassword = document.getElementById('reset-new-password').value;
    const confirmPassword = document.getElementById('reset-confirm-password').value;
    const errEl = document.getElementById('reset-error');
    errEl.style.display = 'none';
    
    if (!token) {
        errEl.textContent = 'Invalid or expired reset link. Request a new one.';
        errEl.style.display = 'block';
        return;
    }
    if (!newPassword || newPassword.length < 8) {
        errEl.textContent = 'Password must be at least 8 characters.';
        errEl.style.display = 'block';
        return;
    }
    if (newPassword !== confirmPassword) {
        errEl.textContent = 'Passwords do not match.';
        errEl.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, new_password: newPassword })
        });
        const data = await response.json().catch(() => ({}));
        
        if (response.ok) {
            showLoginFormFromReset();
            alert(data.message || 'Password updated. You can sign in with your new password.');
        } else {
            errEl.textContent = data.error || 'Something went wrong. Please try again.';
            errEl.style.display = 'block';
        }
    } catch (error) {
        errEl.textContent = 'Unable to connect. Please try again.';
        errEl.style.display = 'block';
    }
}

// ==================== EMPTY STATE ====================

function buildEmptyState() {
    const suggestions = [];
    const travelRanges = onboardingData.travel_time_ranges || [];
    const maxTravel = getMaxTravelTimeMinutes();

    if (maxTravel <= 15) {
        suggestions.push({
            icon: '🗺️',
            text: 'Expand your travel time to 30+ minutes',
            action: 'expandTravelTime()'
        });
    }
    if ((onboardingData.interests || []).length <= 3) {
        suggestions.push({
            icon: '🎯',
            text: 'Add more interests for wider results',
            action: 'editPreference("interests")'
        });
    }
    if (onboardingData.budget === 'free') {
        suggestions.push({
            icon: '💰',
            text: 'Include paid activities for more options',
            action: null
        });
    }
    suggestions.push({
        icon: '📍',
        text: 'Try a different location',
        action: 'editPreference("location")'
    });

    return `
        <div class="empty-state" role="status">
            <div class="empty-state-icon">🔍</div>
            <h3 class="empty-state-title">No recommendations found</h3>
            <p class="empty-state-subtitle">Here are some things you can try:</p>
            <div class="empty-state-suggestions">
                ${suggestions.map(s => `
                    <div class="empty-suggestion" ${s.action ? `onclick="${s.action}" style="cursor:pointer"` : ''}>
                        <span class="empty-suggestion-icon">${s.icon}</span>
                        <span>${s.text}</span>
                        ${s.action ? '<span class="empty-suggestion-arrow">→</span>' : ''}
                    </div>
                `).join('')}
            </div>
            <button class="btn btn-primary" onclick="refreshRecommendations()" style="width: auto; margin-top: 1.5rem;">
                Try Again
            </button>
        </div>
    `;
}

function expandTravelTime() {
    // Add 30-60 to travel time ranges
    const btn30 = document.querySelector('.travel-time-toggles .quick-toggle[data-value="30-60"]');
    if (btn30 && !btn30.classList.contains('active')) {
        btn30.classList.add('active');
    }
    gatherQuickAdjustments();
    loadDashboardRecommendations();
}

window.expandTravelTime = expandTravelTime;

function retryWithBackoff() {
    const btn = document.getElementById('retry-btn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Retrying...';
    }
    retryCount++;
    if (retryCount > MAX_RETRIES) {
        retryCount = 0; // Reset for next attempt
    }
    const delay = getRetryDelay();
    setTimeout(() => {
        refreshRecommendations();
    }, delay);
}

window.retryWithBackoff = retryWithBackoff;

// ==================== SHARE ====================

async function shareRecommendation(recId) {
    const item = window.currentDigest?.items?.find(i => i.rec_id === recId);
    if (!item) return;

    const title = item.title || 'Activity Recommendation';
    const url = item.event_link || item.source_url || item.google_maps_url || '';
    const text = `Check out ${title}${item.address ? ' at ' + item.address : ''}`;

    // Try native Web Share API (works great on mobile)
    if (navigator.share) {
        try {
            await navigator.share({ title, text, url });
            return;
        } catch (err) {
            if (err.name === 'AbortError') return; // user cancelled
        }
    }

    // Fallback: copy to clipboard
    const shareText = url ? `${text}\n${url}` : text;
    try {
        await navigator.clipboard.writeText(shareText);
        showToast('Link copied to clipboard!');
    } catch {
        // Last resort: prompt
        prompt('Copy this link:', shareText);
    }
}

function showToast(message, duration = 2500) {
    // Remove existing toast
    const existing = document.getElementById('toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => toast.classList.add('visible'));
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

window.shareRecommendation = shareRecommendation;

function clearCache() {
    localStorage.clear();
    sessionStorage.clear();
    alert('Cache cleared! Refreshing...');
    window.location.reload();
}
