# 🚀 TESTE TON BOT VINTED MAINTENANT!

## ✅ TES SERVEURS SONT ACTIFS

- **Backend**: http://localhost:8001 ✅
- **Frontend**: http://localhost:5004 ✅

---

## 🎯 ÉTAPE PAR ÉTAPE - PREMIÈRE PUBLICATION

### 1️⃣ CONFIGURE TA SESSION VINTED (5 minutes)

**Pourquoi tu n'as jamais publié sur Vinted?**
➡️ Parce que tu n'as jamais configuré ton cookie Vinted!

**Comment faire:**

1. Ouvre **Chrome/Edge**
2. Va sur **https://www.vinted.fr**
3. **Connecte-toi** à ton compte
4. Appuie sur **F12** (DevTools)
5. Va dans l'onglet **"Application"**
6. Dans le menu gauche:
   - Clique sur **"Cookies"**
   - Clique sur **"https://www.vinted.fr"**
7. **Copie TOUS les cookies** en format:
   ```
   _vinted_fr_session=abc123; anon_id=xyz789; _gcl_au=123; ...
   ```

8. **Colle-les dans ton app**:
   - Va sur http://localhost:5004/settings
   - Colle dans "Vinted Cookie"
   - Clique **"Tester ma session"**
   - **Doit être VERT** ✅

---

### 2️⃣ UPLOAD 1-2 PHOTOS DE TEST (2 minutes)

1. Va sur http://localhost:5004/upload
2. Glisse **1-2 photos** (n'importe quoi pour tester)
3. Clique **"Analyser avec IA"**
4. Attends 30 secondes
5. Tu seras redirigé vers **/drafts**

---

### 3️⃣ VÉRIFIE TON DRAFT (1 minute)

1. Sur http://localhost:5004/drafts
2. Tu devrais voir **1 nouveau draft**
3. Vérifie que les infos sont OK:
   - Titre
   - Prix
   - Description
   - Photos

4. Si besoin, clique **"Edit"** pour modifier

---

### 4️⃣ PUBLIE SUR VINTED! (2 minutes)

1. Clique sur **"Publish to Vinted"** sur ton draft
2. **Attends 1-2 minutes** (le bot va):
   - ✅ Ouvrir Vinted.fr/items/new
   - ✅ Uploader les photos
   - ✅ Remplir le formulaire
   - ✅ Publier

3. **Vérifie sur Vinted.fr**:
   - Va sur ton profil Vinted
   - Tu devrais voir **ton nouvel article publié**!

---

## 🔍 DEBUGGING SI ÇA NE MARCHE PAS

### ❌ "Not authenticated"
➡️ Retourne à l'étape 1, ton cookie n'est pas configuré

### ❌ "SESSION_EXPIRED"
➡️ Ton cookie a expiré, recupère-en un nouveau (étape 1)

### ❌ "Photo not found"
➡️ Re-upload tes photos (étape 2)

### ❌ "Captcha detected"
➡️ Ouvre Vinted.fr et résous le captcha, puis réessaye

---

## 📋 CHECKLIST AVANT DE TESTER

- [ ] ✅ Backend actif (http://localhost:8001)
- [ ] ✅ Frontend actif (http://localhost:5004)
- [ ] ✅ Cookie Vinted configuré ET testé (vert)
- [ ] ✅ Photos uploadées
- [ ] ✅ Draft créé
- [ ] ✅ Connecté à internet

---

## 🎬 COMMANDES RAPIDES

**Teste ta session Vinted:**
```
http://localhost:5004/settings → "Tester ma session"
```

**Upload des photos:**
```
http://localhost:5004/upload → Glisse photos → "Analyser avec IA"
```

**Publier:**
```
http://localhost:5004/drafts → "Publish to Vinted"
```

---

## 📚 DOCUMENTATION COMPLÈTE

Pour plus de détails, lis le fichier:
**`GUIDE_PUBLICATION_VINTED.md`**

---

## 💡 CONSEIL PRO

**Pour tester rapidement:**
1. Utilise 1-2 photos de vêtements que tu as déjà sur Vinted
2. Teste la publication en mode "brouillon" d'abord
3. Une fois que ça marche, upload en masse!

---

## 🆘 BESOIN D'AIDE?

Si ça ne marche toujours pas après avoir suivi ce guide:

1. **Vérifie les logs du backend** (terminal avec uvicorn)
2. **Vérifie que ta session est VERTE** dans Settings
3. **Partage-moi les logs** et je t'aiderai

---

## 🎯 MAINTENANT: VA SUR http://localhost:5004/settings

**Et configure ton cookie Vinted!** C'est la seule chose qui manque pour que tout fonctionne! 🚀
