# 📱 VintedBot - Prompt pour Frontend Lovable

## 🎯 Objectif
Créer une interface mobile-first pour uploader des photos de vêtements depuis smartphone et obtenir automatiquement des annonces Vinted complètes générées par IA (GPT-4 Vision).

## 🔗 Configuration API Backend

```typescript
const API_BASE_URL = "https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev"
```

## 🚀 Workflow Utilisateur

### 1️⃣ Upload Photos (Mobile-Friendly)
```
Écran: "Ajouter des vêtements"
→ Bouton camera/galerie (mobile)
→ Sélection multiple (1-500 photos)
→ Upload vers API
→ IA analyse automatiquement
→ Brouillons créés
```

### 2️⃣ Voir les Brouillons
```
Écran: "Mes brouillons"
→ Liste des annonces générées
→ Chaque brouillon contient:
   • Titre auto-généré
   • Prix suggéré (€)
   • Description complète
   • Catégorie détectée
   • État/condition
   • Couleur, taille, marque
   • 1-4 photos
```

### 3️⃣ Éditer & Publier
```
Écran: "Modifier brouillon"
→ Modifier n'importe quel champ
→ Bouton "Publier sur Vinted"
→ Annonce publiée automatiquement
```

## 📡 Endpoints API Essentiels

### 📤 Upload Photos & Analyse IA (Principal)
```http
POST /bulk/photos/analyze
Content-Type: multipart/form-data

Paramètres:
- files: File[] (1-500 images JPG/PNG/WEBP, max 15MB chacune)
- photos_per_item: number (défaut: 4, range: 1-10)

Réponse:
{
  "job_id": "uuid",
  "status": "processing",
  "total_photos": 8,
  "estimated_items": 2,
  "message": "Analysis started"
}
```

### 📊 Suivre Progression
```http
GET /bulk/jobs/{job_id}

Réponse:
{
  "job_id": "uuid",
  "status": "completed",  // processing | completed | failed
  "progress_percent": 100.0,
  "total_items": 2,
  "completed_items": 2,
  "failed_items": 0,
  "created_drafts": ["draft-id-1", "draft-id-2"],
  "errors": []
}
```

### 📋 Lister Brouillons
```http
GET /bulk/drafts?status=pending&page=1&page_size=50

Réponse:
{
  "drafts": [
    {
      "id": "uuid",
      "title": "Hoodie Nike Noir Taille M - Très Bon État",
      "description": "Sweat à capuche Nike en excellent état...",
      "price": 25.00,
      "category": "hoodie",
      "condition": "very_good",
      "color": "noir",
      "brand": "Nike",
      "size": "M",
      "photos": [
        "/temp_photos/abc123.jpg",
        "/temp_photos/def456.jpg"
      ],
      "status": "pending",
      "created_at": "2025-10-14T15:30:00Z",
      "confidence_score": 0.92
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

### ✏️ Modifier Brouillon
```http
PATCH /bulk/drafts/{draft_id}
Content-Type: application/json

Body:
{
  "title": "Nouveau titre",
  "price": 30.00,
  "description": "Nouvelle description..."
}

Réponse: Brouillon mis à jour
```

### 🚀 Publier sur Vinted
```http
POST /bulk/drafts/{draft_id}/publish
Content-Type: application/json

Body:
{
  "vinted_category_id": 123,  // optionnel
  "dry_run": false
}

Réponse:
{
  "status": "published",
  "vinted_url": "https://vinted.fr/items/...",
  "message": "Listing published successfully"
}
```

### 🗑️ Supprimer Brouillon
```http
DELETE /bulk/drafts/{draft_id}

