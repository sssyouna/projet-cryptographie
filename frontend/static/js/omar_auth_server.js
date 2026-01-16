// Check for OAuth2 parameters on page load
window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search);
    const responseType = urlParams.get('response_type');
    const clientId = urlParams.get('client_id');
    const redirectUri = urlParams.get('redirect_uri');
    const scope = urlParams.get('scope');
    const state = urlParams.get('state');
    
    if (responseType && clientId && redirectUri) {
        // Store OAuth2 parameters
        sessionStorage.setItem('oauth2_params', JSON.stringify({
            response_type: responseType,
            client_id: clientId,
            redirect_uri: redirectUri,
            scope: scope,
            state: state
        }));
    }
};

// Authenticate user
function authenticateUser() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const authResult = document.getElementById('auth-result');
    
    if (!username || !password) {
        authResult.innerHTML = '<p style="color: #dc3545;">Please enter both username and password</p>';
        return;
    }
    
    // Simulate authentication
    authResult.innerHTML = '<p style="color: #1e3c72;">Authenticating...</p>';
    
    setTimeout(() => {
        if (username === 'alice' && password === 'password123') {
            authResult.innerHTML = '<p style="color: #28a745;">Authentication successful!</p>';
            
            // Show consent screen
            setTimeout(() => {
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('consentSection').style.display = 'block';
            }, 1000);
        } else {
            authResult.innerHTML = '<p style="color: #dc3545;">Invalid username or password</p>';
        }
    }, 1500);
}

// Grant consent
function grantConsent() {
    const consentResult = document.getElementById('consent-result');
    consentResult.innerHTML = '<p style="color: #1e3c72;">Processing authorization...</p>';
    
    setTimeout(() => {
        // Get stored OAuth2 parameters
        const oauth2Params = JSON.parse(sessionStorage.getItem('oauth2_params'));
        
        if (!oauth2Params) {
            consentResult.innerHTML = '<p style="color: #dc3545;">OAuth2 parameters not found</p>';
            return;
        }
        
        // Generate authorization code
        const authCode = 'auth_code_' + Math.random().toString(36).substr(2, 9);
        
        // Redirect back to client application
        consentResult.innerHTML = '<p style="color: #28a745;">Authorization granted! Redirecting back...</p>';
        
        setTimeout(() => {
            const redirectUrl = `${oauth2Params.redirect_uri}?code=${authCode}&state=${oauth2Params.state || ''}`;
            window.location.href = redirectUrl;
        }, 1500);
    }, 1500);
}

// Deny consent
function denyConsent() {
    const consentResult = document.getElementById('consent-result');
    consentResult.innerHTML = '<p style="color: #dc3545;">Authorization denied. Redirecting back...</p>';
    
    setTimeout(() => {
        // Get stored OAuth2 parameters
        const oauth2Params = JSON.parse(sessionStorage.getItem('oauth2_params'));
        
        if (oauth2Params) {
            const redirectUrl = `${oauth2Params.redirect_uri}?error=access_denied&state=${oauth2Params.state || ''}`;
            window.location.href = redirectUrl;
        }
    }, 1500);
}

// Allow Enter key to submit login form
document.addEventListener('DOMContentLoaded', function() {
    const passwordField = document.getElementById('password');
    passwordField.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            authenticateUser();
        }
    });
});