# Multi-Tier Photo Storage System

Système de stockage multi-tier optimisé pour minimiser les coûts tout en maintenant de bonnes performances.

## 📊 Architecture

### Les 3 Tiers de Stockage

#### **TIER 1 - TEMP** (Fly.io Volumes)
- **Coût:** Gratuit
- **Durée:** 24-48 heures
- **Usage:** Stockage temporaire pour photos en attente d'analyse IA
- **Path:** `/app/backend/data/photos/temp/`

#### **TIER 2 - HOT** (Cloudflare R2)
- **Coût:** $0.015/GB/mois
- **Egress:** Gratuit (CDN illimité)
- **Durée:** Jusqu'à 90 jours
- **Usage:** Stockage actif pour drafts non publiés
- **CDN:** URLs publiques optimisées

#### **TIER 3 - COLD** (Backblaze B2)
- **Coût:** $0.006/GB/mois (60% moins cher que HOT)
- **Durée:** Jusqu'à 365 jours
- **Usage:** Archive long terme pour photos rarement accédées
- **Egress:** $0.01/GB (après 3× gratuit)

## 🔄 Lifecycle des Photos

```
┌─────────────────────────────────────────────────────────────┐
│                    Photo Upload                              │
│                         ↓                                     │
│              TIER 1 (TEMP) - 48h                             │
│                         ↓                                     │
│              ┌──────────┴──────────┐                         │
│              │                     │                         │
│         Publié sur           Draft reste                     │
│           Vinted              non publié                     │
│              │                     │                         │
│       Garde 7 jours          TIER 2 (HOT)                   │
│       puis DELETE             90 jours                       │
│                                    │                         │
│                            TIER 3 (COLD)                     │
│                               365 jours                      │
│                                    │                         │
│                                 DELETE                        │
└─────────────────────────────────────────────────────────────┘
```

### Règles de Lifecycle

1. **Upload** → Photo sauvegardée dans TIER 1 (TEMP)
   - Compression automatique (50-70% réduction)
   - Durée: 48 heures

2. **Si publiée sur Vinted** → Garde 7 jours puis DELETE
   - Économie de ~80% des coûts (photos déjà sur Vinted)

3. **Si draft non publié** → TEMP → HOT après 48h
   - Promotion automatique vers stockage permanent

4. **Après 90 jours sans accès** → HOT → COLD
   - Archivage automatique vers stockage moins cher

5. **Après 365 jours** → DELETE
   - Suppression définitive

## 💾 Modules

### `storage_manager.py`
Orchestrateur principal pour toutes les opérations de stockage.

**Méthodes principales:**
```python
# Upload photo
metadata = await storage_manager.upload_photo(
    user_id="user123",
    file_data=photo_bytes,
    filename="photo.jpg",
    draft_id="draft_abc"  # optionnel
)

# Marquer comme publié sur Vinted
await storage_manager.mark_published_to_vinted(photo_id)

# Promouvoir vers HOT storage
await storage_manager.promote_to_hot_storage(photo_id)

# Archiver vers COLD storage
await storage_manager.archive_to_cold_storage(photo_id)

# Supprimer photo
await storage_manager.delete_photo(photo_id)

# Obtenir URL CDN
url = await storage_manager.get_photo_url(photo_id)
```

### `tier1_local.py`
Gestion du stockage local (Fly.io Volumes).

- Upload/download synchrone
- Pas de CDN (fichiers locaux)
- Gratuit

### `tier2_r2.py`
Gestion Cloudflare R2 (HOT storage).

**Configuration requise (env vars):**
```env
R2_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=vintedbot-photos
R2_CDN_DOMAIN=photos.votredomaine.com  # optionnel
```

### `tier3_b2.py`
Gestion Backblaze B2 (COLD storage).

**Configuration requise (env vars):**
```env
B2_APPLICATION_KEY_ID=xxx
B2_APPLICATION_KEY=xxx
B2_BUCKET_NAME=vintedbot-archive
```

### `compression.py`
Compression d'images pour réduire les coûts.

**Optimisations:**
- Réduction qualité JPEG (85%)
- Resize max 2000×2000px
- Conversion RGBA → RGB pour JPEG
- Progressive JPEG pour chargement optimisé

**Résultats:**
- 50-70% réduction de taille
- Qualité visuelle préservée

### `lifecycle_manager.py`
Gestion automatique du cycle de vie des photos.

