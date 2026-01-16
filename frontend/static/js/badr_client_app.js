// Configuration - In a real application, these would be loaded from environment variables
const CONFIG = {
    AUTH_SERVER_URL: window.location.protocol + '//' + window.location.hostname + ':3000',
    RESOURCE_SERVER_URL: window.location.protocol + '//' + window.location.hostname + ':5000',
    CLIENT_REDIRECT_URI: window.location.protocol + '//' + window.location.hostname + ':8080/badr_client_app.html',
    CLIENT_ID: 'badr_app',
    CLIENT_SECRET: 'secret123'  // Updated to match database
};

// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Check for stored session on load
    checkStoredSession();
    
    // Parse URL parameters for OAuth2 callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    
    if (code && state) {
        // Handle OAuth2 callback
        handleOAuth2Callback(code, state);
        
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

// Reset provider selection
function resetProviderSelection() {
    // Remove selected class from all providers
    const providers = document.querySelectorAll('.provider-option');
    providers.forEach(p => p.classList.remove('selected'));

    // Hide login container and show provider selection
    document.getElementById('oauth-login-container').style.display = 'none';
    document.getElementById('provider-selection').style.display = 'block';
    document.getElementById('provider-result').innerHTML = '';
}

// Select OAuth provider
function selectProvider(provider, element) {
    // Remove selected class from all providers
    const providers = document.querySelectorAll('.provider-option');
    providers.forEach(p => p.classList.remove('selected'));

    if (provider === 'omar') {
        // Add selected class to the clicked provider
        if (element) {
            element.classList.add('selected');
        }
        
        // Store selected provider
        sessionStorage.setItem('oauth2_provider', 'omar');
        
        // Update the confirmation message with provider name
        document.getElementById('selected-provider-name').textContent = 'Omar Auth Server';
        
        // Show success message
        document.getElementById('provider-result').innerHTML = '<div class="result-message success">Awesome choice! Omar Auth Server selected. You\'re one step closer to fun!</div>';
        
        // Hide provider selection and show login button
        document.getElementById('provider-selection').style.display = 'none';
        document.getElementById('oauth-login-container').style.display = 'block';
    } else if (provider === 'google' || provider === 'github') {
        document.getElementById('provider-result').innerHTML = '<div class="result-message error">Oh no! This provider isn\'t ready yet. But we\'re working on it!</div>';
    } else {
        document.getElementById('provider-result').innerHTML = '<div class="result-message error">Oops! That\'s not a valid provider. Try again!</div>';
    }
}

// Initiate OAuth flow after provider selection
function initiateOAuthFlow() {
    const loginButton = document.getElementById('loginButton');
    loginButton.disabled = true;
    loginButton.textContent = 'Hold on tight!';
    loginButton.style.opacity = '0.7';
    
    // Show a loading message
    const loginResult = document.getElementById('login-result');
    loginResult.innerHTML = '<div class="result-message info centered">Getting everything ready for your login adventure... Off we go!</div>';
    
    // Get selected provider
    const provider = sessionStorage.getItem('oauth2_provider');
    
    // Generate state parameter for security
    const state = Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem('oauth2_state', state);
    
    // Set up redirect URI
    const redirectUri = CONFIG.CLIENT_REDIRECT_URI;
    
    let authUrl;
    if (provider === 'omar') {
        // Redirect to Omar's authorization server
        authUrl = `${CONFIG.AUTH_SERVER_URL}/authorize?response_type=code&client_id=${CONFIG.CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=profile%20read:orders%20write:orders&state=${state}`;
    } else {
        // Default to Omar for any other case
        authUrl = `${CONFIG.AUTH_SERVER_URL}/authorize?response_type=code&client_id=${CONFIG.CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=profile%20read:orders%20write:orders&state=${state}`;
    }
    
    // Redirect immediately to the authorization server
    window.location.href = authUrl;
}

// Handle OAuth2 callback
function handleOAuth2Callback(code, state) {
    try {
        // Verify state parameter
        const storedState = sessionStorage.getItem('oauth2_state');
        if (state !== storedState) {
            displayError({ message: "Security alert! State parameter doesn't match. This might be a sneaky attack!" }, 'login-result');
            return;
        }
        
        // Exchange authorization code for tokens
        exchangeCodeForTokens(code);
    } catch (error) {
        console.error('Error handling OAuth2 callback:', error);
        displayError({ message: "An error occurred during authentication. Please try again." }, 'login-result');
    }
}

// Exchange authorization code for tokens
function exchangeCodeForTokens(code) {
    displayInfo({ message: "Magic time! Exchanging your special code for shiny tokens..." }, 'login-result');
    
    // Call the real token endpoint
    fetch(`${CONFIG.AUTH_SERVER_URL}/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            redirect_uri: CONFIG.CLIENT_REDIRECT_URI,
            client_id: CONFIG.CLIENT_ID,
            client_secret: CONFIG.CLIENT_SECRET  // Updated to use config
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.access_token) {
            // Store real tokens with expiration time
            const now = new Date();
            const accessTokenExpiry = new Date(now.getTime() + (data.expires_in * 1000));

            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('accessTokenExpiry', accessTokenExpiry.toISOString());

            if (data.refresh_token) {
                localStorage.setItem('refreshToken', data.refresh_token);
            }

            // Update session status
            document.getElementById('sessionStatus').value = 'Logged in';
            document.getElementById('userName').value = 'Alice';

            // Show success message
            displayResult({
                message: "Hooray! You're now logged in and ready for adventures!",
                access_token: data.access_token.substring(0, 20) + "...",
                refresh_token: data.refresh_token ? data.refresh_token.substring(0, 20) + "..." : "Not provided"
            }, 'login-result');

            // Switch to dashboard tab
            switchTab('dashboard');
        } else {
            displayError({ message: "Oh no! Token exchange failed: " + JSON.stringify(data) }, 'login-result');
        }
    })
    .catch(error => {
        console.error('Token exchange error:', error);
        displayError({ message: "Network error during token exchange: " + error.toString() }, 'login-result');
    });
}

// Check if access token is expired
function isAccessTokenExpired() {
    const expiry = localStorage.getItem('accessTokenExpiry');
    if (!expiry) return true;

    const expiryDate = new Date(expiry);
    const now = new Date();

    return now >= expiryDate;
}

// Refresh access token using refresh token
function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
        return Promise.reject(new Error('No refresh token available'));
    }

    return fetch(`${CONFIG.AUTH_SERVER_URL}/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            grant_type: 'refresh_token',
            refresh_token: refreshToken,
            client_id: CONFIG.CLIENT_ID,
            client_secret: 'e2a8d3f7c9d5b1a4e6f8c2d7a9b3e5f1'  // In production, this should be stored securely
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.access_token) {
            // Store new access token with expiration time
            const now = new Date();
            const accessTokenExpiry = new Date(now.getTime() + (data.expires_in * 1000));

            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('accessTokenExpiry', accessTokenExpiry.toISOString());

            // If a new refresh token is provided, store it
            if (data.refresh_token) {
                localStorage.setItem('refreshToken', data.refresh_token);
            }

            return data.access_token;
        } else {
            throw new Error('Failed to refresh token: ' + JSON.stringify(data));
        }
    })
    .catch(error => {
        console.error('Refresh token error:', error);
        throw error;
    });
}

