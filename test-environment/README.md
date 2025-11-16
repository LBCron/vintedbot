# 🧪 VintedBot Test Environment

Environment de test automatisé complet pour VintedBot avec simulation utilisateur humaine.

## 📋 Vue d'ensemble

Ce système de test permet de:
- ✅ Déployer l'application dans un environnement Docker isolé
- 🤖 Simuler un utilisateur humain testant toutes les fonctionnalités
- 📸 Capturer des screenshots de chaque bug
- 📊 Générer un rapport HTML détaillé avec tous les problèmes trouvés
- 💡 Suggérer des améliorations UX/performance

## 🚀 Quick Start

### Prérequis

- Docker & Docker Compose installés
- Python 3.11+ (pour le simulateur)
- Playwright (installé automatiquement)

### Installation

```bash
# 1. Donner les permissions d'exécution
chmod +x test-environment/*.sh

# 2. Lancer le setup de l'environnement
./test-environment/setup.sh

# 3. Lancer les tests
./test-environment/run-tests.sh
```

## 📁 Structure

```
test-environment/
├── setup.sh                  # Configure l'environnement Docker
├── run-tests.sh              # Lance tous les tests
├── human_simulator.py        # Simulateur utilisateur intelligent
├── fixtures/                 # Images de test (optionnel)
│   ├── shirt_front.jpg
│   ├── shirt_back.jpg
│   └── shirt_label.jpg
└── README.md                 # Cette documentation

test-results/
├── report.html               # Rapport HTML détaillé
├── report.json               # Rapport JSON (pour CI/CD)
└── screenshots/              # Screenshots des bugs
    ├── no-logo_1234567890.png
    ├── error_signup_1234567891.png
    └── ...
```

## 🐳 Architecture Docker

L'environnement de test déploie:

- **PostgreSQL** (port 5433) - Base de données de test
- **Redis** (port 6380) - Cache de test
- **Backend** (port 8001) - API FastAPI
- **Frontend** (port 5174) - Interface React

Tous les services sont interconnectés dans un réseau Docker isolé.

## 🤖 Simulateur Humain

Le simulateur teste automatiquement:

### 1. Homepage & First Visit
- ✅ Temps de chargement (<3s)
- ✅ Présence du logo
- ✅ Call-to-action visible
- ✅ SEO (title, meta)

### 2. Signup Flow
- ✅ Validation email
- ✅ Validation mot de passe
- ✅ Redirection après signup
- ✅ Message de bienvenue

### 3. Dashboard
- ✅ Navigation complète
- ✅ État vide (nouveau compte)
- ✅ Liens vers toutes les fonctionnalités

### 4. Upload & AI Draft
- ✅ Upload d'images
- ✅ Previews visibles
- ✅ Génération IA (titre, description, prix)
- ✅ Temps de traitement (<15s)
- ✅ Qualité du contenu généré

### 5. Langue
- ✅ Sélecteur de langue visible
- ✅ Switch FR/EN fonctionnel
- ✅ Contenu traduit

### 6. Performance
- ✅ DNS lookup time
- ✅ Time to First Byte (TTFB)
- ✅ Page load time
- ✅ Bundle size

### 7. Mobile Responsive
- ✅ Affichage mobile (375px)
- ✅ Pas de scroll horizontal
- ✅ Navigation adaptée

### 8. Accessibility
- ✅ Alt text sur images
- ✅ Hiérarchie headings (H1-H6)
- ✅ Labels sur inputs
- ✅ Contraste couleurs

## 📊 Rapport Généré

Le rapport HTML contient:

### 🔴 Bugs Trouvés
Chaque bug inclut:
- **Sévérité**: Critical, High, Medium, Low
- **Type**: UI, Backend, Performance, Security, etc.
- **Description**: Problème exact
- **Screenshot**: Image du bug
- **Comment reproduire**: Étapes détaillées
- **Fix suggéré**: Solution recommandée

