# Resource Server - Documentation API Complète

## Vue d'ensemble

Cette API protège les ressources utilisateur en utilisant OAuth2/OIDC. Tous les endpoints protégés nécessitent un access token JWT valide dans le header `Authorization`.

Base URL: `http://localhost:5000`



## Authentification

### Format du Header

Tous les endpoints protégés nécessitent:

```http
Authorization: Bearer <access_token>


### Obtenir un Access Token

L'access token est obtenu via le flux OAuth2 Authorization Code avec l'Authorization Server (Omar):

1. Redirection vers /authorize (Authorization Server)
2. Login utilisateur & consent
3. Échange du code contre un token sur `/token`
4. Utilisation du token pour appeler cette API

### Exemple de Token JWT (décodé)

```json

  "iss": "http://localhost:3000",
  "aud": "api://resource-server",
  "sub": "user-123",
  "email": "john.doe@example.com",
  "name": "John Doe",
  "scope": "profile read:orders write:orders",
  "roles": ["user"],
  "iat": 1702213200,
  "exp": 1702216800





## Endpoints

### Résumé

| Méthode | Endpoint | Auth | Scope requis | Role requis | Description |
|---------|----------|------|--------------|-------------|-------------|
| GET | `/api/health` | Non | - | - | Health check |
| GET | `/api/public` | Non | - | - | Endpoint public |
| GET | `/api/me` | Oui | `profile` or `openid` | - | Infos utilisateur |
| GET | `/api/orders` | Oui | `read:orders` | - | Liste des commandes |
| POST | `/api/orders` | Oui | `write:orders` | - | Créer commande |
| GET | `/api/admin/stats` | Oui | - | `admin` | Stats admin |
| GET | `/api/admin/users` | Oui | `admin:read` | `admin` | Liste utilisateurs |



## Endpoints Publics

### GET /api/health

Health check du service.

**Authentification:** Non requise

**Réponse (200)**
```json

  "status": "healthy",
  "service": "resource-server",
  "timestamp": "2024-12-10T14:30:00.000Z"



**Exemple curl:**
```bash
curl http://localhost:5000/api/health




### GET /api/public

Endpoint de démonstration public.

**Authentification:** Non requise

**Réponse (200)**
```json

  "message": "Ceci est un endpoint public",
  "info": "Pas d'authentification requise",
  "timestamp": "2024-12-10T14:30:00.000Z"



**Exemple curl:**
```bash
curl http://localhost:5000/api/public




## Endpoints Protégés - Utilisateur

### GET /api/me

Récupère les informations de l'utilisateur authentifié.

**Authentification:** Requise  
**Scope requis:** `profile` OU `openid`

**Headers:**
```http
Authorization: Bearer <access_token>


**Réponse (200)**
```json

  "user_id": "user-123",
  "email": "john.doe@example.com",
  "name": "John Doe",
  "scopes": ["profile", "read:orders", "write:orders"],
  "roles": ["user"]



**Erreurs**

**401 Unauthorized** - Token absent ou invalide
```json

  "error": "invalid_token",
  "error_description": "Missing or invalid Authorization header"


Header: `WWW-Authenticate: Bearer realm="api"`

**403 Forbidden** - Scope insuffisant
```json

  "error": "insufficient_scope",
  "error_description": "Required scope: profile or openid"


Header: `WWW-Authenticate: Bearer error="insufficient_scope", scope="profile openid"`

**Exemples curl:**

Succès
```bash
curl -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:5000/api/me


Sans token
```bash
curl http://localhost:5000/api/me
# → 401 Unauthorized


Token invalide
```bash
curl -H "Authorization: Bearer invalid_token" \
     http://localhost:5000/api/me
# → 401 Unauthorized




### GET /api/orders

Liste les commandes de l'utilisateur authentifié.

**Authentification:** Requise  
**Scope requis:** `read:orders`

**Headers:**
```http
Authorization: Bearer <access_token>


**Réponse (200)**
```json

  "orders": [
    
      "id": "order-001",
      "user_id": "user-123",
      "product": "Laptop Dell XPS 15",
      "amount": 1299.99,
      "status": "delivered",
      "date": "2024-12-01"
    
    
      "id": "order-002",
      "user_id": "user-123",
      "product": "Wireless Mouse",
      "amount": 29.99,
      "status": "pending",
      "date": "2024-12-08"
    
  
  "total": 2



**Erreurs**

- 401 - Token invalide
- 403 - Scope `read:orders` manquant

**Exemple curl:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/orders




### POST /api/orders

Crée une nouvelle commande pour l'utilisateur authentifié.

**Authentification:** Requise  
**Scope requis:** `write:orders`

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json


**Body (JSON):**
```json

  "product": "Mechanical Keyboard",
  "amount": 149.99



