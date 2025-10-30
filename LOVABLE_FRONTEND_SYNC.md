# 🔄 Guide de Synchronisation Frontend Lovable

## Vue d'ensemble
Le backend VintedBot a été transformé en plateforme SaaS multi-utilisateurs avec authentification JWT, abonnements Stripe, et quotas. Voici tout ce que votre frontend Lovable doit implémenter.

---

## 🔐 1. AUTHENTIFICATION JWT

### Nouvelles Routes d'Authentification

#### **POST /auth/register**
Créer un nouveau compte utilisateur.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Jean Dupont"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Jean Dupont",
    "is_active": true,
    "subscription_tier": "free",
    "created_at": "2025-10-30T12:00:00Z"
  }
}
```

**Erreurs:**
- `400` : Email déjà utilisé

---

#### **POST /auth/login**
Connexion utilisateur existant.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Jean Dupont",
    "is_active": true,
    "subscription_tier": "free",
    "stripe_customer_id": "cus_xxxxx",
    "stripe_subscription_id": null,
    "subscription_status": null,
    "created_at": "2025-10-30T12:00:00Z"
  }
}
```

**Erreurs:**
- `401` : Email ou mot de passe incorrect

---

#### **GET /auth/me**
Récupérer les infos de l'utilisateur connecté + quotas actuels.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Jean Dupont",
  "is_active": true,
  "subscription_tier": "free",
  "stripe_customer_id": "cus_xxxxx",
  "stripe_subscription_id": null,
  "subscription_status": null,
  "created_at": "2025-10-30T12:00:00Z",
  "quotas": {
    "ai_analyses": {"used": 5, "limit": 20},
    "drafts_created": {"used": 12, "limit": 50},
    "publications": {"used": 2, "limit": 10},
    "storage_mb": {"used": 45.3, "limit": 500.0}
  }
}
```

**Erreurs:**
- `401` : Token manquant ou invalide

---

### Comment Utiliser le JWT

**1. Stocker le token après login/register:**
```javascript
// Après succès login/register
const { access_token } = response.data;
localStorage.setItem('auth_token', access_token);
```

**2. Inclure le token dans TOUTES les requêtes protégées:**
```javascript
const token = localStorage.getItem('auth_token');

fetch('https://your-backend.repl.co/bulk/ingest', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({...})
});
```

**3. Gérer l'expiration (HTTP 401):**
```javascript
if (response.status === 401) {
  localStorage.removeItem('auth_token');
  window.location.href = '/login';
}
```

---

## 💳 2. FACTURATION STRIPE

### Routes de Gestion d'Abonnement

#### **POST /billing/checkout**
Créer une session de paiement Stripe pour upgrader.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "tier": "starter",
  "success_url": "https://yourapp.com/success",
  "cancel_url": "https://yourapp.com/pricing"
}
```

**Response (200):**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_xxxxx"
}
```

**Tiers disponibles:** `starter`, `pro`, `scale`

---

#### **POST /billing/portal**
Créer une session du portail client Stripe (gérer carte, annuler abonnement).

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "return_url": "https://yourapp.com/dashboard"
}
```

**Response (200):**
```json
{
  "portal_url": "https://billing.stripe.com/p/session/xxxxx"
}
```

---

