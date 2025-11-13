# 💬 GUIDE - Messages Vinted & Automation

## 🎯 FONCTIONNALITÉS DISPONIBLES

Ton bot VintedBot a **DÉJÀ** ces fonctionnalités Premium intégrées:

### 1. **Messages Vinted** 📬
- Voir tous tes messages reçus sur Vinted
- Répondre aux conversations
- Marquer comme lu
- Suggestions IA pour répondre rapidement

### 2. **Auto-Messages** 💬
- Envoyer automatiquement un message quand quelqu'un ajoute ton article en favori (like)
- Personnaliser le message avec des variables
- Définir un délai (pour paraître humain)
- Limite journalière configurable

---

## 🚀 COMMENT UTILISER

### 📬 ÉTAPE 1: Voir tes messages Vinted

1. **Va sur http://localhost:5004**
2. **Clique sur "Messages"** dans le menu
3. **Tu verras toutes tes conversations Vinted**
   - Liste des conversations à gauche
   - Messages dans chaque conversation
   - Suggestions IA pour répondre

**Note**: Pour l'instant, la page Messages utilise des données de démonstration. Les vrais messages Vinted seront synchronisés automatiquement par le backend.

---

### 💬 ÉTAPE 2: Configurer les messages automatiques aux "likers"

1. **Va sur http://localhost:5004**
2. **Clique sur "Automation"** dans le menu
3. **Clique sur l'onglet "Auto-Messages"**
4. **Configure ton template de message:**

```
Hi! I noticed you liked my {item_title}. I can offer it to you for {price}€. Interested?
```

**Variables disponibles:**
- `{item_title}` - Titre de l'article
- `{price}` - Prix de l'article
- `{brand}` - Marque
- `{category}` - Catégorie

5. **Configure les paramètres:**
   - **Délai après le like**: 30 minutes (pour paraître humain)
   - **Limite journalière**: 30 messages max par jour
   - **Déclencheurs**: Coche "new_like" (quand quelqu'un like)

6. **Clique sur "Save Template"**

---

## 🔧 COMMENT ÇA MARCHE

### Backend - Synchronisation automatique

Le backend synchronise automatiquement:
- ✅ **Messages Vinted** - Toutes les 15 minutes
- ✅ **Nouveaux likes** - Détecte quand quelqu'un like un article
- ✅ **Envoie les auto-messages** - Selon ta configuration

### Workflow Auto-Messages:

```
1. Quelqu'un like ton article sur Vinted
   └─> Backend détecte le nouveau like

2. Backend attend le délai configuré (ex: 30 min)
   └─> Pour paraître humain et pas spam

3. Backend génère le message personnalisé
   └─> Remplace {item_title}, {price}, etc.

4. Backend envoie le message via Playwright
   └─> Simule un vrai utilisateur sur Vinted

5. Message envoyé! ✅
   └─> Visible dans ta page Messages
```

---

## 🎯 EXEMPLE COMPLET

### Scénario:

1. Tu as publié un "Nike Air Max 90" à **89€**
2. Marie ajoute ton article en favori ❤️
3. Après **30 minutes**, elle reçoit automatiquement:

```
Hi! I noticed you liked my Nike Air Max 90.
I can offer it to you for 89€. Interested?
```

4. Marie répond "Oui je suis intéressée!"
5. Tu vois sa réponse dans **Messages** et tu réponds

---

## 📋 CONFIGURATION RECOMMANDÉE

### Pour paraître humain et éviter le spam:

```yaml
Message Template:
  "Hi! I noticed you liked my {item_title}.
   I can offer it to you for {price}€. Interested? 😊"

Délai: 30-60 minutes
  └─> Ne pas envoyer instantanément

Limite journalière: 20-30 messages/jour
  └─> Vinted peut détecter si tu envoies trop

Déclencheurs: new_like uniquement
  └─> Focusfocus sur les gens intéressés
```

---

## 🔍 ENDPOINTS BACKEND DISPONIBLES

Ton backend a déjà ces endpoints configurés:

### Messages:
- `GET /vinted/messages` - Liste des conversations
- `GET /vinted/messages/{thread_id}` - Messages d'une conversation
- `POST /vinted/messages/{thread_id}/reply` - Répondre à un message
- `POST /vinted/messages/bulk-mark-read` - Marquer comme lu

### Automation:
- `GET /automation/rules` - Voir toutes tes règles d'automation
- `POST /automation/messages/config` - Configurer auto-messages
- `GET /automation/summary` - Statistiques d'automation

---

## ✅ VÉRIFICATION

### Pour vérifier que tout fonctionne:

1. **Messages backend actifs:**
   ```bash
   # Dans les logs backend tu devrais voir:
   [INBOX] Running inbox sync job
   ✅ Inbox sync completed
   ```

2. **Automation active:**
   ```bash
   # Dans les logs backend:
   [AUTOMATION] Running automation executor...
   ```

3. **Session Vinted valide:**
   - Va sur Settings
   - Teste ta session Vinted
   - Doit être VERT ✅

---

## 🆘 DÉPANNAGE

### ❌ "Pas de messages dans la page Messages"
**Solution**: Les messages sont synchronisés toutes les 15 minutes. Attends un peu ou redémarre le backend.

### ❌ "Auto-messages ne s'envoient pas"
**Vérifications:**
1. ✅ Cookie Vinted configuré dans Settings (et testé VERT)
2. ✅ Auto-messages activé dans Automation
3. ✅ Template de message configuré
4. ✅ Backend en cours d'exécution

### ❌ "Erreur: Not authenticated"
**Solution**: Configure ton cookie Vinted dans Settings (voir `PROBLEME_RESOLU.md`)

---

## 💡 ASTUCES PRO

### 1. Template multi-variantes
Crée plusieurs templates pour varier les messages:

```
Template 1: "Hi! Interested in my {item_title} for {price}€?"
Template 2: "Hello! I saw you liked my {item_title}. Still available! 😊"
Template 3: "Hey! {item_title} is waiting for you at {price}€!"
```

### 2. Délai intelligent
- **30 min** pour les articles > 50€ (plus "premium")
- **1-2 heures** pour les articles < 20€ (moins urgent)

### 3. Limite journalière
- **Compte nouveau**: 10-15 messages/jour
- **Compte établi**: 30-50 messages/jour
- **Ne JAMAIS dépasser 100/jour** (risque de ban)

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ **Configure ton cookie Vinted** (Settings)
2. ✅ **Configure ton template Auto-Messages** (Automation)
3. ✅ **Publie quelques articles** (Upload → Drafts → Publish)
4. ✅ **Attends les premiers likes**
5. ✅ **Vérifie que les messages s'envoient automatiquement**
6. ✅ **Réponds dans la page Messages**

---

## 📊 STATISTIQUES

Tu pourras voir dans **Automation** → **Active Rules**:
- Nombre de messages envoyés aujourd'hui
- Taux de réponse
- Dernière exécution
- Prochaine exécution planifiée

---

**Tu as maintenant un bot Vinted COMPLET avec messages automatiques! 🎉**

**Questions? Vérifie les logs du backend pour débugger!**