// Get access token, refreshing if necessary
async function getAccessToken() {
    // Check if we have an access token
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        throw new Error('No access token available');
    }

    // Check if token is expired
    if (isAccessTokenExpired()) {
        // Try to refresh the token
        try {
            return await refreshAccessToken();
        } catch (error) {
            // If refresh fails, clear tokens and throw error
            localStorage.removeItem('accessToken');
            localStorage.removeItem('accessTokenExpiry');
            localStorage.removeItem('refreshToken');
            throw new Error('Token expired and refresh failed: ' + error.message);
        }
    }

    return accessToken;
}

// Check for stored session
function checkStoredSession() {
    const accessToken = localStorage.getItem('accessToken');
    if (accessToken) {
        document.getElementById('sessionStatus').value = 'Logged in';
        document.getElementById('userName').value = 'Alice';
        switchTab('dashboard');

        // Show welcome message
        document.getElementById('login-result').innerHTML = '<div class="result-message success centered">Welcome back, friend! You\'re already logged in. Ready for some fun?</div>';
    }
}

// Logout
function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    sessionStorage.removeItem('oauth2_state');
    sessionStorage.removeItem('oauth2_provider');

    document.getElementById('sessionStatus').value = 'Not logged in';
    document.getElementById('userName').value = 'None';

    // Reset provider selection
    resetProviderSelection();

    // Switch to login tab
    switchTab('login');

    // Show logout message
    document.getElementById('login-result').innerHTML = '<div class="result-message info centered">You\'ve been logged out. Come back soon!</div>';
}

