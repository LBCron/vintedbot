"""
Script de test local pour l'envoi de draft sur Vinted avec Playwright
Permet de tester la création de draft en mode visible (headless=False)
"""
import asyncio
import sys
import argparse
import traceback
from pathlib import Path
from typing import Optional, List

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.vinted_client import VintedClient, CaptchaDetected
from backend.core.session import SessionVault, VintedSession
from backend.settings import settings


async def test_draft_creation(
    title: str = "Test Draft - Sweat Homme",
    price: float = 25.0,
    description: str = "Sweat en excellent état, taille M",
    brand: str = "Nike",
    size: str = "M",
    condition: str = "Très bon état",
    color: str = "Noir",
    category_hint: str = "Homme > Sweats",
    photos: Optional[List[str]] = None,
    cookie: Optional[str] = None
):
    """
    Teste la création d'un draft sur Vinted avec Playwright
    
    Args:
        title: Titre de l'annonce
        price: Prix en euros
        description: Description de l'annonce
        brand: Marque
        size: Taille
        condition: État
        color: Couleur
        category_hint: Catégorie
        photos: Liste des chemins vers les photos de test
        cookie: Cookie Vinted (optionnel, sinon charge depuis le vault)
    """
    print("\n" + "="*60)
    print("🧪 TEST CRÉATION DRAFT VINTED (MODE VISIBLE)")
    print("="*60)
    
    # 1. Charger la session Vinted
    print("\n[1/5] Chargement de la session Vinted...")
    session = None
    
    if cookie:
        print("   → Utilisation du cookie fourni en argument")
        session = VintedSession(
            cookie=cookie,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    else:
        print("   → Chargement depuis le vault...")
        vault = SessionVault(
            key=settings.ENCRYPTION_KEY,
            storage_path=settings.SESSION_STORE_PATH
        )
        session = vault.load_session()
        
        if not session:
            print("\n❌ ERREUR: Aucune session Vinted trouvée!")
            print("   Options:")
            print("   1. Passer un cookie en argument: --cookie 'votre_cookie'")
            print("   2. Créer une session via l'API: POST /vinted/auth/session")
            return False
    
    print(f"   ✅ Session chargée: user={session.username or 'unknown'}")
    
    # 2. Préparer les photos de test
    print("\n[2/5] Préparation des photos...")
    if photos is None:
        # Chercher des photos de test dans différents emplacements possibles
        test_photo_paths = [
            "backend/tests/test_photos/photo1.jpg",
            "backend/data/temp_photos/test.jpg",
            "test_photos/photo1.jpg"
        ]
        photos = []
        for path in test_photo_paths:
            if Path(path).exists():
                photos.append(path)
                print(f"   ✅ Photo trouvée: {path}")
        
        if not photos:
            print("   ⚠️  Aucune photo de test trouvée")
            print("   → Le test continuera sans photos (upload optionnel)")
            photos = []
    else:
        # Vérifier que les photos existent
        valid_photos = []
        for photo in photos:
            if Path(photo).exists():
                valid_photos.append(photo)
                print(f"   ✅ Photo trouvée: {photo}")
            else:
                print(f"   ⚠️  Photo non trouvée: {photo}")
        photos = valid_photos
    
    # 3. Créer le client Playwright en mode visible
    print("\n[3/5] Initialisation de Playwright (mode VISIBLE)...")
    print("   → Le navigateur va s'ouvrir, vous pourrez voir les actions")
    
    client = None
    try:
        async with VintedClient(headless=False) as client:
            # Créer le contexte avec la session
            print("   → Création du contexte navigateur avec session...")
            await client.create_context(session)
            page = await client.new_page()
            
            print("   ✅ Navigateur initialisé")
            print(f"   → URL actuelle: {page.url}")
            
            # 4. Tester la création du draft
            print("\n[4/5] Création du draft sur Vinted...")
            print(f"   → Titre: {title}")
            print(f"   → Prix: {price}€")
            print(f"   → Description: {description[:50]}...")
            print(f"   → Marque: {brand}")
            print(f"   → Taille: {size}")
            print(f"   → État: {condition}")
            print(f"   → Couleur: {color}")
            print(f"   → Catégorie: {category_hint}")
            print(f"   → Photos: {len(photos)} fichier(s)")
            
            print("\n   → Démarrage du processus de création...")
            success, error, result_data = await client.publish_item_complete(
                page=page,
                title=title,
                price=price,
                description=description,
                photos=photos,
                brand=brand,
                size=size,
                condition=condition,
                color=color,
                category_hint=category_hint,
                publish_mode="draft"  # Mode draft
            )
            
            # 5. Afficher les résultats
            print("\n[5/5] Résultats:")
            if success:
                draft_id = result_data.get("vinted_draft_id") if result_data else None
                draft_url = result_data.get("vinted_draft_url") if result_data else None
                
                print("   ✅ SUCCÈS!")
                if draft_id:
                    print(f"   → Draft ID: {draft_id}")
                if draft_url:
                    print(f"   → Draft URL: {draft_url}")
                else:
                    print(f"   → URL actuelle: {page.url}")
                
                print("\n   📋 Le navigateur reste ouvert pour inspection...")
                print("   → Vous pouvez vérifier le draft sur Vinted")
                print("   → Appuyez sur Entrée pour fermer le navigateur.")
                
                # Attendre que l'utilisateur appuie sur Entrée
                input()
                
                return True
            else:
                error_msg = error or "Erreur inconnue"
                print(f"   ❌ ÉCHEC: {error_msg}")
                
                # Détecter le type d'erreur pour donner des conseils
                error_lower = error_msg.lower()
                if "captcha" in error_lower or "challenge" in error_lower:
                    print("\n   ⚠️  CAPTCHA/VERIFICATION DÉTECTÉ")
                    print("   → Vinted a détecté une activité automatisée")
                    print("   → Vous devez compléter la vérification manuellement")
                    print("   → Attendez quelques minutes avant de réessayer")
                elif "session" in error_lower or "expir" in error_lower or "login" in error_lower:
                    print("\n   ⚠️  SESSION EXPIRÉE")
                    print("   → Votre cookie Vinted n'est plus valide")
                    print("   → Récupérez un nouveau cookie depuis votre navigateur")
                    print("   → Utilisez: --cookie 'nouveau_cookie'")
                elif "timeout" in error_lower:
                    print("\n   ⚠️  TIMEOUT")
                    print("   → Le processus a pris trop de temps")
                    print("   → Vérifiez votre connexion internet")
                    print("   → Réessayez dans quelques instants")
                
                print("\n   📋 Le navigateur reste ouvert pour inspection...")
                print("   → Vous pouvez voir l'état actuel de la page")
                print("   → Appuyez sur Entrée pour fermer le navigateur.")
                
                input()
                
                return False
                
    except CaptchaDetected as e:
        print(f"\n❌ CAPTCHA DÉTECTÉ: {e}")
        print("\n   ⚠️  Vinted a détecté une activité automatisée")
        print("   → Le navigateur reste ouvert pour inspection")
        print("   → Vous pouvez essayer de compléter le captcha manuellement")
        print("   → Appuyez sur Entrée pour fermer le navigateur.")
        input()
        return False
        
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        print("\n   Détails de l'erreur:")
        traceback.print_exc()
        print("\n   📋 Le navigateur reste ouvert pour inspection...")
        print("   → Appuyez sur Entrée pour fermer le navigateur.")
        input()
        return False


def main():
    """Point d'entrée principal avec arguments CLI"""
    parser = argparse.ArgumentParser(
        description="Test local de création de draft sur Vinted avec Playwright"
    )
    parser.add_argument(
        "--cookie",
        type=str,
        help="Cookie Vinted (sinon charge depuis le vault)"
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Test Draft - Sweat Homme",
        help="Titre de l'annonce"
    )
    parser.add_argument(
        "--price",
        type=float,
        default=25.0,
        help="Prix en euros"
    )
    parser.add_argument(
        "--description",
        type=str,
        default="Sweat en excellent état, taille M",
        help="Description de l'annonce"
    )
    parser.add_argument(
        "--brand",
        type=str,
        default="Nike",
        help="Marque"
    )
    parser.add_argument(
        "--size",
        type=str,
        default="M",
        help="Taille"
    )
    parser.add_argument(
        "--condition",
        type=str,
        default="Très bon état",
        help="État"
    )
    parser.add_argument(
        "--color",
        type=str,
        default="Noir",
        help="Couleur"
    )
    parser.add_argument(
        "--category",
        type=str,
        default="Homme > Sweats",
        help="Catégorie"
    )
    parser.add_argument(
        "--photos",
        type=str,
        nargs="+",
        help="Chemins vers les photos de test"
    )
    
    args = parser.parse_args()
    
    # Lancer le test
    success = asyncio.run(test_draft_creation(
        title=args.title,
        price=args.price,
        description=args.description,
        brand=args.brand,
        size=args.size,
        condition=args.condition,
        color=args.color,
        category_hint=args.category,
        photos=args.photos,
        cookie=args.cookie
    ))
    
    if success:
        print("\n✅ Test terminé avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Test échoué")
        sys.exit(1)


if __name__ == "__main__":
    main()

