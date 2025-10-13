# PROMPT LOVABLE — Frontend Vinted Integration

## 📋 Objectif

Créer l'interface frontend pour la publication automatisée de posts Vinted via le backend FastAPI.

**Backend API URL:**
```
https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev
```

---

## 🎯 Pages à créer / mettre à jour

### 1. `/settings` - Configuration de la session Vinted

**Fonctionnalités:**
- Formulaire pour enregistrer Cookie + User-Agent
- Instructions claires pour obtenir les credentials depuis DevTools
- Bouton "Tester la connexion" → appel GET `/vinted/auth/check`
- État de connexion affiché (✅ Connecté / ❌ Déconnecté)
- Bouton "Déconnexion" (clear session côté frontend)

**UI suggérée:**
```
┌─────────────────────────────────────────┐
│  🔐 Configuration Vinted                │
│                                         │
│  État: ✅ Connecté (utilisateur: x)     │
│                                         │
│  📝 Comment obtenir vos identifiants:   │
│  1. Ouvrir vinted.fr et se connecter    │
│  2. DevTools (F12) → Network            │
│  3. Rafraîchir la page                  │
│  4. Cliquer sur une requête             │
│  5. Copier Cookie et User-Agent         │
│                                         │
│  [Cookie (masqué)]  [____________]      │
│  [User-Agent]       [____________]      │
│                                         │
│  [Enregistrer Session]  [Tester]        │
└─────────────────────────────────────────┘
```

**Appels API:**
- POST `/vinted/auth/session` avec `{ cookie, user_agent, expires_at: null }`
- GET `/vinted/auth/check` pour vérifier l'état

---

### 2. `/upload` - Upload de photos

**Fonctionnalités:**
- Zone de drag & drop pour images (1-20 photos)
- Prévisualisation des photos uploadées
- Upload automatique via POST `/vinted/photos/upload`
- Liste des `temp_id` pour utilisation dans le draft
- Bouton "Supprimer" pour chaque photo

**État à maintenir:**
```typescript
interface UploadedPhoto {
  temp_id: string;
  url: string;
  filename: string;
}

const [photos, setPhotos] = useState<UploadedPhoto[]>([]);
```

**Appel API:**
```typescript
const formData = new FormData();
formData.append('file', file);

const response = await fetch(`${API_BASE_URL}/vinted/photos/upload`, {
  method: 'POST',
  body: formData
});

const data = await response.json();
setPhotos([...photos, data.photo]);
```

---

### 3. `/listings/new` - Créer un listing

**Fonctionnalités:**
- Formulaire complet pour les détails du produit
- Sélection des photos uploadées (depuis `/upload`)
- Bouton "Préparer (Dry-run)" → POST `/vinted/listings/prepare` avec `dry_run: true`
- Affichage du `confirm_token` + `preview_url`
- Affichage du screenshot (base64) si disponible

**Champs du formulaire:**
```typescript
interface ListingForm {
  title: string;          // max 160 chars
  price: number;          // > 0
  description: string;
  brand?: string;
  size?: string;
  condition?: string;     // "neuf", "très bon", "bon", "satisfaisant"
  color?: string;
  category_hint?: string; // ex: "Homme > Sweats"
  photos: string[];       // array of temp_id
  dry_run: boolean;       // true par défaut
}
```

**Appel API:**
```typescript
const response = await fetch(`${API_BASE_URL}/vinted/listings/prepare`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
});

const result = await response.json();
// Stocker result.confirm_token pour la publication
```

---

### 4. `/listings/publish` - Publier le listing

**Fonctionnalités:**
- Affichage du résumé du draft (depuis `/listings/new`)
- Toggle "Mode réel" (désactivé par défaut = dry-run)
- Bouton "Publier" avec confirmation modale
- Gestion de l'idempotency key (générer `uuid()`)
- Affichage du résultat:
  - ✅ Succès → `listing_id` + lien vers `listing_url`
  - ⚠️ Challenge détecté → `needs_manual: true` avec instructions
  - ❌ Erreur → afficher le message

**Modal de confirmation (si dry_run = false):**
```
⚠️ Êtes-vous sûr de vouloir publier ce listing sur Vinted ?

Cette action est RÉELLE et créera un post public.

[ Annuler ]  [ Confirmer la publication ]
```

**Appel API:**
```typescript
const idempotencyKey = crypto.randomUUID();

const response = await fetch(`${API_BASE_URL}/vinted/listings/publish`, {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Idempotency-Key': idempotencyKey
  },
  body: JSON.stringify({
    confirm_token: confirmToken,
    dry_run: !isRealMode
  })
});

const result = await response.json();

if (result.needs_manual) {
  alert('⚠️ Captcha/Vérification détectée. Veuillez compléter manuellement sur Vinted.');
} else if (result.listing_url) {
  window.open(result.listing_url, '_blank');
}
```

---

## 🔧 Configuration (`.env` / `config.ts`)

```typescript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  'https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev';
```

---

## 📊 Gestion d'état globale (optionnel)

**Si vous utilisez React Context / Zustand / Redux:**

```typescript
interface VintedState {
  isAuthenticated: boolean;
  username: string | null;
  uploadedPhotos: UploadedPhoto[];
  currentDraft: ListingForm | null;
  confirmToken: string | null;
}

// Actions
- checkAuth()
- saveSession(cookie, userAgent)
- uploadPhoto(file)
- prepareListing(form)
- publishListing(confirmToken, dryRun)
```

---

## 🎨 UI/UX Recommandations