**Champs requis:**
- `product` (string) - Nom du produit
- `amount` (number) - Montant en devise

**Réponse (201 Created)**
```json

  "id": "order-003",
  "user_id": "user-123",
  "product": "Mechanical Keyboard",
  "amount": 149.99,
  "status": "pending",
  "date": "2024-12-10T14:35:22.123Z"



**Erreurs**

**400 Bad Request** - Champs manquants
```json

  "error": "invalid_request",
  "error_description": "Missing required fields: product, amount"



- 401 - Token invalide  
- 403 - Scope `write:orders` manquant

**Exemples curl:**

Succès
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product": "Mechanical Keyboard", "amount": 149.99}' \
  http://localhost:5000/api/orders


Champs manquants
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:5000/api/orders
# → 400 Bad Request




## Endpoints Protégés - Admin

### GET /api/admin/stats

Récupère les statistiques globales (réservé aux admins).

**Authentification:** Requise  
**Scope requis:** Aucun spécifique  
**Role requis:** `admin`

**Headers:**
```http
Authorization: Bearer <access_token>


**Réponse (200)**
```json

  "total_users": 1523,
  "total_orders": 8945,
  "revenue": 425678.90,
  "timestamp": "2024-12-10T14:40:00.000Z"



**Erreurs**

- 401 - Token invalide  
- 403 - Role `admin` manquant
```json

  "error": "forbidden",
  "error_description": "Required role: admin"



**Exemple curl:**
```bash
curl -H "Authorization: Bearer ADMIN_TOKEN" \
     http://localhost:5000/api/admin/stats




### GET /api/admin/users

Liste tous les utilisateurs du système (admin seulement).

**Authentification:** Requise  
**Scope requis:** `admin:read`  
**Role requis:** `admin`

