# 🚀 Guide de Déploiement VintedBot - ULTRA SIMPLE

## ✅ Ce qui a été préparé pour toi

J'ai créé **TOUS** les fichiers nécessaires :
- ✅ `Dockerfile` - Pour construire ton app
- ✅ `fly.toml` - Configuration Fly.io
- ✅ `.dockerignore` - Fichiers à ignorer
- ✅ `deploy.ps1` - **Script automatique qui fait TOUT**

---

## 🎯 Ce que TU dois faire (2 étapes)

### ÉTAPE 1 : Installer Fly CLI (1 fois seulement)

**Ouvre PowerShell en tant qu'Administrateur** (clic droit → "Exécuter en tant qu'administrateur")

```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

Attends que ça s'installe (30 secondes).

**Ferme et rouvre PowerShell** (normal, pas admin cette fois).

---

### ÉTAPE 2 : Lancer le script de déploiement

**Dans PowerShell normal :**

```powershell
cd "C:\Users\Ronan\OneDrive\桌面\vintedbots"
.\deploy.ps1
```

**Le script va :**
1. ✅ Générer tes secrets de sécurité
2. ✅ Te connecter à Fly.io
3. ✅ Créer ton application
4. ✅ Configurer le stockage
5. ✅ Te demander tes clés API (OpenAI, Stripe)
6. ✅ Déployer automatiquement
7. ✅ Te donner l'URL de ton app !

**Durée totale : 10 minutes** ⏱️

---

## 🔑 Clés API à préparer

Pendant que le script tourne, il te demandera :

### 1. OpenAI API Key
- Va sur : https://platform.openai.com/api-keys
- Clique "Create new secret key"
- Copie la clé : `sk_...`

### 2. Stripe API Key (optionnel, pour tester)
- Va sur : https://dashboard.stripe.com/test/apikeys
- Copie "Secret key" : `sk_test_...`

**Tu peux aussi laisser vide et configurer plus tard !**

---

## ❓ Si tu as une erreur

### Erreur : "fly not recognized"
👉 Tu n'as pas fermé/rouvert PowerShell après l'install de Fly CLI

### Erreur : "Unauthorized"
👉 Vérifie que tu es bien connecté à ton compte Fly.io

### Erreur pendant le build
👉 Copie-colle l'erreur et dis-moi, je t'aide !

---

## 🎉 Après le déploiement

Tu verras :
```
🎉 DÉPLOIEMENT RÉUSSI !
📱 Ton app est disponible sur : https://ton-app.fly.dev
```

**Teste ton app :**
```
https://ton-app.fly.dev/health
```

Tu devrais voir :
```json
{
  "status": "ok"
}
```

---

## 📊 Commandes utiles

```powershell
# Voir les logs en direct
fly logs --app ton-app

# Status de l'app
fly status --app ton-app

# Ouvrir le dashboard
fly dashboard

# SSH dans la machine
fly ssh console --app ton-app
```

---

## 💡 Notes importantes

1. **Tes secrets sont sauvegardés** dans `secrets.txt` - GARDE CE FICHIER PRÉCIEUSEMENT !
2. Le déploiement prend **5-10 minutes** la première fois
3. Fly.io est **GRATUIT** jusqu'à un certain usage
4. Si tu veux changer un secret : `fly secrets set MA_CLE="valeur" --app ton-app`

---

## 🆘 Besoin d'aide ?

Si ça bloque, dis-moi où ça coince et je t'aide ! 💪