**Job quotidien (3h du matin):**
1. Supprime photos TEMP expirées (>48h)
2. Supprime photos publiées (>7j après publication)
3. Promotionne TEMP → HOT (drafts >48h)
4. Archive HOT → COLD (>90j sans accès)
5. Supprime COLD → permanent (>365j)

### `metrics.py`
Tracking des coûts et usage du stockage.

**Métriques disponibles:**
```python
# Stats globales
stats = await metrics.get_storage_stats()
# {
#   "temp_count": 150,
#   "temp_size_gb": 0.5,
#   "hot_count": 5000,
#   "hot_size_gb": 50,
#   "cold_count": 2000,
#   "cold_size_gb": 20,
#   "total_count": 7150,
#   "total_size_gb": 70.5,
#   "monthly_cost_estimate": 0.87,
#   "savings_vs_all_hot": 14.63
# }

# Détail des coûts par tier
breakdown = await metrics.get_cost_breakdown()

# Recommandations d'optimisation
recommendations = await metrics.get_optimization_recommendations()
```

## 🛠️ API Endpoints

### Upload Photo
```http
POST /api/storage/upload
Content-Type: multipart/form-data

file: <photo.jpg>
draft_id: "draft_abc"  # optionnel

Response:
{
  "photo_id": "550e8400-e29b-41d4-a716-446655440000",
  "tier": "temp",
  "file_size_bytes": 2048000,
  "compressed_size_bytes": 614400,
  "compression_ratio": 70.0,
  "scheduled_deletion": "2025-11-15T15:00:00Z",
  "cdn_url": null
}
```

### Marquer Draft Comme Publié
```http
POST /api/storage/drafts/{draft_id}/publish
{
  "draft_id": "draft_abc",
  "photo_ids": ["photo1", "photo2", "photo3"]
}

Response:
{
  "ok": true,
  "message": "Draft draft_abc marked as published. Photos will be deleted in 7 days.",
  "results": {
    "updated_count": 3,
    "failed": []
  }
}
```

### Stats de Stockage
```http
GET /api/storage/stats

Response:
{
  "temp_count": 150,
  "temp_size_gb": 0.5,
  "hot_count": 5000,
  "hot_size_gb": 50,
  "cold_count": 2000,
  "cold_size_gb": 20,
  "total_count": 7150,
  "total_size_gb": 70.5,
  "monthly_cost_estimate": 0.87,
  "savings_vs_all_hot": 14.63
}
```

### Détail Coûts
```http
GET /api/storage/stats/breakdown

Response:
{
  "ok": true,
  "breakdown": {
    "temp": {"cost": 0.00, "size_gb": 0.5, "percentage": 0},
    "hot": {"cost": 0.75, "size_gb": 50, "percentage": 86},
    "cold": {"cost": 0.12, "size_gb": 20, "percentage": 14},
    "total": 0.87
  }
}
```

### Métriques Lifecycle
```http
GET /api/storage/metrics/lifecycle?days=30

Response:
{
  "ok": true,
  "period_days": 30,
  "metrics": {
    "photos_uploaded": 1000,
    "photos_promoted": 200,
    "photos_archived": 50,
    "photos_deleted": 750
  }
}
```

### Recommandations
```http
GET /api/storage/metrics/recommendations

Response:
{
  "ok": true,
  "recommendations": [
    "✅ Stockage bien optimisé !"
  ],
  "count": 1
}
```

### URL Photo
```http
GET /api/storage/photo/{photo_id}/url

Response:
{
  "ok": true,
  "photo_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://photos.votredomaine.com/hot/550e8400-e29b-41d4-a716-446655440000.jpg"
}
```

### Metadata Photo
```http
GET /api/storage/photo/{photo_id}/metadata

Response:
{
  "ok": true,
  "metadata": {
    "photo_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123",
    "tier": "hot",
    "upload_date": "2025-11-13T10:00:00Z",
    "last_access_date": "2025-11-13T10:00:00Z",
    "scheduled_deletion": null,
    "file_size_bytes": 2048000,
    "compressed_size_bytes": 614400,
    "draft_id": "draft_abc",
    "published_to_vinted": false
  }
}
```

### Supprimer Photo
```http
DELETE /api/storage/photo/{photo_id}

Response:
{
  "ok": true,
  "message": "Photo 550e8400-e29b-41d4-a716-446655440000 deleted successfully",
  "photo_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Usage Utilisateur
```http
GET /api/storage/user/usage

