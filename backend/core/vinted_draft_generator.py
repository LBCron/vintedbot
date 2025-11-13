"""
Générateur de descriptions Vinted optimales
"""

from typing import List, Dict, Optional
import re

def generate_vinted_draft(
    item_type: str,
    brand: str,
    size: str,
    color: str,
    condition: str,
    price: float,
    defects: List[str] = None,
    material: Optional[str] = None,
    style: Optional[str] = None,
    purchase_price: Optional[float] = None,
    worn_times: Optional[int] = None
) -> Dict:
    """
    Génère un brouillon Vinted complet et optimisé

    Args:
        item_type: Type d'article (hoodie, tshirt, jean, sneakers, etc.)
        brand: Marque du vêtement
        size: Taille (XS, S, M, L, XL, ou numérique)
        color: Couleur principale
        condition: État (neuf, très bon, bon, satisfaisant)
        price: Prix de vente en euros
        defects: Liste des défauts (vide si aucun)
        material: Matière du vêtement
        style: Style (streetwear, vintage, casual, etc.)
        purchase_price: Prix d'achat original (optionnel)
        worn_times: Nombre de fois porté (optionnel)

    Returns:
        Dict avec title, description, tags, confidence_score
    """

    defects = defects or []

    # === GÉNÉRATION DU TITRE ===
    title = _generate_title(item_type, brand, color, size, condition)

    # === GÉNÉRATION DE LA DESCRIPTION ===
    description = _generate_description(
        item_type, brand, size, color, condition, price,
        defects, material, style, purchase_price, worn_times
    )

    # === GÉNÉRATION DES TAGS ===
    tags = _generate_tags(item_type, brand, color, style, condition)

    # === CALCUL DU SCORE DE CONFIANCE ===
    confidence_score = _calculate_confidence(
        title, description, defects, material, style
    )

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "confidence_score": confidence_score,
        "seo_keywords": _extract_keywords(item_type, brand, style)
    }


def _generate_title(item_type: str, brand: str, color: str, size: str, condition: str) -> str:
    """Génère un titre accrocheur optimisé"""

    # Normaliser le type d'article
    item_display = {
        "hoodie": "Hoodie",
        "tshirt": "T-shirt",
        "jean": "Jean",
        "sneakers": "Sneakers",
        "jacket": "Veste",
        "dress": "Robe",
        "shoes": "Chaussures",
        "bag": "Sac",
        "sweat": "Sweat",
        "pull": "Pull",
        "chemise": "Chemise",
        "pantalon": "Pantalon",
        "short": "Short",
        "jupe": "Jupe",
    }.get(item_type.lower(), item_type.capitalize())

    # Condition en français
    condition_text = ""
    if condition.lower() in ["neuf", "très bon"]:
        condition_text = "– Excellent état"
    elif condition.lower() == "bon":
        condition_text = "– Bon état"

    # Construction du titre (max 65 caractères)
    title = f"{item_display} {brand} {color} – Taille {size} {condition_text}"

    # Tronquer si trop long
    if len(title) > 65:
        title = f"{item_display} {brand} {color} – {size}"

    return title.strip()


def _generate_description(
    item_type: str, brand: str, size: str, color: str,
    condition: str, price: float, defects: List[str],
    material: Optional[str], style: Optional[str],
    purchase_price: Optional[float], worn_times: Optional[int]
) -> str:
    """Génère une description complète et vendeuse"""

    parts = []

    # === PARAGRAPHE 1 : PRÉSENTATION ===
    item_display = {
        "hoodie": "Hoodie",
        "tshirt": "T-shirt",
        "jean": "Jean",
        "sneakers": "Sneakers",
        "jacket": "Veste",
        "dress": "Robe",
        "shoes": "Chaussures",
        "bag": "Sac",
    }.get(item_type.lower(), item_type.capitalize())

    intro = f"{item_display} {brand}"

    if material:
        intro += f" en {material}"

    intro += f", couleur {color}, taille {size}."

    # Contexte d'achat si disponible
    if purchase_price or worn_times is not None:
        context = []
        if purchase_price:
            context.append(f"acheté {purchase_price}€")
        if worn_times is not None:
            if worn_times == 0:
                context.append("jamais porté")
            elif worn_times <= 3:
                context.append(f"porté {worn_times} fois seulement")
            else:
                context.append(f"porté {worn_times} fois")

        if context:
            intro += f" {context[0].capitalize()}"
            if len(context) > 1:
                intro += f" et {context[1]}"
            intro += "."

    parts.append(intro)

    # === PARAGRAPHE 2 : ÉTAT ===
    condition_text = {
        "neuf": "Article neuf avec étiquette, jamais porté ! État impeccable.",
        "très bon": "En très bon état, quasi neuf. Aucun signe visible d'usure.",
        "bon": "En bon état général. Quelques légères traces d'usage mais rien de gênant.",
        "satisfaisant": "État correct avec quelques signes d'usure visible."
    }.get(condition.lower(), f"État : {condition}.")

    parts.append(condition_text)

    # Défauts si présents
    if defects:
        defects_text = "À noter : " + ", ".join(defects) + "."
        parts.append(defects_text)
    else:
        parts.append("Aucun défaut à signaler.")

    # === PARAGRAPHE 3 : DÉTAILS TECHNIQUES ===
    details = []

    if item_type.lower() == "hoodie":
        details.append("Capuche avec cordon de serrage")
        details.append("poches kangourou pratiques")
    elif item_type.lower() == "tshirt":
        details.append("Col rond classique")
    elif item_type.lower() == "jean":
        details.append("5 poches")
    elif item_type.lower() == "sneakers":
        details.append("Semelle antidérapante")

    if material:
        details.append(f"matière {material}")

    if details:
        parts.append("Détails : " + ", ".join(details) + ".")

    # === PARAGRAPHE 4 : STYLE & CONSEILS ===
    if style:
        style_text = {
            "streetwear": "Parfait pour un look streetwear décontracté !",
            "vintage": "Pièce vintage authentique qui fera sensation.",
            "casual": "Idéal pour un style casual et confortable au quotidien.",
            "sportswear": "Parfait pour le sport ou un look athleisure.",
            "chic": "Parfait pour un look élégant et sophistiqué.",
            "preppy": "Style preppy intemporel qui ne se démode jamais.",
        }.get(style.lower(), f"Style {style} qui s'adapte à de nombreuses tenues.")

        parts.append(style_text)

    # === PARAGRAPHE 5 : CONCLUSION & ENVOI ===
    parts.append("Envoi soigné sous 24-48h 📦")
    parts.append("N'hésitez pas si vous avez des questions !")

    # Assemblage
    description = "\n\n".join(parts)

    return description


