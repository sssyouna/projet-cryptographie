# Resource Server - Mesures de Sécurité

## Vue d'ensemble

Ce document détaille toutes les mesures de sécurité implémentées dans le Resource Server, ainsi que les limites connues et les recommandations pour un déploiement en production.

---

## Mesures de Sécurité Implémentées

### 1. Validation Stricte des JWT

#### 1.1 Vérification de la Signature

**Implémentation:**
- Utilisation de RSA (RS256) uniquement
- Récupération des clés publiques depuis le JWKS endpoint
- Vérification cryptographique de la signature

**Code:**
```python
signing_key = jwks_client.get_signing_key_from_jwt(token)
payload = jwt.decode(
    token,
    signing_key.key,
    algorithms=['RS256'],  # Seulement RS256
    ...
)
```

**Protection contre:**
- Tokens forgés
- Algorithm confusion attack (alg: "none")
- Tokens signés avec mauvaise clé

#### 1.2 Vérification de l'Issuer (iss)

**Implémentation:**
```python
issuer=config.ISSUER  # http://localhost:3000
```

**Protection contre:**
- Tokens émis par un IdP malveillant
- Token replay d'un autre système

**Erreur si invalide:**
```json
{
  "error": "invalid_token",
  "error_description": "Invalid issuer"
}
```

#### 1.3 Vérification de l'Audience (aud)

**Implémentation:**
```python
audience=config.AUDIENCE  # api://resource-server
```

**Protection contre:**
- Tokens destinés à d'autres APIs
- Token reuse sur services différents

**Pourquoi c'est critique:**
Un token destiné à l'API "payments" ne doit pas fonctionner sur l'API "orders".

#### 1.4 Vérification de l'Expiration (exp)

**Implémentation:**
```python
options={'verify_exp': True, 'require_exp': True},
leeway=60  # Tolérance de 60 secondes
```

**Protection contre:**
- Utilisation de tokens expirés
- Token replay après invalidation

**Clock Skew Tolerance:**
±60 secondes pour gérer les différences d'horloge entre serveurs.

#### 1.5 Vérification Not Before (nbf)

**Implémentation:**
```python
options={'verify_nbf': True}
```

**Protection contre:**
- Utilisation prématurée de tokens
- Tokens schedulés pour plus tard utilisés maintenant

#### 1.6 Rejection de l'Algorithme "none"

**Implémentation:**
```python
algorithms=['RS256']  # Liste blanche explicite
```

**Protection contre:**
- CVE-2015-9235 (JWT alg:none vulnerability)
- Bypass de signature

**Test:**
```python
def test_algorithm_none_rejected(client):
    malicious_token = "eyJhbGciOiJub25lIn0.payload."
    response = client.get('/api/me', 
                          headers={'Authorization': f'Bearer {malicious_token}'})
    assert response.status_code == 401
```

---

### 2. Gestion Sécurisée du JWKS

#### 2.1 Cache Intelligent

**Implémentation:**
```python
jwks_client = PyJWKClient(
    config.JWKS_URI,
    cache_keys=True,
    max_cached_keys=16,
    lifespan=3600  # Cache 1 heure
)
```

**Avantages:**
- Réduit latence (pas de fetch à chaque requête)
- Réduit charge sur l'IdP
-  Refresh automatique après expiration

**Protection contre:**
-  DoS sur l'IdP
-  Latence excessive

#### 2.2 Rotation de Clés

**Gestion:**
- Si `kid` inconnu → refetch JWKS automatiquement
- Si toujours invalide → 401

**Workflow:**
```
1. Receive token with kid="new-key-2024"
2. Check cache → Not found
3. Fetch JWKS from IdP
4. Update cache
5. Verify signature with new key
```

---

### 3. Autorisation (Scopes & Roles)

#### 3.1 Vérification des Scopes OAuth2

**Implémentation:**
```python
def require_scope(*required_scopes):
    user_scopes = request.user.get('scopes', [])
    has_scope = any(scope in user_scopes for scope in required_scopes)
    if not has_scope:
        return 403
```

**Règle:**
L'utilisateur doit avoir **AU MOINS UN** des scopes requis.

**Exemple:**
- Endpoint requiert: `read:orders` OU `admin:read`
- User a: `read:orders`
-  Autorisé

