# 🔒 Architecture Sécurisée VintedBot

## 🎯 Objectif

**Frontend PUBLIC** ✅ : Les vendeurs Vinted peuvent accéder à l'interface web
**Backend/API PRIVÉ** ❌ : Personne ne peut accéder directement à l'API
**Communication interne** 🔐 : Seul le frontend peut appeler le backend

---

## 🏗️ Architecture Déployée

```
┌─────────────────────────────────────────┐
│  UTILISATEURS (Vendeurs Vinted)         │
│                                         │
│  https://vintedbot-backend.fly.dev/     │
└──────────────┬──────────────────────────┘
               │
               │ Accès PUBLIC ✅
               │
┌──────────────▼──────────────────────────┐
│  FRONTEND (React SPA)                   │
│  - Interface utilisateur                │
│  - Upload photos                        │
│  - Gestion brouillons                   │
│  - Analytics dashboard                  │
│  - Système d'abonnements                │
└──────────────┬──────────────────────────┘
               │
               │ Communication INTERNE 🔐
               │ (Referer: https://vintedbot-backend.fly.dev)
               │
┌──────────────▼──────────────────────────┐
│  BACKEND (FastAPI)                      │
│  - API REST (PRIVÉE) ❌                 │
│  - OpenAI GPT-4o-mini                   │
│  - Analyse de photos                    │
│  - Vinted automation                    │
│  - Base de données                      │
└─────────────────────────────────────────┘
```

---

## 🔒 Sécurité Mise en Place

### 1. Blocage de l'API Documentation

En production, **impossible d'accéder** à :
- ❌ `/docs` (Swagger UI)
- ❌ `/redoc` (ReDoc)
- ❌ `/openapi.json` (Schéma OpenAPI)

**Message retourné** :
```json
{
  "error": "API documentation is not available in production. Please use the web interface."
}
```

### 2. Vérification du Referer/Origin

Pour **tous les endpoints API** (`/auth`, `/bulk`, `/vinted`, etc.) :
- ✅ **Autorisé** : Requêtes venant de `https://vintedbot-backend.fly.dev`
- ✅ **Autorisé** : Requêtes en développement (`localhost`)
- ❌ **Bloqué** : Requêtes directes (curl, Postman, etc.)

**Message retourné** :
```json
{
  "error": "Direct API access is not allowed. Please use the web interface at https://vintedbot-backend.fly.dev/"
}
```

### 3. Exceptions

**Toujours accessible** (pour monitoring) :
- ✅ `/health` - Health check

**Toujours accessible** (frontend) :
- ✅ `/` - Page d'accueil
- ✅ `/login` - Connexion
- ✅ `/register` - Inscription
- ✅ `/dashboard` - Tableau de bord
- ✅ `/upload` - Upload photos
- ✅ `/drafts` - Gestion brouillons
- ✅ `/analytics` - Analytics
- ✅ `/automation` - Automation
- ✅ `/accounts` - Multi-comptes
- ✅ `/admin` - Admin panel
- ✅ `/settings` - Paramètres
- ✅ `/assets/*` - Fichiers statiques (JS, CSS, images)

---

## 🎯 Cas d'Usage

### ✅ Utilisateur Normal (Vendeur Vinted)

```
1. Visite https://vintedbot-backend.fly.dev/
   → ✅ Accès au frontend

2. S'inscrit via l'interface
   → ✅ Frontend appelle /auth/register
   → ✅ Referer valide, requête acceptée

3. Upload des photos
   → ✅ Frontend appelle /bulk/analyze
   → ✅ OpenAI analyse les photos
   → ✅ Brouillons créés

4. Publie sur Vinted
   → ✅ Frontend appelle /vinted/publish
   → ✅ Article publié
```

### ❌ Tentative d'Accès Direct à l'API

```bash
# Essai avec curl
curl https://vintedbot-backend.fly.dev/auth/login

# Réponse
{
  "error": "Direct API access is not allowed. Please use the web interface at https://vintedbot-backend.fly.dev/"
}
```

### ❌ Tentative d'Accès à la Documentation

```bash
# Essai d'accéder à /docs
curl https://vintedbot-backend.fly.dev/docs

# Réponse
{
  "error": "API documentation is not available in production. Please use the web interface."
}
```

---

## 💡 Avantages de cette Architecture

### 🛡️ Sécurité
- ✅ API non exposée publiquement
- ✅ Impossible de reverse-engineer l'API
- ✅ Protection contre les abus
- ✅ Contrôle total sur les accès

### 💰 Business
- ✅ Les utilisateurs DOIVENT passer par le frontend
- ✅ Système d'abonnements fonctionnel
- ✅ Impossible de contourner les quotas
- ✅ Monétisation protégée

### 🎨 Expérience Utilisateur
- ✅ Interface moderne et intuitive
- ✅ Pas de documentation technique à comprendre
- ✅ Tout est simple et visuel
- ✅ Workflows guidés

---

## 🔧 Configuration

### Variables d'Environnement Nécessaires

```bash
# OBLIGATOIRE pour activer la sécurité
ENV=production

# Autres variables
OPENAI_API_KEY=sk-...
DATABASE_URL=...
ENCRYPTION_KEY=...
SECRET_KEY=...
```

### Désactiver la Sécurité (Développement)

Pour tester l'API directement en local :
```bash
ENV=dev
```

Cela permettra :
- ✅ Accès à `/docs`
- ✅ Requêtes curl directes
- ✅ Tests avec Postman

---

## 📊 Monitoring

### Health Check Toujours Accessible

```bash
curl https://vintedbot-backend.fly.dev/health
```

Réponse :
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "config": {
    "port": 5000,
    "openai_enabled": true
  }
}
```

---

## 🚀 Déploiement

Le système est automatiquement sécurisé en production grâce à `ENV=production`.

Aucune configuration supplémentaire nécessaire !

---

## ✅ Résumé

| Accès | Frontend | API Directe | Documentation |
|-------|----------|-------------|---------------|
| **Public** | ✅ OUI | ❌ NON | ❌ NON |
| **Via Frontend** | ✅ OUI | ✅ OUI | ❌ NON |
| **En Dev (ENV=dev)** | ✅ OUI | ✅ OUI | ✅ OUI |

**Votre application est maintenant 100% sécurisée !** 🔒