def _generate_tags(
    item_type: str, brand: str, color: str,
    style: Optional[str], condition: str
) -> List[str]:
    """Génère des tags pertinents"""

    tags = []

    # Tag type
    tags.append(item_type.lower())

    # Tag marque
    tags.append(brand.lower())

    # Tag couleur
    tags.append(color.lower())

    # Tag style si présent
    if style:
        tags.append(style.lower())

    # Tag état
    if condition.lower() in ["neuf", "très bon"]:
        tags.append("comme neuf")

    # Tags contextuels selon le type
    type_tags = {
        "hoodie": ["sweat", "capuche", "confort"],
        "tshirt": ["tee", "casual", "basique"],
        "jean": ["denim", "pantalon", "casual"],
        "sneakers": ["baskets", "chaussures", "sport"],
        "jacket": ["veste", "manteau", "outdoor"],
        "dress": ["robe", "femme", "soirée"],
    }

    if item_type.lower() in type_tags:
        tags.extend(type_tags[item_type.lower()][:2])

    # Limiter à 8 tags max
    return tags[:8]


def _calculate_confidence(
    title: str, description: str, defects: List[str],
    material: Optional[str], style: Optional[str]
) -> int:
    """Calcule un score de confiance (0-100)"""

    score = 100

    # Titre trop court
    if len(title) < 20:
        score -= 10

    # Description trop courte
    if len(description) < 150:
        score -= 20
    elif len(description) < 100:
        score -= 40

    # Défauts non mentionnés réduit la confiance
    if not defects:
        score += 5  # Bonus transparence

    # Manque d'informations
    if not material:
        score -= 5

    if not style:
        score -= 5

    # Bonus qualité rédaction
    if len(description) > 250:
        score += 5

    # Vérifier présence mots-clés importants
    keywords = ["état", "taille", "couleur"]
    desc_lower = description.lower()
    for kw in keywords:
        if kw not in desc_lower:
            score -= 10

    return max(0, min(100, score))


def _extract_keywords(item_type: str, brand: str, style: Optional[str]) -> List[str]:
    """Extrait les mots-clés SEO"""

    keywords = [item_type.lower(), brand.lower()]

    if style:
        keywords.append(style.lower())

    # Mots-clés génériques
    keywords.extend(["vinted", "occasion", "seconde main"])

    return keywords


# === EXEMPLES D'USAGE ===

if __name__ == "__main__":

    # Exemple 1 : Hoodie en excellent état
    draft1 = generate_vinted_draft(
        item_type="hoodie",
        brand="Nike",
        size="M",
        color="gris chiné",
        condition="très bon",
        price=30,
        defects=[],
        material="coton",
        style="streetwear",
        purchase_price=60,
        worn_times=3
    )

    print("=== EXEMPLE 1 : HOODIE NIKE ===")
    print(f"Titre : {draft1['title']}")
    print(f"\nDescription :\n{draft1['description']}")
    print(f"\nTags : {', '.join(draft1['tags'])}")
    print(f"\nScore de confiance : {draft1['confidence_score']}%")
    print("\n" + "="*60 + "\n")

    # Exemple 2 : Jean avec défauts
    draft2 = generate_vinted_draft(
        item_type="jean",
        brand="Levi's",
        size="32",
        color="bleu délavé",
        condition="bon",
        price=25,
        defects=["légère décoloration au niveau des genoux"],
        material="denim",
        style="vintage",
        worn_times=15
    )

    print("=== EXEMPLE 2 : JEAN LEVI'S ===")
    print(f"Titre : {draft2['title']}")
    print(f"\nDescription :\n{draft2['description']}")
    print(f"\nTags : {', '.join(draft2['tags'])}")
    print(f"\nScore de confiance : {draft2['confidence_score']}%")
    print("\n" + "="*60 + "\n")

    # Exemple 3 : Sneakers neuves
    draft3 = generate_vinted_draft(
        item_type="sneakers",
        brand="Adidas",
        size="42",
        color="blanc",
        condition="neuf",
        price=80,
        defects=[],
        material="cuir synthétique",
        style="sportswear",
        purchase_price=120,
        worn_times=0
    )

    print("=== EXEMPLE 3 : SNEAKERS ADIDAS ===")
    print(f"Titre : {draft3['title']}")
    print(f"\nDescription :\n{draft3['description']}")
    print(f"\nTags : {', '.join(draft3['tags'])}")
    print(f"\nScore de confiance : {draft3['confidence_score']}%")
