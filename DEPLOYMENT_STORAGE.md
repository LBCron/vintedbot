# 🚀 Guide de Déploiement - Système de Stockage Multi-Tier

Ce guide explique comment déployer le système de stockage photo multi-tier sur Fly.io avec Cloudflare R2 et Backblaze B2.

---

## 📋 Prérequis

- ✅ Compte Fly.io (app `vintedbot-backend` déjà créée)
- ⬜ Compte Cloudflare avec R2 activé
- ⬜ Compte Backblaze B2 (optionnel mais recommandé)

---

## ÉTAPE 1 : Configurer Cloudflare R2 (HOT Storage)

### 1.1 Créer le Bucket R2

```bash
# Via Cloudflare Dashboard
1. Aller sur https://dash.cloudflare.com
2. Cliquer sur "R2" dans le menu gauche
3. Cliquer "Create bucket"
4. Nom du bucket : "vintedbot-photos"
5. Location : Automatic (ou choisir région proche de tes users)
6. Cliquer "Create bucket"
```

### 1.2 Créer les API Tokens R2

```bash
# Dans le dashboard Cloudflare R2
1. Aller dans "R2" → "Overview"
2. Cliquer "Manage R2 API Tokens"
3. Cliquer "Create API Token"
4. Nom : "VintedBot Storage"
5. Permissions : "Object Read & Write"
6. Buckets : "vintedbot-photos" (ou "All buckets")
7. TTL : Never expire
8. Cliquer "Create API Token"

# ⚠️ SAUVEGARDER IMMÉDIATEMENT :
- Access Key ID : s3_abc123...
- Secret Access Key : def456...
- Endpoint URL : https://[account-id].r2.cloudflarestorage.com
```

### 1.3 (Optionnel) Configurer CDN Public

Pour avoir des URLs publiques optimisées :

```bash
# Dans R2 Dashboard → vintedbot-photos
1. Onglet "Settings"
2. Section "Public access"
3. Cliquer "Allow Access"
4. Copier le domaine R2.dev : vintedbot-photos.r2.dev

# OU configurer custom domain :
1. Section "Custom Domains"
2. Cliquer "Connect Domain"
3. Entrer : photos.votredomaine.com
4. Suivre instructions DNS
```

---

## ÉTAPE 2 : Configurer Backblaze B2 (COLD Storage)

### 2.1 Créer le Bucket B2

```bash
# Via Backblaze Dashboard
1. Aller sur https://www.backblaze.com/b2/cloud-storage.html
2. Se connecter à ton compte
3. Aller dans "Buckets"
4. Cliquer "Create a Bucket"
5. Nom : "vintedbot-archive"
6. Files in Bucket : Private
7. Default Encryption : Disable (optionnel)
8. Object Lock : Disable
9. Cliquer "Create a Bucket"
```

### 2.2 Créer Application Key

```bash
# Dans B2 Dashboard
1. Aller dans "App Keys"
2. Cliquer "Add a New Application Key"
3. Name : "VintedBot Archive Storage"
4. Allow access to Bucket(s) : vintedbot-archive
5. Type of Access : Read and Write
6. Allow List All Bucket Names : ✓
7. Cliquer "Create New Key"

# ⚠️ SAUVEGARDER IMMÉDIATEMENT :
- keyID : 005a1b2c3d4e5f6...
- applicationKey : K005abc123...
```

---

## ÉTAPE 3 : Configurer Secrets Fly.io

### 3.1 Configurer R2 (Obligatoire)

```bash
flyctl secrets set \
  R2_ENDPOINT_URL="https://[VOTRE-ACCOUNT-ID].r2.cloudflarestorage.com" \
  R2_ACCESS_KEY_ID="[VOTRE-R2-ACCESS-KEY-ID]" \
  R2_SECRET_ACCESS_KEY="[VOTRE-R2-SECRET-KEY]" \
  R2_BUCKET_NAME="vintedbot-photos" \
  --app vintedbot-backend

# Si tu as configuré un CDN/custom domain :
flyctl secrets set \
  R2_CDN_DOMAIN="photos.votredomaine.com" \
  --app vintedbot-backend

# OU si tu utilises R2.dev :
flyctl secrets set \
  R2_CDN_DOMAIN="vintedbot-photos.r2.dev" \
  --app vintedbot-backend
```

### 3.2 Configurer B2 (Optionnel mais recommandé)

```bash
flyctl secrets set \
  B2_APPLICATION_KEY_ID="[VOTRE-B2-KEY-ID]" \
  B2_APPLICATION_KEY="[VOTRE-B2-APPLICATION-KEY]" \
  B2_BUCKET_NAME="vintedbot-archive" \
  --app vintedbot-backend
```

### 3.3 Vérifier les Secrets

```bash
# Lister tous les secrets configurés
flyctl secrets list --app vintedbot-backend

# Tu devrais voir :
# - R2_ENDPOINT_URL
# - R2_ACCESS_KEY_ID
# - R2_SECRET_ACCESS_KEY
# - R2_BUCKET_NAME
# - R2_CDN_DOMAIN (si configuré)
# - B2_APPLICATION_KEY_ID (si B2 activé)
# - B2_APPLICATION_KEY (si B2 activé)
# - B2_BUCKET_NAME (si B2 activé)
```

