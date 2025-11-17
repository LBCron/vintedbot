# 🔍 BUGS TROUVÉS - SIMULATION DE DÉPLOIEMENT

**Date:** 17 Novembre 2025
**Type:** Simulation de déploiement complet
**Méthode:** Analyse statique + tests d'imports + vérification configuration

---

## 🔴 BUGS CRITIQUES TROUVÉS (3)

### BUG #48: Incohérence de ports Dockerfile vs Fly.io 🔥

**Gravité:** 🔴 CRITIQUE - BLOQUE LE DÉPLOIEMENT

**Fichiers affectés:**
- `backend/Dockerfile:56, 63`
- `fly.toml:8, 17`

**Problème:**
```dockerfile
# Dockerfile
EXPOSE 8001
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8001"]
```

```toml
# fly.toml
[env]
PORT = "8000"

[http_service]
internal_port = 8000
```

**Impact:**
- ❌ L'app démarre sur port 8001
- ❌ Fly.io route le traffic vers port 8000
- ❌ **503 Service Unavailable** garanti au déploiement!

**Fix:**
```dockerfile
# Option 1: Changer Dockerfile pour utiliser variable ENV
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

OU

```toml
# Option 2: Changer fly.toml pour matcher
[env]
PORT = "8001"

[http_service]
internal_port = 8001
```

---

### BUG #49: fly.staging.toml port mismatch 🔥

**Gravité:** 🔴 CRITIQUE - BLOQUE DÉPLOIEMENT STAGING

**Fichiers affectés:**
- `backend/Dockerfile:63`
- `fly.staging.toml:13, 22, 37`

**Problème:**
- Dockerfile utilise port 8001
- fly.staging.toml attend port 8080 (3 endroits!)

**Impact:**
- ❌ Déploiement staging cassé
- ❌ Healthchecks échouent
- ❌ Pas d'accès à l'app

**Fix:**
Choisir UN port et l'utiliser partout. Recommandation: 8080 pour staging, 8000 pour prod.

```dockerfile
# Dockerfile - utiliser variable ENV
ENV PORT=8000
EXPOSE ${PORT}
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT}"]
```

---

### BUG #50: Healthcheck timeout trop court 🔥

**Gravité:** 🔴 CRITIQUE - PEUT CAUSER RESTART LOOPS

**Fichiers affectés:**
- `backend/Dockerfile:59`
- `fly.staging.toml:32`

**Problème:**
```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=5s
```

```toml
# fly.staging.toml
timeout = "5s"
```

**Impact:**
- ❌ 5 secondes trop court pour apps avec cold start
- ❌ Playwright init peut prendre 3-5 secondes
- ❌ Database connection peut timeout
- ❌ App marquée unhealthy alors qu'elle démarre

**Fix:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3
```

```toml
[[http_service.checks]]
  timeout = "10s"  # Au moins 10 secondes
```

---

## 🟠 BUGS ÉLEVÉS TROUVÉS (5)

### BUG #51: Section [[statics]] invalide dans fly.staging.toml

**Gravité:** 🟠 ÉLEVÉ - Configuration invalide

**Fichier:** `fly.staging.toml:61-63`

**Problème:**
```toml
[[statics]]
  guest_path = "/app/static"
  url_prefix = "/static"
```

**Impact:**
- ❌ Syntaxe invalide pour Fly.io v2
- ❌ Fichiers statiques ne seront pas servis
- ❌ Peut causer erreur au deployment

**Fix:**
```toml
# Supprimer [[statics]], utiliser http_service à la place
[http_service]
  ...
  [[http_service.static_files]]
    guest_path = "/app/static"
    url_prefix = "/static"
```

---

### BUG #52: Dockerfile runs as root

**Gravité:** 🟠 ÉLEVÉ - Sécurité

**Fichier:** `backend/Dockerfile`

**Problème:**
- Aucune directive `USER` dans le Dockerfile
- App s'exécute en tant que root (UID 0)

**Impact:**
- ❌ Violation des best practices de sécurité
- ❌ Si l'app est compromise, attaquant a accès root
- ❌ Fichiers créés appartiennent à root

**Fix:**
```dockerfile
# Après COPY, avant CMD
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### BUG #53: .dockerignore ignore *.md (documentation)

**Gravité:** 🟡 MOYEN - Manque documentation

**Fichier:** `backend/.dockerignore:34`

**Problème:**
```dockerignore
*.md
```

**Impact:**
- ❌ README.md, API docs, etc. non inclus dans l'image
- ❌ Pas de documentation disponible en production
- ❌ Debugging plus difficile

**Fix:**
```dockerignore
# Garder la documentation importante
!README.md
!API_DOCS.md
*.md
```

---

### BUG #54: Missing environment validation script

**Gravité:** 🟡 MOYEN - Déploiement fragile

**Problème:**
- Aucun script pour valider que toutes les variables d'environnement requises sont définies
- Déploiement peut échouer silencieusement

**Variables requises (selon fly.staging.toml:66-77):**
```
DATABASE_URL
REDIS_URL
S3_ACCESS_KEY
S3_SECRET_KEY
OPENAI_API_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_STARTER
STRIPE_PRICE_PRO
STRIPE_PRICE_ENTERPRISE
JWT_SECRET
ENCRYPTION_KEY  # Ajouté dans nos fixes
SECRET_KEY  # Ajouté dans nos fixes
```

**Fix:**
Créer `backend/validate_env.py`:
```python
#!/usr/bin/env python3
import os
import sys

