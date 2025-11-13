# 🚀 Guide de Setup - Monitoring Automatique Vinted

Ce guide vous aide à configurer le système de monitoring automatique en **10 minutes**.

## ⚡ Quick Start

### 1. Installer les dépendances (2 min)

```bash
# Installer les packages Python
pip install playwright anthropic requests loguru python-dotenv colorama

# Installer Chromium pour Playwright
playwright install chromium
```

### 2. Récupérer votre Cookie Vinted (3 min)

#### Sur Chrome/Edge/Firefox:

1. Ouvrez https://www.vinted.fr et **connectez-vous**
2. Appuyez sur **F12** (DevTools)
3. Onglet **Network** (Réseau)
4. Rafraîchissez la page (F5)
5. Cliquez sur une requête vers `vinted.fr`
6. Section **Request Headers**
7. Trouvez `Cookie:` et **copiez toute la valeur**

   Exemple:
   ```
   _vinted_fr_session=xyz123...; _ga=GA1.2...; ...
   ```

### 3. Créer un Bot Telegram (2 min)

1. Ouvrez Telegram et cherchez **@BotFather**
2. Envoyez `/newbot`
3. Suivez les instructions
4. Copiez le **token** fourni
5. Parlez à **@userinfobot** pour obtenir votre **Chat ID**

### 4. Configurer les variables d'environnement (2 min)

Créez un fichier `.env` à la racine:

```bash
# Copier le template
cp backend/monitoring/.env.example .env
```

Éditez `.env` et ajoutez:

```bash
# OBLIGATOIRE
VINTED_COOKIE="collez_votre_cookie_ici"

# RECOMMANDÉ (pour les notifications)
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_CHAT_ID="123456789"

# OPTIONNEL (pour l'analyse Claude)
ANTHROPIC_API_KEY="sk_ant-..."
ENABLE_CLAUDE_AUTO_FIX="false"
```

### 5. Tester l'installation (1 min)

```bash
# Vérifier que tout est configuré
python backend/monitoring/test_setup.py

# Tester le monitoring
python backend/monitoring/run_monitor.py

# Tester Telegram
python backend/monitoring/telegram_notifier.py
```

## 🔧 Configuration GitHub Actions (pour monitoring automatique)

### 1. Ajouter les Secrets GitHub

Allez dans votre repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Ajoutez ces secrets:

| Secret Name | Description | Requis? |
|-------------|-------------|---------|
| `VINTED_COOKIE` | Votre cookie Vinted | ✅ Oui |
| `TELEGRAM_BOT_TOKEN` | Token de votre bot Telegram | ⚠️ Recommandé |
| `TELEGRAM_CHAT_ID` | Votre chat ID Telegram | ⚠️ Recommandé |
| `ANTHROPIC_API_KEY` | Clé API Claude (pour auto-fix) | ❌ Optionnel |

### 2. Activer GitHub Actions

Le workflow est dans `.github/workflows/vinted-monitor.yml`

Il s'exécute automatiquement:
- **Tous les jours à 8h UTC** (9h Paris hiver, 10h Paris été)
- **À chaque push** sur `backend/monitoring/**`
- **Manuellement** depuis l'onglet Actions

### 3. Tester manuellement

1. Allez dans **Actions**
2. Sélectionnez **Vinted Platform Monitor**
3. Cliquez **Run workflow**
4. Attendez 1-2 minutes
5. Vérifiez les résultats et votre Telegram

## 📱 Format des Notifications Telegram

Vous recevrez des messages comme:

```
🚨 ALERTE CRITIQUE - Vinted Bot

📅 Date: 2025-01-15T08:00:00
📊 Status: CRITICAL

🔍 Changements détectés (2):
1. [CRITICAL] Form selector missing: title
2. [HIGH] Button selector missing: publish

❌ Tests échoués (1):
• form_selectors: Title input not found

🔧 Actions requises:
1. Vérifier les changements détectés
2. Mettre à jour les sélecteurs si nécessaire
3. Tester manuellement le bot
```