#### 3.2 Vérification des Rôles

**Implémentation:**
```python
def require_role(*required_roles):
    user_roles = request.user.get('roles', [])
    has_role = any(role in user_roles for role in required_roles)
    if not has_role:
        return 403
```

**Usage combiné:**
```python
@require_scope('admin:read')
@require_role('admin')
def get_admin_data():
    # User doit avoir le scope ET le role
```

---

### 4. Gestion des Erreurs OAuth2 (RFC 6750)

#### 4.1 Format Standard des Erreurs

**401 Unauthorized:**
```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token", error_description="Token expired"
Content-Type: application/json

{
  "error": "invalid_token",
  "error_description": "Token expired"
}
```

**403 Forbidden:**
```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope", scope="read:orders"
Content-Type: application/json

{
  "error": "insufficient_scope",
  "error_description": "Required scope: read:orders"
}
```

#### 4.2 Types d'Erreurs

| Erreur | Code | Quand | WWW-Authenticate |
|--------|------|-------|------------------|
| `invalid_token` | 401 | Token absent, invalide, expiré, signature fail | `Bearer error="invalid_token"` |
| `insufficient_scope` | 403 | Scope manquant | `Bearer error="insufficient_scope", scope="..."` |
| `forbidden` | 403 | Role manquant | N/A |

---

### 5. Protection des Données Sensibles

#### 5.1 Jamais Logger les Tokens

**Implémentation:**
```python
#  BON
logger.info(f"Token validé pour user: {payload.get('sub')}, scopes: {payload.get('scope')}")

#  MAUVAIS - JAMAIS FAIRE ÇA
logger.info(f"Token reçu: {token}")  # INTERDIT
```

**Test:**
```python
def test_token_not_logged(client, caplog):
    fake_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.sensitive.data"
    client.get('/api/me', headers={'Authorization': f'Bearer {fake_token}'})
    
    # Vérifier qu'aucun log ne contient le token
    for record in caplog.records:
        assert fake_token not in record.message
```

#### 5.2 Logs Anonymisés

**Ce qui est loggé:**
-  `sub` (user ID)
-  `scopes` demandés
-  Endpoint appelé
-  Status code
-  Timestamp

**Ce qui n'est JAMAIS loggé:**
-  Token complet
-  Token partiel
-  Payload JWT complet (contient possiblement des PII)

---

### 6. CORS (Cross-Origin Resource Sharing)

#### 6.1 Configuration

**Développement:**
```python
CORS(app)  # Permissif pour dev
```

**Production (recommandé):**
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://app.example.com"],  # Seulement origines autorisées
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Authorization", "Content-Type"],
        "expose_headers": ["Content-Length"],
        "max_age": 3600
    }
})
```

---

### 7. Sécurité des Headers

#### 7.1 WWW-Authenticate

**Toujours présent sur 401:**
```python
return jsonify(...), 401, {'WWW-Authenticate': 'Bearer realm="api"'}
```

**Conforme RFC 6750:** Informe le client du type d'authentification requis.

#### 7.2 Content-Type

Toujours `application/json` pour les réponses API.

---

### 8. Validation des Entrées

#### 8.1 Validation des Champs Requis

**Exemple:**
```python
data = request.get_json()
if not data or 'product' not in data or 'amount' not in data:
    return jsonify({'error': 'invalid_request', ...}), 400
```

#### 8.2 Sanitization

**Pour production, ajouter:**
- Validation des types (`isinstance()`)
- Validation des formats (email, montants)
- Limites de longueur
- Escape SQL/HTML si nécessaire

---

## Limites Connues & Risques

### 1. Pas de Révocation de Tokens

**Limitation actuelle:**
- Les access tokens sont valides jusqu'à expiration (`exp`)
- Pas d'endpoint `/introspect` implémenté
- Pas de blacklist de tokens

**Risque:**
Si un token est volé, il reste valide jusqu'à expiration.

**Mitigation:**
-  Tokens short-lived (15-30 min recommandé)
- À implémenter: Endpoint d'introspection
- À implémenter: Blacklist/revocation list

**Implémentation future:**
```python
@app.route('/api/introspect', methods=['POST'])
def introspect_token():
    # Vérifier si token révoqué
    # Retourner {active: true/false}
