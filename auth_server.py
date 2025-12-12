"""
Authorization Server (Omar) - OAuth2/OIDC Identity Provider
Author: Youness
Description: Serveur d'autorisation qui implémente le flux OAuth2 Authorization Code
"""

from flask import Flask, request, redirect, jsonify, render_template_string, session
import jwt
import os
import uuid
from datetime import datetime, timedelta
import json
import logging
import bcrypt
import secrets
import sqlite3
import time
from collections import defaultdict
import re
from flask_cors import CORS

# Import database and user management modules
from db import db
from user_management import user_manager

# Simple rate limiting implementation
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            'auth_attempts': {'limit': 5, 'window': 300},  # 5 attempts per 5 minutes
            'token_requests': {'limit': 10, 'window': 60},  # 10 requests per minute
            'registration': {'limit': 3, 'window': 3600}    # 3 registrations per hour
        }
    
    def is_allowed(self, ip, limit_type):
        """Check if request is allowed based on rate limits"""
        now = time.time()
        limit_config = self.limits.get(limit_type, {'limit': 10, 'window': 60})
        limit = limit_config['limit']
        window = limit_config['window']
        
        # Clean old requests
        self.requests[ip] = [req_time for req_time in self.requests[ip] if now - req_time < window]
        
        # Check if under limit
        if len(self.requests[ip]) < limit:
            self.requests[ip].append(now)
            return True
        else:
            return False
    
    def get_retry_after(self, ip, limit_type):
        """Get seconds until next allowed request"""
        now = time.time()
        limit_config = self.limits.get(limit_type, {'limit': 10, 'window': 60})
        window = limit_config['window']
        
        if self.requests[ip]:
            oldest_request = min(self.requests[ip])
            return int(oldest_request + window - now)
        return 0

# Global rate limiter instance
rate_limiter = RateLimiter()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)  # Enable CORS for all routes

