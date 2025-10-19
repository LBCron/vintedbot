"""
AI-powered photo analysis and listing generation using OpenAI GPT-4 Vision
Analyzes clothing photos and generates: title, description, price, category, condition, color
"""
import os
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import tempfile
from PIL import Image
import pillow_heif

# the newest OpenAI model is "gpt-4o" 
from openai import OpenAI

# Use user's personal OpenAI API key (from Replit Secrets)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("✅ Using personal OpenAI API key")

# Register HEIF opener with PIL
pillow_heif.register_heif_opener()


def convert_heic_to_jpeg(heic_path: str) -> str:
    """
    Convert HEIC/HEIF image to JPEG format for OpenAI compatibility
    
    Args:
        heic_path: Path to HEIC/HEIF file
        
    Returns:
        Path to converted JPEG file (temp file)
    """
    try:
        # Open HEIC image
        image = Image.open(heic_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create temp JPEG file
        temp_jpeg = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        jpeg_path = temp_jpeg.name
        
        # Save as JPEG
        image.save(jpeg_path, 'JPEG', quality=90)
        
        print(f"✅ Converted HEIC → JPEG: {Path(heic_path).name}")
        return jpeg_path
        
    except Exception as e:
        print(f"❌ HEIC conversion error for {heic_path}: {e}")
        # Return original path as fallback
        return heic_path


def encode_image_to_base64(image_path: str) -> str:
    """Convert local image to base64 string, handles HEIC conversion"""
    # Convert HEIC/HEIF to JPEG if needed
    if image_path.lower().endswith(('.heic', '.heif')):
        image_path = convert_heic_to_jpeg(image_path)
    
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_clothing_photos(photo_paths: List[str]) -> Dict[str, Any]:
    """
    Analyze clothing photos using GPT-4 Vision
    
    Args:
        photo_paths: List of local file paths to analyze
        
    Returns:
        Dictionary with:
        - title: Product title
        - description: Detailed description
        - price: Suggested price in euros
        - category: Clothing category (t-shirt, hoodie, jeans, etc.)
        - condition: Condition assessment (new, very good, good, satisfactory)
        - color: Dominant color
        - brand: Detected brand (if visible)
        - size: Detected size (if visible)
        - confidence: Confidence score (0-1)
    """
    
    try:
        # Prepare images for API call
        image_contents = []
        for path in photo_paths[:6]:  # Limit to 6 photos max
            if not Path(path).exists():
                print(f"⚠️ Photo not found: {path}")
                continue
                
            # Encode image to base64
            base64_image = encode_image_to_base64(path)
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        
        if not image_contents:
            raise ValueError("No valid images found")
        
        # Create prompt for single-item clothing analysis
        prompt = """Tu es l'assistant VintedBot. Analyse ces photos d'UN SEUL vêtement et génère un listing Vinted conforme.

RÈGLES STRICTES (QUALITY GATE):
- title: ≤70 chars, format "Catégorie Couleur Marque? Taille? – État", ZÉRO emoji, ZÉRO superlatif
- description: 5-8 lignes factuelles, ZÉRO emoji, ZÉRO marketing ("parfait pour", "style tendance", "look")
- hashtags: 3-5 hashtags À LA FIN de la description (#marque #catégorie #couleur)
- price: Prix réaliste (t-shirt 10€, hoodie 25€, jeans 25€, veste 35€) × multiplicateurs
- INTERDITS ABSOLUS: emojis, superlatifs ("magnifique", "parfait", "tendance"), phrases marketing

TAILLES (normalisation):
- Si taille enfant/ado (16Y, 165cm), calculer équivalence adulte (ex: 16Y ≈ XS)
- Noter : "16Y / 165 cm (≈ XS adulte)"

DESCRIPTION (structure obligatoire):
1) Ce que c'est (catégorie/coupe/logo)
2) État factuel + défauts précis
3) Matière/fit/détails
4) Taille + équivalence si calculée
5) Mesures à ajouter
6) Logistique + remise lot
Exemple: "T-shirt Burberry noir, logo imprimé devant, coupe classique. Très bon état : matière propre, pas de trou. Coton confortable, col rond. Taille 16Y / 165 cm — équiv. XS adulte. Mesures conseillées : poitrine et longueur en cm. Envoi rapide. #burberry #tshirt #noir #xs #streetwear"

SORTIE JSON OBLIGATOIRE:
{
    "title": "T-shirt noir Burberry XS – très bon état",
    "description": "T-shirt Burberry noir, logo imprimé devant. Très bon état : matière propre, pas de trou. Coton, col rond. Taille 16Y / 165 cm (≈ XS). Mesures à ajouter : poitrine et longueur. Envoi rapide. #burberry #tshirt #noir #xs #streetwear",
    "price": 50,
    "category": "t-shirt",
    "condition": "Très bon état",
    "color": "noir",
    "brand": "Burberry",
    "size": "16Y / 165 cm (≈ XS)",
    "confidence": 0.90
}

Analyse les photos et génère le JSON:"""

        # Build messages
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents
                ]
            }
        ]
        
        print(f"🔍 Analyzing {len(image_contents)} photos with GPT-4 Vision...")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4 with vision capabilities
            messages=messages,  # type: ignore
            max_completion_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        
        print(f"✅ Analysis complete: {result.get('title', 'Unknown')}")
        print(f"   Category: {result.get('category')}, Price: {result.get('price')}€")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        # Return fallback result
        return generate_fallback_analysis(photo_paths)
        
    except Exception as e:
        print(f"❌ AI analysis error: {e}")
        # Return fallback result
        return generate_fallback_analysis(photo_paths)


