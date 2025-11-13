# 🔍 Système de Monitoring Automatique Vinted

Ce système détecte automatiquement les changements sur la plateforme Vinted qui pourraient affecter le bot, et envoie des notifications Telegram (avec analyse optionnelle par Claude AI).

## 🎯 Fonctionnalités

✅ **Détection automatique des changements**
- Structure des pages (hashes MD5)
- Sélecteurs de formulaires (titre, description, prix, etc.)
- Boutons d'action (publier, brouillon)
- Validité de session
- Fonctionnalité d'upload

📱 **Notifications Telegram**
- Alertes en temps réel
- Rapports détaillés avec niveau de sévérité
- Messages formatés en HTML

🤖 **Auto-analyse par Claude (optionnel)**
- Analyse intelligente des changements
- Suggestions de corrections de code
- Sélecteurs alternatifs proposés

⏰ **Exécution automatique quotidienne**
- GitHub Actions workflow
- Scheduling flexible (8h du matin par défaut)
- Archivage des résultats

## 🚀 Installation

### 1. Installer les dépendances

```bash
pip install anthropic requests playwright
playwright install chromium
```

### 2. Configurer les secrets

#### Variables d'environnement locales (`.env`):

```bash
# Required
VINTED_COOKIE="your_vinted_cookie_here"

# Optional
VINTED_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"
ANTHROPIC_API_KEY="your_claude_api_key"
ENABLE_CLAUDE_AUTO_FIX="false"  # Set to "true" to enable
ENABLE_TELEGRAM="true"
```

#### GitHub Secrets (pour GitHub Actions):

Allez dans **Settings → Secrets → Actions** et ajoutez:

- `VINTED_COOKIE` (requis)
- `VINTED_USER_AGENT` (optionnel)
- `TELEGRAM_BOT_TOKEN` (optionnel)
- `TELEGRAM_CHAT_ID` (optionnel)
- `ANTHROPIC_API_KEY` (optionnel)

### 3. Configuration Telegram

#### Créer un bot Telegram:

