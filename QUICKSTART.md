# Quickstart - Resource Server

Guide de démarrage rapide pour lancer le Resource Server et tester l'authentification OAuth2.

---

## Démarrage en 5 Minutes

### 1. Installation

```bash
# Cloner/créer le projet
mkdir resource-server && cd resource-server

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier config
cp .env.example .env

# Éditer .env
nano .env
```

**Valeurs à configurer (obtenir d'Omar):**
```bash
OAUTH_ISSUER=http://localhost:3000
OAUTH_JWKS_URI=http://localhost:3000/.well-known/jwks.json
OAUTH_AUDIENCE=api://resource-server
```

### 3. Lancer

```bash
python app.py
```

**API disponible sur:** `http://localhost:5000`

---

## Tests Rapides

### Test 1: Health Check (Public)

```bash
curl http://localhost:5000/api/health
```

**Attendu:**
```json
{
  "status": "healthy",
  "service": "resource-server",
  "timestamp": "2024-12-10T14:30:00.000Z"
}
```

### Test 2: Endpoint Protégé Sans Token (401)

```bash
curl http://localhost:5000/api/me
```

**Attendu:**
```json
{
  "error": "invalid_token",
  "error_description": "Missing or invalid Authorization header"
}
```

### Test 3: Endpoint Protégé Avec Token (200)

**Étape 1: Obtenir un token d'Omar/Badr**

```bash
# Demander à Badr de te donner un access token
# ou utiliser le flux OAuth2 complet
export TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Étape 2: Appeler l'API**

```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:5000/api/me
```

**Attendu:**
```json
{
  "user_id": "user-123",
  "email": "user@example.com",
  "name": "Test User",
  "scopes": ["profile", "read:orders"],
  "roles": ["user"]
}
```

---

## Checklist de Validation

Avant d'intégrer avec les autres composants:

### Configuration
- [ ] Variables `.env` configurées
- [ ] `OAUTH_ISSUER` match l'IdP d'Omar
- [ ] `OAUTH_JWKS_URI` accessible
- [ ] `OAUTH_AUDIENCE` confirmé avec Omar

### Tests Fonctionnels
- [ ] `/api/health` répond 200
- [ ] `/api/public` répond 200
- [ ] `/api/me` sans token → 401
- [ ] `/api/me` avec token valide → 200
- [ ] `/api/orders` sans scope → 403

### Intégration
- [ ] Coordonné scopes avec Omar
- [ ] Coordonné endpoints avec Badr
- [ ] Testé avec un vrai token de l'IdP

---

## Dépannage Rapide

### Problème: "Unable to find a signing key"

**Cause:** JWKS URI inaccessible

**Solution:**
```bash
# Vérifier que le JWKS est accessible
curl http://localhost:3000/.well-known/jwks.json

# Doit retourner quelque chose comme:
# {
#   "keys": [
#     {
#       "kty": "RSA",
#       "use": "sig",
#       "kid": "key-1",
#       "n": "...",
#       "e": "AQAB"
#     }
#   ]
# }
```

### Problème: "Invalid issuer"

**Cause:** `OAUTH_ISSUER` ne match pas le claim `iss` du token

**Solution:**
```bash
# Décoder le token pour voir l'issuer
# https://jwt.io

# S'assurer que OAUTH_ISSUER = claim 'iss'
```

### Problème: "Invalid audience"

**Cause:** `OAUTH_AUDIENCE` n'est pas dans le claim `aud` du token

**Solution:**
```bash
# Décoder le token pour voir l'audience
# Confirmer avec Omar que 'aud' contient "api://resource-server"
```

### Problème: "Token expired"

**Cause:** Token trop vieux

**Solution:**
```bash
# Demander un nouveau token
# Vérifier les horloges système (NTP)
date  # Doit être synchronisé
```

---

## Workflow d'Intégration

### Phase 1: Setup Solo (Fait)
- [x] Installation
- [x] Configuration
- [x] Tests endpoints publics

### Phase 2: Intégration avec IdP (Omar)
- [ ] Obtenir valeurs config (issuer, jwks_uri, audience)
- [ ] Tester avec un token de test d'Omar
- [ ] Valider structure des claims
- [ ] Confirmer liste des scopes

### Phase 3: Intégration avec Client (Badr)
- [ ] Partager doc API
- [ ] Tester flux complet: Login → Token → API call
- [ ] Valider gestion des erreurs (401/403)
- [ ] Tests end-to-end

### Phase 4: Tests de Sécurité (Brahim)
- [ ] Tests avec tokens invalides
- [ ] Tests avec scopes insuffisants
- [ ] Tests avec algorithme "none"
- [ ] Validation des logs (pas de tokens loggés)

---

## 📞 Points de Coordination

### Avec Omar (Authorization Server)
**Tu as besoin de:**
- ✅ URL de l'issuer
- ✅ URL du JWKS
- ✅ Identifiant audience
- ✅ Liste des scopes
- ✅ Format des claims (sub, email, roles...)
- ✅ Token de test

**Tu fournis:**
- ✅ Audience attendue (`api://resource-server`)
- ✅ Scopes nécessaires pour chaque endpoint
- ✅ Format des erreurs OAuth2

### Avec Badr (Client App)
**Tu fournis:**
- ✅ Documentation API (`docs/API.md`)
- ✅ Exemples curl
- ✅ Collection Postman
- ✅ Liste des scopes par endpoint

**Tu as besoin de:**
- 🔄 Tests avec son app cliente
- 🔄 Validation UX des erreurs

### Avec Brahim (Sécurité)
**Tu fournis:**
- ✅ Documentation sécurité (`docs/SECURITY.md`)
- ✅ Liste des mesures implémentées
- ✅ Liste des limites/risques

**Tu attends:**
- 🔄 Audit de sécurité
- 🔄 Tests d'intrusion
- 🔄 Feedback sur améliorations

---

## 📚 Documentation Complète

Une fois lancé, consulte:

1. **README.md** - Vue d'ensemble et installation complète
2. **docs/API.md** - Documentation détaillée des endpoints
3. **docs/SECURITY.md** - Mesures de sécurité
4. **tests/test_auth.py** - Tests automatisés

---

## ✅ Prêt pour la Suite

Une fois ces tests passés, tu es prêt pour:

1. **Intégration IdP** - Tester avec de vrais tokens d'Omar
2. **Intégration Client** - Permettre à Badr d'appeler ton API
3. **Tests Sécurité** - Laisser Brahim auditer
4. **Documentation Finale** - Compléter la doc du projet global

---

**Besoin d'aide ?** Vérifie la section Dépannage ou consulte la doc complète.

**Prêt ?** Continue avec l'intégration avec l'IdP d'Omar ! 🚀