// API Base URL
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':5000';

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Load saved tokens
    loadTokens();
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

// API Call Functions
async function callApi(endpoint, method, authType, body = null) {
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
    } else if (authType === 'expired') {
        // Simulate expired token
        headers['Authorization'] = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDIyMjEyMDB9.signature';
    }
    
    // Prepare request options
    const options = {
        method: method,
        headers: headers
    };
    
    // Add body for POST requests
    if (body) {
        options.body = JSON.stringify(body);
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

// Public Endpoints
async function testHealthCheck() {
    try {
        const result = await callApi('/api/health', 'GET');
        displayResult(result, 'health-result');
    } catch (error) {
        displayError(error, 'health-result');
    }
}

async function testPublicEndpoint() {
    try {
        const result = await callApi('/api/public', 'GET');
        displayResult(result, 'public-result');
    } catch (error) {
        displayError(error, 'public-result');
    }
}

// User Endpoints
async function getUserInfo() {
    try {
        const result = await callApi('/api/me', 'GET', 'access');
        displayResult(result, 'me-result');
    } catch (error) {
        displayError(error, 'me-result');
    }
}

async function getOrders() {
    try {
        const result = await callApi('/api/orders', 'GET', 'access');
        displayResult(result, 'orders-result');
    } catch (error) {
        displayError(error, 'orders-result');
    }
}

async function createOrder() {
    const product = document.getElementById('product').value;
    const amount = document.getElementById('amount').value;
    
    if (!product || !amount) {
        displayError({message: "Product name and amount are required"}, 'create-order-result');
        return;
    }
    
    try {
        const result = await callApi('/api/orders', 'POST', 'access', {
            product: product,
            amount: parseFloat(amount)
        });
        displayResult(result, 'create-order-result');
    } catch (error) {
        displayError(error, 'create-order-result');
    }
}

// Admin Endpoints
async function getAdminStats() {
    try {
        const result = await callApi('/api/admin/stats', 'GET', 'admin');
        displayResult(result, 'admin-stats-result');
    } catch (error) {
        displayError(error, 'admin-stats-result');
    }
}

async function getAllUsers() {
    try {
        const result = await callApi('/api/admin/users', 'GET', 'admin');
        displayResult(result, 'admin-users-result');
    } catch (error) {
        displayError(error, 'admin-users-result');
    }
}

// Error Testing
async function testWithoutToken() {
    try {
        const result = await callApi('/api/me', 'GET');
        displayResult(result, 'no-token-result');
    } catch (error) {
        displayError(error, 'no-token-result');
    }
}

async function testInvalidToken() {
    try {
        const result = await callApi('/api/me', 'GET', 'invalid');
        displayResult(result, 'invalid-token-result');
    } catch (error) {
        displayError(error, 'invalid-token-result');
    }
}

async function testExpiredToken() {
    try {
        const result = await callApi('/api/me', 'GET', 'expired');
        displayResult(result, 'expired-token-result');
    } catch (error) {
        displayError(error, 'expired-token-result');
    }
}

// Display functions
function displayResult(result, elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = formatResult(result);
    element.className = 'result success';
}

function displayError(error, elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = formatError(error);
    element.className = 'result error';
}

function showResult(message, type, elementId) {
    const resultElement = document.getElementById(elementId);
    if (resultElement) {
        resultElement.textContent = message;
        resultElement.className = `result ${type}`;
    }
}

function formatResult(result) {
    return `Status: ${result.status} ${result.statusText}\n\n${JSON.stringify(result.data, null, 2)}`;
}

function formatError(error) {
    if (error instanceof Response) {
        return `HTTP Error: ${error.status} ${error.statusText}\n\n${error.statusText}`;
    } else if (error.message) {
        return `Error: ${error.message}`;
    } else {
        return `Unknown error occurred`;
    }
}