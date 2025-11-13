# VintedBot - AI-Powered Vinted Automation Platform

## 🎯 Overview
VintedBot est la plateforme d'automatisation Vinted la plus sophistiquée du marché, combinant analyse IA (GPT-4 Vision), analytics dashboard unique, et automation premium (auto-bump, auto-follow, auto-messages). Interface React moderne + backend FastAPI robuste.

## 👤 User Preferences
- Communication: Français, langage simple et clair
- Zero failed drafts requirement - validation stricte avant création
- Mode Draft préféré pour éviter les captchas Vinted

## 🏗️ Architecture Globale

### **Backend (Python FastAPI)**
- API REST complète avec 17 tables SQLite
- Scheduler APScheduler (6 jobs automatiques)
- Playwright pour automation Vinted (bump/follow/messages)
- GPT-4 Vision pour analyse photos
- JWT authentication + quotas par plan
- Chiffrement AES-256 pour sessions Vinted

### **Frontend (React + TypeScript)**
- React 18 + Vite + TailwindCSS
- 10 pages complètes (Dashboard, Upload, Analytics, Automation, Accounts, Settings)
- Mobile-first responsive design
- Recharts pour graphiques analytics
- JWT interceptor Axios
- 228 packages installés avec Bun

## ✨ Fonctionnalités Premium Uniques

### 1. 📊 **Analytics Dashboard** (UNIQUE - absent des concurrents)
- Performance heatmap jour/heure
- Top/bottom performers
- Analyse par catégorie
- Métriques temps réel : vues, likes, messages, conversion rate

### 2. 🔄 **Auto-Bump Intelligent**
- Delete + recreate pour remonter en tête (économise vs bumps payants 0.95€)
- Rotation intelligente + skip recent bumps
- Scheduler automatique toutes les 5 min
- Tracking analytics de chaque bump

### 3. 👥 **Auto-Follow/Unfollow**
- Follow automatique d'utilisateurs ciblés
- Auto-unfollow après X jours si pas de follow-back
- Prévention duplicates
- Tracking complet dans table `follows`

### 4. 💬 **Auto-Messages**
- Templates avec variables (`{{username}}`, `{{item_title}}`, `{{price}}`)
- Typing caractère par caractère (50-150ms delays)
- Déclencheurs configurables
- Limites quotidiennes

### 5. 🤖 **Analyse IA Photos (GPT-4 Vision)**
- Upload multiple jusqu'à 500 photos
- Génération automatique : titre, description, prix, catégorie, taille, couleur, marque, état
- Auto-batching pour >25 photos
- Hashtags automatiques (3-5 en fin de description)

## 🗄️ Base de Données (17 Tables SQLite)

### Tables Principales
- `users` - Comptes utilisateurs avec JWT
- `listings` - Annonces Vinted publiées
- `drafts` - Brouillons en attente
- `bulk_jobs` - Jobs d'analyse IA
- `photo_plans` - Plans de grouping photos

### Tables Premium (Nouvelles - Nov 2025)
- `analytics_events` - Tracking vues/likes/messages
- `aggregated_metrics` - Métriques pré-calculées
- `automation_rules` - Configuration automation (bump/follow/messages)
- `automation_jobs` - Historique exécutions
- `vinted_accounts` - Multi-comptes Vinted
- `message_templates` - Templates messages
- `conversations` - Historique conversations
- `follows` - Tracking follow/unfollow

## 📊 Scheduler Automatique (6 Jobs)

1. **Inbox Sync** - Toutes les 15 min (sync conversations Vinted)
2. **Publish Queue Poll** - Toutes les 30s (vérifie publications en attente)
3. **Price Drop** - Quotidien 03:00 (réduction 5% avec floor protection)
4. **Vacuum & Prune** - Quotidien 02:00 (nettoie anciens drafts/logs)
5. **Clean Temp Photos** - Toutes les 6h (supprime dossiers >24h)
6. **Automation Executor** - Toutes les 5 min ⭐ (exécute auto-bump/follow/messages)

## 🔐 Authentification & Sécurité

### JWT Authentication
- Tokens avec expiration configurable
- Refresh tokens pour sessions longues
- AuthContext React pour état global

### Quotas par Plan
| Plan | AI Analyses | Drafts | Publications | Storage |
|------|-------------|--------|--------------|---------|
| Free | 20/mois | 50 | 10/mois | 500 MB |
| Starter | 100/mois | 200 | 50/mois | 2 GB |
| Pro | 500/mois | 1000 | 200/mois | 10 GB |
| Scale | Illimité | Illimité | Illimité | 50 GB |

### Vinted Session Management
- Chiffrement AES-256 pour cookies/user-agents
- Session vault avec rotation automatique
- Détection captcha intelligente

## 🛡️ Anti-Détection Vinted

### Mesures Playwright
- Délais aléatoires entre actions (1000-3000ms)
- Typing caractère par caractère avec timing humain
- Multiple selectors pour robustesse
- User-agents réalistes
- Gestion cookies avancée

### Workflow Automation
- Auto-bump : vérifie last bump, rotation, skip recent
- Auto-follow : vérifie duplicates, respect daily limits
- Auto-messages : délais variables, templates réalistes

## 📡 API Structure (FastAPI)

### Routes Authentification
- `POST /auth/register` - Créer compte
- `POST /auth/login` - Se connecter
- `GET /auth/me` - Infos user + quotas

