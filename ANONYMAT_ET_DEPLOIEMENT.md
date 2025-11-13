# 🕶️ Guide Complet: Anonymat et Déploiement Sécurisé

## ⚠️ DISCLAIMER LÉGAL

**IMPORTANT:** L'automatisation de Vinted viole leurs Conditions Générales d'Utilisation (CGU). Ce guide est fourni à **titre éducatif uniquement**.

**Risques:**
- ❌ Ban de vos comptes Vinted
- ⚠️ Possibles actions légales de Vinted
- ⚠️ Responsabilité légale si vous commercialisez ce bot

**Recommandation:** Utilisez ce bot uniquement pour **usage personnel** et consultez un avocat avant toute commercialisation.

---

## 🎭 Partie 1: Rester Anonyme

### 1.1 Identité en Ligne

#### GitHub Anonyme

```bash
# Créer un nouveau compte GitHub
# - Utilisez un email jetable (temp-mail.org, guerrillamail.com)
# - Utilisez un pseudonyme unique
# - N'utilisez pas votre vrai nom

# Configurer Git avec pseudonyme
git config user.name "YourPseudonym"
git config user.email "pseudonym@tempmail.com"
```

#### Email Jetable

Services recommandés:
- **ProtonMail** (anonyme, chiffré)
- **Tutanota** (anonyme, sécurisé)
- **temp-mail.org** (temporaire)

### 1.2 Masquer votre IP

#### Option 1: VPN Commercial

**Recommandés pour l'anonymat:**
- **Mullvad** - Paiement crypto, pas de logs
- **ProtonVPN** - No-log, en Suisse
- **IVPN** - Anonymous payment

```bash
# Installer OpenVPN
sudo apt install openvpn

# Connecter au VPN
sudo openvpn --config your-vpn.ovpn
```

#### Option 2: Proxies Rotatifs

Le bot supporte la rotation de proxies:

```python
# Dans votre code
from backend.core.proxy_manager import ProxyManager

proxy_manager = ProxyManager()

# Ajouter des proxies
proxy_manager.add_proxy("proxy1.example.com", 8080, "http", country="FR")
proxy_manager.add_proxy("proxy2.example.com", 8080, "http", country="FR")

# Utiliser avec Playwright
proxy_config = proxy_manager.get_playwright_proxy_config()
context = await browser.new_context(proxy=proxy_config)
```

**Où acheter des proxies:**
- **Bright Data** (cher mais fiable)
- **Smartproxy** (résidentiel)
- **Oxylabs** (premium)
- **ProxyRack** (abordable)

#### Option 3: Tor (Maximum Anonymat)

```bash
# Installer Tor
sudo apt install tor

# Démarrer Tor
sudo service tor start

# Configurer proxy SOCKS5
# Host: 127.0.0.1, Port: 9050
```

**⚠️ Attention:** Tor est lent et peut déclencher des captchas.

### 1.3 Fingerprinting Anti-Détection

Le bot inclut déjà des protections:

```python
from backend.core.anti_detection import setup_stealth_page
from backend.core.anonymity import AnonymityManager

# Générer fingerprint aléatoire
fingerprint = AnonymityManager.generate_fingerprint()

# Appliquer à la page Playwright
async with VintedClient() as client:
    page = await client.new_page()
    await setup_stealth_page(page)
    # Maintenant la page est protégée contre la détection
```

**Ce qui est randomisé:**
- User-Agent
- Résolution d'écran
- Timezone
- Canvas fingerprint
- WebGL fingerprint
- AudioContext
- Fonts

### 1.4 Cookies & Sessions

**Rotation de cookies:**

```python
from backend.core.cookie_manager import CookieManager

manager = CookieManager()

# Ajouter plusieurs comptes
manager.add_cookie("account1", "cookie1...", "user_agent1", expires_days=30)
manager.add_cookie("account2", "cookie2...", "user_agent2", expires_days=30)

# Rotation automatique
cookie = manager.get_next_cookie()
```

**Bonnes pratiques:**
- 🔄 Rotez les cookies toutes les 50-100 requêtes
- ⏰ Changez de compte toutes les 2-3 heures
- 📊 Surveillez le taux d'échec (si >10%, changez de compte)

