# 🚀 COMMENT PUBLIER SUR VINTED

## ✅ 1. OBTENIR TON COOKIE VINTED (session valide)

Pour publier sur Vinted, tu dois donner à l'app un accès temporaire à ton compte Vinted via un **cookie de session**.

### **Étapes détaillées** :

1. **Ouvre Chrome/Firefox** et va sur [https://www.vinted.fr](https://www.vinted.fr)
2. **Connecte-toi** à ton compte Vinted
3. **Ouvre la console développeur** :
   - **Chrome** : Clique droit → "Inspecter" → onglet "Console"
   - **Firefox** : Clique droit → "Examiner l'élément" → onglet "Console"
4. **Copie cette commande** dans la console et appuie sur Entrée :

```javascript
document.cookie.split('; ').find(row => row.startsWith('_vinted_fr_session')).split('=')[1]
```

5. **Copie la valeur retournée** (ça ressemble à `eyJhbGci...` ou `abc123def456...`)
6. **Va dans Settings de l'app** VintedBot
7. **Colle le cookie** dans le champ "Vinted Session Cookie"
8. **Sauvegarde**

### **⚠️ Notes importantes** :

- ✅ Le cookie est valide **pendant plusieurs jours** (tu ne dois le refaire qu'une fois par semaine environ)
- ✅ C'est **100% sécurisé** : le cookie ne donne accès qu'à ton compte (pas à tes paiements)
- ❌ **NE PARTAGE JAMAIS** ton cookie avec quelqu'un d'autre
- 🔄 Si tu vois "session expirée", refais ces étapes pour obtenir un nouveau cookie

---

## 📸 2. PUBLIER TES VÊTEMENTS

Une fois le cookie configuré :

1. **Upload tes photos** (6-20 photos recommandées par article)
2. **Attends l'analyse IA** (15-30 secondes)
3. **Vérifie le brouillon** généré automatiquement :
   - Titre ≤70 caractères ✅
   - Description avec puces (•) ✅
   - 4-7 hashtags à la fin ✅
   - Prix suggéré réaliste ✅
4. **Clique sur "Publier sur Vinted"**
5. **Attends 10-15 secondes** → ton annonce est en ligne ! 🎉

---

## 🎯 EXEMPLES DE DESCRIPTION GÉNÉRÉE PAR L'IA

### Exemple 1 : Hoodie Karl Lagerfeld
```
• Hoodie Karl Lagerfeld noir et blanc, broderie poitrine
• Très bon état général
• Matières : 59% coton, 32% rayonne, 9% spandex
• Coupe droite, capuche réglable, poignets élastiqués
• Taille L
• Envoi rapide soigné
#karllagerfeld #hoodie #bicolore #streetwear #L
```

### Exemple 2 : T-shirt Burberry
```
• T-shirt Burberry noir, logo imprimé devant
• Très bon état : matière propre, pas de trous
• Coton confortable, col rond
• Taille XS
• Envoi rapide
#burberry #tshirt #noir #xs #streetwear
```

---

## 🚨 PROBLÈMES COURANTS

### **"Session Vinted expirée"**
➡️ Ton cookie a expiré. Va dans Settings et colle un nouveau cookie (voir étape 1).

### **"Photos introuvables"**
➡️ Actualise la page. Les photos s'affichent maintenant correctement !

### **"Brouillon non validé"**
➡️ Vérifie que :
- Le titre fait ≤70 caractères
- Il y a entre 4-7 hashtags à la fin de la description
- Toutes les photos sont visibles

---

## 💡 ASTUCES POUR VENDRE PLUS

1. **Upload 6-12 photos minimum** : vue de face, dos, détails, étiquettes
2. **Privilégie la lumière naturelle** pour les photos
3. **Montre les défauts** si présents (transparence = confiance)
4. **Prix réaliste** : l'IA suggère le meilleur prix selon la marque et l'état
5. **Hashtags pertinents** : l'IA les génère automatiquement en fonction de ton article

---

## 📊 TARIFS SELON LES MARQUES

L'IA ajuste automatiquement les prix selon les marques :

| Marque | Multiplicateur | Exemple |
|--------|---------------|---------|
| Burberry, Dior, Gucci | ×3.0 à ×5.0 | T-shirt : 50-90€ |
| Karl Lagerfeld, Ralph Lauren | ×2.0 à ×2.5 | Hoodie : 65-75€ |
| Zara, H&M, Uniqlo | ×1.0 | T-shirt : 15-20€ |

---

**Besoin d'aide ?** Contacte le support ou consulte la documentation complète.