---

## ÉTAPE 4 : Déployer sur Fly.io

### 4.1 Build et Deploy

```bash
# Depuis le dossier /home/user/vintedbot
cd /home/user/vintedbot

# Déployer
flyctl deploy --app vintedbot-backend

# Cela va :
# 1. Builder l'image Docker
# 2. Installer les nouvelles dépendances (b2sdk)
# 3. Redémarrer l'app avec les nouveaux secrets
# 4. Lancer le cron job de lifecycle à 3 AM
```

### 4.2 Suivre le Déploiement

```bash
# Voir les logs en temps réel
flyctl logs --app vintedbot-backend

# Tu devrais voir :
# ✅ HEIC/HEIF support registered for PIL
# ✅ Backend ready on port 5000
# 📊 Scheduler started with 7 jobs
#    - Storage Lifecycle: 0 3 * * * (daily at 03:00)
```

---

## ÉTAPE 5 : Tester le Système

### 5.1 Test Santé API

```bash
# Vérifier que l'API est up
curl https://vintedbot-backend.fly.dev/health

# Response attendue :
# {"status": "healthy"}
```

### 5.2 Test Endpoint Storage

```bash
# Obtenir info sur les tiers
curl https://vintedbot-backend.fly.dev/api/storage/tiers/info | jq

# Response attendue :
# {
#   "ok": true,
#   "tiers": {
#     "temp": { ... },
#     "hot": { ... },
#     "cold": { ... }
#   }
# }
```

### 5.3 Test Stats Storage

```bash
# Obtenir statistiques (devrait être vide au début)
curl https://vintedbot-backend.fly.dev/api/storage/stats | jq

# Response attendue :
# {
#   "temp_count": 0,
#   "hot_count": 0,
#   "cold_count": 0,
#   "total_size_gb": 0,
#   "monthly_cost_estimate": 0
# }
```

### 5.4 Test Upload Photo (avec authentification)

```bash
# D'abord, login pour obtenir un token
TOKEN=$(curl -X POST https://vintedbot-backend.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ton@email.com","password":"ton_password"}' \
  | jq -r '.access_token')

# Upload une photo test
curl -X POST https://vintedbot-backend.fly.dev/api/storage/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/test_photo.jpg" \
  -F "draft_id=test_draft_123" \
  | jq

# Response attendue :
# {
#   "photo_id": "550e8400-...",
#   "tier": "temp",
#   "file_size_bytes": 2048000,
#   "compressed_size_bytes": 614400,
#   "compression_ratio": 70.0,
#   "scheduled_deletion": "2025-11-15T...",
#   "cdn_url": null
# }
```

---

## ÉTAPE 6 : Monitoring & Vérification

### 6.1 Vérifier le Cron Job

```bash
# Vérifier que le lifecycle job est bien configuré
flyctl logs --app vintedbot-backend | grep "Storage Lifecycle"

# Tu devrais voir au démarrage :
# "Storage Lifecycle: 0 3 * * * (daily at 03:00)"
```

### 6.2 Tester le Lifecycle Job Manuellement

```bash
# Lancer manuellement le job (nécessite admin auth)
curl -X POST https://vintedbot-backend.fly.dev/api/storage/lifecycle/run-now \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq

# Response attendue :
# {
#   "ok": true,
#   "message": "Lifecycle job completed successfully",
#   "stats": {
#     "temp_deleted": 0,
#     "published_deleted": 0,
#     "promoted_to_hot": 0,
#     "archived_to_cold": 0,
#     "old_deleted": 0
#   }
# }
```

### 6.3 Vérifier R2 Bucket

```bash
# Via Cloudflare Dashboard
1. Aller dans R2 → vintedbot-photos
2. Tu devrais voir un dossier "hot/" si des photos ont été uploadées
3. Vérifier la taille du bucket

# Via CLI (si configuré)
wrangler r2 object list vintedbot-photos --prefix hot/
```

### 6.4 Vérifier B2 Bucket (si configuré)

```bash
# Via Backblaze Dashboard
1. Aller dans Buckets → vintedbot-archive
2. Après 90 jours, tu devrais voir un dossier "cold/"
3. Vérifier la taille et le nombre d'objets
```

---

## 📊 Métriques à Surveiller

### Quotidien

```bash
# Stats de stockage
curl https://vintedbot-backend.fly.dev/api/storage/stats | jq

# Recommandations d'optimisation
curl https://vintedbot-backend.fly.dev/api/storage/metrics/recommendations | jq
```

### Hebdomadaire

```bash
# Détail des coûts par tier
curl https://vintedbot-backend.fly.dev/api/storage/stats/breakdown | jq

# Métriques de lifecycle (7 derniers jours)
curl https://vintedbot-backend.fly.dev/api/storage/metrics/lifecycle?days=7 | jq
```

### Mensuel