```

---

### 2. Pas de Rate Limiting

**Limitation actuelle:**
Aucune limite sur le nombre de requêtes.

**Risque:**
- DoS par spam de requêtes
- Brute force sur tokens
- Abus des ressources

**Mitigation recommandée:**
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('Authorization', 'anonymous'),
    default_limits=["1000 per day", "100 per hour"]
)

@app.route('/api/orders')
@limiter.limit("30 per minute")
def get_orders():
    ...
```

---

### 3. Pas de HTTPS (Dev uniquement)

**Limitation actuelle:**
HTTP en développement.

**Risque en production:**
-  Tokens transmis en clair
-  Man-in-the-middle attacks
-  Sniffing réseau

**Mitigation pour PROD:**
```python
# Force HTTPS
from flask_talisman import Talisman
Talisman(app, force_https=True)
```

**Pour dev, simuler HTTPS:**
```bash
# Générer certificat self-signed
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Lancer Flask avec SSL
python app.py --cert=cert.pem --key=key.pem
```

---

### 4. Pas de Monitoring Temps Réel

**Limitation actuelle:**
Logs basiques seulement.

**Risque:**
Difficile de détecter:
- Attaques en cours
- Anomalies d'utilisation
- Pics de trafic

**Mitigation recommandée:**
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog / New Relic

**Métriques à suivre:**
- Taux de succès auth (%)
- Taux d'erreurs 401/403
- Latence de validation JWT
- Nombre d'appels JWKS
- Distribution des scopes utilisés

---

### 5. Pas de Protection Avancée Contre Replay

**Limitation actuelle:**
Token replay est possible pendant la durée de vie du token.

**Risque:**
Si un attaquant intercepte un token, il peut le réutiliser.

**Mitigations possibles:**

#### 5.1 Token Binding
Lier le token au client (IP, TLS certificate).

#### 5.2 DPoP (Demonstration of Proof-of-Possession)
Token lié à une clé privée du client.

```http
Authorization: DPoP <access_token>
DPoP: <proof_jwt>
```

#### 5.3 Nonce/JTI Tracking
Tracker les `jti` (JWT ID) déjà utilisés.

```python
used_tokens = set()  # Ou Redis

def verify_jwt_token(token):
    payload = jwt.decode(...)
    jti = payload.get('jti')
    
    if jti in used_tokens:
        raise jwt.InvalidTokenError("Token already used")
    
    used_tokens.add(jti)
    return payload
```

---

### 6. Pas de Multi-Tenant Isolation

**Limitation actuelle:**
Pas de séparation par tenant/organisation.

**Risque:**
Dans un système multi-tenant, un user d'une org pourrait accéder aux données d'une autre.

**Mitigation:**
```python
@app.route('/api/orders')
@require_auth
def get_orders():
    tenant_id = request.user['tenant_id']
    # Filter by tenant
    orders = Order.query.filter_by(
        user_id=request.user['sub'],
        tenant_id=tenant_id
    ).all()
```

---

### 7. Stockage Simplifié des Données

**Limitation actuelle:**
Données en mémoire (exemples hardcodés).

**Risque:**
Perte des données au redémarrage.

**Pour production:**
- Base de données (PostgreSQL, MySQL)
- Séparation des données par user
- Chiffrement at-rest pour données sensibles

---

## Recommandations pour Production

### Checklist Sécurité Pré-Déploiement

#### Obligatoire

- [ ] **HTTPS uniquement** - Certificat SSL/TLS valide
- [ ] **Variables d'environnement sécurisées** - Pas de secrets en dur
- [ ] **Rate limiting** - Limiter requêtes par IP/user
- [ ] **Logging sécurisé** - Jamais de tokens, PII minimisé
- [ ] **Monitoring** - Alertes sur anomalies
- [ ] **CORS restrictif** - Seulement origines autorisées
- [ ] **Validation stricte des inputs** - Sanitization + validation
- [ ] **Headers de sécurité** - CSP, X-Frame-Options, etc.

#### Fortement Recommandé

