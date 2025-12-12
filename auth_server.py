# Clé publique correspondante (à exposer via /.well-known/jwks.json)
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyTeRtlcFpV+V8/FfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFf
GfFfG
-----END PUBLIC KEY-----"""

# ================== UTILITAIRES ==================
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
    
    # En production, utiliser PyJWT avec une vraie clé privée
    token = jwt.encode(payload, RSA_PRIVATE_KEY, algorithm='RS256')
    return token

def generate_authorization_code(client_id, user_info, scopes, redirect_uri):
    """Génère un code d'autorisation temporaire"""
    code = str(uuid.uuid4())
    auth_requests[code] = {
        'client_id': client_id,
        'user_info': user_info,
        'scopes': scopes,
        'redirect_uri': redirect_uri,
        'expires_at': datetime.utcnow() + timedelta(seconds=config.AUTH_CODE_EXPIRY)
    }
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
    # Paramètres requis
    response_type = request.args.get('response_type')
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    scope = request.args.get('scope', 'openid profile')
    state = request.args.get('state')
    
    logger.info(f"Authorization request received: client_id={client_id}")
    
    # Validation basique
    if response_type != 'code':
        error_params = f'?error=unsupported_response_type&error_description=Only+code+response+type+supported'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params)
    
    if client_id not in clients:
        error_params = f'?error=unauthorized_client&error_description=Invalid+client_id'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params)
    
    # Vérifier redirect_uri
    if redirect_uri not in clients[client_id]['redirect_uris']:
        error_params = f'?error=invalid_request&error_description=Invalid+redirect_uri'
        if state:
            error_params += f'&state={state}'
        return redirect(redirect_uri + error_params)
    
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
    login_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Omar Auth Server</title>
        <style>
            body {{ 
                font-family: 'Comic Sans MS', cursive, sans-serif; 
                max-width: 450px; 
                margin: 30px auto; 
                padding: 25px; 
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            .login-form {{ 
                border: 3px dashed #1e3c72; 
                padding: 25px; 
                border-radius: 15px; 
                background: white;
                text-align: center;
            }}
            h2 {{ 
                color: #1e3c72; 
                margin-top: 0;
                font-size: 28px;
            }}
            .client-info {{
                background: #e8f4f8;
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #1e3c72;
            }}
            input {{ 
                width: 100%; 
                padding: 12px; 
                margin: 12px 0; 
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                box-sizing: border-box;
            }}
            input:focus {{
                border-color: #1e3c72;
                outline: none;
                box-shadow: 0 0 5px rgba(30, 60, 114, 0.3);
            }}
            button {{ 
                background: #1e3c72; 
                color: white; 
                padding: 14px 25px; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                transition: all 0.3s;
            }}
            button:hover {{ 
                background: #2a5298; 
                transform: scale(1.05);
            }}
            .demo-creds {{
                background: #fff3cd;
                padding: 15px;
                border-radius: 10px;
                margin-top: 20px;
                border: 1px dashed #ffc107;
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
            <div class="fun-icon">🔐</div>
            <h2>Hey there! 👋</h2>
            <p>Looks like you want to log in to <strong>{auth_request['client_id']}</strong></p>
            
            <div class="client-info">
                <p>🔧 They want to access:</p>
                <p><strong>{auth_request['scope'] or 'profile openid'}</strong></p>
            </div>
            
            <form method="POST" action="/authenticate">
                <input type="hidden" name="auth_req_id" value="{auth_req_id}">
                <label>👤 Username:</label>
                <input type="text" name="username" placeholder="Type your username here..." required>
                <label>🔑 Password:</label>
                <input type="password" name="password" placeholder="Shhh... secret password..." required>
                <button type="submit">🎉 Let me in!</button>
            </form>
            
            <div class="demo-creds">
                <p>💡 Hint: Try <strong>alice</strong> with <strong>password123</strong></p>
                <p>(Don't worry, we won't tell anyone! 😇)</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return login_html

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Authentifie l'utilisateur et génère le code d'autorisation"""
    auth_req_id = request.form.get('auth_req_id')
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not auth_req_id or auth_req_id not in auth_requests:
        return "Invalid authorization request", 400
    
    auth_request = auth_requests[auth_req_id]
    
    # Vérifier les identifiants
    if username not in users or users[username]['password'] != password:
        # Return to login page with error
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Failed - Omar Auth Server</title>
            <style>
                body {{ 
                    font-family: 'Comic Sans MS', cursive, sans-serif; 
                    max-width: 450px; 
                    margin: 30px auto; 
                    padding: 25px; 
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }}
                .error {{ 
                    color: #721c24; 
                    padding: 20px; 
                    background: #f8d7da; 
                    border-radius: 10px;
                    border: 3px dashed #f5c6cb;
                    text-align: center;
                }}
                h2 {{ 
                    color: #721c24; 
                    margin-top: 0;
                    font-size: 28px;
                }}
                a {{ 
                    color: #1e3c72; 
                    text-decoration: none; 
                    font-weight: bold;
                    padding: 10px 20px;
                    background: #e8f4f8;
                    border-radius: 8px;
                    display: inline-block;
                    margin-top: 15px;
                    transition: all 0.3s;
                }}
                a:hover {{
                    background: #d1ecf1;
                    transform: scale(1.05);
                }}
                .fun-icon {{
                    font-size: 40px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <div class="fun-icon">😢</div>
                <h2>Oops! Something went wrong...</h2>
                <p>Looks like your username or password didn't match.</p>
                <p>Don't worry, it happens to the best of us! 🤷‍♂️</p>
                <p><a href="/login?auth_req_id={auth_req_id}">← Try again</a></p>
            </div>
        </body>
        </html>
        """
        return error_html
    
    # Authentification réussie
    user_info = {
        'username': username,
        'email': users[username]['email'],
        'name': users[username]['name'],
        'roles': users[username]['roles']
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
    redirect_params = f"?code={auth_code}"
    if auth_request['state']:
        redirect_params += f"&state={auth_request['state']}"
    
    # Nettoyer la demande d'autorisation
    del auth_requests[auth_req_id]
    
    return redirect(auth_request['redirect_uri'] + redirect_params)

@app.route('/token', methods=['POST'])
def token():
    """Endpoint de token - échange le code contre des tokens"""
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    redirect_uri = request.form.get('redirect_uri')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    
    logger.info(f"Token request received: grant_type={grant_type}, client_id={client_id}")
    
    # Validation
    if grant_type != 'authorization_code':
        return jsonify({
            'error': 'unsupported_grant_type',
            'error_description': 'Only authorization_code grant type supported'
        }), 400
    
    if not code or code not in auth_requests:
        return jsonify({
            'error': 'invalid_grant',
            'error_description': 'Invalid authorization code'
        }), 400
    
    auth_data = auth_requests[code]
    
    # Vérifier client_id
    if client_id != auth_data['client_id']:
        return jsonify({
            'error': 'invalid_client',
            'error_description': 'Client ID mismatch'
        }), 400
    
    # Vérifier redirect_uri
    if redirect_uri != auth_data['redirect_uri']:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Redirect URI mismatch'
        }), 400
    
    # Générer les tokens
    access_token = generate_access_token(auth_data['user_info'], auth_data['scopes'])
    refresh_token = str(uuid.uuid4())  # En production, stocker et valider
    
    # Nettoyer le code d'autorisation
    del auth_requests[code]
    
    response_data = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': config.TOKEN_EXPIRY,
        'scope': ' '.join(auth_data['scopes'])
    }
    
    # Ajouter refresh_token si demandé
    if 'offline_access' in auth_data['scopes']:
        response_data['refresh_token'] = refresh_token
    
    logger.info(f"Token issued for user: {auth_data['user_info']['username']}")
    
    return jsonify(response_data)

@app.route('/.well-known/jwks.json')
def jwks():
    """Endpoint JWKS - expose la clé publique pour validation"""
    # En production, retourner la vraie clé publique au format JWKS
    jwks_data = {
        "keys": [{
            "kty": "RSA",
            "kid": "key-2024-01",
            "use": "sig",
            "alg": "RS256",
            "n": "yTeRtlcFpV-V8_FfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGfFfGf......TRUNCATED......",
            "e": "AQAB"
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