// Switch to a specific tab
function switchTab(tabId) {
    // Remove active class from all buttons and panes
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabPanes.forEach(pane => pane.classList.remove('active'));

    // Add active class to the specified tab button and pane
    document.querySelector(`.tab-button[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// Display result message
function displayResult(data, elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="result-message success">
            <p>${data.message}</p>
            ${data.access_token ? `<p><strong>Token preview:</strong> ${data.access_token}</p>` : ''}
            ${data.refresh_token ? `<p><strong>Refresh token preview:</strong> ${data.refresh_token}</p>` : ''}
        </div>
    `;
    element.style.display = 'block';
}

// Display info message
function displayInfo(data, elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="result-message info">
            <p>${data.message}</p>
        </div>
    `;
    element.style.display = 'block';
}

// Display error message
function displayError(data, elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="result-message error">
            <p>${data.message}</p>
        </div>
    `;
    element.style.display = 'block';
}

// API Functions
async function getUserInfo() {
    try {
        const accessToken = await getAccessToken();

        displayInfo({ message: "Fetching your profile information..." }, 'profile-result');

        const response = await fetch(`${CONFIG.RESOURCE_SERVER_URL}/api/me`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            displayResult({ message: "Here's your profile information:", data: JSON.stringify(data, null, 2) }, 'profile-result');
        } else {
            displayError({ message: "Failed to fetch profile: " + JSON.stringify(data) }, 'profile-result');
        }
    } catch (error) {
        displayError({ message: "Failed to fetch profile: " + error.toString() }, 'profile-result');
    }
}

function getPublicInfo() {
    displayInfo({ message: "Fetching public information..." }, 'public-result');

    fetch(`${CONFIG.RESOURCE_SERVER_URL}/api/public`)
    .then(response => response.json())
    .then(data => {
        displayResult({ message: "Here's some public information:", data: JSON.stringify(data, null, 2) }, 'public-result');
    })
    .catch(error => {
        displayError({ message: "Failed to fetch public info: " + error.toString() }, 'public-result');
    });
}

async function getOrders() {
    try {
        const accessToken = await getAccessToken();

        displayInfo({ message: "Fetching your orders..." }, 'orders-result');

        const response = await fetch(`${CONFIG.RESOURCE_SERVER_URL}/api/orders`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            displayResult({ message: "Here are your orders:", data: JSON.stringify(data, null, 2) }, 'orders-result');
        } else {
            displayError({ message: "Failed to fetch orders: " + JSON.stringify(data) }, 'orders-result');
        }
    } catch (error) {
        displayError({ message: "Failed to fetch orders: " + error.toString() }, 'orders-result');
    }
}

async function createOrder() {
    try {
        const accessToken = await getAccessToken();

        displayInfo({ message: "Creating a new order..." }, 'orders-result');

        const response = await fetch(`${CONFIG.RESOURCE_SERVER_URL}/api/orders`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product: "Awesome Product",
                amount: 99.99
            })
        });

        const data = await response.json();

        if (response.ok) {
            displayResult({ message: "Order created successfully!", data: JSON.stringify(data, null, 2) }, 'orders-result');
        } else {
            displayError({ message: "Failed to create order: " + JSON.stringify(data) }, 'orders-result');
        }
    } catch (error) {
        displayError({ message: "Failed to create order: " + error.toString() }, 'orders-result');
    }
}

async function getAdminStats() {
    try {
        const accessToken = await getAccessToken();

        displayInfo({ message: "Fetching admin statistics..." }, 'admin-result');

        const response = await fetch(`${CONFIG.RESOURCE_SERVER_URL}/api/admin/stats`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            displayResult({ message: "Here are the admin statistics:", data: JSON.stringify(data, null, 2) }, 'admin-result');
        } else {
            displayError({ message: "Failed to fetch admin stats: " + JSON.stringify(data) }, 'admin-result');
        }
    } catch (error) {
        displayError({ message: "Failed to fetch admin stats: " + error.toString() }, 'admin-result');
    }
}

async function getAdminUsers() {
    try {
        const accessToken = await getAccessToken();

        displayInfo({ message: "Fetching user list..." }, 'admin-result');

        const response = await fetch(`${CONFIG.RESOURCE_SERVER_URL}/api/admin/users`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            displayResult({ message: "Here's the user list:", data: JSON.stringify(data, null, 2) }, 'admin-result');
        } else {
            displayError({ message: "Failed to fetch users: " + JSON.stringify(data) }, 'admin-result');
        }
    } catch (error) {
        displayError({ message: "Failed to fetch users: " + error.toString() }, 'admin-result');
    }
}