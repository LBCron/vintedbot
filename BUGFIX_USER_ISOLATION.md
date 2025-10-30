# 🐛 Correction - Isolation des Brouillons par Utilisateur

## Problème Détecté par Lovable

**Symptôme :** 
- `GET /bulk/drafts` retournait les brouillons
- `POST /bulk/drafts/{id}/publish` retournait 404 "Draft not found"

**Cause racine :**
Les endpoints de gestion des brouillons n'avaient **PAS d'isolation par utilisateur** :
1. ❌ `GET /bulk/drafts` retournait TOUS les brouillons (de tous les utilisateurs)
2. ❌ `POST /bulk/drafts/{id}/publish` ne vérifiait pas la propriété du brouillon
3. ❌ `GET /bulk/drafts/{id}` ne vérifiait pas la propriété du brouillon
4. ❌ Aucune authentification requise sur ces endpoints

---

## ✅ Corrections Appliquées

### 1. **GET /bulk/drafts** - Liste des brouillons
**AVANT :**
```python
@router.get("/drafts")
async def list_drafts(status: Optional[str] = None):
    # Retournait TOUS les drafts (tous utilisateurs confondus)
    db_drafts_raw = get_store().get_drafts(status=status, limit=1000)
```

**APRÈS :**
```python
@router.get("/drafts")
async def list_drafts(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)  # ✅ JWT requis
):
    # Filtre par user_id
    db_drafts_raw = get_store().get_drafts(
        status=status, 
        limit=1000, 
        user_id=str(current_user.id)  # ✅ Isolation
    )
```

---

### 2. **GET /bulk/drafts/{id}** - Détails d'un brouillon
**AVANT :**
```python
@router.get("/drafts/{draft_id}")
async def get_draft(draft_id: str):
    # Pas de vérification de propriété
    if draft_id not in drafts_storage:
        raise HTTPException(404, "Draft not found")
    return drafts_storage[draft_id]
```

**APRÈS :**
```python
@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user)  # ✅ JWT requis
):
    draft_data = get_store().get_draft_by_id(draft_id)
    
    if not draft_data:
        raise HTTPException(404, "Draft not found")
    
    # ✅ Vérification de propriété
    if draft_data.get("user_id") != str(current_user.id):
        raise HTTPException(403, "Ce brouillon ne vous appartient pas")
    
    return draft_data
```

---

### 3. **POST /bulk/drafts/{id}/publish** - Publication Vinted
**AVANT :**
```python
@router.post("/drafts/{draft_id}/publish")
async def publish_draft(draft_id: str):
    # Pas de vérification de propriété
    if draft_id not in drafts_storage:
        raise HTTPException(404, "Draft not found")
    
    draft = drafts_storage[draft_id]
    # Publication sans vérifier qui publie quoi
```

**APRÈS :**
```python
@router.post("/drafts/{draft_id}/publish")
async def publish_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user)  # ✅ JWT requis
):
    draft_data = get_store().get_draft_by_id(draft_id)
    
    if not draft_data:
        print(f"⚠️  [PUBLISH] Draft {draft_id} not found")
        raise HTTPException(404, {
            "error": "draft_not_found",
            "message": "Ce brouillon n'existe plus.",
            "draft_id": draft_id
        })
    
    # ✅ Vérification de propriété CRITIQUE
    if draft_data.get("user_id") != str(current_user.id):
        print(f"⚠️  [PUBLISH] User {current_user.id} trying to publish draft owned by {draft_data['user_id']}")
        raise HTTPException(403, "Ce brouillon ne vous appartient pas")
    
    # ✅ Vérification du quota publications
    await check_and_consume_quota(current_user, "publications", amount=1)
    
    print(f"✅ [PUBLISH] User {current_user.id} publishing draft {draft_id}")
    # Continue...
```

---

## 📊 Résumé des Changements

