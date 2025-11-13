# 🚀 VintedBot - Application Complète Déployée !

## ✅ Tout est prêt et fonctionnel

### 🌐 Accès à votre application

**Frontend (Interface web)** : https://vintedbot-backend.fly.dev/

**API Backend** : https://vintedbot-backend.fly.dev/docs

---

## 📱 Comment utiliser l'application

### 1. Créer un compte
1. Allez sur https://vintedbot-backend.fly.dev/
2. Cliquez sur "Register" (S'inscrire)
3. Créez votre compte avec email + mot de passe

### 2. Upload et Analyse de Photos

#### Via l'interface web (FACILE) :
1. Connectez-vous sur https://vintedbot-backend.fly.dev/
2. Allez dans "Upload Photos" ou "Dashboard"
3. Glissez-déposez vos photos ou cliquez pour sélectionner
4. **OpenAI GPT-4o-mini va automatiquement :**
   - ✨ Analyser toutes vos photos
   - 🧠 Grouper les photos par article
   - ✍️ Créer des brouillons avec titre, description, prix, etc.

#### Via API (pour développeurs) :
```bash
# 1. Se connecter
curl -X POST https://vintedbot-backend.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "votre@email.com", "password": "motdepasse"}'

# 2. Uploader et analyser des photos
curl -X POST https://vintedbot-backend.fly.dev/bulk/analyze \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "files=@photo3.jpg"
```

### 3. Gérer vos brouillons
1. Dans l'interface : section "Drafts"
2. Vous verrez tous les articles créés par l'IA
3. Vous pouvez :
   - ✏️ Modifier les titres, descriptions, prix
   - 🔄 Réorganiser les photos
   - ➕ Ajouter des photos
   - 🗑️ Supprimer des brouillons
   - 🚀 Publier sur Vinted

### 4. Publier sur Vinted
1. Cliquez sur "Publish" sur un brouillon
2. L'article sera automatiquement publié sur Vinted
3. Vous recevrez une confirmation

---

## 🎯 Fonctionnalités Principales

### ✨ Analyse IA (OpenAI GPT-4o-mini)
- **Upload de masse** : Jusqu'à 20 photos à la fois
- **Groupement intelligent** : L'IA regroupe automatiquement les photos par article
- **Génération automatique** :
  - Titre accrocheur
  - Description détaillée
  - Prix suggéré
  - Catégorie
  - Marque
  - Taille
  - Couleur
  - État

### 📊 Analytics (Premium)
- Statistiques de ventes
- Vues et likes
- Performance par catégorie
- Évolution dans le temps

### 🤖 Automation (Premium)
- Auto-bump (remonter les annonces)
- Auto-follow
- Messages automatiques
- Upselling intelligent

### 👥 Multi-comptes
- Gérer plusieurs comptes Vinted
- Basculer facilement entre comptes

---

## 🎨 Styles de Description Disponibles

Quand vous uploadez des photos, vous pouvez choisir :

1. **Classique** (par défaut) : Élégant et professionnel
2. **Streetwear** : Style urbain et tendance
3. **Minimal** : Court et concis

---

## 📸 Formats Supportés

- **Images** : JPG, PNG, WEBP, HEIC (iPhone), GIF, BMP
- **Taille max** : 15 MB par photo
- **Nombre max** : 20 photos par upload

---

## 🔑 Plans & Quotas

### Free Plan
- ✅ 10 analyses IA par mois
- ✅ 5 publications par mois
- ✅ 500 MB stockage

### Premium Plan
- ✅ Analyses IA illimitées
- ✅ Publications illimitées
- ✅ 10 GB stockage
- ✅ Analytics avancés
- ✅ Automation
- ✅ Multi-comptes

---

## 📚 Liens Utiles

- **Application** : https://vintedbot-backend.fly.dev/
- **Documentation API** : https://vintedbot-backend.fly.dev/docs
- **Health Check** : https://vintedbot-backend.fly.dev/health

---

## ❓ FAQ

### L'analyse IA ne fonctionne pas ?
- Vérifiez que vous êtes connecté
- Vérifiez que vos photos sont valides (formats supportés)
- Vérifiez votre quota d'analyses restant

### Comment changer mon plan ?
- Allez dans "Settings" → "Billing"
- Cliquez sur "Upgrade to Premium"

### Comment ajouter un compte Vinted ?
- Allez dans "Accounts"
- Cliquez sur "Add Account"
- Connectez-vous avec vos identifiants Vinted

---

## 🛠️ Support

Pour toute question ou problème :
- 📧 Email : ronanchenlopes@gmail.com
- 💬 GitHub : https://github.com/ronanchenlopes

---

## 🎉 C'EST TOUT !

Votre application est **100% fonctionnelle** et déployée !

Vous pouvez maintenant :
1. ✅ Uploader vos photos
2. ✅ L'IA les analyse automatiquement
3. ✅ Des brouillons sont créés
4. ✅ Publier sur Vinted en 1 clic

**Profitez-en ! 🚀**