---

## 🚀 Partie 2: Déploiement Anonyme

### 2.1 Hébergement Anonyme

#### Option 1: VPS Anonyme

**Providers acceptant Bitcoin:**
- **Njalla** (recommandé, Suède)
- **1984 Hosting** (Islande)
- **Privex** (Suède)
- **FlokiNET** (Offshore)

**Setup:**
```bash
# Se connecter via SSH avec clé
ssh -i your-key.pem user@your-vps-ip

# Installer dependencies
sudo apt update
sudo apt install python3.11 python3-pip git

# Cloner repo (via Tor pour anonymat)
git clone https://github.com/yourpseudo/vintedbot.git
```

#### Option 2: Replit (Moins Anonyme)

**Avantages:**
- ✅ Gratuit
- ✅ Facile à déployer

**Inconvénients:**
- ❌ IP partagée
- ❌ Limitations ressources
- ❌ Peut demander vérification

#### Option 3: Docker Local + VPN

**Le plus sûr:**

```bash
# Dockerfile inclus dans le projet
docker-compose up -d

# Tout tourne en local, protégé par votre VPN
```

### 2.2 Base de Données Chiffrée

**Chiffrer SQLite:**

```python
# Utiliser SQLCipher pour chiffrer la DB
from sqlcipher3 import dbapi2 as sqlite3

conn = sqlite3.connect('backend/data/db.sqlite')
conn.execute("PRAGMA key='your-secret-passphrase'")
```

**Ou utiliser le chiffrement du système:**

```bash
# Linux: LUKS encryption
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup open /dev/sdX encrypted_disk
sudo mkfs.ext4 /dev/mapper/encrypted_disk
```

### 2.3 Logs Chiffrés

Le bot supporte le logging chiffré:

```python
from backend.core.encrypted_logging import EncryptedLogger

logger = EncryptedLogger()
logger.info("Message sensible")  # Automatiquement chiffré
```

### 2.4 Variables d'Environnement Sécurisées

**Ne jamais commit les secrets:**

```bash
# .gitignore déjà configuré
.env
*.key
*_secret*
cookies.db
```

**Utiliser des secrets managers:**

```bash
# Option 1: GitHub Secrets (pour CI/CD)
# Settings → Secrets → Actions

# Option 2: HashiCorp Vault
vault kv put secret/vinted cookie="..." token="..."

# Option 3: AWS Secrets Manager
aws secretsmanager create-secret --name vinted-cookie --secret-string "..."
```

---

## 🛡️ Partie 3: Sécurité Opérationnelle (OpSec)

### 3.1 Checklist de Sécurité

**Avant chaque déploiement:**

- [ ] VPN/Proxy activé
- [ ] Email anonyme configuré
- [ ] Pas de vraies infos dans le code
- [ ] Logs chiffrés activés
- [ ] Cookies récents (< 7 jours)
- [ ] User-Agent à jour
- [ ] Anti-détection activé
- [ ] Rate limiting configuré
- [ ] Backup automatique activé

### 3.2 Comportement Humain

**Simuler un humain:**

```python
# Délais aléatoires
await asyncio.sleep(random.uniform(2, 8))

# Mouvement de souris
await AntiDetection.simulate_human_behavior(page)

# Interactions aléatoires
await AntiDetection.random_page_interaction(page)
```

**Patterns à éviter:**
- ❌ Requêtes régulières (ex: toutes les 5 sec exactement)
- ❌ Trop rapide (< 1 sec entre actions)
- ❌ Pas de pause (humains font des pauses)
- ❌ Même timing tous les jours

**Patterns à adopter:**
- ✅ Délais randomisés (2-10 sec)
- ✅ Pauses longues occasionnelles (30-60 sec)
- ✅ Arrêt la nuit (23h-7h)
- ✅ Pauses déjeuner/dîner

### 3.3 Rate Limiting Intelligent

```python
from backend.core.smart_rate_limiter import SmartRateLimiter

limiter = SmartRateLimiter(
    max_requests_per_hour=50,
    max_requests_per_day=500,
    adaptive=True  # S'adapte si détection de limitation
)

# Avant chaque action
await limiter.wait_if_needed()
await perform_action()
limiter.record_request()
```