### Design System
- **Couleurs:**
  - Vert: Succès (`#10b981`)
  - Orange: Warning (`#f59e0b`)
  - Rouge: Erreur (`#ef4444`)
  - Bleu: Action principale (`#3b82f6`)

- **Icons:**
  - 🔐 Session / Auth
  - 📸 Photos
  - 📝 Draft
  - 🚀 Publish
  - ⚠️ Warning/Captcha

### Feedback visuel
- **Loading states:** Spinner pendant les requêtes API
- **Success toast:** "✅ Session enregistrée avec succès"
- **Error toast:** "❌ Erreur: [message]"
- **Progress bar:** Upload photos (0-100%)

### Navigation
```
Navbar:
- [Logo] VintedBot
- [Connexion] /settings
- [Photos] /upload
- [Nouveau Listing] /listings/new
- [Mes Listings] /listings (future)
```

---

## 🔒 Sécurité & Bonnes Pratiques

1. **Cookie masqué:** Ne jamais afficher le cookie en clair (utiliser `type="password"`)
2. **HTTPS uniquement:** Le backend Replit utilise HTTPS
3. **Dry-run par défaut:** Toujours `dry_run: true` sauf opt-in explicite
4. **Confirmation modale:** Obligatoire pour `dry_run: false`
5. **Idempotency:** Générer un UUID unique par requête de publication

---

## ✅ Checklist d'intégration

### Phase 1: Session
- [ ] Page `/settings` créée
- [ ] Formulaire Cookie + User-Agent
- [ ] Appel POST `/vinted/auth/session`
- [ ] Appel GET `/vinted/auth/check`
- [ ] Affichage état connexion

### Phase 2: Upload
- [ ] Page `/upload` créée
- [ ] Drag & drop images
- [ ] Appel POST `/vinted/photos/upload` (multipart)
- [ ] Prévisualisation photos
- [ ] Stockage `temp_id` dans state

### Phase 3: Draft
- [ ] Page `/listings/new` créée
- [ ] Formulaire complet (title, price, description, etc.)
- [ ] Sélection photos uploadées
- [ ] Appel POST `/vinted/listings/prepare` (dry_run: true)
- [ ] Stockage `confirm_token`
- [ ] Affichage screenshot (base64)

### Phase 4: Publish
- [ ] Page `/listings/publish` créée
- [ ] Toggle dry-run / mode réel
- [ ] Modal de confirmation
- [ ] Appel POST `/vinted/listings/publish`
- [ ] Header `Idempotency-Key`
- [ ] Gestion `needs_manual: true`
- [ ] Affichage `listing_url` si succès

---

## 📝 Exemple de Flow Utilisateur

1. **Connexion:**
   - Aller sur `/settings`
   - Copier Cookie + User-Agent depuis DevTools
   - Cliquer "Enregistrer Session"
   - Vérifier état: ✅ Connecté

2. **Upload Photos:**
   - Aller sur `/upload`
   - Drag & drop 3 photos
   - Attendre upload → voir 3 miniatures

3. **Créer Draft:**
   - Aller sur `/listings/new`
   - Remplir: Titre, Prix, Description, Marque, Taille, État
   - Sélectionner les 3 photos uploadées
   - Cliquer "Préparer (Dry-run)"
   - Voir screenshot + confirm_token

4. **Publier:**
   - Aller sur `/listings/publish`
   - Voir résumé du draft
   - Activer "Mode réel" (toggle)
   - Cliquer "Publier"
   - Modal: Confirmer
   - Résultat:
     - ✅ → Lien vers Vinted
     - ⚠️ → "Captcha détecté, action manuelle requise"

---

## 🚀 Code Starter (React + TypeScript)

### API Client (`lib/vinted-api.ts`)

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const vintedApi = {
  // Auth
  async saveSession(cookie: string, userAgent: string) {
    const res = await fetch(`${API_BASE_URL}/vinted/auth/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cookie, user_agent: userAgent, expires_at: null })
    });
    return res.json();
  },

  async checkAuth() {
    const res = await fetch(`${API_BASE_URL}/vinted/auth/check`);
    return res.json();
  },

  // Photos
  async uploadPhoto(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/vinted/photos/upload`, {
      method: 'POST',
      body: formData
    });
    return res.json();
  },

  // Listings
  async prepareListing(data: any) {
    const res = await fetch(`${API_BASE_URL}/vinted/listings/prepare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async publishListing(confirmToken: string, dryRun: boolean) {
    const res = await fetch(`${API_BASE_URL}/vinted/listings/publish`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Idempotency-Key': crypto.randomUUID()
      },
      body: JSON.stringify({ confirm_token: confirmToken, dry_run: dryRun })
    });
    return res.json();
  }
};
```

---

## 📚 Documentation API Backend

Toute la doc API interactive est disponible sur:
```
https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev/docs
```

Endpoints disponibles:
- `POST /vinted/auth/session`
- `GET /vinted/auth/check`
- `POST /vinted/photos/upload`
- `POST /vinted/listings/prepare`
- `POST /vinted/listings/publish`

---

## ⚡ Quick Start

1. **Variable d'environnement:**
   ```
   VITE_API_BASE_URL=https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev
   ```

2. **Installer client HTTP:**
   ```bash
   # Si Next.js
   npm install axios
   # Ou utiliser fetch natif
   ```

3. **Créer les 4 pages:**
   - `/settings` → Session Vinted
   - `/upload` → Photos
   - `/listings/new` → Draft
   - `/listings/publish` → Publication

4. **Tester en dry-run d'abord !**

---

Bonne intégration ! 🚀