Response:
{
  "ok": true,
  "user_id": "user123",
  "usage": {
    "total_photos": 50,
    "total_size_gb": 2.5,
    "by_tier": {
      "temp": {"count": 5, "size_gb": 0.1},
      "hot": {"count": 40, "size_gb": 2.0},
      "cold": {"count": 5, "size_gb": 0.4}
    }
  }
}
```

### Lancer Lifecycle Manuellement (Admin)
```http
POST /api/storage/lifecycle/run-now

Response:
{
  "ok": true,
  "message": "Lifecycle job completed successfully",
  "stats": {
    "temp_deleted": 10,
    "published_deleted": 50,
    "promoted_to_hot": 5,
    "archived_to_cold": 2,
    "old_deleted": 1
  }
}
```

### Info sur les Tiers
```http
GET /api/storage/tiers/info

Response:
{
  "ok": true,
  "tiers": {
    "temp": {
      "name": "TIER 1 - TEMP",
      "storage": "Fly.io Volumes",
      "cost_per_gb": 0.00,
      "duration": "24-48 hours",
      "description": "Temporary storage for photos awaiting AI analysis",
      "rules": [...]
    },
    ...
  },
  "lifecycle_summary": {
    "upload": "Photo → TEMP (48h)",
    "published": "Published → delete after 7 days (saves 80% cost)",
    "draft": "Draft → TEMP (48h) → HOT (90 days) → COLD (365 days) → delete",
    "total_lifecycle": "Max 365 days retention"
  }
}
```

## ⏰ Cron Job

Job quotidien configuré dans `backend/jobs.py`:

```python
# Storage lifecycle - daily at 3 AM
scheduler.add_job(
    storage_lifecycle_job,
    trigger=CronTrigger(hour=3, minute=0),
    id="storage_lifecycle",
    name="Storage Lifecycle Manager",
    replace_existing=True
)
```

**Actions:**
- 🗑️ Suppression photos expirées
- ⬆️ Promotion TEMP → HOT
- 📦 Archivage HOT → COLD
- 🔥 Suppression définitive COLD anciennes

## 💰 Économies de Coûts

### Scénario Exemple

**Workflow typique:**
- 1000 photos uploadées/mois
- 800 photos publiées sur Vinted (80%)
- 200 photos en drafts non publiés

**Sans système multi-tier (tout en HOT):**
- 1000 photos × 2 MB = 2 GB
- 2 GB × $0.015 = **$0.03/mois**
- Après 1 an: 24 GB × $0.015 = **$0.36/mois**

**Avec système multi-tier:**
- 800 photos publiées → supprimées après 7j
- 200 photos en drafts → HOT (90j) → COLD
- COLD: ~150 photos × 2 MB = 0.3 GB × $0.006 = **$0.002/mois**
- HOT: ~50 photos × 2 MB = 0.1 GB × $0.015 = **$0.0015/mois**
- **Total: ~$0.004/mois** (vs $0.36)

**Économie: 99% !** 🎉

### Calculateur de Coûts

```python
from backend.storage.metrics import StorageMetrics

metrics = StorageMetrics()
stats = await metrics.get_storage_stats()