def generate_fallback_analysis(photo_paths: List[str]) -> Dict[str, Any]:
    """
    Generate a basic fallback analysis when AI fails
    Uses simple heuristics - MUST comply with strict quality gates
    """
    return {
        "title": "Vêtement à identifier – bon état",
        "description": "Article en bon état visible sur photos. Matière et détails à préciser selon photos fournies. Taille à vérifier. Mesures recommandées pour confirmation avant achat. Envoi rapide. Remise possible si achat groupé. #mode #vinted #occasion",
        "price": 20,
        "category": "autre",
        "condition": "Bon état",
        "color": "Non spécifié",
        "brand": "Non spécifié",
        "size": "Non spécifié",
        "confidence": 0.3,
        "fallback": True
    }


def batch_analyze_photos(photo_groups: List[List[str]]) -> List[Dict[str, Any]]:
    """
    Analyze multiple groups of photos (for bulk upload)
    Each group represents one clothing item
    
    Args:
        photo_groups: List of photo path lists, e.g. [[photo1, photo2], [photo3, photo4]]
        
    Returns:
        List of analysis results (one per group)
    """
    results = []
    
    for i, group in enumerate(photo_groups):
        print(f"\n📸 Analyzing group {i+1}/{len(photo_groups)} ({len(group)} photos)...")
        try:
            result = analyze_clothing_photos(group)
            result['group_index'] = i
            result['photos'] = group  # CRITICAL: Attach photos to result for draft creation
            results.append(result)
        except Exception as e:
            print(f"❌ Group {i+1} failed: {e}")
            fallback = generate_fallback_analysis(group)
            fallback['group_index'] = i
            fallback['photos'] = group  # CRITICAL: Attach photos to fallback result
            results.append(fallback)
    
    return results


def smart_group_photos(photo_paths: List[str], max_per_group: int = 7) -> List[List[str]]:
    """
    Intelligently group photos into clothing items
    Simple version: groups by sequences (every N photos = 1 item)
    
    TODO: Use image similarity (CLIP embeddings) for smarter grouping
    
    Args:
        photo_paths: All photo paths
        max_per_group: Maximum photos per item (default 7 minimum)
        
    Returns:
        List of photo groups
    """
    # Simple sequential grouping for now
    groups = []
    current_group = []
    
    for path in photo_paths:
        current_group.append(path)
        
        if len(current_group) >= max_per_group:
            groups.append(current_group)
            current_group = []
    
    # Add remaining photos as last group
    if current_group:
        groups.append(current_group)
    
    print(f"📦 Grouped {len(photo_paths)} photos into {len(groups)} items")
    return groups