## 🤖 Utiliser Claude pour l'Auto-Fix (Optionnel)

Si vous activez `ENABLE_CLAUDE_AUTO_FIX=true`, Claude analysera automatiquement les problèmes et proposera des solutions.

### Obtenir une clé API Claude:

1. Allez sur https://console.anthropic.com
2. Créez un compte ou connectez-vous
3. Allez dans **API Keys**
4. Créez une nouvelle clé
5. Copiez-la dans `ANTHROPIC_API_KEY`

### Ce que Claude fait:

- ✅ Analyse les sélecteurs manquants
- ✅ Propose des sélecteurs alternatifs
- ✅ Suggère des modifications de code
- ✅ Génère un rapport détaillé en JSON

**Note:** Les suggestions de Claude sont **sauvegardées** mais **pas appliquées automatiquement** pour des raisons de sécurité. Vous devez les reviewer manuellement.

## 📊 Voir les Résultats

### Localement:

```bash
# Derniers résultats
cat backend/monitoring/snapshots/monitor_results_latest.json

# Analyse Claude (si activée)
cat backend/monitoring/analyses/claude_analysis_latest.json
```

### Sur GitHub:

1. Allez dans **Actions**
2. Cliquez sur le dernier run
3. Téléchargez les **artifacts**:
   - `monitoring-results-XXX` : Résultats JSON
   - `monitoring-snapshots-XXX` : Snapshots complets

## 🔍 Personnaliser le Monitoring

### Changer la fréquence:

Éditez `.github/workflows/vinted-monitor.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # 8h UTC tous les jours

  # Autres exemples:
  # - cron: '0 */6 * * *'   # Toutes les 6 heures
  # - cron: '0 8 * * 1-5'   # Lundi à vendredi à 8h
  # - cron: '0 0,12 * * *'  # À minuit et midi
```

### Ajouter vos propres tests:

Éditez `backend/monitoring/vinted_monitor.py` et ajoutez votre fonction de test.

Voir le README complet: `backend/monitoring/README.md`

## ❓ Problèmes Courants

### ❌ "VINTED_COOKIE environment variable required"

→ Votre `.env` n'est pas chargé ou le cookie est vide
→ Vérifiez que le fichier `.env` est à la racine du projet

### ❌ "Session expired" dans les résultats

→ Votre cookie Vinted a expiré (durée de vie ~30 jours)
→ Récupérez un nouveau cookie depuis le navigateur

### ❌ "Telegram connection failed"

→ Vérifiez que `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` sont corrects
→ Testez avec: `python backend/monitoring/telegram_notifier.py`

### ❌ Playwright ne démarre pas

```bash
# Réinstaller Chromium
playwright install chromium

# Sur Linux, installer les dépendances système
playwright install-deps
```

### ❌ Module 'anthropic' not found

```bash
pip install anthropic
```

## 🎯 Checklist Complète

- [ ] Python 3.9+ installé
- [ ] Dépendances pip installées
- [ ] Playwright Chromium installé
- [ ] Cookie Vinted récupéré
- [ ] Bot Telegram créé (optionnel)
- [ ] Fichier `.env` configuré
- [ ] Test setup passé (`test_setup.py`)
- [ ] Test monitoring passé (`run_monitor.py`)
- [ ] Secrets GitHub configurés
- [ ] Workflow GitHub Actions testé manuellement

## 📚 Documentation Complète

Pour plus de détails, consultez:
- `backend/monitoring/README.md` : Documentation technique complète
- `.github/workflows/vinted-monitor.yml` : Configuration du workflow
- `backend/monitoring/` : Code source

## 🆘 Besoin d'Aide?

1. Exécutez le diagnostic: `python backend/monitoring/test_setup.py`
2. Vérifiez les logs détaillés dans les résultats JSON
3. Testez chaque composant individuellement
4. Créez une issue GitHub avec les logs

---

**Temps total estimé: 10 minutes** ⏱️

Une fois configuré, le système surveille automatiquement Vinted tous les jours et vous alerte en cas de changement! 🎉