### 3.4 Monitoring Discret

**Utiliser Telegram pour les alertes:**
- ✅ Chiffré de bout en bout
- ✅ Pas d'email trace
- ✅ Notifications instantanées

**Éviter:**
- ❌ Emails non chiffrés
- ❌ SMS
- ❌ Webhooks publics

---

## 🔍 Partie 4: Détection et Contre-Mesures

### 4.1 Signes de Détection

**Vous êtes détecté si:**
- 🚨 Captchas fréquents
- 🚨 Redirections vers login
- 🚨 "Activité suspecte" messages
- 🚨 Ban de compte
- 🚨 Rate limiting agressif

### 4.2 Que faire si détecté?

**Plan d'action:**

1. **Arrêter immédiatement** toutes les requêtes
2. **Changer d'IP** (VPN, proxy)
3. **Changer de User-Agent**
4. **Attendre 24-48h** avant de reprendre
5. **Réduire la fréquence** des requêtes
6. **Améliorer l'anti-détection**

```python
# Si détection = pause automatique
if detected:
    logger.warning("Détection possible - pause de 24h")
    await asyncio.sleep(24 * 3600)
    # Changer fingerprint
    new_fingerprint = AnonymityManager.generate_fingerprint()
```

### 4.3 Techniques Avancées

**Residential Proxies:**
- Utilisent de vraies IPs résidentielles
- Plus chers mais plus difficiles à détecter
- Providers: Luminati, Smartproxy, GeoSurf

**Browser Profiles:**
- Sauvegarder état complet du navigateur
- Cookies, storage, cache
- Réutiliser pour paraître comme utilisateur régulier

---

## 📊 Partie 5: Métriques & Analytics

### 5.1 Tracking Sans Traces

```python
# Logger localement, chiffré
from backend.core.encrypted_logging import EncryptedLogger

logger = EncryptedLogger()
logger.metric("listings_published", count=10)
logger.metric("success_rate", rate=0.95)
```

### 5.2 Dashboard Local

```bash
# Dashboard web local uniquement (pas exposé)
python backend/dashboard/app.py

# Accessible sur http://localhost:8080
# Protégé par mot de passe
```

---

## ⚡ Partie 6: Performance & Optimisation

### 6.1 Parallélisation Sécurisée

```python
# Limiter la concurrence pour ne pas être détecté
import asyncio

async def publish_with_delay(items):
    for item in items:
        await publish_item(item)
        await asyncio.sleep(random.uniform(30, 120))  # 30-120 sec entre chaque
```

### 6.2 Cache Intelligent

```python
# Cache les données Vinted pour réduire les requêtes
from backend.core.smart_cache import SmartCache

cache = SmartCache(ttl=3600)  # 1h

# Utiliser le cache
@cache.cached
async def get_vinted_categories():
    # Seulement appelé si pas en cache
    return await fetch_categories()
```

---

## 🎓 Résumé: Best Practices

### DO ✅

1. **Utilisez un VPN/Proxy fiable**
2. **Rotez les IPs régulièrement**
3. **Randomisez tout** (timing, fingerprints)
4. **Simulez un comportement humain**
5. **Monitorer la détection** (Telegram alerts)
6. **Backup automatique** quotidien
7. **Logs chiffrés** uniquement
8. **Rate limiting** intelligent
9. **Testez en dev** d'abord
10. **Documentez** vos tests

### DON'T ❌

1. **Pas de vraies infos** personnelles
2. **Pas de commits** de secrets
3. **Pas de requêtes** trop rapides
4. **Pas de patterns** réguliers
5. **Pas d'API publique** exposée
6. **Pas de logs** non chiffrés
7. **Pas de scaling** agressif
8. **Pas de commercialisation** sans légal
9. **Pas d'ignore** les alertes
10. **Pas de test** en production

---

## 📞 Support

Pour des questions:
- 📧 Contact via email jetable seulement
- 💬 Telegram @your_anonymous_handle
- 🔒 PGP key disponible sur demande

**Restez safe! 🕶️**