1. Parlez à [@BotFather](https://t.me/botfather) sur Telegram
2. Envoyez `/newbot` et suivez les instructions
3. Copiez le token fourni → `TELEGRAM_BOT_TOKEN`

#### Obtenir votre Chat ID:

1. Parlez à [@userinfobot](https://t.me/userinfobot)
2. Il vous donnera votre ID → `TELEGRAM_CHAT_ID`
3. Ou créez un groupe, ajoutez votre bot, et utilisez l'ID du groupe

#### Tester la connexion:

```bash
python backend/monitoring/telegram_notifier.py
```

### 4. Obtenir votre Cookie Vinted

#### Méthode 1: Depuis le navigateur (Chrome/Edge)

1. Connectez-vous sur https://www.vinted.fr
2. Ouvrez les DevTools (F12)
3. Onglet **Network** → Rafraîchir la page
4. Cliquez sur une requête vers `vinted.fr`
5. Onglet **Headers** → Section **Request Headers**
6. Copiez la valeur du header `Cookie`

#### Méthode 2: Avec une extension

- **Cookie Editor** (Chrome/Firefox)
- Exportez tous les cookies de `vinted.fr`
- Formatez-les en une seule chaîne: `name1=value1; name2=value2; ...`

## 📖 Utilisation

### Exécution locale (test unique)

```bash
# Monitoring simple
python backend/monitoring/run_monitor.py

# Orchestrateur complet (avec Telegram + Claude)
python backend/monitoring/orchestrator.py
```

### Exécution automatique quotidienne

Le workflow GitHub Actions s'exécute automatiquement tous les jours à 8h UTC.

**Pour déclencher manuellement:**

1. Allez dans **Actions** → **Vinted Platform Monitor**
2. Cliquez sur **Run workflow**

### Tester le monitoring manuellement

```bash
# Test du monitoring seul
python backend/monitoring/vinted_monitor.py

# Test de Telegram
python backend/monitoring/telegram_notifier.py

# Test de Claude auto-fix (nécessite ANTHROPIC_API_KEY)
python backend/monitoring/claude_auto_fix.py
```

## 📊 Résultats du Monitoring

Les résultats sont sauvegardés dans:
```
backend/monitoring/snapshots/
├── monitor_results_latest.json       # Dernier rapport
├── monitor_results_YYYYMMDD_HHMMSS.json  # Historique
├── items_new_latest.json             # Snapshot de structure
└── ...
```

Les analyses Claude sont dans:
```
backend/monitoring/analyses/
├── claude_analysis_latest.json
└── claude_analysis_YYYYMMDD_HHMMSS.json
```

## 🔧 Configuration Avancée

### Personnaliser le scheduling

Éditez `.github/workflows/vinted-monitor.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # 8h UTC tous les jours
  # Exemples:
  # - cron: '0 */6 * * *'   # Toutes les 6 heures
  # - cron: '0 8 * * 1-5'   # 8h, lundi à vendredi
  # - cron: '0 0,12 * * *'  # Midi et minuit
```

### Ajouter des tests personnalisés

Éditez `backend/monitoring/vinted_monitor.py` et ajoutez votre test:

```python
async def _test_custom_feature(self, page: Page, client: VintedClient):
    """Test custom feature"""
    test_name = "custom_feature"

    try:
        # Your test logic here
        await page.goto("https://www.vinted.fr/custom-page")
        element = await page.query_selector(".custom-selector")

        if not element:
            self.results["changes_detected"].append({
                "test": test_name,
                "message": "Custom feature broken",
                "severity": "high"
            })

        self.results["tests"].append({
            "name": test_name,
            "status": "passed" if element else "failed"
        })
    except Exception as e:
        self.results["tests"].append({
            "name": test_name,
            "status": "failed",
            "error": str(e)
        })
```

Puis appelez-le dans `run_all_tests()`:
```python
await self._test_custom_feature(page, client)
```

### Personnaliser les notifications Telegram

Éditez `backend/monitoring/telegram_notifier.py` pour changer le format des messages.

### Activer l'auto-correction Claude

⚠️ **Attention:** L'auto-correction automatique est désactivée par défaut pour des raisons de sécurité.

Pour l'activer:

1. Définissez `ENABLE_CLAUDE_AUTO_FIX=true`
2. Claude analysera les problèmes et suggérera des corrections
3. Les suggestions seront sauvegardées dans `backend/monitoring/analyses/`
4. **Review manuellement** avant d'appliquer les changements

## 🛠 Dépannage

### "Session expired" dans les tests

→ Votre cookie Vinted a expiré. Récupérez-en un nouveau.

### "Telegram connection failed"

→ Vérifiez `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID`

### "Claude API not configured"

→ Ajoutez `ANTHROPIC_API_KEY` à vos variables d'environnement

### Playwright ne démarre pas

```bash
playwright install chromium
playwright install-deps  # Linux seulement
```

### Tests échouent sur GitHub Actions

→ Vérifiez que tous les secrets sont configurés dans GitHub

## 📈 Amélirations Futures

- [ ] Dashboard web pour visualiser l'historique
- [ ] Détection de patterns dans les changements
- [ ] Auto-PR avec corrections Claude (avec review humaine)
- [ ] Support multi-plateformes (Vinted + autres)
- [ ] Alertes webhook (Slack, Discord, etc.)
- [ ] Machine learning pour prédire les changements

## 🤝 Contribution

Pour ajouter de nouvelles fonctionnalités:

1. Ajoutez votre test dans `vinted_monitor.py`
2. Testez localement
3. Mettez à jour cette documentation
4. Committez et pushez

## 📝 License

Voir LICENSE dans le repository principal.

## 🆘 Support

En cas de problème:
1. Vérifiez les logs dans GitHub Actions
2. Consultez `backend/monitoring/snapshots/monitor_results_latest.json`
3. Testez localement avec des logs verbeux
4. Créez une issue GitHub avec les détails

---

**Fait avec ❤️ et Claude Code**
