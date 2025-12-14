# OAuth2 System - Complete Implementation

> **Author:** Youness  
> **Project:** OAuth2/OIDC System with Authorization Server, Resource Server, and Client Application  
> **Description:** Complete OAuth2 implementation with all components: Authorization Server, Resource Server API, and Client Dashboard

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Project Structure](#project-structure)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [API Endpoints](#api-endpoints)
8. [Authentication & Authorization](#authentication--authorization)
9. [Security](#security)

---

## Overview

This project is a complete OAuth2 implementation with three main components:

1. **Authorization Server** - Handles user authentication and token issuance
2. **Resource Server** - Protects API resources with JWT token validation
3. **Client Application** - Provides a dashboard for interacting with the OAuth2 system

The system demonstrates the complete OAuth2 Authorization Code flow with JWT tokens for secure API access.

---

## System Architecture

```
┌────────────────┐    ┌────────────────────┐    ┌─────────────────┐
│   Client App   │    │  Authorization     │    │   Resource      │
│   (Badr)       │    │  Server (Omar)     │    │   Server        │
│                │    │                    │    │                 │
└────────────────┘    └────────────────────┘    └─────────────────┘
       │                      │                         ▲
       │ 1. Redirect to       │                         │
       │    /authorize        │                         │
       │◀─────────────────────┘                         │
       │                                                │
       │ 2. User login & consent                       │
       │                                                │
       │ 3. Receive authorization code                  │
       │                                                │
       │ 4. Exchange code → access_token                │
       │───────────────────────────────────────────────▶│
       │                                                │
       │ 5. Call API with Bearer token                  │
       │────────────────────────────────────────────────────────────────▶
       │                                                │
       │ 6. Validate token (signature, exp, aud, scope) │
       │                                                │
       │◀────────────────────────────────────────────────────────────────
       │ 7. Return protected resource                   │
```

## Project Structure

```
project/
├── app.py                 # Resource Server API implementation
├── auth_server.py         # Authorization Server implementation
├── db.py                  # Database management functions
├── user_management.py     # User management functions
├── start_all.py           # Script to start all system components
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable examples
├── setup_project.ps1      # Automated setup script
├── QUICKSTART.md         # Quick start guide
├── oauth2.db             # SQLite database
│
├── docs/
│   ├── API.md            # Detailed API documentation
│   └── SECURITY.md       # Security documentation
│
├── frontend/
│   ├── index.html         # Main dashboard page
│   ├── omar_auth_server.html  # Authorization Server interface
│   ├── resource_server.html   # Resource Server interface
│   ├── badr_client_app.html   # Client application interface
│   ├── app.js             # Client-side JavaScript
│   ├── styles.css         # CSS styling
│   └── server.py          # Simple web server for frontend
│
└── venv/                 # Virtual environment (gitignored)
```

---

### Token Validation Flow

```
1. Client sends: Authorization: Bearer <access_token>
                       │
                       ▼
2. Resource Server extracts the token
                       │
                       ▼
3. Decode JWT header to get 'kid'
                       │
                       ▼
4. Retrieve public key from JWKS (with cache)
                       │
                       ▼
5. Verify signature + iss + aud + exp + nbf
                       │
                  ┌────┴────┐
                  │         │
             Valid     Invalid
                  │         │
                  ▼         ▼
          6. Verify     Return 401
             scopes         │
                  │         │
             ┌────┴────┐    │
             │         │    │
        Sufficient  Insufficient
             │         │    │
             ▼         ▼    │
     Return 200   Return 403│
                             │
                             ▼
                   WWW-Authenticate header
```

---

## Installation

### Prerequisites

- Python 3.9+
- pip
- virtualenv (recommended)

### Automated Setup (Windows)

On Windows, you can use the automated setup script:

```powershell
# Run the setup script
./setup_project.ps1
```

This script will:
- Create the project structure
- Set up a virtual environment
- Install dependencies
- Create the .env file from .env.example

### Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate the environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy configuration
cp .env.example .env
# On Windows:
copy .env.example .env

# 5. Edit .env with Omar's values (IdP)
nano .env
# On Windows:
notepad .env
```

---

## Configuration

### Variables d'environnement (.env)

```bash
# Flask
FLASK_ENV=development
PORT=5000

# OAuth2/OIDC - À OBTENIR D'OMAR
OAUTH_ISSUER=http://localhost:3000
OAUTH_JWKS_URI=http://localhost:3000/.well-known/jwks.json
OAUTH_AUDIENCE=api://resource-server
```

### Coordination avec Omar (Authorization Server)

**Avant de démarrer, tu DOIS obtenir d'Omar :**

| Info nécessaire | Exemple | Description |
|----------------|---------|-------------|
| `OAUTH_ISSUER` | `http://localhost:3000` | URL de base de l'IdP |
| `OAUTH_JWKS_URI` | `http://localhost:3000/.well-known/jwks.json` | Endpoint des clés publiques |
| `OAUTH_AUDIENCE` | `api://resource-server` | Identifiant de ton API dans les tokens |
| Scopes disponibles | `profile`, `read:orders`, `write:orders` | Liste des scopes OAuth2 |
| Structure des claims | `sub`, `email`, `roles`, `scope` | Format du payload JWT |

---

## Running the Application

### Development Mode

#### Running Individual Components
```bash
# Run Authorization Server (Omar)
python auth_server.py

# Run Resource Server API
python app.py

# Run Frontend Dashboard
python frontend/server.py
```

#### Running All Components
To start the complete system with all components (Authorization Server, Resource Server, and Frontend), use the start script:

```bash
# On Windows
python start_all.py

# On Linux/Mac
python3 start_all.py
```

This script automatically starts:
- **Authorization Server (Omar)** on `http://localhost:3000`
- **Resource Server API** on `http://localhost:5000`
- **Frontend Dashboard** on `http://localhost:8080`

### Production Mode (with waitress for Windows compatibility)

The project uses `waitress` for Windows compatibility in production:

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run with waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

The API will be accessible on `http://localhost:5000`

---

## API Endpoints

### Public Endpoints (no authentication required)

#### `GET /api/health`
Service health check

**Response:**
```json
{
  "status": "healthy",
  "service": "resource-server",
  "timestamp": "2024-12-10T12:00:00Z"
}
```

#### `GET /api/public`
Public demonstration endpoint

**Response:**
```json
{
  "message": "This is a public endpoint",
  "info": "No authentication required"
}
```

---

### Protected Endpoints

#### `GET /api/me`
Retrieve information of the authenticated user

**Required Scope:** `profile` or `openid`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "user_id": "user-123",
  "email": "user@example.com",
  "name": "John Doe",
  "scopes": ["profile", "read:orders"],
  "roles": ["user"]
}
```

**Errors:**
- `401` - Missing or invalid token
- `403` - Insufficient scope

---

#### `GET /api/orders`
List user's orders

**Required Scope:** `read:orders`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "orders": [
    {
      "id": "order-001",
      "user_id": "user-123",
      "product": "Laptop",
      "amount": 1200.00,
      "status": "delivered",
      "date": "2024-12-01"
    }
  ],
  "total": 1
}
```

---

#### `POST /api/orders`
Create a new order

**Required Scope:** `write:orders`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body:**
```json
{
  "product": "Mouse",
  "amount": 25.99
}
```

**Response (201):**
```json
{
  "id": "order-003",
  "user_id": "user-123",
  "product": "Mouse",
  "amount": 25.99,
  "status": "pending",
  "date": "2024-12-10T14:30:00Z"
}
```

**Errors:**
- `400` - Missing required fields
- `401` - Invalid token
- `403` - Insufficient scope

---

#### `GET /api/admin/stats`
Administrator statistics

**Required Role:** `admin`

**Response (200):**
```json
{
  "total_users": 150,
  "total_orders": 1234,
  "revenue": 125000.50,
  "timestamp": "2024-12-10T14:30:00Z"
}
```

---

#### `GET /api/admin/users`
List all users (admin only)

**Required Scope:** `admin:read`  
**Required Role:** `admin`

**Response (200):**
```json
{
  "users": [
    {
      "id": "user-001",
      "email": "user1@example.com",
      "status": "active"
    }
  ],
  "total": 1
}
```

---

## Authentication & Authorization

### JWT Token Format

Tokens must contain the following claims:

```json
{
  "iss": "http://localhost:3000",
  "aud": "api://resource-server",
  "sub": "user-123",
  "email": "user@example.com",
  "name": "John Doe",
  "scope": "profile read:orders write:orders",
  "roles": ["user"],
  "iat": 1702213200,
  "exp": 1702216800,
  "nbf": 1702213200
}
```

### Token Validation

The Resource Server automatically verifies:

1. **Signature** - with public key from JWKS
2. **Issuer (iss)** - must match `OAUTH_ISSUER`
3. **Audience (aud)** - must contain `OAUTH_AUDIENCE`
4. **Expiration (exp)** - token not expired
5. **Not Before (nbf)** - token already valid
6. **Algorithm** - only RS256 (not "none")

### OAuth2 Scopes

| Scope | Permission |
|-------|-----------|
| `profile` or `openid` | Access to user info (`/api/me`) |
| `read:orders` | Read orders |
| `write:orders` | Create/modify orders |
| `admin:read` | Read admin data |

### Roles

| Role | Access |
|------|-------|
| `user` | Standard user endpoints |
| `admin` | Admin endpoints (`/api/admin/*`) |

---

## Tests

### Lancer les tests

```bash
# Tous les tests
pytest tests/ -v

# Avec coverage
pytest tests/ --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_auth.py -v

# Ignorer les tests skippés
pytest tests/ -v -k "not skip"
```

### Tests implémentés

- Endpoints publics accessibles
- Endpoints protégés → 401 sans token
- Token malformé → 401
- Token expiré → 401 (avec mock)
- Scope insuffisant → 403 (avec mock)
- Role insuffisant → 403 (avec mock)
- Algorithm "none" rejeté
- Tokens jamais loggés

### Mock JWKS pour tests

Pour tester avec de vrais tokens, vous devez mocker le JWKS client:

```python
@pytest.fixture(autouse=True)
def mock_jwks(mocker):
    mock_key = mocker.Mock()
    mock_key.key = your_public_key
    mocker.patch('app.jwks_client.get_signing_key_from_jwt', 
                 return_value=mock_key)
```

---

## Security

### Implemented Security Measures

1. **Strict JWT Validation**
   - RSA Signature (RS256)
   - Issuer, audience, expiration verification
   - Rejection of "none" algorithm

2. **Standard OAuth2 Error Handling (RFC 6750)**
   - 401 with `WWW-Authenticate` header
   - 403 with required scope description
   - Standardized error messages

3. **No Token Logging**
   - Anonymized logs (user ID only)
   - Tokens never written in plain text

4. **Intelligent JWKS Cache**
   - 1 hour TTL
   - Automatic refresh

5. **Clock Skew Tolerance**
   - ±60 seconds for exp/nbf

6. **Configured CORS**
   - Only for authorized origins (in production)

### Best Practices for Production

- [ ] **Mandatory HTTPS** - Use TLS/SSL
- [ ] **Rate limiting** - Limit requests per IP/user
- [ ] **Centralized logging** - ELK stack, Datadog
- [ ] **Monitoring** - Metrics on auth success/fail
- [ ] **Introspection** - `/introspect` endpoint to check revocation
- [ ] **Token binding** - Bind token to client (DPoP)
- [ ] **Short-lived tokens** - Access tokens 15-30 min
- [ ] **Key rotation** - Process for JWKS rotation

---

## Integration with Other Components

### With Authorization Server (Omar)

**You need:**
- The JWKS endpoint URL
- The exact issuer
- The list of scopes
- The claims structure

**You provide:**
- The audience to put in tokens (`api://resource-server`)
- The scopes needed for each endpoint
- OAuth2 error format

### With Client App (Badr)

**You provide:**
- Endpoint documentation
- Required scopes per endpoint
- curl/Postman request examples
- Error format

**You need:**
- Confirmation that the client gets the right scopes
- Endpoint-by-endpoint integration tests

---

## Support & Debugging

### Common Issues

**Error: "Invalid issuer"**
```
Solution: Verify that OAUTH_ISSUER exactly matches the 'iss' claim in the token
```

**Error: "Invalid audience"**
```
Solution: Verify that OAUTH_AUDIENCE is in the 'aud' claim of the token
```

**Error: "Unable to find a signing key"**
```
Solution: Verify that OAUTH_JWKS_URI is accessible and returns the keys
Test: curl http://localhost:3000/.well-known/jwks.json
```

**Error: "Token expired"**
```
Solution: Token too old. Check system clocks (NTP)
Clock skew tolerance: ±60s
```

### Useful Logs

```bash
# Enable debug logs
export LOG_LEVEL=DEBUG
python app.py

# Check token validation
# Logs show: user_id, scopes, but NEVER the complete token
```

---

## References

- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [RFC 6750 - Bearer Token Usage](https://tools.ietf.org/html/rfc6750)
- [RFC 7519 - JWT](https://tools.ietf.org/html/rfc7519)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

## TODO

- [ ] Get OAuth2 config from Omar
- [ ] Integration tests with IdP
- [ ] Integration tests with Client
- [ ] `/introspect` endpoint for revocation
- [ ] Prometheus metrics
- [ ] OpenAPI/Swagger documentation
- [ ] CI/CD pipeline

---

**Author:** Youness  
**Date:** December 2024  
**Version:** 1.0