#### **GET /billing/subscription**
Récupérer les détails de l'abonnement actuel.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "subscription_tier": "starter",
  "subscription_status": "active",
  "stripe_subscription_id": "sub_xxxxx",
  "current_period_end": "2025-11-30T23:59:59Z",
  "cancel_at_period_end": false
}
```

---

### Plans d'Abonnement

| Plan | Prix/mois | Brouillons | Publications | Analyses IA | Stockage |
|------|-----------|------------|--------------|-------------|----------|
| **Free** | 0€ | 50 | 10 | 20 | 500 MB |
| **Starter** | 19€ | 500 | 100 | 200 | 5 GB |
| **Pro** | 49€ | 2000 | 500 | 1000 | 20 GB |
| **Scale** | 99€ | 10000 | 2500 | 5000 | 100 GB |

---

## 🚨 3. GESTION DES QUOTAS

### Erreur HTTP 429 - Quota Dépassé

Tous les endpoints protégés retournent maintenant **HTTP 429** quand un quota est atteint.

**Exemple de réponse:**
```json
{
  "detail": "Vous avez atteint votre limite de brouillons (50). Passez au plan 'starter' pour 500 brouillons/mois."
}
```

**Comment gérer dans le frontend:**
```javascript
if (response.status === 429) {
  const message = response.data.detail;
  
  // Afficher message d'upgrade
  showUpgradeModal({
    message: message,
    ctaText: "Voir les plans",
    ctaUrl: "/pricing"
  });
}
```

---

### Afficher les Quotas en Temps Réel

**Récupérer les quotas depuis /auth/me:**
```javascript
const user = await fetch('/auth/me', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

const quotas = user.quotas;
// {
//   ai_analyses: {used: 5, limit: 20},
//   drafts_created: {used: 12, limit: 50},
//   publications: {used: 2, limit: 10},
//   storage_mb: {used: 45.3, limit: 500.0}
// }
```

**Exemple d'UI:**
```jsx
<QuotaBar 
  label="Brouillons" 
  used={quotas.drafts_created.used} 
  limit={quotas.drafts_created.limit} 
/>
// Affiche: "12/50 brouillons utilisés"
```

---

## 📋 4. ENDPOINTS MODIFIÉS (17 ENDPOINTS PROTÉGÉS)

### ⚠️ TOUS ces endpoints nécessitent maintenant l'authentification

#### **Opérations en Masse (Bulk)**

| Endpoint | Auth Required | Quotas Vérifiés |
|----------|---------------|-----------------|
| `POST /bulk/ingest` | ✅ | AI analyses + Storage |
| `POST /bulk/upload` | ✅ | AI analyses + Storage |
| `POST /bulk/analyze` | ✅ | AI analyses + Storage |
| `POST /bulk/photos/analyze` | ✅ | AI analyses + Storage |
| `POST /bulk/plan` | ✅ | - |
| `POST /bulk/generate` | ✅ | Drafts (multi-unités) |
| `PATCH /bulk/drafts/{id}` | ✅ | - |
| `DELETE /bulk/drafts/{id}` | ✅ | - |

#### **Automatisation Vinted**

| Endpoint | Auth Required | Quotas Vérifiés |
|----------|---------------|-----------------|
| `POST /vinted/photos/upload` | ✅ | AI analyses (si auto_analyze=true) |
| `POST /vinted/listings/prepare` | ✅ | - |
| `POST /vinted/listings/publish` | ✅ | Publications |

#### **Upload Simple**

| Endpoint | Auth Required | Quotas Vérifiés |
|----------|---------------|-----------------|
| `POST /ingest/upload` | ✅ | Drafts + Storage |

---

## 🛠️ 5. EXEMPLE D'INTÉGRATION COMPLÈTE

### Configuration Axios Globale

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://your-backend.repl.co',
});

// Interceptor: Ajouter le token automatiquement
api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor: Gérer les erreurs 401/429
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    if (error.response?.status === 429) {
      const message = error.response.data.detail;
      showUpgradeModal(message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

---

### Workflow Complet: Login → Upload Photos → Check Quotas

```javascript
// 1. Login
const loginResponse = await api.post('/auth/login', {
  email: 'user@example.com',
  password: 'password123'
});

const { access_token } = loginResponse.data;
localStorage.setItem('auth_token', access_token);

// 2. Récupérer les quotas actuels
const userResponse = await api.get('/auth/me');
const quotas = userResponse.data.quotas;

console.log(`AI analyses: ${quotas.ai_analyses.used}/${quotas.ai_analyses.limit}`);
console.log(`Brouillons: ${quotas.drafts_created.used}/${quotas.drafts_created.limit}`);

// 3. Upload photos (protégé par quotas)
const formData = new FormData();
files.forEach(file => formData.append('files', file));

try {
  const uploadResponse = await api.post('/bulk/ingest', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  console.log('Success:', uploadResponse.data);
  
} catch (error) {
  if (error.response?.status === 429) {
    // Quota dépassé
    alert(error.response.data.detail);
  }
}

// 4. Rafraîchir les quotas après l'opération
const updatedUser = await api.get('/auth/me');
updateQuotasUI(updatedUser.data.quotas);
```

---

## 📊 6. CHANGEMENTS DE STRUCTURE DES RÉPONSES

### Avant (Single-User)
```json
{
  "ok": true,
  "job_id": "abc123",
  "total_photos": 18
}
```

### Maintenant (Multi-User)
```json
{
  "ok": true,
  "job_id": "abc123",
  "total_photos": 18,
  "user_id": 1,
  "quotas_consumed": {
    "ai_analyses": 1,
    "storage_mb": 12.5
  }
}
```

**Note:** Les champs `user_id` et `quotas_consumed` sont ajoutés automatiquement par le backend, mais pas nécessaires dans vos requêtes.

---

## 🚀 7. CHECKLIST D'IMPLÉMENTATION FRONTEND

### Phase 1: Authentification
- [ ] Page de login (/login)
- [ ] Page de register (/register)
- [ ] Stocker le JWT dans localStorage
- [ ] Ajouter le header `Authorization: Bearer <token>` à toutes les requêtes
- [ ] Gérer HTTP 401 → Rediriger vers /login
- [ ] Afficher les infos utilisateur (depuis /auth/me)

### Phase 2: Affichage des Quotas
- [ ] Barre de progression pour chaque quota
- [ ] Récupérer les quotas depuis /auth/me
- [ ] Rafraîchir les quotas après chaque opération
- [ ] Afficher un badge "Free/Starter/Pro/Scale" selon le tier

### Phase 3: Gestion des Limites
- [ ] Gérer HTTP 429 → Afficher modal d'upgrade
- [ ] Bloquer les boutons si quota atteint (UI preventive)
- [ ] Message clair: "12/50 brouillons utilisés"

### Phase 4: Facturation
- [ ] Page de pricing (/pricing)
- [ ] Bouton "Upgrade" → POST /billing/checkout → Rediriger vers Stripe
- [ ] Bouton "Gérer mon abonnement" → POST /billing/portal
- [ ] Afficher le statut d'abonnement actuel
- [ ] Gérer le success_url après paiement Stripe

### Phase 5: Sécurité
- [ ] Ne jamais stocker le password en clair
- [ ] Supprimer le token du localStorage au logout
- [ ] Rediriger les non-authentifiés vers /login
- [ ] Protéger les routes frontend (React Router guards)

---

## 🔧 8. CONFIGURATION REQUISE

### Variables d'Environnement Backend (déjà configurées)
```env
JWT_SECRET=<auto-generated 512-bit key>
STRIPE_SECRET_KEY=<your_stripe_key>
STRIPE_WEBHOOK_SECRET=<your_webhook_secret>
OPENAI_API_KEY=<your_openai_key>
DATABASE_URL=<auto-configured>
```

### Variables d'Environnement Frontend (à configurer dans Lovable)
```env
VITE_API_BASE_URL=https://your-backend.repl.co
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
```

---

## 📞 9. SUPPORT & DÉPANNAGE

### Erreurs Fréquentes

**❌ "Not authenticated" (HTTP 401)**
- Vérifier que le token est bien envoyé dans le header `Authorization: Bearer <token>`
- Vérifier que le token n'a pas expiré (durée de vie: 7 jours)
- Re-login si nécessaire

**❌ "Vous avez atteint votre limite..." (HTTP 429)**
- L'utilisateur a dépassé un quota
- Afficher un message d'upgrade vers un plan supérieur
- Rediriger vers /pricing

**❌ "CORS error"**
- Le backend accepte déjà `https://*.lovable.dev`
- Vérifier que vous utilisez la bonne URL backend

---

## 📚 10. RESSOURCES COMPLÉMENTAIRES

### Documentation OpenAPI
- **Swagger UI:** `https://your-backend.repl.co/docs`
- **ReDoc:** `https://your-backend.repl.co/redoc`
- **OpenAPI JSON:** `https://your-backend.repl.co/openapi.json`

### Fichiers Backend Modifiés
- `backend/core/auth.py` - Logique JWT
- `backend/middleware/quota_checker.py` - Vérification des quotas
- `backend/core/stripe_client.py` - Intégration Stripe
- `backend/api/v1/routers/auth.py` - Routes d'authentification
- `backend/api/v1/routers/billing.py` - Routes de facturation
- `backend/api/v1/routers/bulk.py` - 8 endpoints protégés
- `backend/api/v1/routers/vinted.py` - 3 endpoints protégés
- `backend/api/v1/routers/ingest.py` - 1 endpoint protégé

---

## ✅ RÉSUMÉ RAPIDE

**Ce qui a changé:**
1. ✅ Tous les endpoints nécessitent maintenant un JWT (`Authorization: Bearer <token>`)
2. ✅ Nouveaux endpoints: `/auth/register`, `/auth/login`, `/auth/me`, `/billing/*`
3. ✅ Nouveaux codes d'erreur: **HTTP 401** (non authentifié), **HTTP 429** (quota dépassé)
4. ✅ Nouveaux champs dans les réponses: `user_id`, `quotas_consumed`
5. ✅ 4 types de quotas: `ai_analyses`, `drafts_created`, `publications`, `storage_mb`

**Ce qui n'a PAS changé:**
- ✅ Structure des requêtes (multipart/form-data, JSON, etc.)
- ✅ Validation des fichiers (HEIC support, taille max, formats acceptés)
- ✅ Logique métier (AI grouping, anti-saucisson, price estimation)
- ✅ Réponses des endpoints (structure identique + nouveaux champs)

---

**Bon courage pour l'intégration ! 🚀**