```bash
# Coût mensuel estimé
curl https://vintedbot-backend.fly.dev/api/storage/stats | jq '.monthly_cost_estimate'

# Comparer avec facture Cloudflare R2
# Comparer avec facture Backblaze B2
```

---

## 🐛 Troubleshooting

### Erreur : "R2_ENDPOINT_URL not found"

```bash
# Vérifier que le secret est bien configuré
flyctl secrets list --app vintedbot-backend | grep R2

# Si manquant, reconfigurer :
flyctl secrets set R2_ENDPOINT_URL="https://xxx.r2.cloudflarestorage.com" --app vintedbot-backend
```

### Erreur : "Access Denied" sur R2

```bash
# Vérifier les permissions du token R2
# 1. Dashboard Cloudflare → R2 → Manage R2 API Tokens
# 2. Vérifier que le token a bien "Object Read & Write"
# 3. Vérifier que le bucket "vintedbot-photos" est autorisé

# Recréer le token si nécessaire
# Puis reconfigurer :
flyctl secrets set \
  R2_ACCESS_KEY_ID="nouveau_key_id" \
  R2_SECRET_ACCESS_KEY="nouveau_secret" \
  --app vintedbot-backend
```

### Photos ne sont pas supprimées

```bash
# Vérifier que le cron job tourne
flyctl logs --app vintedbot-backend | grep STORAGE

# Forcer un run manuel
curl -X POST https://vintedbot-backend.fly.dev/api/storage/lifecycle/run-now \
  -H "Authorization: Bearer $TOKEN"

# Vérifier les logs
flyctl logs --app vintedbot-backend --tail
```

### B2 ne fonctionne pas (optionnel)

```bash
# Le système peut fonctionner sans B2 (seulement TEMP et HOT)
# Pour activer B2 :
flyctl secrets set \
  B2_APPLICATION_KEY_ID="xxx" \
  B2_APPLICATION_KEY="xxx" \
  B2_BUCKET_NAME="vintedbot-archive" \
  --app vintedbot-backend

# Redéployer
flyctl deploy --app vintedbot-backend
```

---

## 💰 Estimation des Coûts

### Scénario Réaliste

**Usage typique :**
- 1000 photos uploadées/mois
- 800 photos publiées sur Vinted (80%)
- 200 photos en drafts non publiés

**Coûts mensuels :**

```
TIER 1 (TEMP - Fly.io Volumes) :
  → Gratuit (inclus dans Fly.io)

TIER 2 (HOT - Cloudflare R2) :
  → ~50 photos actives × 2 MB = 0.1 GB
  → 0.1 GB × $0.015/GB = $0.0015/mois
  → Egress : GRATUIT

TIER 3 (COLD - Backblaze B2) :
  → ~150 photos archivées × 2 MB = 0.3 GB
  → 0.3 GB × $0.006/GB = $0.0018/mois
  → Egress : 3× gratuit, puis $0.01/GB

TOTAL : ~$0.003 - $0.01/mois
```

**Vs. Sans système multi-tier (tout en HOT) :**
```
→ 1000 photos × 2 MB = 2 GB
→ 2 GB × $0.015/GB = $0.03/mois (premier mois)
→ Après 1 an : 24 GB × $0.015 = $0.36/mois

Économie : 99% ! 🎉
```

---

## 📈 Scaling

### Si ton volume augmente (10,000+ photos/mois)

1. **Activer B2** si pas encore fait (économie de 60% sur archives)
2. **Augmenter Fly.io Volumes** pour TEMP storage
3. **Optimiser compression** (réduire quality à 80)
4. **Réduire retention** (archives à 180 jours au lieu de 365)

### Configuration avancée

```bash
# Variables optionnelles pour tuning
flyctl secrets set \
  STORAGE_COMPRESSION_QUALITY="80" \
  STORAGE_MAX_WIDTH="1800" \
  STORAGE_COLD_RETENTION_DAYS="180" \
  --app vintedbot-backend
```

---

## ✅ Checklist Finale

Avant de considérer le déploiement comme réussi :

- [ ] R2 bucket créé et accessible
- [ ] B2 bucket créé (optionnel)
- [ ] Secrets Fly.io configurés
- [ ] Déploiement réussi sans erreurs
- [ ] API health check OK
- [ ] Endpoint /api/storage/tiers/info répond
- [ ] Upload d'une photo test fonctionne
- [ ] Photo apparaît dans R2 bucket
- [ ] Lifecycle job configuré (vérifier logs)
- [ ] Métriques accessibles
- [ ] Coûts surveillés

---

## 🎯 Prochaines Étapes

Une fois déployé avec succès :

1. **Intégrer avec le frontend** pour upload de photos
2. **Configurer alertes** (coût > $50, erreurs lifecycle)
3. **Monitorer pendant 1 semaine** pour valider le workflow
4. **Ajuster la compression** selon feedback utilisateurs
5. **Documenter pour l'équipe** comment utiliser le système

---

**Support :** Si problème, vérifier les logs avec `flyctl logs --app vintedbot-backend` et consulter le README.md dans backend/storage/

**Documentation complète :** backend/storage/README.md