# Security headers middleware
@app.after_request
def after_request(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    return response

# ================== CONFIGURATION ==================
class Config:
    """Configuration OAuth2/OIDC"""
    ISSUER = os.getenv('OAUTH_ISSUER', 'http://localhost:3000')
    AUDIENCE = os.getenv('OAUTH_AUDIENCE', 'api://resource-server')
    TOKEN_EXPIRY = int(os.getenv('TOKEN_EXPIRY', 3600))  # 1 heure par défaut
    AUTH_CODE_EXPIRY = 300  # 5 minutes pour les codes d'autorisation

config = Config()

# ================== STOCKAGE EN MÉMOIRE ==================
# En production, utiliser une base de données persistante
# Les clients sont maintenant stockés dans la base de données

# Stockage des demandes d'autorisation en attente
auth_requests = {}

# Stockage des refresh tokens
refresh_tokens = {}

# Utilisateurs avec mot de passe hashé
# Les utilisateurs sont maintenant stockés dans la base de données

# ================== CLÉS RSA ==================
# Clés RSA pour la signature des JWT - EN PRODUCTION, UTILISER DES CLÉS RÉELLES
RSA_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDJoecunuPOWXoB
PzzFUuoZARlcU5kqh1Y+QHFMBG5FTuo0QWzGCoA8TL3ODyNSbUJ4KIzpOLcXyAHq
slCwtNRG30+CkUMMVc2yPkKDPkh0BeMn/AMjtyMZb4XwKnRkThuFjIHCZ6vqYVC9
3vQw8RYDpPiDH2CKmDNhu+cmQ+1suDuE9bIat4KPdDGDuQq0wwhUclYCXhQkHE/j
REHV1ohOtXFYjp9o/9wDbXpc6fFWTxmq/LMJwuOoiOtfiT/9obyva1mpqSB6JeLh
LfNxUhQ0JmKxYQxdOg/zPInxz0ep/cI7NqbBzbd1EJiNdNf7IY2CLYyUZp925qsD
8ArsBVZ/AgMBAAECggEAWjYLMmMZZiXHPc6WuGwv268Psyyd7xatAd4gMpQa5/x2
MZoB+hsRo6jsFMjWE1dZ8VunK+NZm5S7Ms/D5UOKZAkeUDsApgCvrqtHY+PWU76c
krOgjfauh/9LDBhaidQeYSJrndh3ZL5UexbI5yq+IDRLkZLUxT1yY6xHr2mdzNFX
KcmBF8Y+XbsDCc8aYRX53aUOK4pz0SqYmBEcWxbn9wN1SF8LLEaj1IlCMn1cRSZY
qpshvbNe7bLZdw2Uf04EnrJidufRviy6TuoBwRD7n+YpjKBwJGYdhVYEHZGNYH9s
G0uPhD1cWOT4F0J94Y7+Kw++/5RiRKyQKNernCBZPQKBgQDs4bso7axLnlOqtUSY
K3l/WQpxIWxADPkwG14Ur/iY1tZ0AQ3nJLr8cNqCFJ3fk/QYm8OlKFQM6D+IIti7
MyIkyhkGhkcMt6PGaF1h5WmH6ptObOdW4HmPRFcuZ8xrIYlvjNPbZGOZPo2NMljR
3pDzFYyKex9JTUH4tWOI4IztgwKBgQDZ5+Cfb+JC+AMpnrEbebrwlt8ViNmP/laQ
T4afcyHWtVqelEnCUUDcUH6KyHFgzsdEgVlmFtsQjp5+dwPkm63siNupwh1+2PAb
NYcxh2oRUuQ2WZhncJZ0s1pJAL1i+mScakwfRiFstrHVM34l5mQxKldUGHRianQZ
FimaAhx+VQKBgCiGhcp+vtdBAvdVg6K07VhIF207VpWuooMEa5gGcvVS6+V0uLgu
pH7Dn95ZQJkbass6+sGqoJaEtTnJHGMKYHEC0j03g7g9QpuTB0bURLWoAWHtZ7aJ
OMK14mRiBareVfDrmuMRzahN91GMp31gIlQz/5NBdRzJRtwRzDGCmRmZAoGAKz53
N2zuzDeH+SSDJV69GK34S7/C3W6uIymFH/OrTX7kIwBuut+BLbfTxRsOVRX0OcYp
xbbXdqu3DIX2AdJba8ulPEVHsTrAO8YdtFiZViLLI3YYZr7TPQmy6zX4X8ItYVU/
Eh3K2FZRaGw1prPYQmGSvx+zSSyzKZ9aVjQBD5kCgYBb0kblC1Zbd6Q5t73xDsW3
fyfwSEbco9bAkipek7f+scsjspvnGRspr8WiR31dTUNNjGm9gMOscXMTYfBIzVii
nIA3GViPYuIrYxVkeSq0jbSlW4Z4CyVzecpVT5j4CU2EZYzZ8zQfiXFrxuVfvR73
V83za2pGqW2bqP2bsXEsPg==
-----END PRIVATE KEY-----"""

RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqk0rRf1EEYmtsv1hanrU
rMJtQxGVZvMa5Wr0sriQl7xx1BRnP+Po7q6CdseRl+MipYD7QGPWGF4uBPzS3D/E
8k7/yNjQdDlXZxKCGdWjpVDpxncGbBEC1gagtDDgWiPNFpvShsydqEUQTVUTkG7i
dCaM+0hkoyYV7h0z0ULeYTRGt938O1x3wLurR1sfGdywOsa1syGUMTldIQa2Bai6
AEmLCRJgrdpT4ED//D3sSO4ja6Adiut4gT4b8CMtrREP3RBoYbVU2Lr7nz8xBq59
+iuIi7PK3Vdl4GY183DQY9+BiHr9VB8WjlW1FSUDT4CnrfXT+M/MkhipstlBDnge
wQIDAQAB
-----END PUBLIC KEY-----"""

# ================== UTILITAIRES ==================
def sanitize_input(input_str):
    """Sanitize user input to prevent injection attacks"""
    if input_str is None:
        return None
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(input_str))
    # Limit length
    return sanitized[:100]

