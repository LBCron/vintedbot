# 🤖 N8N Automation Hub - Discord Command Center

Système d'automatisation complet qui connecte tous vos services via Discord avec intelligence ChatGPT.

## 🎯 Fonctionnalités

### Services Connectés:
- 📧 **Gmail** - Envoyer/lire emails
- 📱 **Instagram** - Poster/gérer contenu
- 💬 **Discord** - Interface de commande
- 🤖 **ChatGPT** - Traitement intelligent
- 🔔 **Telegram** - Notifications
- 📊 **Analytics** - Statistiques d'utilisation

### Commandes Discord:

```
# Gmail
!email envoyer [destinataire] [sujet] [message]
!email lire [nombre]
!email rechercher [terme]

# Instagram
!insta poster [image_url] [caption]
!insta story [image_url]
!insta stats

# VintedBot
!vinted publier [produit]
!vinted stats
!vinted bump [listing_id]

# Général
!help
!status
```

## 📦 Installation

### 1. Installer N8N

```bash
npm install -g n8n

# Ou avec Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### 2. Importer les workflows

```bash
# Copier les fichiers de workflows dans N8N
cp n8n/workflows/*.json ~/.n8n/workflows/
```

### 3. Configurer les credentials

Dans N8N (http://localhost:5678):
1. Settings → Credentials
2. Ajouter pour chaque service:
   - Discord Webhook
   - Gmail OAuth2
   - Instagram API
   - OpenAI API
   - Telegram Bot

## 🔧 Configuration

Créez `.env` dans le dossier n8n:

```bash
# Discord
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
DISCORD_BOT_TOKEN="your_bot_token"
DISCORD_GUILD_ID="your_server_id"

# Gmail
GMAIL_CLIENT_ID="your_client_id"
GMAIL_CLIENT_SECRET="your_client_secret"
GMAIL_REFRESH_TOKEN="your_refresh_token"

# Instagram
INSTAGRAM_USERNAME="your_username"
INSTAGRAM_PASSWORD="your_password"
INSTAGRAM_SESSION="your_session"

# OpenAI
OPENAI_API_KEY="sk-..."

# Telegram
TELEGRAM_BOT_TOKEN="your_token"

# VintedBot API
VINTEDBOT_API_URL="http://localhost:5000"
VINTEDBOT_API_KEY="your_api_key"
```

## 📚 Documentation complète

Voir les fichiers individuels:
- `workflows/` - Workflows N8N
- `docs/` - Documentation détaillée
- `examples/` - Exemples d'utilisation