def smart_analyze_and_group_photos(
    photo_paths: List[str], 
    style: str = "classique"
) -> List[Dict[str, Any]]:
    """
    INTELLIGENT GROUPING WITH AUTO-BATCHING: Analyze ALL photos by chunks and let AI group them
    
    If >25 photos: splits into batches of 25, analyzes each, returns all items
    If ≤25 photos: analyzes all together
    
    Args:
        photo_paths: All photo paths to analyze (no limit!)
        style: "minimal", "streetwear", or "classique" (default)
        
    Returns:
        List of analyzed items with their grouped photos
    """
    total_photos = len(photo_paths)
    BATCH_SIZE = 25  # Safe batch size to stay under 30k token limit
    
    # If ≤25 photos, analyze all together
    if total_photos <= BATCH_SIZE:
        return _analyze_single_batch(photo_paths, style)
    
    # If >25 photos, split into batches and analyze each
    print(f"📦 Auto-batching: {total_photos} photos → splitting into batches of {BATCH_SIZE}")
    
    all_items = []
    offset = 0
    batch_num = 1
    total_batches = (total_photos + BATCH_SIZE - 1) // BATCH_SIZE
    
    while offset < total_photos:
        batch_photos = photo_paths[offset:offset + BATCH_SIZE]
        print(f"\n🔄 Batch {batch_num}/{total_batches}: Analyzing photos {offset+1}-{offset+len(batch_photos)}...")
        
        try:
            batch_items = _analyze_single_batch(batch_photos, style, offset)
            all_items.extend(batch_items)
            print(f"✅ Batch {batch_num} complete: {len(batch_items)} items detected")
        except Exception as e:
            print(f"❌ Batch {batch_num} failed: {e}, using fallback")
            # Fallback: group batch photos by 7 photos per item
            fallback_groups = smart_group_photos(batch_photos, max_per_group=7)
            fallback_items = batch_analyze_photos(fallback_groups)
            all_items.extend(fallback_items)
        
        offset += BATCH_SIZE
        batch_num += 1
    
    print(f"\n✅ Auto-batching complete: {len(all_items)} total items from {total_photos} photos")
    return all_items


def _analyze_single_batch(
    photo_paths: List[str],
    style: str = "classique",
    photo_offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Internal: Analyze a single batch of photos (≤25 photos)
    
    Args:
        photo_paths: Photos to analyze (max 25)
        style: Description style
        photo_offset: Offset for photo indices (used in batching)
        
    Returns:
        List of analyzed items
    """
    try:
        # Prepare images for API call
        image_contents = []
        valid_paths = []
        
        for path in photo_paths:  # Already limited to BATCH_SIZE
            if not Path(path).exists():
                print(f"⚠️ Photo not found: {path}")
                continue
                
            # Encode image to base64
            base64_image = encode_image_to_base64(path)
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
            valid_paths.append(path)
        
        if not image_contents:
            raise ValueError("No valid images found")
        
        # Create intelligent grouping prompt with strict quality rules
        prompt = f"""Tu es l'assistant "Photo → Listing" de VintedBot Studio. Tu reçois {len(image_contents)} photos et tu dois les GROUPER intelligemment par pièce/vêtement, puis générer un listing pour chaque groupe.

RÈGLES DE GROUPEMENT (anti-saucisson):
1. Si ≤80 photos OU confidence de séparation <0.6 → TOUJOURS grouper en 1 seul article
2. Détecter les mini-clusters ≤2 photos (étiquettes/détails/macros) → les fusionner automatiquement avec le plus grand groupe
3. Pour chaque groupe, analyser : même vêtement/objet, même couleur dominante, même style
4. INTERDICTION: Ne JAMAIS créer un article composé uniquement d'étiquettes (care labels, brand tags, size labels)
5. Les étiquettes DOIVENT être rattachées au vêtement principal correspondant

TAILLES (normalisation tops/vêtements) :
- Conserver original_size (ex. 16Y / 165 cm)
- Si taille enfant/ado (\\d+Y, ans) ou hauteur (cm), calculer normalized_size adulte XS/S/M/L…
- Règles génériques unisex (tops) : 152–158 cm → XXS ; 160–166 cm → XS ; 167–172 cm → S
- Ajouter size_notes (ex. « ≈ XS adulte, équiv. 16Y/165 cm ; vérifier mesures »)

LISTING POUR CHAQUE GROUPE:

title (≤70 chars, format « {{Catégorie}} {{Couleur}} {{Marque?}} {{Taille?}} – {{État}} »)
  Exemple: "T-shirt noir Burberry XS (≈ 16Y/165 cm) – très bon état"
  INTERDITS: emojis, superlatifs ("magnifique", "parfait"), marketing ("découvrez", "idéal pour")

description (5–8 lignes, FR, style humain minimal, ZÉRO emoji, ZÉRO marketing)
  Structure: 
  1) ce que c'est (catégorie/coupe/logo)
  2) état factuel + défauts précis
  3) matière/fit/saison/extras
  4) taille d'origine + équivalence adulte si calculée
  5) invite à vérifier mesures en cm
  6) logistique + remise lot
  
  Exemple: "T-shirt Burberry noir, logo imprimé devant, coupe classique. Très bon état : matière propre, couleur uniforme, pas de trou ou tâche visibles. Coton confortable, col rond. Taille d'origine : 16Y / 165 cm — équiv. XS adulte selon le guide générique. Mesures conseillées à ajouter : poitrine (à plat) et longueur dos, en cm. Envoi rapide ; remise possible si achat de plusieurs pièces. #burberry #tshirt #noir #xs #streetwear"
  
  INTERDITS ABSOLUS: emojis, phrases marketing ("parfait pour", "style tendance", "casual chic", "look"), superlatifs