def validate_client_id(client_id):
    """Validate client_id format"""
    if not client_id:
        return False
    # Client ID should be alphanumeric and underscores/hyphens only
    return re.match(r'^[a-zA-Z0-9_-]+$', client_id) is not None

def validate_redirect_uri(redirect_uri, allowed_uris):
    """Validate redirect URI against allowed URIs"""
    if not redirect_uri or not allowed_uris:
        return False
    return redirect_uri in allowed_uris

def validate_scope(scope):
    """Validate requested scopes"""
    if not scope:
        return False
    # Define allowed scopes
    allowed_scopes = {'profile', 'read:orders', 'write:orders', 'admin:read'}
    requested_scopes = set(scope.split())
    return requested_scopes.issubset(allowed_scopes)

def generate_access_token(user_info, scopes):
    """Génère un JWT access token"""
    now = datetime.utcnow()
    payload = {
        'iss': config.ISSUER,
        'aud': config.AUDIENCE,
        'sub': user_info['username'],
        'exp': now + timedelta(seconds=config.TOKEN_EXPIRY),
        'iat': now,
        'scope': ' '.join(scopes),
        'email': user_info['email'],
        'name': user_info['name'],
        'roles': user_info['roles']
    }
    
    # Sign with the real private key
    token = jwt.encode(payload, RSA_PRIVATE_KEY, algorithm='RS256')
    return token

def generate_authorization_code(client_id, user_info, scopes, redirect_uri):
    """Génère un code d'autorisation temporaire"""
    code = str(uuid.uuid4())
    # Stocker la demande d'autorisation dans la base de données
    db.create_auth_request(code, client_id, user_info, scopes, redirect_uri)
    return code

# ================== ENDPOINTS ==================
@app.route('/')
def home():
    """Page d'accueil du serveur d'autorisation"""
    return jsonify({
        'message': 'Authorization Server (Omar) - OAuth2/OIDC Identity Provider',
        'issuer': config.ISSUER,
        'endpoints': {
            'authorization': '/authorize',
            'token': '/token',
            'jwks': '/.well-known/jwks.json'
        }
    })

@app.route('/authorize')
def authorize():
    """Endpoint d'autorisation - démarre le flux OAuth2"""
    # Paramètres requis avec sanitization
    response_type = sanitize_input(request.args.get('response_type'))
    client_id = sanitize_input(request.args.get('client_id'))
    redirect_uri = request.args.get('redirect_uri')  # Will validate separately
    scope = sanitize_input(request.args.get('scope', 'openid profile'))
    state = sanitize_input(request.args.get('state'))
    
    logger.info(f"Authorization request received: client_id={client_id}")
    
    # Validation basique
    if response_type != 'code':
        error_params = f'?error=unsupported_response_type&error_description=Only+code+response+type+supported'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params) if redirect_uri else jsonify({'error': 'invalid_request'}), 400
    
    # Validate client ID format
    if not validate_client_id(client_id):
        error_params = f'?error=invalid_client&error_description=Invalid+client_id+format'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params) if redirect_uri else jsonify({'error': 'invalid_client'}), 400
    
    # Récupérer le client depuis la base de données
    client = db.get_client(client_id)
    if not client:
        error_params = f'?error=unauthorized_client&error_description=Invalid+client_id'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params) if redirect_uri else jsonify({'error': 'unauthorized_client'}), 400
    
    # Validate redirect URI - normalize localhost/127.0.0.1 for comparison
    normalized_redirect_uri = redirect_uri.replace('http://localhost:', 'http://127.0.0.1:')
    normalized_client_uris = [uri.replace('http://localhost:', 'http://127.0.0.1:') for uri in client['redirect_uris']]
    
    if not validate_redirect_uri(normalized_redirect_uri, normalized_client_uris):
        error_params = f'?error=invalid_request&error_description=Invalid+redirect_uri'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params) if redirect_uri else jsonify({'error': 'invalid_request'}), 400
    
    # Validate scope
    if scope and not validate_scope(scope):
        error_params = f'?error=invalid_scope&error_description=Invalid+scope+format'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params) if redirect_uri else jsonify({'error': 'invalid_scope'}), 400
    
    # Stocker la demande d'autorisation
    auth_request_id = f"auth_req_{os.urandom(8).hex()}"
    session_data = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'state': state
    }
    auth_requests[auth_request_id] = session_data
    
    # Rediriger vers la page de login
    login_url = f"/login?auth_req_id={auth_request_id}"
    return redirect(login_url)

