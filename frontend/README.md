# Resource Server API Frontend Dashboard

A web interface for interacting with the Resource Server API endpoints.

## Features

- Interactive dashboard for all API endpoints
- Token management for authentication
- Tabbed interface for different endpoint categories
- Real-time API response display
- Error testing capabilities

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the frontend server:
   ```bash
   python server.py
   ```

3. Visit `http://localhost:8080` in your browser

## Usage

1. Enter your access token and admin token in the "Authentication Tokens" section
2. Click "Save Tokens" to store them locally
3. Navigate between tabs to test different endpoints:
   - **Public Endpoints**: Health check and public endpoint
   - **User Endpoints**: User info, orders listing, and order creation
   - **Admin Endpoints**: Admin stats and user listing
   - **Error Testing**: Test error responses

## API Endpoints

### Public Endpoints
- `GET /api/health` - Service health check
- `GET /api/public` - Public information

### User Endpoints
- `GET /api/me` - User profile information (requires `profile` or `openid` scope)
- `GET /api/orders` - List user orders (requires `read:orders` scope)
- `POST /api/orders` - Create new order (requires `write:orders` scope)

### Admin Endpoints
- `GET /api/admin/stats` - System statistics (requires `admin` role)
- `GET /api/admin/users` - List all users (requires `admin:read` scope and `admin` role)

### Error Testing
- Test endpoints without tokens to see 401 responses
- Test with invalid tokens to see authentication errors