### Routes Upload & IA
- `POST /bulk/photos/analyze` - Upload + analyse GPT-4 Vision
- `GET /bulk/jobs/{job_id}` - Suivi progression
- `GET /bulk/drafts` - Liste brouillons
- `PATCH /bulk/drafts/{id}` - Modifier
- `POST /bulk/drafts/{id}/publish` - Publier (auto ou draft mode)

### Routes Analytics (PREMIUM)
- `GET /analytics/dashboard` - Dashboard complet
- `POST /analytics/events/view` - Track vue
- `POST /analytics/events/like` - Track like
- `POST /analytics/events/message` - Track message

### Routes Automation (PREMIUM)
- `GET /automation/rules` - Liste règles
- `POST /automation/bump/configure` - Config auto-bump
- `POST /automation/follow/configure` - Config auto-follow
- `POST /automation/messages/configure` - Config auto-messages
- `POST /automation/bump/execute` - Exécuter bump manuel
- `POST /automation/follow/execute` - Exécuter follow manuel

### Routes Multi-Account
- `GET /accounts/list` - Liste comptes Vinted
- `POST /accounts/add` - Ajouter compte
- `POST /accounts/{id}/switch` - Switch compte actif
- `DELETE /accounts/{id}` - Supprimer compte

## 🎨 Frontend React (10 Pages)

### Pages Publiques
1. `/login` - Connexion JWT
2. `/register` - Inscription

### Pages Protégées
3. `/` - Dashboard (stats + recent drafts)
4. `/upload` - Upload photos drag-drop
5. `/drafts` - Liste brouillons avec filtres
6. `/drafts/:id` - Édition draft individuel
7. **`/analytics`** - Dashboard analytics (UNIQUE)
8. **`/automation`** - Panel automation (auto-bump/follow/messages)
9. `/accounts` - Multi-account management
10. `/settings` - Profil + quotas + subscription

### Composants Réutilisables
- `Layout`, `Navbar`, `Sidebar` - Structure
- `ProtectedRoute` - Auth guard
- `LoadingSpinner`, `QuotaCard`, `DraftCard`, `StatsCard`
- `HeatmapChart` - Graphique Recharts

## 🚀 Workflows Replit

### Backend Workflow
```bash
Name: VintedBot Backend
Command: uvicorn backend.app:app --host 0.0.0.0 --port 8000
Port: 8000
Output: console
```

### Frontend Workflow
```bash
Name: VintedBot Frontend
Command: cd frontend && bun run dev
Port: 5000
Output: webview
```

## 🔧 Configuration Variables

### Obligatoires (Replit Secrets)
- `OPENAI_API_KEY` - Clé OpenAI pour GPT-4 Vision

### Optionnelles - Stripe
- `STRIPE_SECRET_KEY` - Paiements
- `STRIPE_WEBHOOK_SECRET` - Webhooks
- `STRIPE_STARTER_PRICE_ID` - Plan Starter
- `STRIPE_PRO_PRICE_ID` - Plan Pro
- `STRIPE_SCALE_PRICE_ID` - Plan Scale

### Optionnelles - CORS
- `ALLOWED_ORIGINS` - Origins autorisées (défaut: localhost)

## 🎯 Différenciateurs vs Concurrents

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
| Frontend React | ✅ | ❌ | ❌ | ❌ |

## 📝 Règles Strictes AI

### Titres (≤70 chars)
- Format: "Catégorie Couleur Marque Taille – État"
- Exemple: "Jogging noir Burberry XS – bon état"
- NO emojis, NO parenthèses, NO mesures

### Descriptions
- 5-8 lignes factuelles
- ZERO emojis, ZERO marketing phrases
- Hashtags 3-5 TOUJOURS à la fin
- Structure: quoi, état, matière, taille, mesures, shipping

### Tailles Normalisées
- Enfant/ado auto-converti vers adulte (16Y → XS)
- Format simple: XS/S/M/L/XL
- NO détails supplémentaires dans size field

### Conditions Normalisées
- Mapping français automatique
- Valeurs standard: "neuf avec étiquette", "très bon état", "bon état", "satisfaisant"

## 🐛 Debugging

### Logs Backend
```bash
tail -f backend/data/app.log
curl http://localhost:8000/health
```

### Logs Frontend
```bash
# Console navigateur F12
# Ou logs Vite dans console Replit
```

### Problèmes Courants
- Session expirée → Reconnect account in Settings
- Quota exceeded → Check /auth/me
- Captcha détecté → Use Draft mode

## 📦 Structure Fichiers

```
vintedbot/
├── backend/
│   ├── api/v1/routers/          # Routes API
│   │   ├── analytics.py         # Analytics dashboard
│   │   ├── automation.py        # Auto-bump/follow/messages
│   │   ├── accounts.py          # Multi-account
│   │   └── ...
│   ├── core/
│   │   ├── storage.py           # SQLite database
│   │   ├── vinted_client.py     # Playwright automation
│   │   └── session.py           # Encrypted session vault
│   ├── data/
│   │   ├── vbs.db              # Main database
│   │   └── uploads/            # User uploads
│   ├── app.py                  # FastAPI app
│   └── jobs.py                 # Scheduler (6 jobs)
├── frontend/
│   ├── src/
│   │   ├── api/client.ts       # API client + JWT
│   │   ├── pages/              # 10 pages React
│   │   ├── components/         # 9 components
│   │   └── contexts/           # AuthContext
│   └── vite.config.ts
└── README.md
```

## 🎓 Next Steps Development
- ✅ Analytics dashboard operational
- ✅ Automation executor scheduler running
- ✅ Frontend React complet
- 🔄 Mobile app (future)
- 🔄 Chrome extension (future)