@app.route('/login')
def login_page():
    """Page de login HTML"""
    auth_req_id = request.args.get('auth_req_id')
    
    if not auth_req_id or auth_req_id not in auth_requests:
        return "Invalid authorization request", 400
    
    auth_request = auth_requests[auth_req_id]
    
    # In a real implementation, this would be an HTML login page
    # For this demo, we'll return a simple login form
    client_id = auth_request['client_id']
    scope = auth_request['scope'] or 'profile openid'
    
    login_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Login - Omar Auth Server</title>
    <style>
        /* Clean Black and White Theme with Blue Accent */
        :root {{
            --primary-black: #000000;
            --secondary-black: #333333;
            --light-gray: #f5f5f5;
            --medium-gray: #e0e0e0;
            --white: #ffffff;
            --accent-blue: #2196F3;
            --accent-blue-hover: #1976D2;
            --warning-yellow: #FFC107;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 450px;
            margin: 30px auto;
            padding: 25px;
            background-color: var(--white);
            color: var(--primary-black);
            border: 1px solid var(--medium-gray);
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}

        .login-form {{
            padding: 25px;
            background-color: var(--white);
            text-align: center;
        }}

        h2 {{
            color: var(--primary-black);
            margin-top: 0;
            font-size: 28px;
        }}

        .client-info {{
            background-color: var(--light-gray);
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid var(--accent-blue);
        }}

        input {{
            width: 100%;
            padding: 12px;
            margin: 12px 0;
            border: 1px solid var(--medium-gray);
            border-radius: 4px;
            font-size: 16px;
            box-sizing: border-box;
            background-color: var(--white);
            color: var(--primary-black);
        }}

        input:focus {{
            border-color: var(--accent-blue);
            outline: none;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
        }}

        button {{
            background-color: var(--accent-blue);
            color: var(--white);
            padding: 14px 25px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 18px;
            font-weight: 500;
            margin-top: 10px;
            transition: background-color 0.3s ease;
        }}

        button:hover {{
            background-color: var(--accent-blue-hover);
        }}

        .demo-creds {{
            background-color: var(--light-gray);
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            border: 1px solid var(--medium-gray);
            font-size: 14px;
        }}

        .fun-icon {{
            font-size: 40px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="login-form">
        <div class="fun-icon"></div>
        <h2>Hey there!</h2>
        <p>Looks like you want to log in to <strong>{client_id}</strong></p>
        
        <div class="client-info">
            <p>They want to access:</p>
            <p><strong>{scope}</strong></p>
        </div>
        
        <form method="POST" action="/authenticate">
            <input type="hidden" name="auth_req_id" value="{auth_req_id}">
            <label>Username:</label>
            <input type="text" name="username" placeholder="Type your username here..." required>
            <label>Password:</label>
            <input type="password" name="password" placeholder="Shhh... secret password..." required>
            <button type="submit">Let me in!</button>
        </form>
        
        <div class="demo-creds">
            <p>Hint: Try <strong>alice</strong> with <strong>password123</strong></p>
            <p>(Don't worry, we won't tell anyone!)</p>
        </div>
    </div>
</body>
</html>"""
    
    return login_html

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Authentifie l'utilisateur et génère le code d'autorisation"""
    # Get client IP for rate limiting
    client_ip = request.remote_addr or 'unknown'
    
    # Check rate limit for authentication attempts
    if not rate_limiter.is_allowed(client_ip, 'auth_attempts'):
        retry_after = rate_limiter.get_retry_after(client_ip, 'auth_attempts')
        return jsonify({
            'error': 'too_many_requests',
            'error_description': 'Too many authentication attempts. Please try again later.',
            'retry_after': retry_after
        }), 429
    
    auth_req_id = request.form.get('auth_req_id')
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not auth_req_id or auth_req_id not in auth_requests:
        return "Invalid authorization request", 400
    
    auth_request = auth_requests[auth_req_id]
    
    # Récupérer l'utilisateur depuis la base de données
    user = db.get_user(username)
    
    # Vérifier les identifiants avec bcrypt via user manager
    if not user or not user_manager.verify_password(password, user['password_hash']):
        # Log failed authentication attempt
        logger.warning(f"Failed authentication attempt for user: {username} from IP: {client_ip}")
        
        # Return to login page with error
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Failed - Omar Auth Server</title>
            <style>
                /* Clean Black and White Theme with Blue Accent */
                :root {{
                    --primary-black: #000000;
                    --secondary-black: #333333;
                    --light-gray: #f5f5f5;
                    --medium-gray: #e0e0e0;
                    --white: #ffffff;
                    --accent-blue: #2196F3;
                    --accent-blue-hover: #1976D2;
                    --error-red: #f44336;
                }}

                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 450px;
                    margin: 30px auto;
                    padding: 25px;
                    background-color: var(--white);
                    color: var(--primary-black);
                    border: 1px solid var(--medium-gray);
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }}

                .error {{
                    color: var(--error-red);
                    padding: 20px;
                    background-color: rgba(244, 67, 54, 0.1);
                    border-radius: 8px;
                    border: 1px solid var(--error-red);
                    text-align: center;
                }}

                h2 {{
                    color: var(--error-red);
                    margin-top: 0;
                    font-size: 28px;
                }}

                a {{
                    color: var(--accent-blue);
                    text-decoration: none;
                    font-weight: 500;
                    padding: 10px 20px;
                    background-color: var(--light-gray);
                    border-radius: 4px;
                    display: inline-block;
                    margin-top: 15px;
                    transition: background-color 0.3s ease;
                }}

                a:hover {{
                    background-color: var(--medium-gray);
                }}

                .fun-icon {{
                    font-size: 40px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <div class="fun-icon"></div>
                <h2>Oops! Something went wrong...</h2>
                <p>Looks like your username or password didn't match.</p>
                <p>Don't worry, it happens to the best of us!</p>
                <p><a href="/login?auth_req_id={auth_req_id}">← Try again</a></p>
            </div>
        </body>
        </html>
        """
        return error_html
    
    # Authentification réussie
    user_info = {
        'username': username,
        'email': user['email'],
        'name': user['name'],
        'roles': user['roles']
    }
    
    # Générer le code d'autorisation
    scopes = auth_request['scope'].split() if auth_request['scope'] else ['openid', 'profile']
    auth_code = generate_authorization_code(
        auth_request['client_id'],
        user_info,
        scopes,
        auth_request['redirect_uri']
    )
    
    # Construire l'URL de redirection
    # Handle cases where redirect_uri might already contain query parameters
    separator = '&' if '?' in auth_request['redirect_uri'] else '?'
    redirect_params = f"{separator}code={auth_code}"
    if auth_request['state']:
        redirect_params += f"&state={auth_request['state']}"
    
    # Nettoyer la demande d'autorisation
    del auth_requests[auth_req_id]
    
    # Log successful authentication
    logger.info(f"Successful authentication for user: {username} from IP: {client_ip}")
    
    # Construct the full redirect URL
    redirect_url = auth_request['redirect_uri'] + redirect_params
    logger.info(f"Redirecting to: {redirect_url}")
    
    try:
        return redirect(redirect_url)
    except Exception as e:
        logger.error(f"Failed to redirect to {redirect_url}: {str(e)}")
        return jsonify({'error': 'server_error', 'error_description': 'Failed to redirect'}), 500

@app.route('/token', methods=['POST'])
def token():
    """Endpoint de token - échange le code contre des tokens"""
    # Get client IP for rate limiting
    client_ip = request.remote_addr or 'unknown'
    
    # Check rate limit for token requests
    if not rate_limiter.is_allowed(client_ip, 'token_requests'):
        retry_after = rate_limiter.get_retry_after(client_ip, 'token_requests')
        return jsonify({
            'error': 'too_many_requests',
            'error_description': 'Too many token requests. Please try again later.',
            'retry_after': retry_after
        }), 429
    
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    redirect_uri = request.form.get('redirect_uri')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    refresh_token = request.form.get('refresh_token')
    
    logger.info(f"Token request received: grant_type={grant_type}, client_id={client_id}")
    
    # Validation
    if grant_type == 'authorization_code':
        return handle_authorization_code_grant(code, redirect_uri, client_id, client_secret)
    elif grant_type == 'refresh_token':
        return handle_refresh_token_grant(refresh_token, client_id, client_secret)
    else:
        return jsonify({
            'error': 'unsupported_grant_type',
            'error_description': 'Only authorization_code and refresh_token grant types supported'
        }), 400

def handle_authorization_code_grant(code, redirect_uri, client_id, client_secret):
    """Handle authorization code grant type"""
    # Sanitize inputs
    code = sanitize_input(code)
    redirect_uri = sanitize_input(redirect_uri)
    client_id = sanitize_input(client_id)
    client_secret = sanitize_input(client_secret)
    
    # Validate inputs
    if not code or not redirect_uri or not client_id:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Missing required parameters'
        }), 400
    
    # Récupérer la demande d'autorisation depuis la base de données
    auth_data = db.get_auth_request(code)
    if not auth_data:
        return jsonify({
            'error': 'invalid_grant',
            'error_description': 'Invalid authorization code'
        }), 400
    
    # Vérifier si le code est expiré
    if datetime.utcnow() > auth_data['expires_at']:
        db.delete_auth_request(code)
        return jsonify({
            'error': 'invalid_grant',
            'error_description': 'Authorization code expired'
        }), 400
    
    # Récupérer le client depuis la base de données
    client = db.get_client(client_id)
    if not client:
        return jsonify({
            'error': 'invalid_client',
            'error_description': 'Invalid client ID'
        }), 400
    
    # Vérifier client_id
    if client_id != auth_data['client_id']:
        return jsonify({
            'error': 'invalid_client',
            'error_description': 'Client ID mismatch'
        }), 400
    
    # Validate redirect_uri - normalize for consistent comparison
    # Normalize both the incoming redirect_uri and stored redirect_uri for comparison
    normalized_request_uri = redirect_uri.replace('http://localhost:', 'http://127.0.0.1:')
    normalized_stored_uri = auth_data['redirect_uri'].replace('http://localhost:', 'http://127.0.0.1:')
    normalized_client_uris = [uri.replace('http://localhost:', 'http://127.0.0.1:') for uri in client['redirect_uris']]
    
    # First check if the redirect_uri is in the allowed list
    if not validate_redirect_uri(normalized_request_uri, normalized_client_uris):
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Redirect URI not in allowed list'
        }), 400
    
    # Then check if it matches what was stored during authorization
    if normalized_request_uri != normalized_stored_uri:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Redirect URI mismatch with authorization request'
        }), 400
    
    # Verify the client_secret
    if not client_secret or client_secret != client['client_secret']:
        return jsonify({
            'error': 'invalid_client',
            'error_description': 'Invalid client credentials'
        }), 401
    
    # Générer les tokens
    access_token = generate_access_token(auth_data['user_info'], auth_data['scopes'])
    refresh_token = str(uuid.uuid4())
    
    # Stocker le refresh token dans la base de données
    db.create_refresh_token(refresh_token, auth_data['user_info'], auth_data['scopes'])
    
    # Nettoyer le code d'autorisation
    db.delete_auth_request(code)
    
    response_data = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': config.TOKEN_EXPIRY,
        'scope': ' '.join(auth_data['scopes']),
        'refresh_token': refresh_token
    }
    
    logger.info(f"Token issued for user: {auth_data['user_info']['username']}")
    
    return jsonify(response_data)

def handle_refresh_token_grant(refresh_token, client_id, client_secret):
    """Handle refresh token grant type"""
    # Sanitize inputs
    refresh_token = sanitize_input(refresh_token)
    client_id = sanitize_input(client_id)
    client_secret = sanitize_input(client_secret)
    
    # Validate inputs
    if not refresh_token:
        return jsonify({
            'error': 'invalid_grant',
            'error_description': 'Refresh token is required'
        }), 400
    
    # Récupérer le refresh token depuis la base de données
    token_data = db.get_refresh_token(refresh_token)
    if not token_data:
        return jsonify({
            'error': 'invalid_grant',
            'error_description': 'Invalid refresh token'
        }), 400
    
    # Vérifier si le refresh token est expiré
    if datetime.utcnow() > token_data['expires_at']:
        db.delete_refresh_token(refresh_token)
        return jsonify({
            'error': 'invalid_grant',
            'error_description': 'Refresh token expired'
        }), 400
    
    # Récupérer le client depuis la base de données
    client = db.get_client(client_id)
    if not client:
        return jsonify({
            'error': 'invalid_client',
            'error_description': 'Invalid client ID'
        }), 400
    
    # Verify the client_secret
    if not client_secret or client_secret != client['client_secret']:
        return jsonify({
            'error': 'invalid_client',
            'error_description': 'Invalid client credentials'
        }), 401
    
    # Générer un nouveau access token
    access_token = generate_access_token(token_data['user_info'], token_data['scopes'])
    
    # Generate a new refresh token
    new_refresh_token = str(uuid.uuid4())
    
    # Store the new refresh token in the database
    db.create_refresh_token(new_refresh_token, token_data['user_info'], token_data['scopes'])
    
    # Remove the old refresh token from the database
    db.delete_refresh_token(refresh_token)
    
    response_data = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': config.TOKEN_EXPIRY,
        'scope': ' '.join(token_data['scopes']),
        'refresh_token': new_refresh_token
    }
    
    logger.info(f"Token refreshed for user: {token_data['user_info']['username']}")
    
    return jsonify(response_data)

@app.route('/register', methods=['POST'])
def register_client():
    """Endpoint d'enregistrement dynamique des clients OAuth2"""
    data = request.get_json()
    
    # Validation requise
    required_fields = ['client_name', 'redirect_uris']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'error': 'invalid_request',
                'error_description': f'Missing required field: {field}'
            }), 400
    
    # Générer un ID et secret client uniques
    client_id = f"client_{uuid.uuid4().hex[:16]}"
    client_secret = secrets.token_urlsafe(32)
    
    # Définir les valeurs par défaut
    client_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'client_name': data['client_name'],
        'redirect_uris': data['redirect_uris'],
        'client_uri': data.get('client_uri', ''),
        'grant_types': data.get('grant_types', ['authorization_code']),
        'response_types': data.get('response_types', ['code']),
        'token_endpoint_auth_method': data.get('token_endpoint_auth_method', 'client_secret_basic'),
        'scopes': data.get('scopes', ['profile'])
    }
    
    # Stocker le client dans la base de données
    db.create_client(client_data)
    
    # Retourner les informations du client
    response_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'client_name': client_data['client_name'],
        'redirect_uris': client_data['redirect_uris'],
        'grant_types': client_data['grant_types'],
        'response_types': client_data['response_types'],
        'token_endpoint_auth_method': client_data['token_endpoint_auth_method']
    }
    
    logger.info(f"New client registered: {client_id}")
    
    return jsonify(response_data), 201

