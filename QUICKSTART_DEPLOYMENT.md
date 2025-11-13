# 🚀 Quickstart : Déployer le Système de Stockage

**5 minutes pour déployer le système de stockage multi-tier**

---

## ✅ Étape 1 : Validation Pré-Déploiement (30 secondes)

```bash
# Exécuter le script de validation
./scripts/validate_storage_deployment.sh

# Résultat attendu :
# ✓ Aucune erreur détectée
# ✓ Système prêt pour le déploiement !
```

---

## 🔑 Étape 2 : Configurer Cloudflare R2 (2 minutes)

### Créer le bucket

1. Aller sur https://dash.cloudflare.com → R2
2. Créer bucket : `vintedbot-photos`
3. Noter l'account ID dans l'URL

### Créer API Token

1. R2 → Manage R2 API Tokens
2. Create API Token
3. Permissions : Object Read & Write
4. Copier les credentials :
   - Access Key ID
   - Secret Access Key
   - Endpoint URL : `https://[account-id].r2.cloudflarestorage.com`

### Configurer sur Fly.io

```bash
flyctl secrets set \
  R2_ENDPOINT_URL="https://[TON-ACCOUNT-ID].r2.cloudflarestorage.com" \
  R2_ACCESS_KEY_ID="[TON-ACCESS-KEY]" \
  R2_SECRET_ACCESS_KEY="[TON-SECRET]" \
  R2_BUCKET_NAME="vintedbot-photos" \
  --app vintedbot-backend
```

---

## 📦 Étape 3 : (Optionnel) Configurer Backblaze B2 (2 minutes)

**Si tu veux COLD storage (recommandé pour économiser 60%)**

### Créer le bucket

1. Aller sur https://www.backblaze.com/b2
2. Créer bucket : `vintedbot-archive` (Private)

### Créer Application Key

1. App Keys → Add New
2. Permissions : Read & Write
3. Copier :
   - keyID
   - applicationKey

### Configurer sur Fly.io

```bash
flyctl secrets set \
  B2_APPLICATION_KEY_ID="[TON-KEY-ID]" \
  B2_APPLICATION_KEY="[TON-APP-KEY]" \
  B2_BUCKET_NAME="vintedbot-archive" \
  --app vintedbot-backend
```

---

## 🚢 Étape 4 : Déployer (1 minute)

```bash
# Depuis /home/user/vintedbot
flyctl deploy --app vintedbot-backend

# Attendre le build et le déploiement...
# ✓ Build successful
# ✓ Deployment successful
```

---

## ✅ Étape 5 : Tester (30 secondes)

```bash
# Test 1 : Health check
curl https://vintedbot-backend.fly.dev/health
# {"status": "healthy"}

# Test 2 : Storage info
curl https://vintedbot-backend.fly.dev/api/storage/tiers/info | jq
# {
#   "ok": true,
#   "tiers": { "temp": {...}, "hot": {...}, "cold": {...} }
# }

# Test 3 : Stats (devrait être vide au début)
curl https://vintedbot-backend.fly.dev/api/storage/stats | jq
# {
#   "temp_count": 0,
#   "hot_count": 0,
#   "cold_count": 0,
#   ...
# }
```

---

## 🎉 C'est Fait !

Le système de stockage multi-tier est maintenant déployé et fonctionnel.

### Prochaines étapes

1. **Accéder à l'interface** : https://votredomaine.com/storage
2. **Uploader une photo test** via le frontend
3. **Vérifier les métriques** dans l'interface
4. **Surveiller les coûts** (devrait être ~$0.01/mois au début)

### Lifecycle automatique

Le job s'exécute automatiquement chaque jour à **3h AM** :
- ✓ Supprime photos TEMP expirées
- ✓ Supprime photos publiées (7j)
- ✓ Promotionne TEMP → HOT
- ✓ Archive HOT → COLD
- ✓ Supprime photos anciennes

Voir les logs :
```bash
flyctl logs --app vintedbot-backend | grep STORAGE
```

---

## 🐛 Problèmes ?

### "Access Denied" sur R2

```bash
# Vérifier les secrets
flyctl secrets list --app vintedbot-backend | grep R2

# Reconfigurer si nécessaire
flyctl secrets set R2_ACCESS_KEY_ID="nouveau_key" --app vintedbot-backend
```

### "B2 credentials not configured"

C'est normal si tu n'as pas configuré B2. Le système fonctionne avec TEMP + HOT seulement.

### Photos ne sont pas supprimées

```bash
# Forcer un run manuel du lifecycle job
curl -X POST https://vintedbot-backend.fly.dev/api/storage/lifecycle/run-now \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 Documentation Complète

Pour plus de détails :
- **Guide complet** : DEPLOYMENT_STORAGE.md
- **Documentation** : backend/storage/README.md
- **Tests** : backend/storage/test_storage.py

---

**Temps total : ~5 minutes** ⏱️

**Économies attendues : 99%** 💰

**Support** : Consulter les logs avec `flyctl logs --app vintedbot-backend`
