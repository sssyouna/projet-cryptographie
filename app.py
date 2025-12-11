"""
Resource Server API - OAuth2/OIDC Protected Endpoints
Author: Youness
Description: API protégée qui valide les JWT access tokens et applique l'autorisation
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
import jwt
from jwt import PyJWKClient
import os
from datetime import datetime, timezone
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ================== CONFIGURATION ==================
class Config:
    """Configuration OAuth2/OIDC"""
    # À coordonner avec Omar (IdP)
    ISSUER = os.getenv('OAUTH_ISSUER', 'http://localhost:3000')
    JWKS_URI = os.getenv('OAUTH_JWKS_URI', 'http://localhost:3000/.well-known/jwks.json')
    AUDIENCE = os.getenv('OAUTH_AUDIENCE', 'api://resource-server')
    ALGORITHMS = ['RS256']  # Seulement RS256, jamais "none"
    CLOCK_SKEW = 60  # Tolérance d'horloge en secondes

config = Config()

# Client JWKS avec cache automatique
jwks_client = PyJWKClient(
    config.JWKS_URI,
    cache_keys=True,
    max_cached_keys=16,
    cache_jwk_set=True,
    lifespan=3600  # Cache 1 heure
)


# ================== MIDDLEWARE D'AUTHENTIFICATION ==================

def extract_token_from_header():
    """Extrait le token Bearer du header Authorization"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def verify_jwt_token(token):
    """
    Vérifie un JWT access token
    
    Vérifie:
    - Signature avec clé publique JWKS
    - Issuer (iss)
    - Audience (aud)
    - Expiration (exp)
    - Not Before (nbf)
    - Algorithme (seulement RS256)
    
    Returns:
        dict: Payload du token décodé
    
    Raises:
        jwt.InvalidTokenError: Si token invalide
    """
    try:
        # Récupérer la clé de signature depuis JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Décoder et valider le token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=config.ALGORITHMS,
            issuer=config.ISSUER,
            audience=config.AUDIENCE,
            leeway=config.CLOCK_SKEW,  # Tolérance pour clock skew
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': True,
                'verify_iss': True,
                'require_exp': True,
                'require_iat': True
            }
        )
        
        # Log succès (sans le token!)
        logger.info(f"Token validé pour user: {payload.get('sub')}, scopes: {payload.get('scope')}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expiré")
        raise jwt.InvalidTokenError("Token expired")
    
    except jwt.InvalidAudienceError:
        logger.warning(f"Audience invalide dans le token")
        raise jwt.InvalidTokenError("Invalid audience")
    
    except jwt.InvalidIssuerError:
        logger.warning(f"Issuer invalide dans le token")
        raise jwt.InvalidTokenError("Invalid issuer")
    
    except Exception as e:
        logger.error(f"Erreur validation token: {str(e)}")
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")