@app.route('/register/user', methods=['POST'])
def register_user():
    """Endpoint d'enregistrement des utilisateurs"""
    # Get client IP for rate limiting
    client_ip = request.remote_addr or 'unknown'
    
    # Check rate limit for user registration
    if not rate_limiter.is_allowed(client_ip, 'registration'):
        retry_after = rate_limiter.get_retry_after(client_ip, 'registration')
        return jsonify({
            'error': 'too_many_requests',
            'error_description': 'Too many registration attempts. Please try again later.',
            'retry_after': retry_after
        }), 429
    
    data = request.get_json()
    
    # Validation requise
    required_fields = ['username', 'password', 'email', 'name']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'error': 'invalid_request',
                'error_description': f'Missing required field: {field}'
            }), 400
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.get_user(data['username'])
    if existing_user:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Username already exists'
        }), 400
    
    # Validate password strength
    if len(data['password']) < 8:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Password must be at least 8 characters long'
        }), 400
    
    # Créer l'utilisateur avec mot de passe hashé
    user_data = user_manager.create_user(
        username=data['username'],
        password=data['password'],
        email=data['email'],
        name=data['name'],
        roles=data.get('roles', ['user'])
    )
    
    # Stocker l'utilisateur dans la base de données
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, name, roles)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_data['username'],
            user_data['password_hash'],
            user_data['email'],
            user_data['name'],
            json.dumps(user_data['roles'])
        ))
        
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error creating user: {e}")
        success = False
    finally:
        conn.close()
    
    if success:
        # Return user info without password hash
        response_data = {
            'username': user_data['username'],
            'email': user_data['email'],
            'name': user_data['name'],
            'roles': user_data['roles']
        }
        
        logger.info(f"New user registered: {user_data['username']} from IP: {client_ip}")
        return jsonify(response_data), 201
    else:
        return jsonify({
            'error': 'server_error',
            'error_description': 'Failed to create user'
        }), 500

