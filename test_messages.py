# -*- coding: utf-8 -*-
"""Test des nouveaux messages naturels"""
import requests
import json
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test 1: Get templates
print("=" * 60)
print("TEST 1: Récupération des templates")
print("=" * 60)

response = requests.post(
    "https://vintedbot-backend.fly.dev/auth/login",
    json={"email": "ronanchenlopes@gmail.com", "password": "2007312Ron"}
)

if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"✓ Connecté avec succès")

    # Get templates
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://vintedbot-backend.fly.dev/automation/upsell/templates", headers=headers)

    if response.status_code == 200:
        templates = response.json()["templates"]
        print(f"\n✓ {len(templates)} templates récupérés:\n")
        for t in templates:
            print(f"  [{t['name']}]")
            print(f"  → {t['template']}\n")
    else:
        print(f"✗ Erreur: {response.status_code}")
        print(response.text)

    # Test 2: Message suggestions
    print("\n" + "=" * 60)
    print("TEST 2: Suggestions de réponses IA")
    print("=" * 60)

    test_messages = [
        {"message": "Il est en bon état ?", "item_title": "Pull Nike", "item_price": "25"},
        {"message": "Tu peux baisser le prix ?", "item_title": "Jean Levis", "item_price": "30"},
        {"message": "Il est encore disponible ?", "item_title": "Veste Zara", "item_price": "35"},
        {"message": "Tu peux m'envoyer plus de photos ?", "item_title": "Chaussures Adidas", "item_price": "40"}
    ]

    for test in test_messages:
        print(f"\n📨 Message: '{test['message']}'")
        response = requests.post(
            "https://vintedbot-backend.fly.dev/automation/messages/suggest",
            headers=headers,
            json=test
        )

        if response.status_code == 200:
            result = response.json()
            print(f"   Contexte détecté: {result['context_detected']}")
            print(f"   Suggestions:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"   {i}. {suggestion}")
        else:
            print(f"   ✗ Erreur: {response.status_code}")

else:
    print(f"✗ Échec de connexion: {response.status_code}")
    print(response.text)