Réponse: 204 No Content
```

## 🎨 Design UI/UX Recommandé

### Écran 1: Upload (Page d'accueil)
```
┌─────────────────────────┐
│  📸 VintedBot           │
│                         │
│  ┌─────────────────┐   │
│  │                 │   │
│  │   📷 AJOUTER    │   │
│  │   DES PHOTOS    │   │
│  │                 │   │
│  └─────────────────┘   │
│                         │
│  Uploadez 1-500 photos  │
│  L'IA crée les annonces │
│  automatiquement        │
│                         │
│  [Mes brouillons (5)]   │
└─────────────────────────┘
```

### Écran 2: Liste Brouillons
```
┌─────────────────────────┐
│  ← Mes Brouillons       │
├─────────────────────────┤
│  ┌──┬──────────────────┐│
│  │📷│ Hoodie Nike Noir ││
│  │  │ 25€ • Très bon   ││
│  │  │ [Modifier][Publier││
│  └──┴──────────────────┘│
│  ┌──┬──────────────────┐│
│  │📷│ Jean Levis 501   ││
│  │  │ 35€ • Bon état   ││
│  │  │ [Modifier][Publier││
│  └──┴──────────────────┘│
└─────────────────────────┘
```

### Écran 3: Édition Brouillon
```
┌─────────────────────────┐
│  ← Modifier             │
├─────────────────────────┤
│  Photos: [🖼️][🖼️][🖼️]   │
│                         │
│  Titre:                 │
│  [Hoodie Nike Noir M  ] │
│                         │
│  Prix: [25] €           │
│                         │
│  Description:           │
│  [Sweat à capuche     ] │
│  [Nike en excellent...] │
│                         │
│  Catégorie: [Hoodie ▼]  │
│  État: [Très bon ▼]     │
│  Couleur: [Noir ▼]      │
│  Taille: [M ▼]          │
│  Marque: [Nike]         │
│                         │
│  [PUBLIER SUR VINTED]   │
└─────────────────────────┘
```

## 📱 Fonctionnalités Clés

### ✅ Upload Mobile Optimisé
- Bouton "Prendre photo" (camera native)
- Bouton "Galerie" (sélection multiple)
- Preview des photos sélectionnées
- Barre de progression upload
- Support drag & drop (desktop)

### ✅ Progression en Temps Réel
- Polling `/bulk/jobs/{job_id}` toutes les 2 secondes
- Barre de progression (0-100%)
- "Analyse en cours: 2/5 articles..."
- Notification quand terminé

### ✅ Gestion Brouillons
- Filtres: Tous / En attente / Publiés
- Tri: Plus récent / Prix / Catégorie
- Action rapide: Publier sans éditer
- Action: Éditer puis publier

### ✅ Validation Formulaire
- Prix minimum: 1€
- Titre max: 200 caractères
- Description max: 2000 caractères
- Photos: 1-4 par article

## 🔧 Code TypeScript Exemple

### Hook Upload Photos
```typescript
async function uploadPhotos(files: File[]) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('photos_per_item', '4');

  const response = await fetch(`${API_BASE_URL}/bulk/photos/analyze`, {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  return data.job_id;
}
```

### Hook Progression
```typescript
async function pollJobProgress(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/bulk/jobs/${jobId}`);
  const job = await response.json();
  
  if (job.status === 'completed') {
    return job.created_drafts; // ["id1", "id2"]
  }
  
  return null; // Still processing
}
```

### Hook Lister Brouillons
```typescript
async function getDrafts() {
  const response = await fetch(`${API_BASE_URL}/bulk/drafts`);
  const data = await response.json();
  return data.drafts;
}
```

### Hook Publier
```typescript
async function publishDraft(draftId: string) {
  const response = await fetch(
    `${API_BASE_URL}/bulk/drafts/${draftId}/publish`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dry_run: false })
    }
  );
  
  return await response.json();
}
```

## 🎯 User Stories Prioritaires

### P0 - MVP (Phase 1)
1. ✅ Upload photos mobile (camera + galerie)
2. ✅ Voir progression analyse IA
3. ✅ Lister brouillons générés
4. ✅ Voir détails brouillon (titre, prix, description auto)
5. ✅ Publier sur Vinted en 1 clic

### P1 - Améliorations (Phase 2)
6. ✅ Éditer brouillon avant publication
7. ✅ Supprimer brouillon
8. ✅ Filtrer/trier brouillons
9. ✅ Preview photos haute résolution
10. ✅ Statistiques (€ total, nb articles)

### P2 - Nice-to-have (Phase 3)
11. 🔄 Synchronisation messages Vinted
12. 🔄 Suivi des ventes
13. 🔄 Suggestions prix dynamiques
14. 🔄 Duplication annonces

## 🌐 CORS & Sécurité

Le backend autorise **TOUS** les domaines Lovable :
- `*.lovableproject.com` ✅
- `*.lovable.dev` ✅
- `*.lovable.app` ✅

Pas de configuration CORS nécessaire côté frontend.

## 🐛 Gestion Erreurs

### Erreur Upload
```typescript
try {
  const jobId = await uploadPhotos(files);
} catch (error) {
  // Afficher: "Erreur upload, vérifiez votre connexion"
}
```

### Erreur Analyse IA
```typescript
const job = await pollJobProgress(jobId);
if (job.failed_items > 0) {
  // Afficher: "X photos n'ont pas pu être analysées"
  // Proposer: "Réessayer" ou "Créer manuellement"
}
```

### Erreur Publication
```typescript
try {
  await publishDraft(draftId);
} catch (error) {
  // Afficher: "Erreur publication, vérifiez session Vinted"
}
```

## 📊 Formats Retournés

### Catégories Possibles
```
t-shirt, hoodie, sweater, jeans, pants, shorts, dress, 
skirt, jacket, coat, shoes, sneakers, boots, bag, accessory
```

### Conditions Possibles
```
new_with_tags, very_good, good, satisfactory
```

### Couleurs Possibles
```
noir, blanc, gris, bleu, rouge, vert, jaune, orange, 
rose, violet, marron, beige, multicolore
```

## 🚀 Démarrage Rapide

### 1. Créer Composant Upload
```tsx
<input 
  type="file" 
  multiple 
  accept="image/jpeg,image/png,image/webp"
  capture="environment"  // Active camera mobile
  onChange={handleUpload}
/>
```

### 2. Upload & Polling
```typescript
const jobId = await uploadPhotos(files);

const interval = setInterval(async () => {
  const drafts = await pollJobProgress(jobId);
  if (drafts) {
    clearInterval(interval);
    navigate('/drafts');
  }
}, 2000);
```

### 3. Afficher Brouillons
```tsx
const drafts = await getDrafts();

drafts.map(draft => (
  <Card key={draft.id}>
    <Image src={draft.photos[0]} />
    <Title>{draft.title}</Title>
    <Price>{draft.price}€</Price>
    <Button onClick={() => publish(draft.id)}>
      Publier
    </Button>
  </Card>
))
```

## 🎉 C'est Parti !

Copiez-collez ce prompt dans **Lovable Chat** :

---

**Prompt Lovable:**

```
Crée une app mobile VintedBot pour uploader des photos de vêtements et obtenir automatiquement des annonces Vinted générées par IA.

API Backend: https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev

Fonctionnalités:
1. Page upload: bouton camera/galerie mobile, upload multiple (1-500 photos)
2. Appel API: POST /bulk/photos/analyze avec FormData
3. Afficher progression: polling GET /bulk/jobs/{job_id} toutes les 2s
4. Page brouillons: GET /bulk/drafts, afficher titre/prix/description auto-générés
5. Bouton "Publier": POST /bulk/drafts/{id}/publish
6. Page édition: PATCH /bulk/drafts/{id} pour modifier avant publication

Design:
- Mobile-first, style moderne, couleurs Vinted (vert/blanc)
- Écran 1: Gros bouton "📷 Ajouter Photos"
- Écran 2: Liste cards avec photo/titre/prix + bouton "Publier"
- Écran 3: Formulaire édition avec preview photos

Utilise React + TypeScript + TailwindCSS + shadcn/ui
```

---

**Et voilà ! 🎊** L'app va uploader vos photos depuis mobile, l'IA génère les annonces, et vous publiez sur Vinted en 1 clic ! 🚀