@app.route('/.well-known/jwks.json')
def jwks():
    """Endpoint JWKS - expose la clé publique pour validation"""
    # Extract the modulus and exponent from the public key
    from cryptography.hazmat.primitives import serialization
    import base64
    
    # Load the public key
    public_key = serialization.load_pem_public_key(RSA_PUBLIC_KEY.encode())
    
    # Extract the numbers
    numbers = public_key.public_numbers()
    n = numbers.n
    e = numbers.e
    
    # Convert to base64url encoding
    def long_to_base64url(n):
        binary = n.to_bytes((n.bit_length() + 7) // 8, 'big')
        return base64.urlsafe_b64encode(binary).decode('utf-8').rstrip('=')
    
    jwks_data = {
        "keys": [{
            "kty": "RSA",
            "kid": "key-2024-01",
            "use": "sig",
            "alg": "RS256",
            "n": long_to_base64url(n),
            "e": long_to_base64url(e)
        }]
    }
    return jsonify(jwks_data)

# ================== POINT D'ENTRÉE ==================
if __name__ == '__main__':
    print(f"""
    Authorization Server (Omar) starting...
    Issuer URL: {config.ISSUER}
    JWKS Endpoint: {config.ISSUER}/.well-known/jwks.json
    Authorization Endpoint: {config.ISSUER}/authorize
    Token Endpoint: {config.ISSUER}/token
    Demo Users:
    - alice/password123 (regular user)
    - admin/admin123 (admin user)
    - bob/password456 (regular user)
    """)
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 3000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )