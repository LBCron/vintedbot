# 🎯 Améliorations Implémentées - VintedBot API

## 📦 Ce Qui A Été Fait (24 Oct 2025)

### ✅ Packages Installés
```bash
✓ tenacity==9.1.2          # Retry logic avec exponential backoff
✓ prometheus-client==0.23.1 # Métriques pour monitoring
✓ sqlmodel==0.0.27         # ORM pour SQLite (déjà présent)
✓ loguru==0.7.3            # Logging avancé (déjà présent)
✓ psutil==7.1.1            # Monitoring système (déjà présent)
```

### ✅ Fichiers Créés

#### 1. `backend/core/metrics.py` (147 lignes)
**Module de métriques Prometheus complet**

Métriques disponibles :
- `vintedbot_publish_total{status}` - Publications par statut (success/fail/captcha/timeout)
- `vintedbot_publish_duration_seconds` - Durée des publications
- `vintedbot_publish_retry_count{attempt}` - Nombre de retries
- `vintedbot_photo_analyze_total{status}` - Analyses IA
- `vintedbot_photo_analyze_duration_seconds` - Durée analyse IA
- `vintedbot_gpt4_vision_calls_total{status}` - Appels GPT-4 Vision
- `vintedbot_publish_queue_size` - Taille de la queue
- `vintedbot_bulk_job_active_total` - Jobs bulk actifs
- `vintedbot_captcha_detected_total{type}` - Captchas détectés
- `vintedbot_captcha_solved_total` - Captchas résolus
- `vintedbot_captcha_failure_total{reason}` - Échecs captcha
- `vintedbot_active_users` - Utilisateurs actifs
- `vintedbot_publish_per_user_total{user_id}` - Publications par user
- `vintedbot_draft_created_total{publish_ready}` - Brouillons créés
- `vintedbot_draft_validation_failures{reason}` - Échecs validation
- `vintedbot_app_info` - Info application

**Usage :**
```python
from backend.core.metrics import publish_total, publish_duration_seconds

# Incrémenter compteur
publish_total.labels(status="success").inc()

# Observer durée
with publish_duration_seconds.time():
    await publish_listing(draft_id)
```

---

#### 2. `backend/core/retry_utils.py` (123 lignes)
**Utilitaires de retry avec exponential backoff**

**Exceptions définies :**
- `RetryableVintedError` - Base pour erreurs retryables
- `VintedNetworkError` - Erreurs réseau
- `VintedTimeoutError` - Timeouts
- `VintedRateLimitError` - Rate limits
- `CaptchaDetectedError` - Captchas (retryable si solver disponible)
- `AIAnalysisError` - Erreurs OpenAI temporaires

**Décorateurs disponibles :**

```python
from backend.core.retry_utils import retry_publish_operation

# Pour publications Vinted (3 tentatives max, backoff 5-60s)
@retry_publish_operation(max_attempts=3, min_wait=5, max_wait=60)
async def publish_listing(draft_id):
    # Votre code ici
    pass
```

```python
from backend.core.retry_utils import retry_ai_analysis

# Pour analyses IA (2 tentatives max, backoff 3-30s)
@retry_ai_analysis(max_attempts=2, min_wait=3, max_wait=30)
async def analyze_photos(photos):
    # Votre code ici
    pass
```

```python
from backend.core.retry_utils import retry_captcha_solve

# Pour résolution captchas (2 tentatives max, backoff 10-30s)
@retry_captcha_solve(max_attempts=2, min_wait=10, max_wait=30)
async def solve_captcha(sitekey, pageurl):
    # Votre code ici
    pass
```

---

#### 3. `backend/api/v1/routers/metrics.py` (29 lignes)
**Endpoint Prometheus `/metrics`**

**Usage :**
```bash
# Tester localement
curl http://localhost:5000/metrics

# Configuration Prometheus
scrape_configs:
  - job_name: 'vintedbot'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Exemple de sortie :**
```
# HELP vintedbot_publish_total Total publications attempts
# TYPE vintedbot_publish_total counter
vintedbot_publish_total{status="success"} 42
vintedbot_publish_total{status="fail"} 3
vintedbot_publish_total{status="captcha"} 2

# HELP vintedbot_publish_duration_seconds Duration of publication process
# TYPE vintedbot_publish_duration_seconds histogram
vintedbot_publish_duration_seconds_bucket{le="5.0"} 10
vintedbot_publish_duration_seconds_bucket{le="30.0"} 35
...
```

---

## 🚀 Comment Activer les Améliorations

### Étape 1: Activer l'endpoint /metrics

**Éditer `backend/app.py` :**
```python
# Ligne 23 - Ajouter import
from backend.api.v1.routers import ingest, health as health_v1, vinted, bulk, ai, metrics

# Ligne 127 - Ajouter router
app.include_router(metrics.router, tags=["monitoring"])
```

**Redémarrer le serveur :**
```bash
# Le serveur redémarrera automatiquement
curl http://localhost:5000/metrics
```

---

### Étape 2: Ajouter Retry Logic à la Publication Vinted

**Éditer `backend/api/v1/routers/vinted.py` :**

```python
# En haut du fichier (après ligne 16)
from backend.core.retry_utils import (
    retry_publish_operation,
    VintedNetworkError,
    VintedTimeoutError,
    CaptchaDetectedError
)
from backend.core.metrics import (
    publish_total,
    publish_duration_seconds,
    publish_retry_count,
    captcha_detected_total
)
import time

# Décorer la fonction publish_listing (ligne ~500)
@router.post("/listings/publish", response_model=ListingPublishResponse)
@limiter.limit("5/minute")
@retry_publish_operation(max_attempts=3, min_wait=5, max_wait=60)
async def publish_listing(
    request: ListingPublishRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    """
    Publish a prepared listing (Phase B - Publish)
    
    NOW WITH RETRY LOGIC + METRICS
    """
    start_time = time.time()
    
    try:
        # ... code existant ...
        
        # Si captcha détecté, incrémenter métrique
        if await client.detect_challenge(page):
            captcha_detected_total.labels(type="unknown").inc()
            raise CaptchaDetectedError("Captcha detected")
        
        # Success
        publish_total.labels(status="success").inc()
        publish_duration_seconds.observe(time.time() - start_time)
        
        return ListingPublishResponse(...)
        
    except CaptchaDetectedError:
        publish_total.labels(status="captcha").inc()
        # Retry automatique via décorateur
        raise
    except Exception as e:
        publish_total.labels(status="fail").inc()
        raise
```

---

### Étape 3: Ajouter Métriques à l'Analyse IA

**Éditer `backend/core/ai_analyzer.py` :**

```python
# En haut du fichier
from backend.core.metrics import (
    photo_analyze_total,
    photo_analyze_duration_seconds,
    gpt4_vision_calls_total
)
from backend.core.retry_utils import retry_ai_analysis, AIAnalysisError
import time

# Dans la fonction batch_analyze_photos
@retry_ai_analysis(max_attempts=2)
async def batch_analyze_photos(photos, auto_grouping=True):
    start_time = time.time()
    
    try:
        # ... code existant ...
        
        # Incrémenter appel GPT-4
        gpt4_vision_calls_total.labels(status="success").inc()
        
        # Success
        photo_analyze_total.labels(status="completed").inc()
        photo_analyze_duration_seconds.observe(time.time() - start_time)
        
        return results
        
    except OpenAIError as e:
        gpt4_vision_calls_total.labels(status="error").inc()
        photo_analyze_total.labels(status="failed").inc()
        
        # Retry si erreur temporaire
        if "rate_limit" in str(e).lower():
            raise AIAnalysisError(f"OpenAI rate limit: {e}")
        raise
```

---

## 📊 Dashboard Grafana (Exemple)

**Créer un dashboard avec ces queries :**

```promql
# Publications par statut
sum(rate(vintedbot_publish_total[5m])) by (status)

# Durée moyenne des publications
histogram_quantile(0.95, sum(rate(vintedbot_publish_duration_seconds_bucket[5m])) by (le))

# Taux d'échec publications
rate(vintedbot_publish_total{status="fail"}[5m]) /
rate(vintedbot_publish_total[5m])

# Captchas détectés
sum(rate(vintedbot_captcha_detected_total[5m])) by (type)

# Queue size temps réel
vintedbot_publish_queue_size

# Durée analyse IA p95
histogram_quantile(0.95, sum(rate(vintedbot_photo_analyze_duration_seconds_bucket[5m])) by (le))
```

---

## 🔐 Intégration 2Captcha (Prochaine Étape)

**Créer `backend/core/captcha_solver.py` :**

```python
"""
2Captcha integration for automatic captcha solving
"""

import requests
import asyncio
from backend.settings import settings
from backend.core.retry_utils import retry_captcha_solve
from backend.core.metrics import captcha_solved_total, captcha_failure_total

class TwoCaptchaSolver:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
    
    @retry_captcha_solve(max_attempts=2, min_wait=10, max_wait=30)
    async def solve_hcaptcha(self, sitekey: str, pageurl: str) -> str:
        """
        Solve hCaptcha using 2Captcha API
        
        Args:
            sitekey: hCaptcha sitekey from page
            pageurl: URL of the page with captcha
            
        Returns:
            Solution token to inject in page
        """
        # 1. Create task
        resp = requests.post(f"{self.base_url}/in.php", data={
            "key": self.api_key,
            "method": "hcaptcha",
            "sitekey": sitekey,
            "pageurl": pageurl,
            "json": 1
        })
        
        if resp.json()["status"] != 1:
            captcha_failure_total.labels(reason="task_creation_failed").inc()
            raise Exception(f"2Captcha error: {resp.json()}")
        
        request_id = resp.json()["request"]
        
        # 2. Poll for solution (max 2 min)
        for _ in range(24):  # 24 × 5s = 120s max
            await asyncio.sleep(5)
            
            r = requests.get(
                f"{self.base_url}/res.php",
                params={
                    "key": self.api_key,
                    "action": "get",
                    "id": request_id,
                    "json": 1
                }
            )
            
            result = r.json()
            
            if result["status"] == 1:
                # Success
                captcha_solved_total.inc()
                return result["request"]
            
            if result["request"] == "CAPCHA_NOT_READY":
                continue
            
            # Error
            captcha_failure_total.labels(reason=result["request"]).inc()
            raise Exception(f"2Captcha error: {result['request']}")
        
        # Timeout
        captcha_failure_total.labels(reason="timeout").inc()
        raise Exception("2Captcha timeout after 120s")


# Usage dans Playwright
async def inject_captcha_solution(page, solution: str):
    """Inject 2Captcha solution into hCaptcha iframe"""
    await page.evaluate(f'''
        document.querySelector("[name='h-captcha-response']").value = "{solution}";
        document.querySelector("[name='g-recaptcha-response']").value = "{solution}";
    ''')
```

**Ajouter dans `.env` :**
```bash
TWOCAPTCHA_API_KEY=votre_cle_2captcha
```

**Utiliser dans `vinted.py` :**
```python
from backend.core.captcha_solver import TwoCaptchaSolver

# Dans publish_listing
if await client.detect_challenge(page):
    solver = TwoCaptchaSolver(settings.TWOCAPTCHA_API_KEY)
    
    # Extraire sitekey
    sitekey = await page.evaluate(
        'document.querySelector("[data-sitekey]").getAttribute("data-sitekey")'
    )
    
    # Résoudre
    solution = await solver.solve_hcaptcha(sitekey, page.url)
    
    # Injecter
    await inject_captcha_solution(page, solution)
    
    # Continuer publication
    await page.click("#submit-button")
```

---

## 📈 Roadmap d'Implémentation

### Phase 1: Monitoring (✅ FAIT - 1h)
- [x] Installer tenacity et prometheus-client
- [x] Créer module metrics.py
- [x] Créer retry_utils.py
- [x] Créer endpoint /metrics

### Phase 2: Intégration Basique (Prochain - 2h)
- [ ] Activer endpoint /metrics dans app.py
- [ ] Ajouter retry aux publications Vinted
- [ ] Ajouter métriques aux publications
- [ ] Tester avec dry_run=true

### Phase 3: Captcha Solver (3h)
- [ ] Créer compte 2Captcha
- [ ] Implémenter captcha_solver.py
- [ ] Intégrer dans workflow publication
- [ ] Tester résolution hCaptcha

### Phase 4: Monitoring Complet (2h)
- [ ] Setup Prometheus server
- [ ] Créer dashboard Grafana
- [ ] Configurer alertes (taux d'échec >10%)
- [ ] Ajouter logs structurés

### Phase 5: Multi-Users (8h)
- [ ] Créer table `users` SQLite
- [ ] Implémenter JWT auth
- [ ] Isolation données par user_id
- [ ] Tests concurrence

---

## 🧪 Tests Recommandés

### Test 1: Endpoint /metrics
```bash
curl http://localhost:5000/metrics

# Devrait retourner:
# HELP vintedbot_publish_total Total publications
# TYPE vintedbot_publish_total counter
...
```

### Test 2: Retry Logic
```python
# Simuler échec réseau
@retry_publish_operation(max_attempts=3)
async def test_retry():
    import random
    if random.random() < 0.7:
        raise VintedNetworkError("Simulated failure")
    return "Success"

# Devrait retry 2-3 fois puis réussir
```

### Test 3: Métriques Incrémentation
```python
from backend.core.metrics import publish_total

# Avant
initial = publish_total.labels(status="success")._value.get()

# Action
publish_total.labels(status="success").inc()

# Après
final = publish_total.labels(status="success")._value.get()
assert final == initial + 1
```

---

## 💡 Bonnes Pratiques

### DO ✅
- Toujours wrapper les appels externes avec retry
- Incrémenter les métriques dans finally blocks
- Logger chaque retry attempt
- Utiliser labels Prometheus pour segmentation
- Monitorer le p95 des durées (pas la moyenne)

### DON'T ❌
- Ne pas retry les erreurs 4xx (bad request)
- Ne pas stocker de secrets dans les métriques
- Ne pas exposer /metrics publiquement (firewall)
- Ne pas retry indéfiniment (max 3 attempts)
- Ne pas oublier d'incrémenter status="fail"

---

## 📚 Ressources

- **Tenacity docs:** https://tenacity.readthedocs.io/
- **Prometheus Python client:** https://github.com/prometheus/client_python
- **2Captcha API:** https://2captcha.com/2captcha-api
- **Grafana Dashboards:** https://grafana.com/grafana/dashboards/

---

**Date:** 24 Octobre 2025  
**Version:** 1.1.0  
**Status:** Ready to Deploy  
**Prochain:** Activer /metrics endpoint + tester retry logic
