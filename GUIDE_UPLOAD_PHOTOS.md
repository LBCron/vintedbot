# Guide : Upload de Photos & Analyse OpenAI GPT-4o-mini

## 🎯 Ce que vous devez faire

Envoyer vos photos à l'API, et OpenAI GPT-4o-mini va automatiquement :
1. Analyser toutes vos photos
2. Grouper les photos par article (intelligemment)
3. Créer un brouillon pour chaque article avec titre, description, prix, etc.

---

## 📡 Endpoint à utiliser

```
POST https://vintedbot-backend.fly.dev/bulk/analyze
```

---

## 🔑 Authentication

Vous devez d'abord vous authentifier pour obtenir un token :

```bash
# 1. S'inscrire (une seule fois)
curl -X POST https://vintedbot-backend.fly.dev/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "votre-email@example.com",
    "password": "votre-mot-de-passe"
  }'

# 2. Se connecter (pour obtenir le token)
curl -X POST https://vintedbot-backend.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "votre-email@example.com",
    "password": "votre-mot-de-passe"
  }'

# Réponse :
# {
#   "access_token": "votre-token-ici",
#   "token_type": "bearer"
# }
```

---

## 📤 Upload et Analyse de Photos

### Option 1 : Avec curl (ligne de commande)

```bash
curl -X POST https://vintedbot-backend.fly.dev/bulk/analyze \
  -H "Authorization: Bearer VOTRE_TOKEN_ICI" \
  -F "files=@/chemin/vers/photo1.jpg" \
  -F "files=@/chemin/vers/photo2.jpg" \
  -F "files=@/chemin/vers/photo3.jpg" \
  -F "style=classique"
```

### Option 2 : Avec Python

```python
import requests

# Votre token d'authentification
token = "VOTRE_TOKEN_ICI"

# Vos photos à uploader
files = [
    ('files', open('photo1.jpg', 'rb')),
    ('files', open('photo2.jpg', 'rb')),
    ('files', open('photo3.jpg', 'rb')),
]

# Upload et analyse
response = requests.post(
    'https://vintedbot-backend.fly.dev/bulk/analyze',
    headers={'Authorization': f'Bearer {token}'},
    files=files,
    data={'style': 'classique'}
)

result = response.json()
print(result)
```

### Option 3 : Avec Postman

1. Créer une requête POST vers : `https://vintedbot-backend.fly.dev/bulk/analyze`
2. Dans **Headers** :
   - Key: `Authorization`
   - Value: `Bearer VOTRE_TOKEN_ICI`
3. Dans **Body** → **form-data** :
   - Ajouter plusieurs lignes avec Key = `files`, Type = `File`
   - Sélectionner vos photos
4. Envoyer la requête

---

## 📊 Réponse de l'API

```json
{
  "job_id": "abc123def",
  "status": "completed",
  "uploaded_count": 15,
  "drafts_created": 3,
  "drafts": [
    {
      "draft_id": "draft-001",
      "title": "Pull en laine beige vintage",
      "description": "Magnifique pull en laine...",
      "price": 25.0,
      "category": "Pulls & Gilets",
      "photos": ["/temp_photos/abc123/photo_001.jpg", ...],
      "brand": "Zara",
      "size": "M",
      "color": "Beige",
      "condition": "Très bon état"
    },
    ...
  ]
}
```

---

## 🎨 Styles disponibles

- `classique` : Description élégante et professionnelle (par défaut)
- `streetwear` : Style urbain et tendance
- `minimal` : Description courte et concise

---

## ✅ Formats de photos supportés

- JPG / JPEG
- PNG
- WEBP
- HEIC / HEIF (iPhone)
- GIF
- BMP

**Taille max** : 15 MB par photo
**Nombre max** : 20 photos par requête

---

## 📋 Récupérer vos brouillons

```bash
# Lister tous vos brouillons
curl https://vintedbot-backend.fly.dev/bulk/drafts \
  -H "Authorization: Bearer VOTRE_TOKEN_ICI"

# Voir un brouillon spécifique
curl https://vintedbot-backend.fly.dev/bulk/drafts/draft-001 \
  -H "Authorization: Bearer VOTRE_TOKEN_ICI"
```

---

## 🚀 Publier sur Vinted

Une fois vos brouillons créés, vous pouvez les publier :

```bash
curl -X POST https://vintedbot-backend.fly.dev/vinted/publish \
  -H "Authorization: Bearer VOTRE_TOKEN_ICI" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pull en laine beige vintage",
    "description": "Magnifique pull en laine...",
    "price": 25.0,
    "category_id": 123,
    "photos": ["/temp_photos/abc123/photo_001.jpg"],
    "brand_id": 53,
    "size_id": 207,
    "color_ids": [1],
    "status_id": 6
  }'
```

---

## 🔧 Tester rapidement

URL de test : https://vintedbot-backend.fly.dev/docs

Vous pouvez tester l'API directement dans votre navigateur avec l'interface Swagger !

---

## ❓ Besoin d'aide ?

- Documentation complète : https://vintedbot-backend.fly.dev/docs
- Health check : https://vintedbot-backend.fly.dev/health
- Support : ronanchenlopes@gmail.com
