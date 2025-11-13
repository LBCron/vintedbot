# 🚀 VintedBot - Le Bot Vinted Le Plus Sophistiqué du Marché

**VintedBot** est une plateforme d'automatisation Vinted alimentée par l'IA qui transforme vos photos de vêtements en annonces complètes en quelques secondes, avec des fonctionnalités d'automation premium uniques sur le marché.

---

## ✨ Fonctionnalités Uniques

### 🤖 **Analyse IA Automatique (GPT-4 Vision)**
- Upload multiple de photos (jusqu'à 500)
- Génération automatique : titre, description, prix, catégorie, taille, couleur, marque, état
- Création de brouillons prêts à publier
- Analyse intelligente par IA

### 📊 **Analytics Dashboard** (UNIQUE - absent de TOUS les concurrents !)
- **Performance heatmap** : découvrez vos meilleures heures/jours pour poster
- **Top/Bottom performers** : identifiez vos annonces les plus/moins performantes
- **Analyse par catégorie** : comparez les performances entre catégories
- Métriques en temps réel : vues, likes, messages, taux de conversion

### 🔄 **Auto-Bump Intelligent**
- Remonte vos annonces automatiquement en tête de liste
- **Économise de l'argent** vs bumps payants Vinted (0.95€/bump)
- Rotation intelligente pour éviter les patterns suspects
- Skip annonces récemment bumpées
- Scheduler automatique toutes les 5 minutes

### 👥 **Auto-Follow/Unfollow**
- Follow automatique d'utilisateurs ciblés
- Unfollow automatique après X jours si pas de follow-back
- Ciblage par catégories
- Tracking complet dans base de données
- Limites quotidiennes configurables

### 💬 **Auto-Messages**
- Système de templates avec variables : `{{username}}`, `{{item_title}}`, `{{price}}`
- Envoi automatique selon déclencheurs (nouveau follower, nouveau like, etc.)
- Frappe caractère par caractère (50-150ms) pour imiter un humain
- Délais aléatoires anti-détection

### 🔐 **Système Multi-Utilisateurs Complet**
- Authentification JWT sécurisée
- Gestion de quotas par plan d'abonnement
- Support multi-comptes Vinted par utilisateur
- Stripe integration pour paiements

---

## 🏗️ Architecture Technique

### **Backend (Python FastAPI)**
- API REST complète avec 17 tables SQLite (backend/data/vbs.db)
- Scheduler APScheduler (6 jobs automatiques)
- Playwright pour automation Vinted
- GPT-4 Vision pour analyse photos
- Chiffrement AES-256 pour sessions
- Rate limiting et gestion quotas

### **Frontend (React + TypeScript)**
- React 18 + Vite + TailwindCSS
- 10 pages complètes (Dashboard, Upload, Analytics, Automation, etc.)
- Responsive mobile-first
- Recharts pour graphiques analytics
- JWT authentication avec interceptor Axios

---

## 🚀 Démarrage Rapide

### **Prérequis**
- Python 3.11+
- Bun ou Node.js 18+
- SQLite (inclus, aucune installation requise)

### **1. Installation Backend**

```bash
# Installer les dépendances Python
pip install -r backend/requirements.txt

# Configurer les variables d'environnement
# Ajouter votre OPENAI_API_KEY dans les Secrets Replit

# Démarrer le backend (port 8000)
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### **2. Installation Frontend**

```bash
# Aller dans le dossier frontend
cd frontend

# Installer les dépendances
bun install

# Démarrer le frontend (port 5000)
bun run dev
```

### **3. Accéder à l'Application**

- **Frontend** : http://localhost:5000 (ou votre webview Replit)
- **Backend API** : http://localhost:8000
- **API Docs** : http://localhost:8000/docs

---

## 📡 Endpoints API Principaux

### **Authentification**
```bash
POST /auth/register  # Créer un compte
POST /auth/login     # Se connecter
GET  /auth/me        # Infos utilisateur + quotas
```

### **Upload & Analyse IA**
```bash
POST /bulk/photos/analyze        # Upload photos + analyse IA
GET  /bulk/jobs/{job_id}         # Suivi progression
GET  /bulk/drafts                # Liste brouillons
PATCH /bulk/drafts/{id}          # Modifier brouillon
POST /bulk/drafts/{id}/publish   # Publier sur Vinted
```

### **Analytics (PREMIUM)**
```bash
GET /analytics/dashboard         # Dashboard complet
POST /analytics/events/view      # Track vue
POST /analytics/events/like      # Track like
POST /analytics/events/message   # Track message
```

### **Automation (PREMIUM)**
```bash
GET  /automation/rules           # Liste règles automation
POST /automation/bump/configure  # Config auto-bump
POST /automation/follow/configure # Config auto-follow
POST /automation/messages/configure # Config auto-messages
POST /automation/bump/execute    # Exécuter bump manuel
```

---

## 🗄️ Base de Données (17 Tables)

### **Tables Principales**
- `users` - Comptes utilisateurs
- `listings` - Annonces Vinted
- `drafts` - Brouillons en attente
- `bulk_jobs` - Jobs d'analyse IA

### **Tables Premium**
- `analytics_events` - Tracking vues/likes/messages
- `aggregated_metrics` - Métriques pré-calculées
- `automation_rules` - Règles d'automation
- `automation_jobs` - Historique exécutions
- `vinted_accounts` - Comptes Vinted multiples
- `message_templates` - Templates messages
- `conversations` - Historique conversations
- `follows` - Tracking follow/unfollow

---

## ⚙️ Configuration

### **Variables d'Environnement (Replit Secrets)**

```bash
# Obligatoire
OPENAI_API_KEY=sk-...

# Optionnel - Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_SCALE_PRICE_ID=price_...

# Optionnel - CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
```

**Note:** Le backend utilise **SQLite** (fichier `backend/data/vbs.db`). Aucune configuration database externe n'est nécessaire !

### **Plans d'Abonnement**

| Plan | AI Analyses | Drafts | Publications | Storage |
|------|-------------|--------|--------------|---------|
| **Free** | 20/mois | 50 | 10/mois | 500 MB |
| **Starter** | 100/mois | 200 | 50/mois | 2 GB |
| **Pro** | 500/mois | 1000 | 200/mois | 10 GB |
| **Scale** | Illimité | Illimité | Illimité | 50 GB |

---

## 🛡️ Sécurité & Anti-Détection

### **Mesures Anti-Détection Vinted**
- Délais aléatoires entre actions (1-3 secondes)
- Frappe caractère par caractère avec timing humain
- Multiple selectors pour robustesse
- Rotation des patterns d'utilisation
- Gestion intelligente des captchas

### **Sécurité Données**
- JWT tokens avec expiration
- Chiffrement AES-256 pour sessions Vinted
- Hashage Argon2 pour mots de passe
- Rate limiting sur toutes les routes
- Validation stricte des inputs

---

## 🎯 Comparaison Concurrents

| Fonctionnalité | VintedBot | Dotb | VatBot | Sales Bot |
|----------------|-----------|------|--------|-----------|
| Analyse IA Photos | ✅ | ❌ | ❌ | ❌ |
| **Analytics Dashboard** | ✅ **UNIQUE** | ❌ | ❌ | ❌ |
| Auto-Bump | ✅ | ✅ | ✅ | ❌ |
| Auto-Follow | ✅ | ❌ | ✅ | ❌ |
| Auto-Messages | ✅ | ✅ | ❌ | ✅ |
| Multi-Comptes | ✅ | ✅ | ❌ | ❌ |
| Mode Draft (évite captcha) | ✅ | ❌ | ❌ | ❌ |
| API Complète | ✅ | ❌ | ❌ | ❌ |

---

## 📊 Scheduler Automatique

Le backend exécute automatiquement 6 jobs :

1. **Inbox Sync** - Toutes les 15 minutes
2. **Publish Poll** - Toutes les 30 secondes  
3. **Price Drop** - Quotidien à 3h
4. **Vacuum & Prune** - Quotidien à 2h
5. **Clean Temp Photos** - Toutes les 6 heures
6. **Automation Executor** - Toutes les 5 minutes ⭐ (exécute auto-bump/follow/messages)

---

## 🐛 Debugging

### **Logs Backend**
```bash
# Logs en temps réel
tail -f backend/data/app.log

# Vérifier santé
curl http://localhost:8000/health
```

### **Logs Frontend**
```bash
# Console navigateur (F12)
# Ou logs Vite dans la console Replit
```

### **Problèmes Courants**

**"Session Vinted expirée"**
→ Reconnecter votre compte Vinted dans Settings

**"Quota exceeded"**
→ Vérifier `/auth/me` pour voir vos limites

**"Captcha détecté"**
→ Utiliser le mode Draft au lieu d'auto-publish

---

## 📝 Structure du Projet

```
vintedbot/
├── backend/                # Backend FastAPI
│   ├── api/               # Routes API v1
│   ├── core/              # Core modules (storage, vinted client, session)
│   ├── data/              # Database + uploads
│   ├── middleware/        # Middlewares (quotas, etc.)
│   ├── routes/            # Routes legacy
│   ├── schemas/           # Pydantic schemas
│   ├── utils/             # Utilities
│   ├── app.py            # FastAPI app
│   └── jobs.py           # Scheduler jobs
│
├── frontend/              # Frontend React
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── contexts/     # React contexts (Auth)
│   │   ├── pages/        # Pages (Dashboard, Analytics, etc.)
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
└── README.md             # This file
```

---

## 🤝 Support

Pour toute question ou problème :
- Consulter la documentation API : http://localhost:8000/docs
- Vérifier les logs backend et frontend
- Tester avec le mode mock (OPENAI_API_KEY non requis)

---

**VintedBot** - Automatisez votre business Vinted avec l'IA 🚀
