#!/usr/bin/env python3
"""
🧪 TEST PLAYWRIGHT - Vérifie que Playwright peut se lancer
"""
import sys
import asyncio
from playwright.async_api import async_playwright

async def test_playwright_launch():
    """Test si Playwright peut lancer un navigateur"""
    print("🧪 [TEST] Lancement de Playwright...")
    
    try:
        async with async_playwright() as p:
            print("✅ [TEST] Playwright initialisé")
            
            # Test avec Chromium (utilisé par Vinted automation)
            # Utiliser le Chromium de Nix au lieu du binaire Playwright
            import subprocess
            chromium_path = subprocess.check_output(['which', 'chromium']).decode().strip()
            print(f"🌐 [TEST] Chromium path: {chromium_path}")
            print("🌐 [TEST] Lancement du navigateur Chromium...")
            browser = await p.chromium.launch(
                executable_path=chromium_path,
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            print("✅ [TEST] Navigateur lancé avec succès!")
            
            # Test création d'une page
            print("📄 [TEST] Création d'une page...")
            page = await browser.new_page()
            print("✅ [TEST] Page créée!")
            
            # Test navigation simple
            print("🔗 [TEST] Navigation vers Google...")
            await page.goto('https://www.google.com', timeout=10000)
            print(f"✅ [TEST] Navigation réussie! Titre: {await page.title()}")
            
            # Nettoyage
            await browser.close()
            print("✅ [TEST] Navigateur fermé proprement")
            
            print("\n" + "="*60)
            print("✅ PLAYWRIGHT FONCTIONNE PARFAITEMENT!")
            print("="*60)
            return True
            
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ ERREUR PLAYWRIGHT: {type(e).__name__}")
        print("="*60)
        print(f"\nDétails: {str(e)}")
        
        # Afficher la stack trace complète
        import traceback
        print("\nStack trace complète:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 TEST PLAYWRIGHT - VÉRIFICATION DÉPENDANCES SYSTÈME")
    print("="*60)
    
    result = asyncio.run(test_playwright_launch())
    
    if result:
        print("\n✅ Résultat: Playwright est prêt pour la publication Vinted!")
        sys.exit(0)
    else:
        print("\n❌ Résultat: Des dépendances système manquent encore")
        sys.exit(1)