hashtags (3–5 pertinents, OBLIGATOIRE, À LA FIN de la description)
  Format: #marque #catégorie #couleur #taille #style
  Exemple: #burberry #tshirt #noir #xs #streetwear

price (suggéré en euros, bases réalistes Vinted 2025)
  BASES CATÉGORIES:
  - T-shirt/polo: 15€ | Chemise: 20€ | Pull/sweat: 25€ | Hoodie: 35€
  - Pantalon/jean: 30€ | Short: 25€ | Jogging: 30€
  - Veste légère: 40€ | Manteau: 60€ | Doudoune: 70€
  
  MULTIPLICATEURS MARQUE (très important pour premium):
  - Luxe (Burberry, Dior, Gucci, LV, Prada): ×3.0 à ×5.0
  - Premium (Ralph Lauren, Karl Lagerfeld, Diesel, Tommy, Lacoste): ×2.0 à ×2.5
  - Streetwear (Fear of God, Essentials, Supreme, Off-White): ×2.5 à ×3.5
  - Sportswear premium (Adidas Yeezy, Nike Jordan): ×2.0 à ×2.8
  - Standard (Zara, H&M, Uniqlo, marques connues): ×1.0
  - Entrée de gamme (no-name, basique): ×0.7
  
  MULTIPLICATEURS CONDITION:
  - Neuf avec étiquettes: ×1.0
  - Très bon état: ×0.85
  - Bon état: ×0.75
  - État correct: ×0.60
  
  ARRONDIS PSYCHOLOGIQUES:
  - <50€ → finit par 9 (ex: 19€, 29€, 39€, 49€)
  - 50-99€ → 59/69/79/89/99€
  - ≥100€ → 99/119/129/149/199€
  
  EXEMPLES CONCRETS:
  - Short Ralph Lauren bon état: 25€ × 2.2 × 0.75 = 41€ → 39€
  - Hoodie Karl Lagerfeld très bon: 35€ × 2.2 × 0.85 = 65€ → 69€
  - T-shirt Burberry correct: 15€ × 3.5 × 0.60 = 31€ → 29€
  - Veste Essentials bon état: 40€ × 2.8 × 0.75 = 84€ → 89€

STYLE (adapte selon "{style}"):
- minimal: Ton sobre, descriptions factuelles courtes
- streetwear: Ton lifestyle direct, sans emojis ni marketing
- classique: Ton boutique sobre, descriptions soignées

QUALITY GATE (SANS-ÉCHEC):
- title.length ≤70
- 3 ≤ hashtags.length ≤5
- AUCUN emoji dans title/description
- AUCUN superlatif ("magnifique", "prestigieuse", "haute qualité", "parfait", "tendance", "idéal")
- AUCUNE phrase marketing ("parfait pour", "style tendance", "casual chic", "look")
- Hashtags UNIQUEMENT à la fin de la description

SORTIE JSON OBLIGATOIRE:
{{
  "groups": [
    {{
      "title": "T-shirt noir Burberry XS – très bon état",
      "description": "T-shirt Burberry noir, logo imprimé devant, coupe classique. Très bon état : matière propre, couleur uniforme, pas de trou ou tâche visibles. Coton confortable, col rond. Taille d'origine : 16Y / 165 cm — équiv. XS adulte. Mesures à ajouter : poitrine et longueur. Envoi rapide. #burberry #tshirt #noir #xs #streetwear",
      "price": 50.0,
      "brand": "Burberry",
      "size": "16Y / 165 cm (≈ XS)",
      "condition": "Très bon état",
      "color": "Noir",
      "category": "t-shirt",
      "confidence": 0.90,
      "photo_indices": [0, 1]
    }}
  ]
}}

Analyse les photos et génère le JSON:"""

        # Build messages
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents
                ]
            }
        ]
        
        print(f"🧠 Analyzing {len(image_contents)} photos with GPT-4 Vision...")
        
        # Call OpenAI API with intelligent grouping
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,  # type: ignore
            max_completion_tokens=3000,  # More tokens for multiple items
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        
        # Map photo indices to actual paths (adjust for batch offset)
        groups = result.get("groups", [])
        for group in groups:
            indices = group.pop("photo_indices", [])
            group["photos"] = [valid_paths[i] for i in indices if i < len(valid_paths)]
        
        print(f"✅ Detected {len(groups)} items in this batch")
        for i, group in enumerate(groups, 1):
            print(f"   • {group.get('title')} ({len(group.get('photos', []))} photos)")
        
        return groups
        
    except Exception as e:
        print(f"❌ Batch analysis error: {e}")
        raise  # Let the caller handle the fallback