def require_auth(f):
    """
    Décorateur pour protéger les endpoints
    Vérifie le token et injecte request.user
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_header()
        
        if not token:
            return jsonify({
                'error': 'invalid_token',
                'error_description': 'Missing or invalid Authorization header'
            }), 401, {'WWW-Authenticate': 'Bearer realm="api"'}
        
        try:
            payload = verify_jwt_token(token)
            
            # Injecter les infos user dans request pour usage ultérieur
            request.user = {
                'sub': payload.get('sub'),
                'email': payload.get('email'),
                'name': payload.get('name'),
                'scopes': payload.get('scope', '').split(),
                'roles': payload.get('roles', []),
                'payload': payload  # Payload complet si besoin
            }
            
            return f(*args, **kwargs)
            
        except jwt.InvalidTokenError as e:
            return jsonify({
                'error': 'invalid_token',
                'error_description': str(e)
            }), 401, {'WWW-Authenticate': 'Bearer error="invalid_token"'}
    
    return decorated


# ================== MIDDLEWARE D'AUTORISATION ==================

def require_scope(*required_scopes):
    """
    Décorateur pour vérifier les scopes OAuth2
    Usage: @require_scope('read:orders', 'write:orders')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_scopes = request.user.get('scopes', [])
            
            # Vérifier si l'utilisateur a AU MOINS UN des scopes requis
            has_scope = any(scope in user_scopes for scope in required_scopes)
            
            if not has_scope:
                return jsonify({
                    'error': 'insufficient_scope',
                    'error_description': f'Required scope: {" or ".join(required_scopes)}'
                }), 403, {
                    'WWW-Authenticate': f'Bearer error="insufficient_scope", scope="{" ".join(required_scopes)}"'
                }
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def require_role(*required_roles):
    """
    Décorateur pour vérifier les rôles
    Usage: @require_role('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_roles = request.user.get('roles', [])
            
            # Vérifier si l'utilisateur a AU MOINS UN des rôles requis
            has_role = any(role in user_roles for role in required_roles)
            
            if not has_role:
                return jsonify({
                    'error': 'forbidden',
                    'error_description': f'Required role: {" or ".join(required_roles)}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


# ================== ENDPOINTS PUBLICS ==================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check - pas d'authentification requise"""
    return jsonify({
        'status': 'healthy',
        'service': 'resource-server',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/public', methods=['GET'])
def public_endpoint():
    """Endpoint public - accessible sans token"""
    return jsonify({
        'message': 'Ceci est un endpoint public',
        'info': 'Pas d\'authentification requise',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# ================== ENDPOINTS PROTÉGÉS ==================

@app.route('/api/me', methods=['GET'])
@require_auth
@require_scope('profile', 'openid')
def get_user_info():
    """
    Récupère les informations de l'utilisateur connecté
    Scope requis: profile ou openid
    """
    return jsonify({
        'user_id': request.user['sub'],
        'email': request.user['email'],
        'name': request.user['name'],
        'scopes': request.user['scopes'],
        'roles': request.user['roles']
    })


@app.route('/api/orders', methods=['GET'])
@require_auth
@require_scope('read:orders')
def get_orders():
    """
    Liste les commandes de l'utilisateur
    Scope requis: read:orders
    """
    # Simulation de données
    orders = [
        {
            'id': 'order-001',
            'user_id': request.user['sub'],
            'product': 'Laptop',
            'amount': 1200.00,
            'status': 'delivered',
            'date': '2024-12-01'
        },
        {
            'id': 'order-002',
            'user_id': request.user['sub'],
            'product': 'Mouse',
            'amount': 25.99,
            'status': 'pending',
            'date': '2024-12-08'
        }
    ]
    
    return jsonify({
        'orders': orders,
        'total': len(orders)
    })


@app.route('/api/orders', methods=['POST'])
@require_auth
@require_scope('write:orders')
def create_order():
    """
    Crée une nouvelle commande
    Scope requis: write:orders
    """
    data = request.get_json()
    
    # Validation basique
    if not data or 'product' not in data or 'amount' not in data:
        return jsonify({
            'error': 'invalid_request',
            'error_description': 'Missing required fields: product, amount'
        }), 400
    
    # Simulation de création
    new_order = {
        'id': 'order-003',
        'user_id': request.user['sub'],
        'product': data['product'],
        'amount': data['amount'],
        'status': 'pending',
        'date': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Commande créée: {new_order['id']} par user: {request.user['sub']}")
    
    return jsonify(new_order), 201


@app.route('/api/admin/stats', methods=['GET'])
@require_auth
@require_role('admin')
def get_admin_stats():
    """
    Statistiques admin
    Role requis: admin
    """
    stats = {
        'total_users': 150,
        'total_orders': 1234,
        'revenue': 125000.50,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    return jsonify(stats)


@app.route('/api/admin/users', methods=['GET'])
@require_auth
@require_scope('admin:read')
@require_role('admin')
def get_all_users():
    """
    Liste tous les utilisateurs (admin seulement)
    Scope requis: admin:read
    Role requis: admin
    """
    users = [
        {'id': 'user-001', 'email': 'user1@example.com', 'status': 'active'},
        {'id': 'user-002', 'email': 'user2@example.com', 'status': 'active'},
        {'id': 'user-003', 'email': 'user3@example.com', 'status': 'inactive'}
    ]
    
    return jsonify({
        'users': users,
        'total': len(users)
    })


# ================== GESTION D'ERREURS ==================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'not_found',
        'error_description': 'Resource not found'
    }), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'error': 'server_error',
        'error_description': 'Internal server error'
    }), 500


# ================== POINT D'ENTRÉE ==================

if __name__ == '__main__':
    print(f"""
    ╔════════════════════════════════════════════════════════╗
    ║        Resource Server API - OAuth2 Protected          ║
    ╠════════════════════════════════════════════════════════╣
    ║  Issuer: {config.ISSUER}
    ║  Audience: {config.AUDIENCE}
    ║  JWKS: {config.JWKS_URI}
    ╚════════════════════════════════════════════════════════╝
    
    Endpoints disponibles:
    - GET  /api/health        (public)
    - GET  /api/public        (public)
    - GET  /api/me            (scope: profile)
    - GET  /api/orders        (scope: read:orders)
    - POST /api/orders        (scope: write:orders)
    - GET  /api/admin/stats   (role: admin)
    - GET  /api/admin/users   (scope: admin:read + role: admin)
    """)
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )