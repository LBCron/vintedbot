# Vinted API - Tests cURL

## Configuration

```bash
export BASE_URL="https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev"
```

---

## 1. Enregistrer une session Vinted

**Endpoint:** `POST /vinted/auth/session`

**Obtenir le cookie et User-Agent:**
1. Ouvrir https://www.vinted.fr dans votre navigateur
2. Se connecter à votre compte
3. Ouvrir DevTools (F12) → Network
4. Rafraîchir la page
5. Cliquer sur une requête → Headers → Copier `Cookie` et `User-Agent`

```bash
curl -sS -X POST "$BASE_URL/vinted/auth/session" \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON'
{
  "cookie": "COPIEZ_VOTRE_COOKIE_ICI",
  "user_agent": "COPIEZ_VOTRE_USER_AGENT_ICI",
  "expires_at": null
}
JSON
```

**Réponse attendue:**
```json
{
  "ok": true,
  "persisted": true,
  "username": null
}
```

---

## 2. Vérifier l'authentification

**Endpoint:** `GET /vinted/auth/check`

```bash
curl -sS "$BASE_URL/vinted/auth/check" | jq
```

**Réponse attendue:**
```json
{
  "authenticated": true,
  "username": null,
  "user_id": null
}
```

---

## 3. Upload une photo

**Endpoint:** `POST /vinted/photos/upload`

```bash
curl -sS -X POST "$BASE_URL/vinted/photos/upload" \
  -F "file=@/chemin/vers/votre/photo.jpg"
```

**Réponse attendue:**
```json
{
  "ok": true,
  "photo": {
    "temp_id": "photo_XYZ123...",
    "url": "/temp_photos/photo_XYZ123_photo.jpg",
    "filename": "photo.jpg"
  }
}
```

---

## 4. Préparer un listing (draft)

**Endpoint:** `POST /vinted/listings/prepare`

```bash
curl -sS -X POST "$BASE_URL/vinted/listings/prepare" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hoodie Diesel noir",
    "price": 35,
    "description": "Hoodie Diesel en bon état, porté quelques fois. Taille L, couleur noir.",
    "brand": "Diesel",
    "size": "L",
    "condition": "bon",
    "color": "noir",
    "category_hint": "Homme > Sweats",
    "photos": [],
    "dry_run": true
  }' | jq
```

**Réponse attendue (dry_run=true):**
```json
{
  "ok": true,
  "dry_run": true,
  "confirm_token": "InRpdGxlIjoiSG9vZGllIERpZXNlbCBub2lyIiwicHJpY2UiOjM1LC...",
  "preview_url": "https://www.vinted.fr/items/new",
  "screenshot_b64": null,
  "draft_context": {
    "title": "Hoodie Diesel noir",
    "price": 35,
    "description": "Hoodie Diesel en bon état...",
    "brand": "Diesel",
    "size": "L",
    "condition": "bon",
    "color": "noir",
    "category_hint": "Homme > Sweats",
    "photos": [],
    "timestamp": "2025-10-13T22:00:00.000000"
  }
}
```

**Copier le `confirm_token` pour l'étape suivante!**

---

## 5. Publier (dry-run d'abord)

**Endpoint:** `POST /vinted/listings/publish`

### Test 1: Dry-run (simulation, aucun risque)

```bash
curl -sS -X POST "$BASE_URL/vinted/listings/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm_token": "COPIEZ_LE_TOKEN_ICI",
    "dry_run": true
  }' | jq
```

**Réponse attendue:**
```json
{
  "ok": true,
  "dry_run": true,
  "listing_id": null,
  "listing_url": null,
  "needs_manual": null,
  "reason": null
}
```

---

### Test 2: Publication réelle (OPT-IN, avec idempotency)

⚠️ **ATTENTION:** Ceci publiera réellement sur Vinted!