**Headers:**
```http
Authorization: Bearer <access_token>


**Réponse (200)**
```json

  "users": [
    
      "id": "user-001",
      "email": "john.doe@example.com",
      "status": "active"
    
    
      "id": "user-002",
      "email": "jane.smith@example.com",
      "status": "active"
    
    
      "id": "user-003",
      "email": "inactive@example.com",
      "status": "inactive"
    
  
  "total": 3



**Erreurs**

- 401 - Token invalide  
- 403 - Scope `admin:read` OU role `admin` manquant

**Exemple curl:**
```bash
curl -H "Authorization: Bearer ADMIN_TOKEN" \
     http://localhost:5000/api/admin/users




## Codes d'Erreur HTTP

### 400 Bad Request
Requête malformée ou données invalides.

**Exemple**
```json

  "error": "invalid_request",
  "error_description": "Missing required fields: product, amount"



### 401 Unauthorized
Authentification requise ou token invalide.

**Header de réponse**
```http
WWW-Authenticate: Bearer realm="api"
WWW-Authenticate: Bearer error="invalid_token"
WWW-Authenticate: Bearer error="invalid_token", error_description="Token expired"


**Exemples**
```json

  "error": "invalid_token",
  "error_description": "Missing or invalid Authorization header"



```json

  "error": "invalid_token",
  "error_description": "Token expired"



### 403 Forbidden
Token valide mais permissions insuffisantes.

**Header de réponse**
```http
WWW-Authenticate: Bearer error="insufficient_scope", scope="read:orders"


**Exemples**
```json

  "error": "insufficient_scope",
  "error_description": "Required scope: read:orders"



```json

  "error": "forbidden",
  "error_description": "Required role: admin"



### 404 Not Found
Route ou ressource inexistante.

```json

  "error": "not_found",
  "error_description": "Resource not found"



### 500 Internal Server Error
Erreur serveur interne.

```json

  "error": "server_error",
  "error_description": "Internal server error"





## Scopes OAuth2

### Liste des Scopes

| Scope | Description | Endpoints |
|-------|-------------|-----------|
| `profile` | Accès aux infos de profil utilisateur | `/api/me` |
| `openid` | Authentification OpenID Connect | `/api/me` |
| `read:orders` | Lecture des commandes | `/api/orders` (GET) |
| `write:orders` | Création/modification des commandes | `/api/orders` (POST) |
| `admin:read` | Lecture des données admin | `/api/admin/users` |

### Comment les Scopes sont Vérifiés

Le middleware vérifie que le claim `scope` du JWT contient au moins un des scopes requis.

**Exemple:**
- Endpoint requiert `read:orders`
- Token contient `scope: "profile read:orders write:orders"`
- Autorisé (car `read:orders` présent)

**Format du scope dans le JWT:**
```json

  "scope": "profile read:orders write:orders"


*Note: Les scopes sont séparés par des espaces (space-separated string)*



## Rôles

### Liste des Rôles

| Rôle | Description | Endpoints |
|------|-------------|-----------|
| `user` | Utilisateur standard | Tous les endpoints user |
| `admin` | Administrateur | `/api/admin/*` |

### Comment les Rôles sont Vérifiés

Le middleware vérifie que le claim `roles` du JWT contient au moins un des rôles requis.

**Format des roles dans le JWT:**
```json

  "roles": ["user", "admin"]


*Note: Les rôles sont un array JSON*



## Tests avec Postman

### Configuration

1. Créer une variable d'environnement `access_token`
2. Ajouter dans Pre-request Script (pour les endpoints protégés):
   ```javascript
   pm.request.headers.add({
     key: 'Authorization',
     value: 'Bearer ' + pm.environment.get('access_token')
   
   

### Collection Postman

Importer la collection fournie `docs/postman_collection.json`

Scénarios de test inclus:
- Health check
- Endpoint public
- /api/me sans token → 401
- /api/me avec token valide
- GET /api/orders
- POST /api/orders
- POST /api/orders scope insuffisant → 403
- Admin stats (token admin)
- Admin stats (token user) → 403



## Workflow d'Intégration

### Étape 1: Obtenir un Token

Demander à Badr (Client App) d'exécuter le flux OAuth2:
1. Redirection vers Authorization Server
2. Login + consent
3. Obtention du token

Ou utiliser curl direct (si Omar a implémenté):
```bash
# 1. Obtenir authorization code
# (navigateur ou curl avec redirect)

# 2. Échanger code contre token
curl -X POST http://localhost:3000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=AUTH_CODE" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "client_id=CLIENT_ID" \
  -d "code_verifier=CODE_VERIFIER"


### Étape 2: Utiliser le Token

```bash
# Stocker le token
export ACCESS_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

# Appeler l'API
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
     http://localhost:5000/api/me


### Étape 3: Tester les Erreurs

```bash
# Token expiré
curl -H "Authorization: Bearer EXPIRED_TOKEN" \
     http://localhost:5000/api/me
# → 401 Token expired

# Scope insuffisant
curl -H "Authorization: Bearer TOKEN_WITHOUT_READ_ORDERS" \
     http://localhost:5000/api/orders
# → 403 insufficient_scope




## Monitoring & Logs

### Ce qui est loggé

User ID (sub)  
Scopes demandés  
Endpoint appelé  
Status code de réponse  
Timestamp

JAMAIS le token complet

### Exemple de log


2024-12-10 14:35:22 - INFO - Token validé pour user: user-123, scopes: profile read:orders
2024-12-10 14:35:23 - INFO - Commande créée: order-003 par user: user-123




## Sécurité

### Validation du Token

Chaque requête avec token déclenche:

1.  Extraction du header `Authorization`
2.  Vérification du format `Bearer <token>`
3.  Décodage du JWT header (kid, alg)
4.  Récupération clé publique depuis JWKS (avec cache)
5.  Vérification signature RSA
6.  Vérification `iss` = OAUTH_ISSUER
7.  Vérification `aud` contient OAUTH_AUDIENCE
8.  Vérification `exp` > now (avec tolérance ±60s)
9.  Vérification `nbf` ≤ now
10.  Vérification scopes/roles requis

### Mesures de Sécurité

- Seulement algorithme RS256 (rejet de "none")
- JWKS cache (TTL 1h, refresh automatique)
- Clock skew tolerance (±60s)
- Headers WWW-Authenticate selon RFC 6750
- Tokens jamais loggés
- CORS configuré
- Validation stricte des claims



## Références

- RFC 6749 - OAuth 2.0 Authorization Framework
- RFC 6750 - Bearer Token Usage
- RFC 7519 - JSON Web Token (JWT)
- OpenID Connect Core 1.0



**Dernière mise à jour:** Décembre 2024  
**Version:** 1.0  
**Auteur:** Youness