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
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=60.0,  # 60 second timeout for API calls
    max_retries=2  # Retry failed requests twice
)
print("✅ Using personal OpenAI API key with timeout=60s, retries=2")

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


def validate_ai_result(result: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate AI-generated listing against quality gates
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check title length
    title = result.get("title", "")
    if len(title) > 70:
        errors.append(f"Title too long ({len(title)} chars, max 70)")
    
    # Check for emojis in title/description
    import re
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    if emoji_pattern.search(title):
        errors.append("Title contains emojis (forbidden)")
    
    description = result.get("description", "")
    if emoji_pattern.search(description):
        errors.append("Description contains emojis (forbidden)")
    
    # Check hashtags (should be 3-5, at end of description)
    hashtag_count = description.count("#")
    if hashtag_count < 3 or hashtag_count > 5:
        errors.append(f"Invalid hashtag count ({hashtag_count}, need 3-5)")
    
    # Check mandatory fields
    if not result.get("condition"):
        errors.append("Missing 'condition' field")
    if not result.get("size"):
        errors.append("Missing 'size' field")
    
    # Check for forbidden marketing phrases
    forbidden_phrases = ["parfait pour", "style tendance", "casual chic", "découvrez", "idéal"]
    for phrase in forbidden_phrases:
        if phrase.lower() in description.lower():
            errors.append(f"Forbidden marketing phrase: '{phrase}'")
    
    return (len(errors) == 0, errors)


def generate_fallback_analysis(photo_paths: List[str]) -> Dict[str, Any]:
    """
    Generate a basic fallback analysis when AI fails
    Uses simple heuristics - MUST comply with strict quality gates
    Ensures condition and size are ALWAYS filled (never null/empty)
    """
    return {
        "title": "Vêtement à identifier – bon état",
        "description": "Article en bon état visible sur photos. Matière et détails à préciser selon photos fournies. Taille à vérifier. Mesures recommandées pour confirmation avant achat. Envoi rapide. Remise possible si achat groupé. #mode #vinted #occasion",
        "price": 20,
        "category": "autre",
        "condition": "Bon état",  # MANDATORY: Default value if AI fails
        "color": "Non spécifié",
        "brand": "Non spécifié",
        "size": "Taille non visible",  # MANDATORY: Default value if AI fails (changed from "Non spécifié")
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
    Intelligently group photos into clothing items using image metadata
    Uses aspect ratio, file size, and color similarity for better grouping
    
    Args:
        photo_paths: All photo paths
        max_per_group: Maximum photos per item (default 7 minimum)
        
    Returns:
        List of photo groups
    """
    import imagehash
    from PIL import Image
    
    # Extract metadata for each photo
    photo_metadata = []
    for path in photo_paths:
        try:
            img = Image.open(path)
            aspect_ratio = img.width / img.height if img.height > 0 else 1.0
            file_size = Path(path).stat().st_size
            # Use pHash for perceptual similarity
            phash = imagehash.phash(img)
            photo_metadata.append({
                'path': path,
                'aspect_ratio': aspect_ratio,
                'file_size': file_size,
                'phash': phash
            })
        except Exception as e:
            print(f"⚠️ Metadata extraction failed for {path}: {e}")
            # Fallback metadata
            photo_metadata.append({
                'path': path,
                'aspect_ratio': 1.0,
                'file_size': 0,
                'phash': None
            })
    
    # Group photos by similarity
    groups = []
    used_indices = set()
    
    for i, meta in enumerate(photo_metadata):
        if i in used_indices:
            continue
            
        # Start new group with current photo
        current_group = [meta['path']]
        used_indices.add(i)
        
        # Find similar photos for this group
        for j, other_meta in enumerate(photo_metadata[i+1:], start=i+1):
            if j in used_indices or len(current_group) >= max_per_group:
                continue
            
            # Check similarity
            is_similar = False
            
            # Similar aspect ratio (within 15%)
            aspect_diff = abs(meta['aspect_ratio'] - other_meta['aspect_ratio'])
            if aspect_diff < 0.15:
                is_similar = True
            
            # Similar file size (within 50% for same photo session)
            if meta['file_size'] > 0 and other_meta['file_size'] > 0:
                size_ratio = min(meta['file_size'], other_meta['file_size']) / max(meta['file_size'], other_meta['file_size'])
                if size_ratio > 0.5:
                    is_similar = True
            
            # Perceptual hash similarity (Hamming distance < 10)
            if meta['phash'] and other_meta['phash']:
                hash_distance = meta['phash'] - other_meta['phash']
                if hash_distance < 10:
                    is_similar = True
            
            if is_similar:
                current_group.append(other_meta['path'])
                used_indices.add(j)
        
        groups.append(current_group)
    
    print(f"📦 Smart grouped {len(photo_paths)} photos into {len(groups)} items (similarity-based)")
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


def _auto_polish_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔧 POLISSAGE AUTOMATIQUE 100% - Garantit que le brouillon est PARFAIT
    
    Corrections automatiques :
    - Supprime TOUS les emojis
    - Supprime TOUTES les phrases marketing
    - Force TOUS les champs obligatoires
    - Corrige les hashtags (3-5, à la fin)
    - Ajuste le prix si nécessaire
    - Raccourcit le titre si trop long
    
    Returns:
        Draft corrigé et 100% prêt à publier
    """
    import re
    
    # 1. NETTOYER EMOJIS (title + description)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    title = draft.get("title", "")
    description = draft.get("description", "")
    
    original_title = title
    original_description = description
    
    title = emoji_pattern.sub("", title).strip()
    description = emoji_pattern.sub("", description).strip()
    
    if title != original_title or description != original_description:
        print(f"🧹 Emojis supprimés automatiquement")
    
    # 2. NETTOYER PHRASES MARKETING
    forbidden_phrases = [
        "parfait pour", "idéal pour", "style tendance", "casual chic", 
        "découvrez", "magnifique", "prestigieuse", "haute qualité",
        "look", "tendance", "must-have", "incontournable"
    ]
    
    description_lower = description.lower()
    for phrase in forbidden_phrases:
        if phrase in description_lower:
            # Supprimer la phrase (simple remplacement)
            description = re.sub(rf'\b{re.escape(phrase)}\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()  # Nettoyer espaces
            print(f"🧹 Phrase marketing supprimée : '{phrase}'")
    
    # 3. GARANTIR CHAMPS OBLIGATOIRES
    
    # condition (JAMAIS vide)
    condition = draft.get("condition", "").strip()
    if not condition:
        print(f"⚠️  'condition' vide → correction : 'Bon état'")
        condition = "Bon état"
    draft["condition"] = condition
    
    # size (JAMAIS vide)
    size = draft.get("size", "").strip()
    if not size:
        print(f"⚠️  'size' vide → correction : 'Taille non visible'")
        size = "Taille non visible"
    draft["size"] = size
    
    # brand (fallback si vide)
    brand = draft.get("brand", "").strip()
    if not brand or brand.lower() in ["", "non spécifié", "unknown", "n/a"]:
        brand = "Marque non visible"
        draft["brand"] = brand
    
    # color (fallback si vide)
    color = draft.get("color", "").strip()
    if not color or color.lower() in ["", "non spécifié", "unknown", "n/a"]:
        color = "Couleur variée"
        draft["color"] = color
    
    # category (fallback si vide)
    category = draft.get("category", "").strip()
    if not category or category.lower() in ["", "non spécifié", "unknown", "autre"]:
        category = "vêtement"
        draft["category"] = category
    
    # 4. CORRIGER HASHTAGS (3-5, à la fin)
    hashtags = re.findall(r'#\w+', description)
    
    if len(hashtags) < 3:
        print(f"⚠️  Pas assez de hashtags ({len(hashtags)}), ajout automatique")
        # Générer hashtags manquants
        missing_count = 3 - len(hashtags)
        auto_hashtags = []
        
        if brand.lower() not in ["marque non visible", "non spécifié"]:
            auto_hashtags.append(f"#{brand.lower().replace(' ', '')}")
        if category and category != "vêtement":
            auto_hashtags.append(f"#{category.lower().replace(' ', '').replace('-', '')}")
        if color.lower() not in ["couleur variée", "non spécifié"]:
            auto_hashtags.append(f"#{color.lower().replace(' ', '')}")
        
        # Ajouter hashtags génériques si besoin
        generic_hashtags = ["#mode", "#vinted", "#occasion", "#vetement"]
        auto_hashtags.extend(generic_hashtags[:missing_count])
        
        hashtags.extend(auto_hashtags[:missing_count])
    
    if len(hashtags) > 5:
        print(f"⚠️  Trop de hashtags ({len(hashtags)}), réduction à 5")
        hashtags = hashtags[:5]
    
    # Supprimer hashtags de la description, puis les remettre à la fin
    description_no_hashtags = re.sub(r'#\w+', '', description).strip()
    description_no_hashtags = re.sub(r'\s+', ' ', description_no_hashtags).strip()
    
    # Ajouter les hashtags à la fin
    hashtag_string = " ".join(hashtags)
    description = f"{description_no_hashtags} {hashtag_string}".strip()
    
    # 5. RACCOURCIR TITRE SI TROP LONG (≤70 chars)
    if len(title) > 70:
        print(f"⚠️  Titre trop long ({len(title)} chars), réduction à 70")
        # Garder début + état
        title = title[:67] + "..."
    
    # 6. AJUSTER PRIX SI NÉCESSAIRE
    original_price = draft.get("price", 20)
    adjusted_price = _adjust_price_if_needed(draft)
    if adjusted_price != original_price:
        print(f"💰 Prix ajusté : {original_price}€ → {adjusted_price}€")
        draft["price"] = adjusted_price
    
    # 7. METTRE À JOUR LE DRAFT
    draft["title"] = title
    draft["description"] = description
    
    return draft


def _adjust_price_if_needed(item: Dict[str, Any]) -> float:
    """
    Ajuster le prix selon les règles réalistes Vinted 2025
    Si l'AI a mal calculé, on corrige automatiquement
    
    Args:
        item: Dict avec brand, category, condition, price
        
    Returns:
        Prix ajusté en euros
    """
    category = (item.get("category") or "").lower()
    brand = (item.get("brand") or "").lower()
    condition = (item.get("condition") or "Bon état").lower()
    
    # BASES CATÉGORIES (prix de départ réalistes)
    base_prices = {
        "t-shirt": 18, "polo": 18, "top": 18,
        "chemise": 20, "blouse": 20,
        "pull": 25, "sweat": 25, "cardigan": 25,
        "hoodie": 38, "sweatshirt": 38,
        "pantalon": 32, "jean": 32, "jeans": 32,
        "short": 25, "bermuda": 25,
        "jogging": 28, "survêtement": 28,
        "veste": 55, "blouson": 55,
        "manteau": 60, "coat": 60,
        "doudoune": 70, "parka": 70
    }
    
    # Trouver la catégorie
    base_price = 20  # Default
    for cat_key, price in base_prices.items():
        if cat_key in category:
            base_price = price
            break
    
    # MULTIPLICATEURS MARQUE
    brand_multiplier = 1.0
    
    # Luxe (×3.0 à ×5.0)
    luxury_brands = ["burberry", "dior", "gucci", "louis vuitton", "lv", "prada", "chanel", "hermès", "hermes", "yves saint laurent", "ysl"]
    if any(b in brand for b in luxury_brands):
        brand_multiplier = 3.5
    
    # Premium (×2.0 à ×2.5) - FIX CRITIQUE : Karl Lagerfeld, Ralph Lauren, etc.
    elif any(b in brand for b in ["ralph lauren", "polo", "karl lagerfeld", "diesel", "tommy hilfiger", "lacoste", "hugo boss", "calvin klein"]):
        brand_multiplier = 2.2
    
    # Streetwear (×2.5 à ×3.5)
    elif any(b in brand for b in ["fear of god", "essentials", "supreme", "off-white", "bape", "a bathing ape"]):
        brand_multiplier = 2.8
    
    # Sportswear premium (×2.0 à ×2.8)
    elif any(b in brand for b in ["yeezy", "jordan", "off white"]):
        brand_multiplier = 2.5
    
    # Standard (×1.0) - Zara, H&M, Uniqlo
    elif any(b in brand for b in ["zara", "h&m", "uniqlo", "mango", "asos"]):
        brand_multiplier = 1.0
    
    # Entrée de gamme (×0.8)
    elif "non spécifié" in brand or not brand:
        brand_multiplier = 0.8
    
    # MULTIPLICATEURS CONDITION
    condition_multiplier = 0.70  # "Bon état" par défaut
    if "neuf avec" in condition:
        condition_multiplier = 1.00
    elif "neuf" in condition:
        condition_multiplier = 0.95
    elif "très bon" in condition:
        condition_multiplier = 0.85
    elif "bon" in condition:
        condition_multiplier = 0.70
    elif "satisfaisant" in condition:
        condition_multiplier = 0.55
    
    # CALCUL
    calculated_price = base_price * brand_multiplier * condition_multiplier
    
    # ARRONDIS PSYCHOLOGIQUES
    if calculated_price < 40:
        # Arrondir à 9, 19, 29, 39
        adjusted = round(calculated_price / 10) * 10 - 1
        if adjusted < 9:
            adjusted = 9
    elif calculated_price < 100:
        # Arrondir à 49, 59, 69, 79, 89, 99
        adjusted = round(calculated_price / 10) * 10 - 1
    else:
        # Arrondir à 99, 119, 129, 149, 199
        adjusted = round(calculated_price / 10) * 10 - 1
    
    return int(adjusted)


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
        
        # Create intelligent grouping prompt with REINFORCED quality rules (condition & size MANDATORY)
        prompt = f"""Tu es l'assistant "Photo → Listing" de VintedBot Studio. Tu reçois {len(image_contents)} photos et tu dois les GROUPER intelligemment par pièce/vêtement, puis générer un listing pour chaque groupe.

RÈGLES DE GROUPEMENT CRITIQUES (anti-saucisson ET anti-mélange):
1. **UNE PIÈCE = UN ARTICLE** : Regrouper TOUTES les photos d'une même pièce/vêtement dans un seul article pour maximiser la visualisation acheteur.

2. **PLUSIEURS PIÈCES = PLUSIEURS GROUPES SÉPARÉS** (RÈGLE ABSOLUE):
   Tu DOIS créer des groupes séparés si tu détectes :
   • Marques DIFFÉRENTES (ex: Burberry ≠ Ralph Lauren → 2 groupes)
   • Couleurs DIFFÉRENTES (ex: t-shirt noir ≠ t-shirt blanc → 2 groupes)  
   • Coupes/styles DIFFÉRENTS (ex: hoodie ≠ t-shirt → 2 groupes)
   • Logos/motifs DIFFÉRENTS (ex: logo Lacoste ≠ logo Polo → 2 groupes)
   • Tailles adultes DIFFÉRENTES (ex: XS ≠ M → 2 groupes)
   
   🔴 INTERDIT ABSOLU : Mélanger des vêtements différents dans le même groupe (ex: t-shirt noir + t-shirt blanc = ERREUR GRAVE)

3. **JAMAIS de listing multi-pièces** : Interdiction absolue de créer "lot de 2 t-shirts" ou combiner plusieurs vêtements dans un article.

4. **Détecter les détails** : Les photos de détails/étiquettes/macros (≤2 photos isolées) doivent être fusionnées avec le groupe principal du même vêtement.

5. Les étiquettes (care labels, brand tags, size labels) DOIVENT être rattachées au vêtement principal correspondant - JAMAIS créer d'article "étiquette seule".

6. **MINIMUM 3 PHOTOS PAR ARTICLE** : Si un groupe a moins de 3 photos, essaie de trouver d'autres photos du même vêtement. Si impossible, ne crée PAS ce groupe (il sera rejeté).

CHAMPS OBLIGATOIRES (NE JAMAIS LAISSER VIDE):

**condition** (OBLIGATOIRE - JAMAIS NULL/VIDE):
  ⚠️ CE CHAMP NE DOIT JAMAIS ÊTRE null, undefined, ou vide ⚠️
  Déterminer l'état selon les photos. TOUJOURS remplir ce champ.
  Valeurs autorisées UNIQUEMENT:
  • "Neuf avec étiquette" : étiquette visible sur la photo
  • "Neuf sans étiquette" : article impeccable, jamais porté
  • "Très bon état" : légères traces d'usage, propre
  • "Bon état" : usure visible mais bon état général
  • "Satisfaisant" : défauts visibles (tâches, trous, décoloration)
  
  🔴 RÈGLE ABSOLUE : Si tu ne vois pas assez de détails pour déterminer l'état précis, tu DOIS choisir "Bon état" par défaut.
  🔴 INTERDIT ABSOLU : Retourner null, undefined, "", ou omettre ce champ. Le JSON sera REJETÉ.

**size** (OBLIGATOIRE - JAMAIS NULL/VIDE):
  ⚠️ CE CHAMP NE DOIT JAMAIS ÊTRE null, undefined, ou vide ⚠️
  TOUJOURS remplir ce champ en cherchant l'étiquette de taille sur les photos.
  Examiner attentivement TOUTES les photos pour trouver la taille (étiquette cousue, tag papier, inscription visible).
  
  🔴 RÈGLE ABSOLUE : Si aucune taille n'est visible sur les photos, tu DOIS écrire "Taille non visible" (texte exact).
  🔴 INTERDIT ABSOLU : Retourner null, undefined, "", ou omettre ce champ. Le JSON sera REJETÉ.

TAILLES (normalisation tops/vêtements):
- Conserver original_size (ex. 16Y / 165 cm)
- Si taille enfant/ado (\\d+Y, ans) ou hauteur (cm), calculer normalized_size adulte XS/S/M/L… avec confidence et range_cm approximatif
- Règles génériques unisex (tops) : 152–158 cm → XXS (0.7) ; 160–166 cm → XS (0.8) ; 167–172 cm → S (0.7)
- Ajuster d'une demi-taille si brand_tier=premium ou fit "oversize/fit slim", et baisser confidence de 0.1
- Ajouter size_notes (ex. « ≈ XS adulte, équiv. 16Y/165 cm ; vérifier mesures »)
- Quality gate taille : si seule la taille enfant est connue mais normalized_size.confidence ≥ 0.6, publish_ready peut rester true ; sinon false et ajouter dans missing_fields: mesures poitrine/longueur

LISTING POUR CHAQUE GROUPE:

title (≤70 chars, format « {{Catégorie}} {{Couleur}} {{Marque?}} {{Taille?}} – {{État}} » ; si taille normalisée disponible, l'inclure : « XS (≈ 16Y/165 cm) »)
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
  
  Exemple: "T-shirt Burberry noir, logo imprimé devant, coupe classique. Très bon état : matière propre, couleur uniforme, pas de trou ou tâche visibles. Coton confortable, col rond. Taille d'origine : 16Y / 165 cm — équiv. XS adulte selon le guide générique. Mesures conseillées à ajouter : poitrine (à plat) et longueur dos, en cm. Envoi rapide ; remise possible si achat de plusieurs pièces."
  
  INTERDITS ABSOLUS: emojis, phrases marketing ("parfait pour", "style tendance", "casual chic", "look", "découvrez", "idéal"), superlatifs

hashtags (3–5 pertinents, OBLIGATOIRE, À LA FIN de la description)
  Format: #marque #catégorie #couleur #taille #style
  Exemple: #burberry #tshirt #noir #xs #streetwear

price (suggéré en euros, bases réalistes Vinted 2025)
  BASES CATÉGORIES:
  - T-shirt/polo: 18€ | Chemise: 20€ | Pull/sweat: 25€ | Hoodie: 38€
  - Pantalon/jean: 32€ | Short: 25€ | Jogging: 28€
  - Veste légère: 55€ | Manteau: 60€ | Doudoune: 70€
  
  MULTIPLICATEURS MARQUE (très important pour premium):
  - Luxe (Burberry, Dior, Gucci, LV, Prada): ×3.0 à ×5.0
  - **Premium (Ralph Lauren, Karl Lagerfeld, Diesel, Tommy Hilfiger, Lacoste, Hugo Boss): ×2.0 à ×2.5**
  - Streetwear (Fear of God Essentials, Supreme, Off-White): ×2.5 à ×3.5
  - Sportswear premium (Adidas Yeezy, Nike Jordan): ×2.0 à ×2.8
  - Standard (Zara, H&M, Uniqlo, marques connues): ×1.0
  - Entrée de gamme (no-name, basique): ×0.8
  
  MULTIPLICATEURS CONDITION:
  - Neuf avec étiquettes: ×1.00
  - Très bon état: ×0.85
  - Bon état: ×0.70
  - Satisfaisant: ×0.55
  
  ARRONDIS PSYCHOLOGIQUES:
  - <40€ → finit par 9 (ex: 19€, 29€, 39€)
  - 40–99€ → 49/59/69/79/89/99€
  - ≥100€ → 99/119/129/149/199€
  
  EXEMPLES CONCRETS:
  - Short Ralph Lauren bon état: 25€ × 2.0 × 0.70 = 35€ → 39€
  - Hoodie Karl Lagerfeld très bon: 38€ × 2.2 × 0.85 = 71€ → 69€
  - T-shirt Burberry satisfaisant: 18€ × 3.5 × 0.55 = 35€ → 39€
  - Veste Essentials bon état: 55€ × 2.8 × 0.70 = 108€ → 99€

STYLE (adapte selon "{style}"):
- minimal: Ton sobre, descriptions factuelles courtes
- streetwear: Ton lifestyle direct, sans emojis ni marketing
- classique: Ton boutique sobre, descriptions soignées

QUALITY GATE (CRITÈRES SANS-ÉCHEC):
- title.length ≤70
- 3 ≤ hashtags.length ≤5
- AUCUN emoji dans title/description
- AUCUN superlatif ("magnifique", "prestigieuse", "haute qualité", "parfait pour", "tendance", "idéal")
- AUCUNE phrase marketing ("parfait pour", "style tendance", "casual chic", "look", "découvrez")
- **condition doit être rempli (valeur par défaut: "Bon état" si impossible à déterminer)**
- **size doit être rempli (valeur par défaut: "Taille non visible" si impossible à lire)**
- Hashtags UNIQUEMENT à la fin de la description

INTERDITS ABSOLUS: emojis, marketing creux ("découvrez", "parfait pour", "style tendance", slogans), liens/contacts, promesses hors plateforme, "authentique/original" sans preuve.

STYLE HUMAIN MINIMAL : aucune phrase creuse ni slogan. Si emoji/superlatif détecté, régénère la même sortie en les supprimant. La description doit tenir en 5–8 lignes factuelles : 1) quoi + couleur/coupe, 2) état concret, 3) matière/détails (col, bords-côtes, poches), 4) taille + repère morpho approximatif, 5) mesures à fournir, 6) logistique/remise lot.

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
        validated_groups = []
        
        for group in groups:
            indices = group.pop("photo_indices", [])
            group["photos"] = [valid_paths[i] for i in indices if i < len(valid_paths)]
            
            # 🔧 POLISSAGE AUTOMATIQUE 100% (Garantit brouillons parfaits)
            group = _auto_polish_draft(group)
            
            # ✅ VALIDATION FINALE (après polissage)
            validation_errors = []
            
            # 1. Vérifier nombre minimum de photos (≥3 photos obligatoire)
            photo_count = len(group.get("photos", []))
            if photo_count < 3:
                validation_errors.append(f"Trop peu de photos ({photo_count}, minimum 3)")
            
            # 2. Vérifier title ≤70 chars
            title = group.get("title", "")
            if len(title) > 70:
                validation_errors.append(f"Titre trop long ({len(title)} chars, max 70)")
            
            # 3. Vérifier hashtags 3-5
            description = group.get("description", "")
            hashtag_count = description.count("#")
            if hashtag_count < 3 or hashtag_count > 5:
                validation_errors.append(f"Hashtags invalides ({hashtag_count}, besoin 3-5)")
            
            # Si validation échoue après polissage, REJETER
            if validation_errors:
                print(f"❌ Article REJETÉ (après polissage) : {title[:50]}")
                for error in validation_errors:
                    print(f"   • {error}")
                continue  # Skip this article
            
            validated_groups.append(group)
        
        print(f"\n{'='*80}")
        print(f"✅ VALIDATION FINALE : {len(validated_groups)}/{len(groups)} articles validés")
        print(f"{'='*80}")
        for i, group in enumerate(validated_groups, 1):
            title = group.get('title', 'N/A')
            photo_count = len(group.get('photos', []))
            condition = group.get('condition', 'N/A')
            price = group.get('price', 0)
            brand = group.get('brand', 'N/A')
            size = group.get('size', 'N/A')
            
            print(f"[{i}] {title}")
            print(f"    📸 Photos: {photo_count} | 💰 Prix: {price}€ | 🏷️  Marque: {brand}")
            print(f"    ✨ État: {condition} | 📏 Taille: {size}")
        
        return validated_groups
        
    except Exception as e:
        print(f"❌ Batch analysis error: {e}")
        raise  # Let the caller handle the fallback