```bash
curl -sS -X POST "$BASE_URL/vinted/listings/publish" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-$(date +%s)" \
  -d '{
    "confirm_token": "COPIEZ_LE_TOKEN_ICI",
    "dry_run": false
  }' | jq
```

**Réponse attendue (succès):**
```json
{
  "ok": true,
  "dry_run": false,
  "listing_id": "123456789",
  "listing_url": "https://www.vinted.fr/items/123456789",
  "needs_manual": false,
  "reason": null
}
```

**Réponse attendue (captcha détecté):**
```json
{
  "ok": true,
  "dry_run": false,
  "listing_id": null,
  "listing_url": null,
  "needs_manual": true,
  "reason": "captcha_or_verification"
}
```

---

## Critères d'acceptation

### ✅ /vinted/auth/session
- [ ] Accepte cookie et user-agent
- [ ] Retourne `persisted: true`
- [ ] Session chiffrée dans `backend/data/session.enc`
- [ ] Cookie JAMAIS loggué en clair

### ✅ /vinted/auth/check
- [ ] `authenticated: false` si pas de session
- [ ] `authenticated: true` si session valide
- [ ] `authenticated: false` si session expirée

### ✅ /vinted/photos/upload
- [ ] Accepte multipart/form-data
- [ ] Rate limit 10/minute appliqué
- [ ] Retourne `temp_id` et `url`
- [ ] Fichier sauvegardé dans `backend/data/temp_photos/`

### ✅ /vinted/listings/prepare
- [ ] Dry-run par défaut (`dry_run: true`)
- [ ] Retourne `confirm_token` avec TTL 30min
- [ ] MOCK_MODE: simulation seulement
- [ ] Mode réel: ouvre /items/new, upload photos, remplit form
- [ ] Détecte captcha/challenge → erreur HTTP 403

### ✅ /vinted/listings/publish
- [ ] Vérifie `confirm_token` (TTL 30min)
- [ ] Dry-run par défaut (`dry_run: true`)
- [ ] Rate limit 5/minute appliqué
- [ ] Détecte captcha → retourne `needs_manual: true`
- [ ] Succès → retourne `listing_id` et `listing_url`
- [ ] Supporte `Idempotency-Key` header

---

## Logs attendus (sobres, sans secrets)

```
✅ Session saved (encrypted): user=unknown
✅ Photo uploaded: photo.jpg -> photo_XYZ123
🔄 [DRY-RUN] Preparing listing: Hoodie Diesel noir
🚀 [REAL] Preparing listing: Hoodie Diesel noir
✅ Listing prepared: Hoodie Diesel noir
🔄 [DRY-RUN] Publishing: Hoodie Diesel noir
🚀 [REAL] Publishing: Hoodie Diesel noir
⚠️ Challenge/Captcha detected - manual action needed
✅ Published: ID=123456789, URL=https://www.vinted.fr/items/123456789
```

---

## Erreurs HTTP explicites

| Code | Condition | Message |
|------|-----------|---------|
| 400 | Token invalide | "Invalid confirm token" |
| 401 | Non authentifié | "Not authenticated. Call /auth/session first." |
| 403 | Captcha détecté (prepare) | "Verification/Captcha detected. Please complete manually." |
| 410 | Token expiré | "Confirm token expired (30 min limit)" |
| 415 | Mauvais type fichier | "Only image files are allowed" |
| 429 | Rate limit dépassé | "Rate limit exceeded" |
| 500 | Erreur serveur | "Prepare failed: {error}" |

---

## Mode MOCK (par défaut)

Tant que `MOCK_MODE=true` dans `.env`, tous les endpoints retournent des simulations:
- Aucune vraie connexion Playwright
- Aucune publication réelle
- `dry_run` forcé à `true`
- Logs préfixés avec `🔄 [DRY-RUN]`

Pour passer en mode réel:
```bash
# backend/.env
MOCK_MODE=false
PLAYWRIGHT_HEADLESS=true
```