| Endpoint | Avant | Après |
|----------|-------|-------|
| `GET /bulk/drafts` | ❌ Tous les brouillons | ✅ Seulement les brouillons de l'utilisateur |
| `GET /bulk/drafts/{id}` | ❌ Pas de vérification | ✅ Vérification propriété (403 si pas owner) |
| `PATCH /bulk/drafts/{id}` | ⚠️  Auth partielle | ✅ Auth + vérification propriété |
| `DELETE /bulk/drafts/{id}` | ⚠️  Auth partielle | ✅ Auth + vérification propriété |
| `POST /bulk/drafts/{id}/publish` | ❌ Pas de vérification | ✅ Auth + propriété + quota publications |

---

## 🔒 Sécurité Améliorée

### Messages d'erreur explicites
```json
// 404 - Brouillon introuvable
{
  "error": "draft_not_found",
  "message": "Ce brouillon n'existe plus. Il a peut-être été supprimé ou a expiré.",
  "draft_id": "abc123"
}

// 403 - Pas le propriétaire
{
  "detail": "Ce brouillon ne vous appartient pas"
}
```

### Logs de debug
```bash
# Console serveur lors d'une tentative d'accès non autorisé
⚠️  [PUBLISH] User 2 trying to publish draft owned by 1
⚠️  [PUBLISH] Draft abc123 not found in database

# Console serveur lors d'une publication réussie
✅ [PUBLISH] User 1 publishing draft abc123
```

---

## 🧪 Tests de Validation

### Scénario 1 : Utilisateur normal
```bash
# Utilisateur A (id=1) crée un brouillon
POST /bulk/ingest → draft_id = "abc123"

# Utilisateur A liste ses brouillons
GET /bulk/drafts → [{"id": "abc123", ...}]  ✅

# Utilisateur A publie son brouillon
POST /bulk/drafts/abc123/publish → 200 OK  ✅
```

### Scénario 2 : Tentative d'accès cross-user
```bash
# Utilisateur B (id=2) tente d'accéder au brouillon de A
GET /bulk/drafts/abc123 → 403 "Ce brouillon ne vous appartient pas"  ✅

# Utilisateur B tente de publier le brouillon de A
POST /bulk/drafts/abc123/publish → 403 "Ce brouillon ne vous appartient pas"  ✅

# Utilisateur B liste ses brouillons
GET /bulk/drafts → []  ✅ (vide, ne voit pas les brouillons de A)
```

### Scénario 3 : Admin bypass
```bash
# Admin (is_admin=true) liste ses brouillons
GET /bulk/drafts → [ses propres brouillons]  ✅

# Admin publie sans limite de quota
POST /bulk/drafts/abc123/publish → 200 OK  ✅ (bypass publications quota)
```

---

## ✅ Checklist de Sécurité

- [x] Tous les endpoints `/bulk/drafts*` nécessitent JWT
- [x] GET /bulk/drafts filtre par user_id
- [x] GET /bulk/drafts/{id} vérifie la propriété (403 si pas owner)
- [x] PATCH /bulk/drafts/{id} vérifie la propriété
- [x] DELETE /bulk/drafts/{id} vérifie la propriété
- [x] POST /bulk/drafts/{id}/publish vérifie propriété + quota
- [x] Messages d'erreur explicites (404 vs 403)
- [x] Logs de debug pour traçabilité
- [x] Admin bypass fonctionnel (is_admin=true)

---

## 🎯 Impact Frontend Lovable

**Avant la correction :**
- Frontend recevait des brouillons d'autres utilisateurs
- Tentatives de publication échouaient avec 404

**Après la correction :**
- Frontend reçoit UNIQUEMENT ses propres brouillons
- Publication fonctionne normalement
- Erreurs 403 si tentative d'accès cross-user

**Aucune modification requise côté frontend** - Les endpoints ont la même signature, seule la logique de filtrage a changé.

---

**Statut : ✅ CORRIGÉ ET TESTÉ**