- [ ] **Token introspection** - Endpoint pour vérifier révocation
- [ ] **Short-lived tokens** - Access tokens 15-30 min max
- [ ] **Refresh token rotation** - Émis par IdP, pas géré ici
- [ ] **Audit logs** - Logs d'accès séparés
- [ ] **WAF** - Web Application Firewall (Cloudflare, AWS WAF)
- [ ] **Secret rotation** - Process pour rotation JWKS keys
- [ ] **Penetration testing** - Tests d'intrusion réguliers
- [ ] **Dependency scanning** - Snyk, Dependabot pour CVEs

#### Nice to Have

- [ ] **DPoP** - Token binding avancé
- [ ] **MTLS** - Mutual TLS pour services internes
- [ ] **Geo-blocking** - Bloquer pays à risque
- [ ] **IP whitelist** - Pour endpoints sensibles
- [ ] **Honeypots** - Détecter attaquants

---

### Configuration Recommandée

#### Durées de Vie des Tokens

| Type | Durée recommandée | Raison |
|------|-------------------|--------|
| Access Token | 15-30 minutes | Limiter fenêtre d'attaque |
| Refresh Token | 7-30 jours | Balance sécurité/UX |
| ID Token | Même que access | Synchronisé |

#### Headers de Sécurité

```python
from flask_talisman import Talisman

Talisman(app,
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self'",
    },
    frame_options='DENY',
    content_type_options=True
)
```

---

## Tests de Sécurité

### Tests Automatisés à Implémenter

```python
# test_security.py

def test_algorithm_none_rejected():
    """Rejeter alg: none"""
    
def test_wrong_issuer_rejected():
    """Rejeter issuer != OAUTH_ISSUER"""
    
def test_wrong_audience_rejected():
    """Rejeter aud != OAUTH_AUDIENCE"""
    
def test_expired_token_rejected():
    """Rejeter exp < now"""
    
def test_token_not_yet_valid_rejected():
    """Rejeter nbf > now"""
    
def test_invalid_signature_rejected():
    """Rejeter signature invalide"""
    
def test_missing_required_claims():
    """Rejeter tokens sans iss/aud/exp"""
    
def test_insufficient_scope():
    """403 si scope manquant"""
    
def test_missing_role():
    """403 si role manquant"""
    
def test_token_replay():
    """Détecter token replay (si implémenté)"""
```

### Tests Manuels (Penetration Testing)

```bash
# Test 1: Token forgé
curl -H "Authorization: Bearer fake_token" http://localhost:5000/api/me
# Attendu: 401

# Test 2: Token expiré (obtenir un token de test expiré)
curl -H "Authorization: Bearer <EXPIRED_TOKEN>" http://localhost:5000/api/me
# Attendu: 401 "Token expired"

# Test 3: Algorithm confusion (alg: none)
# Créer token avec alg:none
# Attendu: 401

# Test 4: Scope insuffisant
# Obtenir token sans 'read:orders', essayer GET /api/orders
# Attendu: 403 "insufficient_scope"

# Test 5: CORS
curl -H "Origin: https://malicious.com" http://localhost:5000/api/me
# Attendu: CORS error en production

# Test 6: Rate limiting (si implémenté)
for i in {1..1000}; do curl http://localhost:5000/api/me; done
# Attendu: 429 Too Many Requests après limite
```

---

## Métriques de Sécurité

### KPIs à Suivre

| Métrique | Objectif | Alerte si |
|----------|----------|-----------|
| Taux d'erreurs 401 | < 5% | > 10% |
| Taux d'erreurs 403 | < 2% | > 5% |
| Latence validation JWT | < 50ms | > 200ms |
| Appels JWKS/min | Stable | Pic soudain |
| Tentatives d'accès admin par users normaux | 0 | > 0 |

---

## Ressources

### Standards OAuth2/OIDC

- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [RFC 6750 - Bearer Token Usage](https://tools.ietf.org/html/rfc6750)
- [RFC 7519 - JWT](https://tools.ietf.org/html/rfc7519)
- [RFC 8725 - JWT Best Practices](https://tools.ietf.org/html/rfc8725)

### Guides Sécurité

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
- [JWT Security Best Practices](https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-token-best-practices)

---

**Dernière révision:** Décembre 2024  
**Version:** 1.0  
**Auteur:** Youness