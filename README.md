# Resource Server API - OAuth2/OIDC Protected

> **Auteur:** Youness  
> **Projet:** Système OAuth2/OIDC - Partie Resource Server  
> **Description:** API REST protégée par OAuth2 qui valide les JWT access tokens

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Lancer l'application](#lancer-lapplication)
6. [Endpoints API](#endpoints-api)
7. [Authentification & Autorisation](#authentification--autorisation)
8. [Tests](#tests)
9. [Sécurité](#sécurité)
10. [Intégration avec les autres composants](#intégration)

---

## 🎯 Vue d'ensemble

Le Resource Server est responsable de :
- ✅ **Valider les access tokens JWT** émis par l'Authorization Server (Omar)
- ✅ **Vérifier les scopes OAuth2** pour l'autorisation
- ✅ **Vérifier les rôles** pour l'autorisation fine-grained
- ✅ **Protéger les ressources** de l'API
- ✅ **Retourner des erreurs OAuth2 standardisées** (RFC 6750)

---

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Client    │         │ Authorization    │         │   Resource      │
│   (Badr)    │────────▶│   Server (Omar)  │         │   Server (Toi)  │
│             │  Login  │                  │         │                 │
└─────────────┘         └──────────────────┘         └─────────────────┘
       │                         │                            ▲
       │   1. Redirige vers      │                            │
       │      /authorize          │                            │
       │◀────────────────────────┘                            │
       │                                                       │
       │   2. User login & consent                            │
       │                                                       │
       │   3. Reçoit authorization code                       │
       │                                                       │
       │   4. Échange code → access_token                     │
       │──────────────────────────────▶                       │
       │                                                       │
       │   5. Appelle API avec Bearer token                   │
       │───────────────────────────────────────────────────────▶
       │                                                       │
       │   6. Vérifie token (signature, exp, aud, scope)      │
       │                                                       │
       │◀─────────────────────────────────────────────────────│
       │   7. Retourne ressource protégée                     │
```

### Flux de validation du token

```
1. Client envoie: Authorization: Bearer <access_token>
                        │
                        ▼
2. Resource Server extrait le token
                        │
                        ▼
3. Décode header JWT pour obtenir 'kid'
                        │
                        ▼
4. Récupère clé publique depuis JWKS (avec cache)
                        │
                        ▼
5. Vérifie signature + iss + aud + exp + nbf
                        │
                   ┌────┴────┐
                   │         │
              Valid     Invalid
                   │         │
                   ▼         ▼
           6. Vérifie    Return 401
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

## 🚀 Installation

### Prérequis

- Python 3.9+
- pip
- virtualenv (recommandé)

### Étapes

```bash
# 1. Cloner le repo (ou créer le dossier)
mkdir resource-server && cd resource-server

# 2. Créer environnement virtuel
python -m venv venv

# 3. Activer l'environnement
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Copier la config
cp .env.example .env

# 6. Éditer .env avec les valeurs d'Omar (IdP)
nano .env
```

---

## ⚙️ Configuration

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

## 🏃 Lancer l'application

### Mode développement

#### Lancer un seul composant
```bash
# Avec Flask directement
python app.py

# Ou avec flask run
export FLASK_APP=app.py
flask run --port 5000
```

#### Lancer tous les composants du système OAuth2
Pour démarrer le système complet avec tous les composants (Authorization Server, Resource Server, et Frontend), utilisez le script de démarrage :

```bash
# Sur Windows
python start_all.py

# Sur Linux/Mac
python3 start_all.py
```

Ce script démarre automatiquement :
- 🔐 **Authorization Server (Omar)** sur `http://localhost:3000`
- 🛡️ **Resource Server (Votre API)** sur `http://localhost:5000`
- 📱 **Frontend Dashboard** sur `http://localhost:8080`

### Mode production (avec gunicorn)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

L'API sera accessible sur `http://localhost:5000`

---

## 📡 Endpoints API

### Endpoints Publics (pas d'authentification)

#### `GET /api/health`
Health check du service

**Réponse:**
```json
{
  "status": "healthy",
  "service": "resource-server",
  "timestamp": "2024-12-10T12:00:00Z"
}
```

#### `GET /api/public`
Endpoint de démonstration public

**Réponse:**
```json
{
  "message": "Ceci est un endpoint public",
  "info": "Pas d'authentification requise"
}
```

---

### Endpoints Protégés

#### `GET /api/me`
Récupère les informations de l'utilisateur connecté

**Scope requis:** `profile` ou `openid`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Réponse (200):**
```json
{
  "user_id": "user-123",
  "email": "user@example.com",
  "name": "John Doe",
  "scopes": ["profile", "read:orders"],
  "roles": ["user"]
}
```

**Erreurs:**
- `401` - Token absent ou invalide
- `403` - Scope insuffisant

---

#### `GET /api/orders`
Liste les commandes de l'utilisateur

**Scope requis:** `read:orders`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Réponse (200):**
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
Crée une nouvelle commande

**Scope requis:** `write:orders`

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

**Réponse (201):**
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

**Erreurs:**
- `400` - Champs requis manquants
- `401` - Token invalide
- `403` - Scope insuffisant

---

#### `GET /api/admin/stats`
Statistiques administrateur

**Role requis:** `admin`

**Réponse (200):**
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
Liste tous les utilisateurs (admin)

**Scope requis:** `admin:read`  
**Role requis:** `admin`

**Réponse (200):**
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

## 🔐 Authentification & Autorisation

### Format du Token JWT

Les tokens doivent contenir les claims suivants:

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

### Validation du Token

Le Resource Server vérifie automatiquement:

1. ✅ **Signature** - avec clé publique JWKS
2. ✅ **Issuer (iss)** - doit matcher `OAUTH_ISSUER`
3. ✅ **Audience (aud)** - doit contenir `OAUTH_AUDIENCE`
4. ✅ **Expiration (exp)** - token non expiré
5. ✅ **Not Before (nbf)** - token déjà valide
6. ✅ **Algorithm** - seulement RS256 (pas "none")

### Scopes OAuth2

| Scope | Permission |
|-------|-----------|
| `profile` ou `openid` | Accès aux infos utilisateur (`/api/me`) |
| `read:orders` | Lecture des commandes |
| `write:orders` | Création/modification des commandes |
| `admin:read` | Lecture des données admin |

### Rôles

| Rôle | Accès |
|------|-------|
| `user` | Endpoints utilisateur standard |
| `admin` | Endpoints admin (`/api/admin/*`) |

---

## 🧪 Tests

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

- ✅ Endpoints publics accessibles
- ✅ Endpoints protégés → 401 sans token
- ✅ Token malformé → 401
- ✅ Token expiré → 401 (avec mock)
- ✅ Scope insuffisant → 403 (avec mock)
- ✅ Role insuffisant → 403 (avec mock)
- ✅ Algorithm "none" rejeté
- ✅ Tokens jamais loggés

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

## 🛡️ Sécurité

### Mesures implémentées

1. ✅ **Validation stricte des JWT**
   - Signature RSA (RS256)
   - Vérification issuer, audience, expiration
   - Rejet de l'algorithme "none"

2. ✅ **Gestion des erreurs OAuth2 standard (RFC 6750)**
   - 401 avec `WWW-Authenticate` header
   - 403 avec description du scope requis
   - Messages d'erreur standardisés

3. ✅ **Pas de logging des tokens**
   - Logs anonymisés (user ID seulement)
   - Tokens jamais écrits en clair

4. ✅ **Cache JWKS intelligent**
   - TTL de 1 heure
   - Rafraîchissement automatique

5. ✅ **Tolérance de clock skew**
   - ±60 secondes pour exp/nbf

6. ✅ **CORS configuré**
   - Seulement pour origines autorisées (en prod)

### Bonnes pratiques à implémenter (production)

- [ ] **HTTPS obligatoire** - Utiliser TLS/SSL
- [ ] **Rate limiting** - Limiter les requêtes par IP/user
- [ ] **Logging centralisé** - ELK stack, Datadog
- [ ] **Monitoring** - Métriques sur auth success/fail
- [ ] **Introspection** - Endpoint `/introspect` pour vérifier révocation
- [ ] **Token binding** - Lier token au client (DPoP)
- [ ] **Short-lived tokens** - Access tokens de 15-30 min
- [ ] **Rotation de clés** - Processus pour rotation JWKS

---

## 🔗 Intégration avec les autres composants

### Avec Authorization Server (Omar)

**Tu as besoin de:**
- L'URL du JWKS endpoint
- L'issuer exact
- La liste des scopes
- La structure des claims

**Tu fournis:**
- L'audience à mettre dans les tokens (`api://resource-server`)
- Les scopes nécessaires pour chaque endpoint
- Format des erreurs OAuth2

### Avec Client App (Badr)

**Tu fournis:**
- Documentation des endpoints
- Scopes requis par endpoint
- Exemples de requêtes curl/Postman
- Format des erreurs

**Tu as besoin de:**
- Confirmation que le client obtient les bons scopes
- Tests d'intégration endpoint par endpoint

---

## 📞 Support & Debugging

### Problèmes courants

**Erreur: "Invalid issuer"**
```
Solution: Vérifier que OAUTH_ISSUER match exactement le claim 'iss' du token
```

**Erreur: "Invalid audience"**
```
Solution: Vérifier que OAUTH_AUDIENCE est dans le claim 'aud' du token
```

**Erreur: "Unable to find a signing key"**
```
Solution: Vérifier que OAUTH_JWKS_URI est accessible et retourne les clés
Test: curl http://localhost:3000/.well-known/jwks.json
```

**Erreur: "Token expired"**
```
Solution: Token trop vieux. Vérifier les horloges système (NTP)
Clock skew tolerance: ±60s
```

### Logs utiles

```bash
# Activer logs debug
export LOG_LEVEL=DEBUG
python app.py

# Vérifier validation token
# Logs montrent: user_id, scopes, mais JAMAIS le token complet
```

---

## 📚 Références

- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [RFC 6750 - Bearer Token Usage](https://tools.ietf.org/html/rfc6750)
- [RFC 7519 - JWT](https://tools.ietf.org/html/rfc7519)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

## 📝 TODO

- [ ] Obtenir config OAuth2 d'Omar
- [ ] Tests d'intégration avec l'IdP
- [ ] Tests d'intégration avec le Client
- [ ] Endpoint `/introspect` pour révocation
- [ ] Métriques Prometheus
- [ ] Documentation OpenAPI/Swagger
- [ ] CI/CD pipeline

---

**Auteur:** Youness  
**Date:** Décembre 2024  
**Version:** 1.0