print(f"Coût mensuel: ${stats['monthly_cost_estimate']}")
print(f"Économies vs all-HOT: ${stats['savings_vs_all_hot']}")
```

## 📊 Base de Données

### Table `photo_metadata`

```sql
CREATE TABLE photo_metadata (
    photo_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    draft_id TEXT,
    tier TEXT NOT NULL CHECK(tier IN ('temp','hot','cold')),
    file_size_bytes INTEGER NOT NULL,
    compressed_size_bytes INTEGER NOT NULL,
    upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
    last_access_date TEXT DEFAULT CURRENT_TIMESTAMP,
    scheduled_deletion TEXT,
    published_to_vinted INTEGER DEFAULT 0,
    published_date TEXT,
    access_count INTEGER DEFAULT 0,
    storage_path TEXT,
    cdn_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (draft_id) REFERENCES drafts(id) ON DELETE SET NULL
);
```

**Indexes:**
- `idx_photos_user` - Par user_id
- `idx_photos_tier` - Par tier
- `idx_photos_draft` - Par draft_id
- `idx_photos_scheduled_deletion` - Par scheduled_deletion
- `idx_photos_published` - Par published_to_vinted
- `idx_photos_upload_date` - Par upload_date
- `idx_photos_last_access` - Par last_access_date

## 🚀 Déploiement

### 1. Configurer Variables d'Environnement

**Cloudflare R2 (obligatoire):**
```env
R2_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=vintedbot-photos
R2_CDN_DOMAIN=photos.votredomaine.com  # optionnel mais recommandé
```

**Backblaze B2 (optionnel mais recommandé):**
```env
B2_APPLICATION_KEY_ID=xxx
B2_APPLICATION_KEY=xxx
B2_BUCKET_NAME=vintedbot-archive
```

### 2. Installer Dépendances

```bash
pip install -r requirements.txt
```

Dépendances ajoutées:
- `boto3==1.34.10` (déjà présent)
- `pillow==11.1.0` (déjà présent)
- `b2sdk==2.1.0` (nouveau)

### 3. Créer Buckets

**Cloudflare R2:**
1. Dashboard Cloudflare → R2 → Create Bucket
2. Nom: `vintedbot-photos`
3. Créer API Token (Read & Write)
4. Configurer CDN (optionnel)

**Backblaze B2:**
1. Dashboard B2 → Create Bucket
2. Nom: `vintedbot-archive`
3. Bucket Settings → Private
4. Generate Application Key

### 4. Déployer

```bash
cd backend
flyctl deploy --app vintedbot-backend
```

### 5. Vérifier

```bash
# Health check
curl https://vintedbot-backend.fly.dev/health

# Storage stats
curl https://vintedbot-backend.fly.dev/api/storage/stats
```

## 🐛 Troubleshooting

### Erreur: "R2_ENDPOINT_URL not found"

```bash
# Vérifier secrets
flyctl secrets list --app vintedbot-backend

# Configurer si manquant
flyctl secrets set \
  R2_ENDPOINT_URL="https://xxx.r2.cloudflarestorage.com" \
  R2_ACCESS_KEY_ID="xxx" \
  R2_SECRET_ACCESS_KEY="xxx" \
  R2_BUCKET_NAME="vintedbot-photos" \
  --app vintedbot-backend
```

### Erreur: "B2 credentials not configured"

B2 est optionnel. Sans B2, le système fonctionne avec TEMP et HOT seulement.

Pour activer COLD storage:
```bash
flyctl secrets set \
  B2_APPLICATION_KEY_ID="xxx" \
  B2_APPLICATION_KEY="xxx" \
  B2_BUCKET_NAME="vintedbot-archive" \
  --app vintedbot-backend
```

### Photos ne sont pas supprimées

Vérifier que le lifecycle job tourne:
```bash
# Voir logs
flyctl logs --app vintedbot-backend | grep STORAGE

# Lancer manuellement
curl -X POST https://vintedbot-backend.fly.dev/api/storage/lifecycle/run-now \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📈 Monitoring

### Métriques à Surveiller

1. **Coût mensuel estimé**
   ```bash
   curl https://vintedbot-backend.fly.dev/api/storage/stats | jq '.monthly_cost_estimate'
   ```

2. **Distribution par tier**
   ```bash
   curl https://vintedbot-backend.fly.dev/api/storage/stats/breakdown
   ```

3. **Recommandations**
   ```bash
   curl https://vintedbot-backend.fly.dev/api/storage/metrics/recommendations
   ```

4. **Lifecycle metrics**
   ```bash
   curl https://vintedbot-backend.fly.dev/api/storage/metrics/lifecycle?days=7
   ```

### Alertes Recommandées

- Coût mensuel > $50
- TEMP photos > 1000 (lifecycle job en panne?)
- HOT storage > 100 GB (trop de photos non archivées)

## 🎯 Bonnes Pratiques

1. **Toujours marquer les drafts comme publiés** quand ils sont sur Vinted
   ```python
   await storage_manager.mark_published_to_vinted(photo_id)
   ```

2. **Utiliser le CDN pour les photos HOT** (gratuit avec R2)
   ```python
   url = await storage_manager.get_photo_url(photo_id)
   ```

3. **Monitorer les coûts régulièrement**
   ```python
   stats = await metrics.get_storage_stats()
   if stats['monthly_cost_estimate'] > 50:
       # Alert!
   ```

4. **Ne pas désactiver le lifecycle job** (économie de 80%+)

5. **Configurer B2 pour archives** (60% moins cher que R2)

---

**Système déployé et fonctionnel ✅**

Pour questions/bugs: Créer une issue sur GitHub
