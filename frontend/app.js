// API Base URL - assuming the backend runs on the same host
const API_BASE_URL = 'http://localhost:5000';

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
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
    
    // Token saving
    const saveTokensBtn = document.getElementById('saveTokens');
    if (saveTokensBtn) {
        saveTokensBtn.addEventListener('click', saveTokens);
    }
    
    // Load saved tokens
    loadTokens();
    
    // API button functionality
    const apiButtons = document.querySelectorAll('.api-btn');
    apiButtons.forEach(button => {
        button.addEventListener('click', handleApiCall);
    });
});

// Token management
function saveTokens() {
    const accessToken = document.getElementById('accessToken').value;
    const adminToken = document.getElementById('adminToken').value;
    
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('adminToken', adminToken);
    
    showResult('Tokens saved successfully!', 'info', 'public-result');
}

function loadTokens() {
    const accessToken = localStorage.getItem('accessToken');
    const adminToken = localStorage.getItem('adminToken');
    
    if (accessToken) {
        document.getElementById('accessToken').value = accessToken;
    }
    
    if (adminToken) {
        document.getElementById('adminToken').value = adminToken;
    }
}

// API Call Handler
async function handleApiCall(event) {
    const button = event.target;
    const endpoint = button.getAttribute('data-endpoint');
    const method = button.getAttribute('data-method');
    const authType = button.getAttribute('data-auth');
    
    // Disable button during request
    button.disabled = true;
    button.textContent = 'Loading...';
    
    try {
        const result = await callApi(endpoint, method, authType);
        displayResult(result, endpoint, method);
    } catch (error) {
        displayError(error, endpoint, method);
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = button.textContent.replace('Loading...', 'Test') || 'Submit';
    }
}

// Main API calling function
async function callApi(endpoint, method, authType) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // Add authentication headers based on authType
    if (authType === 'access') {
        const token = localStorage.getItem('accessToken');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    } else if (authType === 'admin') {
        const token = localStorage.getItem('adminToken');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    } else if (authType === 'invalid') {
        headers['Authorization'] = 'Bearer invalid_token_here';
    }
    
    // Prepare request options
    const options = {
        method: method,
        headers: headers
    };
    
    // Add body for POST requests
    if (method === 'POST') {
        if (endpoint === '/api/orders') {
            const product = document.getElementById('product').value;
            const amount = document.getElementById('amount').value;
            
            if (!product || !amount) {
                throw new Error('Product name and amount are required');
            }
            
            options.body = JSON.stringify({
                product: product,
                amount: parseFloat(amount)
            });
        }
    }
    
    // Make the API call
    const response = await fetch(url, options);
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        return {
            status: response.status,
            statusText: response.statusText,
            data: data
        };
    } else {
        const text = await response.text();
        return {
            status: response.status,
            statusText: response.statusText,
            data: text
        };
    }
}

// Display successful results
function displayResult(result, endpoint, method) {
    const resultId = getResultElementId(endpoint, method);
    const resultElement = document.getElementById(resultId);
    
    if (resultElement) {
        resultElement.innerHTML = formatResult(result);
        resultElement.className = 'result success';
    }
}

// Display errors
function displayError(error, endpoint, method) {
    const resultId = getResultElementId(endpoint, method);
    const resultElement = document.getElementById(resultId);
    
    if (resultElement) {
        resultElement.innerHTML = formatError(error);
        resultElement.className = 'result error';
    }
}

// Show general result message
function showResult(message, type, elementId) {
    const resultElement = document.getElementById(elementId);
    if (resultElement) {
        resultElement.textContent = message;
        resultElement.className = `result ${type}`;
    }
}

// Generate result element ID based on endpoint and method
function getResultElementId(endpoint, method) {
    // Map endpoints to their result element IDs
    const endpointMap = {
        '/api/health': 'health-result',
        '/api/public': 'public-result',
        '/api/me': 'me-result',
        '/api/orders': endpoint.includes('POST') ? 'create-order-result' : 'orders-result',
        '/api/admin/stats': 'admin-stats-result',
        '/api/admin/users': 'admin-users-result'
    };
    
    // Special handling for error testing
    if (endpoint === '/api/me' && method === 'GET' && !document.querySelector('[data-auth]').getAttribute('data-auth')) {
        return 'no-token-result';
    }
    
    if (document.querySelector('[data-auth="invalid"]')) {
        return 'invalid-token-result';
    }
    
    return endpointMap[endpoint] || 'public-result';
}

// Format API result for display
function formatResult(result) {
    return `Status: ${result.status} ${result.statusText}\n\n${JSON.stringify(result.data, null, 2)}`;
}

// Format error for display
function formatError(error) {
    if (error instanceof Response) {
        return `HTTP Error: ${error.status} ${error.statusText}\n\n${error.statusText}`;
    } else if (error.message) {
        return `Error: ${error.message}`;
    } else {
        return `Unknown error occurred`;
    }
}