### 💡 Améliorations Suggérées
Chaque amélioration inclut:
- **Type**: UX, Performance, SEO, Content
- **Description**: Ce qui peut être amélioré
- **Suggestion**: Comment l'améliorer
- **Impact business**: Effet sur conversions/UX
- **Effort**: Temps d'implémentation estimé

### 📈 Métriques
- Tests passed/failed
- Temps d'exécution
- Performance metrics
- Screenshots

## 🎯 Utilisation Avancée

### Variables d'environnement

```bash
# Optionnel: Fournir votre clé OpenAI pour tester l'IA
export OPENAI_API_KEY="sk-..."

# Lancer les tests
./test-environment/run-tests.sh
```

### Mode headless vs visible

```python
# Modifier dans human_simulator.py
simulator = HumanSimulator(
    base_url="http://localhost:5174",
    headless=False  # False = voir le navigateur pendant les tests
)
```

### Ajouter des fixtures d'images

```bash
# Créer le dossier fixtures
mkdir -p test-environment/fixtures

# Ajouter vos images de test
cp your-test-images/*.jpg test-environment/fixtures/
```

## 🛑 Arrêt et Nettoyage

```bash
# Arrêter l'environnement
docker-compose -f docker-compose.test.yml down

# Nettoyer complètement (volumes inclus)
docker-compose -f docker-compose.test.yml down -v

# Supprimer les rapports
rm -rf test-results/
```

## 🔧 Troubleshooting

### Les containers ne démarrent pas

```bash
# Vérifier les logs
docker-compose -f docker-compose.test.yml logs backend
docker-compose -f docker-compose.test.yml logs frontend

# Rebuild from scratch
docker-compose -f docker-compose.test.yml build --no-cache
```

### Tests échouent immédiatement

```bash
# Vérifier que l'environnement est healthy
docker ps

# Tester manuellement les endpoints
curl http://localhost:8001/health
curl http://localhost:5174/
```

### Playwright ne s'installe pas

```bash
# Installer manuellement
pip3 install playwright
playwright install chromium --with-deps
```

## 📚 Exemples de Rapports

### Exemple de bug critique

```
🔴 CRITICAL - JavaScript Error
Type: crash
Issue: Uncaught TypeError: Cannot read property 'map' of undefined
Screenshot: error_dashboard_1234567890.png
Fix: Add null check before mapping drafts array
```

### Exemple d'amélioration

```
💡 MEDIUM - Performance
Issue: Homepage loads in 4.2s (target: <3s)
Suggestion: Enable code splitting, lazy load images, optimize bundle
Business Impact: 5% conversion improvement
Implementation Effort: 2 days
```

## 🎯 Intégration CI/CD

Le rapport JSON peut être utilisé dans votre CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: ./test-environment/run-tests.sh

- name: Check Critical Bugs
  run: |
    critical=$(cat test-results/report.json | jq '.summary.critical_bugs')
    if [ "$critical" -gt 0 ]; then
      echo "❌ $critical critical bugs found!"
      exit 1
    fi
```

## 💰 Valeur

- **Temps économisé**: ~10h de tests manuels automatisés
- **Bugs trouvés**: Avant production = évite incidents
- **Rapport professionnel**: Prêt à partager avec l'équipe
- **Reproductible**: Lancer avant chaque déploiement

## 🤝 Contribution

Pour ajouter de nouveaux tests:

1. Éditer `test-environment/human_simulator.py`
2. Ajouter une nouvelle méthode `async def test_your_feature(self, page: Page)`
3. L'appeler dans `run_complete_simulation()`
4. Relancer les tests

## 📞 Support

Si vous rencontrez des problèmes:

1. Vérifier la section Troubleshooting
2. Consulter les logs Docker
3. Ouvrir une issue avec le rapport JSON

---

**Créé par Claude Code** 🤖
Environnement de test professionnel pour VintedBot
