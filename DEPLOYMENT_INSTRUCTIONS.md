# 🚀 Instructions de Déploiement - Sprint 2

flyctl n'est pas disponible dans cet environnement. Suivez ces instructions pour déployer depuis votre machine locale.

---

## ✅ ÉTAPES DE DÉPLOIEMENT

### 1. Pull les derniers changements

```bash
# Sur votre machine locale
cd ~/vintedbot  # ou votre chemin
git pull origin claude/vintedbot-ui-improvements-011CV6EA4SLB23emooDqKQto
```

### 2. Générer les clés de chiffrement

```bash
# Backend encryption key
cd backend/security
python encryption.py

# Copier la clé affichée (format: ENCRYPTION_KEY=...)
# Exemple output:
# ================================================================================
# NEW ENCRYPTION KEY (SAVE THIS TO .env AS ENCRYPTION_KEY)
# ================================================================================
# qL8x9W3vN5mK2pT6yR4jH7sD1fG3bV9cX8zM2nL5kP4wQ6tY1rE3oA7uI9hG2dF5=
# ================================================================================
```

### 3. Configurer les secrets Fly.io

```bash
cd backend

# Set encryption key
flyctl secrets set ENCRYPTION_KEY="<votre-clé-générée>" --app vintedbot-backend

# Vérifier que JWT_SECRET existe
flyctl secrets list --app vintedbot-backend

# Si JWT_SECRET n'existe pas, le générer:
python security/jwt_manager.py
flyctl secrets set JWT_SECRET="<votre-jwt-secret>" --app vintedbot-backend

# Vérifier OPENAI_API_KEY (pour auto-messages IA)
# Si pas encore configuré:
flyctl secrets set OPENAI_API_KEY="sk-..." --app vintedbot-backend
```

### 4. Déployer le Backend

```bash
cd backend

# Deploy
flyctl deploy --app vintedbot-backend

# Vérifier le statut
flyctl status --app vintedbot-backend

# Voir les logs
flyctl logs --app vintedbot-backend
```

### 5. Déployer le Frontend

```bash
cd ../frontend

# Deploy (pas de changements mais redéploie quand même)
flyctl deploy --app vintedbot-frontend

# Vérifier
flyctl status --app vintedbot-frontend
```

---

## ✅ VÉRIFICATION POST-DÉPLOIEMENT

### Test Backend API

```bash
# Health check
curl https://vintedbot-backend.fly.dev/health

# Test Sprint 2 endpoints
curl https://vintedbot-backend.fly.dev/docs
# Devrait afficher Swagger avec les nouveaux endpoints
```

### Test nouveaux endpoints

Ouvrez https://vintedbot-backend.fly.dev/docs et vérifiez que vous voyez :

**Automation endpoints**:
- `POST /automation/auto-bump/enable`
- `POST /automation/auto-follow/add-targets`
- `POST /automation/auto-messages/enable`
- `POST /automation/schedule/publications`

**Security endpoints**:
- `POST /auth/connect-vinted`
- `POST /auth/2fa/setup`
- `POST /auth/2fa/verify`
- `POST /auth/refresh`

### Test Frontend

```bash
# Ouvrir l'app
open https://vintedbot-frontend.fly.dev

# Login et vérifier que tout fonctionne
```

---

## 📋 CHECKLIST DE DÉPLOIEMENT

- [ ] Git pull effectué
- [ ] Encryption key générée
- [ ] Secrets Fly.io configurés (ENCRYPTION_KEY, JWT_SECRET, OPENAI_API_KEY)
- [ ] Backend déployé
- [ ] Frontend déployé
- [ ] Health checks passés
- [ ] Swagger docs affichent nouveaux endpoints
- [ ] Login fonctionne
- [ ] Test d'un endpoint Sprint 2

---

## 🆘 TROUBLESHOOTING

### Erreur: "ENCRYPTION_KEY not found"

```bash
# Vérifier les secrets
flyctl secrets list --app vintedbot-backend

# Si ENCRYPTION_KEY manque, le set:
flyctl secrets set ENCRYPTION_KEY="<votre-clé>" --app vintedbot-backend
```

### Erreur: "Module 'backend.automation' not found"

Le backend n'a peut-être pas détecté les nouveaux dossiers. Redéployer:

```bash
cd backend
flyctl deploy --app vintedbot-backend --force
```

### Backend crash au démarrage

Voir les logs:

```bash
flyctl logs --app vintedbot-backend -n 100
```

Erreurs communes:
- Secret manquant → Configurer le secret
- Import error → Vérifier que tous les fichiers sont committes et pushés
- Database error → Vérifier que la DB existe et est accessible

---

## 🎯 COMMANDES UTILES

```bash
# Logs en temps réel
flyctl logs --app vintedbot-backend

# SSH dans le container
flyctl ssh console --app vintedbot-backend

# Redémarrer l'app
flyctl apps restart vintedbot-backend

# Voir les machines
flyctl machine list --app vintedbot-backend

# Scale up/down
flyctl scale count 2 --app vintedbot-backend  # 2 instances
```

---

## ✅ SPRINT 2 DÉPLOYÉ !

Une fois déployé, vous aurez :

✅ **Auto-Bump** - Remonte automatiquement vos annonces
✅ **Auto-Follow** - Follow ciblé et intelligent
✅ **Auto-Messages** - Réponses automatiques GPT-4
✅ **Scheduler** - Publications programmées
✅ **Security** - Chiffrement AES-256, JWT, 2FA
✅ **Vinted Auth** - Connexion automatique email/password

**Backend**: https://vintedbot-backend.fly.dev
**Frontend**: https://vintedbot-frontend.fly.dev
**Docs**: https://vintedbot-backend.fly.dev/docs

---

**🚀 Bon déploiement !**
