# 🎯 GUIDE COMPLET - Publier sur Vinted

## 📋 ÉTAPE 1: Configurer ta Session Vinted (OBLIGATOIRE)

Sans cette étape, **tu ne pourras JAMAIS publier sur Vinted**.

### A) Obtenir ton Cookie Vinted

1. **Ouvre Vinted.fr dans ton navigateur** (Chrome/Edge recommandé)
2. **Connecte-toi à ton compte Vinted**
3. **Ouvre les DevTools** (F12 ou Clic droit → Inspecter)
4. **Va dans l'onglet "Application" (ou "Storage")**
5. **Dans le menu de gauche**:
   - Clique sur "Cookies"
   - Clique sur "https://www.vinted.fr"
6. **Copie tous les cookies** dans ce format:
   ```
   _vinted_fr_session=XXX; anon_id=YYY; _gcl_au=ZZZ; ...
   ```

### B) Sauvegarder ton Cookie dans l'App

1. **Va sur http://localhost:5004**
2. **Clique sur "Settings"** dans le menu
3. **Colle ton cookie Vinted** dans le champ
4. **Clique sur "Tester ma session"** ✅
   - Si c'est vert → Tout est OK!
   - Si c'est rouge → Ton cookie est expiré, recommence l'étape A

⚠️ **IMPORTANT**: Ton cookie expire après quelques jours/semaines. Il faudra le renouveler régulièrement.

---

## 📸 ÉTAPE 2: Upload et Analyse de Photos

1. **Va sur la page "Upload"** (http://localhost:5004/upload)
2. **Glisse-dépose tes photos** (JPG, PNG, WEBP, HEIC acceptés)
   - Max 500 photos
   - Max 15MB par photo
   - Le bot va grouper automatiquement les photos par article (6 photos = 1 article)
3. **Clique sur "Analyser avec IA"**
4. **Attends l'analyse** (30 secondes à 2 minutes)
5. **Tu seras redirigé vers /drafts** automatiquement

L'IA va:
- ✅ Analyser chaque photo
- ✅ Détecter la marque, catégorie, couleur, taille
- ✅ Générer un titre optimisé
- ✅ Créer une description vendeuse
- ✅ Suggérer un prix de marché

---

## ✏️ ÉTAPE 3: Vérifier et Modifier les Drafts

1. **Va sur la page "Drafts"** (http://localhost:5004/drafts)
2. **Tu verras tous tes brouillons** créés par l'IA
3. **Clique sur "Edit"** pour modifier un draft:
   - Titre (max 200 caractères)
   - Prix (€)
   - Description (max 2000 caractères)
   - Catégorie, Marque, Taille, Couleur, État
   - Photos (réordonne, ajoute, supprime)

---

## 🚀 ÉTAPE 4: Publier sur Vinted

### Option A: Publication Manuelle (1 article)

1. **Dans la page Drafts**, clique sur **"Publish to Vinted"** sur un draft
2. **Le bot va**:
   - ✅ Ouvrir Vinted.fr/items/new
   - ✅ Uploader toutes les photos (1 par 1)
   - ✅ Remplir le formulaire complet
   - ✅ Cliquer sur "Publier"
3. **Vérifie le résultat**:
   - Si succès → Le draft passe en "published"
   - Si captcha → Résous-le manuellement sur Vinted
   - Si erreur → Vérifie que ton cookie est valide (Étape 1B)

### Option B: Publication en Masse (plusieurs articles)

1. **Sélectionne plusieurs drafts** (coche les cases)
2. **Clique sur "Publish Selected"** dans la barre qui apparaît
3. **Le bot va publier tous les drafts** un par un
4. **Attends la fin** (environ 2 minutes par article)

---

## 🔧 DÉPANNAGE - Pourquoi ça ne marche pas?

### ❌ Erreur: "Not authenticated"
**Problème**: Tu n'as pas configuré ton cookie Vinted
**Solution**: Retourne à l'ÉTAPE 1

### ❌ Erreur: "SESSION_EXPIRED"
**Problème**: Ton cookie Vinted a expiré
**Solution**: Va dans Settings → Colle un nouveau cookie → Teste-le

### ❌ Erreur: "Photo not found"
**Problème**: Les photos uploadées ont été supprimées
**Solution**: Re-upload tes photos (ÉTAPE 2)

### ❌ Erreur: "Captcha detected"
**Problème**: Vinted demande une vérification humaine
**Solution**:
1. Ouvre Vinted.fr dans ton navigateur
2. Résous le captcha
3. Réessaye de publier

### ❌ Rien ne se passe quand je clique sur "Publish"
**Problème**: Le backend n'est pas lancé
**Solution**: Vérifie que tu vois des logs dans le terminal backend

---

## 🎬 FLUX COMPLET (Résumé)

```
1. Configure Cookie Vinted (Settings)
   └─> Teste-le (bouton "Tester ma session")

2. Upload Photos (page Upload)
   └─> Analyse IA automatique

3. Vérifie Drafts (page Drafts)
   └─> Modifie si besoin (page DraftEdit)

4. Publie sur Vinted (page Drafts)
   └─> Clique "Publish to Vinted"
   └─> Vérifie que c'est publié sur Vinted.fr
```

---

## 📊 CHECKLIST AVANT DE PUBLIER

- [ ] ✅ Cookie Vinted configuré ET testé (vert)
- [ ] ✅ Photos uploadées et analysées
- [ ] ✅ Drafts créés avec toutes les infos
- [ ] ✅ Backend en cours d'exécution (port 8001)
- [ ] ✅ Frontend en cours d'exécution (port 5004)
- [ ] ✅ Connecté à internet

---

## 🆘 BESOIN D'AIDE?

### Vérifier les Logs

**Backend** (Terminal 1):
```
[INFO] Listing prepared: [titre]
[INFO] Published: ID=xxx, URL=https://...
```

**Frontend** (Terminal 2):
```
[vite] hmr update
```

### Tester la Configuration

1. **Teste ta session Vinted**:
   ```
   Settings → "Tester ma session" → Doit être VERT
   ```

2. **Teste l'upload**:
   ```
   Upload → Glisse 1 photo → "Analyser avec IA" → Doit créer 1 draft
   ```

3. **Teste la publication** (DRY-RUN):
   ```
   Drafts → Sélectionne 1 draft → "Publish" → Vérifie les logs
   ```

---

## 🎯 TESTER MAINTENANT

**Commande rapide pour tester**:

1. Ouvre http://localhost:5004/settings
2. Colle ton cookie Vinted
3. Clique "Tester ma session"
4. Si VERT → Va sur /upload et teste avec 1-2 photos
5. Attends l'analyse
6. Va sur /drafts
7. Clique "Publish to Vinted" sur 1 draft
8. Vérifie sur Vinted.fr que c'est publié

**Si ça ne marche toujours pas après avoir suivi ce guide, vérifie les logs du backend et partage-les moi!**