REQUIRED_VARS = [
    "DATABASE_URL",
    "REDIS_URL",
    "OPENAI_API_KEY",
    "STRIPE_SECRET_KEY",
    "JWT_SECRET",
    "ENCRYPTION_KEY",
    "SECRET_KEY",
]

missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing:
    print(f"❌ Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

print("✅ All required environment variables are set")
```

---

### BUG #55: Pas de validation des secrets Fly.io

**Gravité:** 🟡 MOYEN - Erreurs de déploiement

**Problème:**
- `fly.staging.toml` liste les secrets requis en commentaire
- Pas de script pour vérifier qu'ils sont définis dans Fly.io

**Fix:**
Créer `scripts/validate_fly_secrets.sh`:
```bash
#!/bin/bash
REQUIRED_SECRETS=(
  "DATABASE_URL"
  "REDIS_URL"
  "STRIPE_SECRET_KEY"
  "JWT_SECRET"
  "ENCRYPTION_KEY"
)

for secret in "${REQUIRED_SECRETS[@]}"; do
  if ! flyctl secrets list | grep -q "$secret"; then
    echo "❌ Missing secret: $secret"
    exit 1
  fi
done

echo "✅ All required secrets are set"
```

---

## 🟡 BUGS MOYENS TROUVÉS (7)

### BUG #56: Services section duplicated in fly.staging.toml

**Gravité:** 🟡 MOYEN - Configuration confuse

**Fichiers:** `fly.staging.toml:21-27, 35-52`

**Problème:**
- `[http_service]` section (lignes 21-33)
- `[[services]]` section (lignes 35-52)
- Les deux configurent le même service HTTP

**Impact:**
- ❌ Configuration ambiguë
- ❌ Peut causer comportement inattendu
- ❌ Fly.io peut ignorer une des sections

**Fix:**
Utiliser SOIT `[http_service]` SOIT `[[services]]`, pas les deux.

Recommandation: Garder `[http_service]` (syntaxe v2), supprimer `[[services]]`.

---

### BUG #57: Memory allocation differs between configs

**Gravité:** 🟡 MOYEN - Incohérence

**Fichiers:**
- `fly.toml:31` - `memory_mb = 512`
- `fly.staging.toml:58` - `memory = "512mb"`

**Problème:**
- Syntaxe différente pour la même valeur
- `[[vm]]` vs `[compute]`

**Impact:**
- ❌ Confusion sur la configuration
- ❌ Migrations difficiles

**Fix:**
Utiliser la même syntaxe partout (recommandation: `[compute]` est plus récent).

---

### BUG #58: Playwright browser download at runtime

**Gravité:** 🟡 MOYEN - Démarrage lent

**Fichier:** `backend/Dockerfile:45`

**Problème:**
```dockerfile
RUN playwright install chromium
```

**Impact:**
- ✅ Browser téléchargé au build (CORRECT)
- Mais: Si Dockerfile cache invalide, re-download
- Image size ~500MB

**Optimisation:**
```dockerfile
# Télécharger seulement le strict nécessaire
RUN playwright install --with-deps chromium-headless-shell
```

---

### BUG #59: No Redis connection retry logic

**Gravité:** 🟡 MOYEN - Startup failures

**Fichier:** `backend/core/cache.py:40-57`

**Problème:**
- Une seule tentative de connexion Redis
- Si Redis démarre après l'app, pas de retry

**Impact:**
- ❌ App démarre sans cache si Redis pas prêt
- ❌ Pas de reconnexion automatique

**Fix:**
Ajouter retry logic avec backoff exponentiel.

---

### BUG #60: Missing CORS configuration validation

**Gravité:** 🟡 MOYEN - Sécurité

**Fichier:** `backend/settings.py:30-31`

**Problème:**
```python
ALLOWED_ORIGINS: str = "*"
CORS_ORIGINS: List[str] = ["*"]
```

**Impact:**
- ❌ Accepte requêtes de n'importe quel domaine
- ❌ Permet attaques CSRF depuis sites malveillants

**Fix:**
```python
# Bloquer wildcard en production
if self.ENV == "production":
    if "*" in self.CORS_ORIGINS:
        raise ValueError("CORS wildcard not allowed in production")
```

---

### BUG #61: SQLite path hardcoded for production

**Gravité:** 🟡 MOYEN - Peut causer data loss

**Fichier:** `backend/settings.py:26-27`

**Problème:**
```python
@property
def VINTEDBOT_DATABASE_URL(self) -> str:
    return f"sqlite:///{self.DATA_DIR}/db.sqlite"
```

**Impact:**
- ❌ SQLite en production (pas idéal, devrait utiliser PostgreSQL)
- ❌ Si container restart, data peut être perdue
- ❌ Pas de backups automatiques

**Recommandation:**
Forcer PostgreSQL en production:
```python
if self.ENV == "production":
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "sqlite" in db_url:
        raise ValueError("PostgreSQL required in production")
```

---

### BUG #62: Pas de logging structured en production

**Gravité:** 🟡 MOYEN - Debugging difficile

**Problème:**
- Pas de configuration de logging pour JSON output
- Logs texte difficiles à parser par monitoring tools

**Fix:**
Ajouter structured logging (JSON) pour production.

---

## 🟢 BUGS BAS / OPTIMISATIONS (5)

### BUG #63: Dockerfile multi-stage build missing

**Gravité:** 🟢 BAS - Optimisation

**Impact:**
- Image Docker plus grosse que nécessaire
- Includes build tools in runtime image

**Fix:**
Utiliser multi-stage build pour réduire image size de ~30%.

---

### BUG #64: No database migration check on startup

**Gravité:** 🟢 BAS - DX

**Problème:**
- App démarre même si migrations pas appliquées
- Peut causer erreurs runtime

**Fix:**
Ajouter check au startup:
```python
async def check_migrations():
    # Vérifier version de schema
    # Refuser de démarrer si migrations pending
```

---

### BUG #65: Missing application metrics

**Gravité:** 🟢 BAS - Observabilité

**Problème:**
- Pas de métriques Prometheus exposées
- Pas de /metrics endpoint

**Fix:**
Ajouter `prometheus-fastapi-instrumentator`.

---

### BUG #66: No rate limiting configured

**Gravité:** 🟢 BAS - DoS protection

**Problème:**
- Pas de rate limiting global visible
- Vulnérable à abuse

**Fix:**
Ajouter SlowAPI ou équivalent.

---

### BUG #67: Health check only tests HTTP

**Gravité:** 🟢 BAS - Faux positifs

**Fichier:** `backend/Dockerfile:60`

**Problème:**
```dockerfile
CMD curl -f http://localhost:8001/health || exit 1
```

**Impact:**
- ❌ Ne teste pas database connection
- ❌ Ne teste pas Redis connection
- ❌ App peut être "healthy" mais non-fonctionnelle

**Fix:**
Endpoint `/health` devrait tester:
- Database connectivity
- Redis connectivity
- Critical services availability

---

## 📊 STATISTIQUES

**Total bugs trouvés:** 20 nouveaux bugs
- 🔴 Critiques: 3
- 🟠 Élevés: 5
- 🟡 Moyens: 7
- 🟢 Bas: 5

**Catégories:**
- Configuration: 8 bugs
- Sécurité: 4 bugs
- Performance: 3 bugs
- Observabilité: 3 bugs
- Autre: 2 bugs

**Impact déploiement:**
- 🔴 **3 bugs bloquants** qui empêchent le déploiement
- 🟠 5 bugs qui causent problèmes en production
- 🟡 7 bugs qui réduisent fiabilité
- 🟢 5 optimisations recommandées

---

## ✅ CORRECTIONS PRIORITAIRES

### Phase 1: AVANT DÉPLOIEMENT (CRITIQUE)

1. **BUG #48**: Fixer port mismatch Dockerfile/fly.toml
2. **BUG #49**: Fixer port mismatch fly.staging.toml
3. **BUG #50**: Augmenter healthcheck timeout à 10s

**Temps estimé:** 30 minutes

### Phase 2: SÉCURITÉ (ÉLEVÉ)

4. **BUG #52**: Ajouter USER non-root au Dockerfile
5. **BUG #54**: Créer script validation environnement
6. **BUG #60**: Bloquer CORS wildcard en production

**Temps estimé:** 1-2 heures

### Phase 3: ROBUSTESSE (MOYEN)

7. **BUG #51**: Corriger section statics
8. **BUG #56**: Résoudre duplication services
9. **BUG #59**: Ajouter Redis retry logic
10. **BUG #61**: Forcer PostgreSQL en production

**Temps estimé:** 2-4 heures

---

## 🎯 ACTIONS IMMÉDIATES

**AVANT de déployer, FAIRE:**

```bash
# 1. Fixer ports
sed -i 's/PORT = "8000"/PORT = "8001"/' fly.toml
sed -i 's/internal_port = 8000/internal_port = 8001/' fly.toml

# 2. Fixer healthcheck timeout
sed -i 's/--timeout=5s/--timeout=10s/' backend/Dockerfile

# 3. Ajouter USER non-root
# Éditer Dockerfile manuellement

# 4. Valider config
fly doctor

# 5. Test local
docker build -t vintedbot-test -f backend/Dockerfile .
docker run -p 8001:8001 -e ENV=production vintedbot-test

# 6. Déployer
fly deploy --config fly.toml
```

---

**Rapport généré:** 17 Novembre 2025
**Méthode:** Simulation de déploiement + analyse statique
**Statut:** ⚠️ 3 BUGS CRITIQUES À CORRIGER AVANT DÉPLOIEMENT
