"""
Quick Telegram test
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env
from dotenv import load_dotenv
load_dotenv()

import requests

# Get credentials from env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"Bot Token: {BOT_TOKEN[:20]}..." if BOT_TOKEN else "Bot Token: NOT FOUND")
print(f"Chat ID: {CHAT_ID}")

if not BOT_TOKEN or not CHAT_ID:
    print("\nERROR: Credentials not loaded from .env")
    sys.exit(1)

# Send test message
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
message = """
🎉 VintedBot - Test de Connexion

✅ Votre monitoring automatique est configuré!

Le système va surveiller Vinted tous les jours à 8h UTC et vous envoyer des alertes ici si des changements sont détectés.

📊 Features actives:
- Monitoring quotidien automatique
- Détection changements structure
- Alertes instantanées
- Rapports détaillés

🚀 Tout est prêt!
"""

try:
    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        },
        timeout=10
    )

    if response.status_code == 200:
        print("\n[SUCCESS] Message sent to Telegram")
        print(f"Check your Telegram (Bot ID: {CHAT_ID})")
        print("\nYou should see a welcome message!")
    else:
        print(f"\n[ERROR] Status: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\nERROR: {e}")
