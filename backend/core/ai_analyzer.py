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
from backend.settings import settings

# Use user's personal OpenAI API key from settings
openai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=60.0,  # 60 second timeout for API calls
    max_retries=2  # Retry failed requests twice
)
print(f"[OK] OpenAI client initialized (timeout=60s, retries=2, key={'configured' if settings.OPENAI_API_KEY else 'MISSING'})")

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
        
        print(f"[OK] Converted HEIC -> JPEG: {Path(heic_path).name}")
        return jpeg_path
        
    except Exception as e:
        print(f"[ERROR] HEIC conversion error for {heic_path}: {e}")
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
    WITH REDIS CACHING + IMAGE OPTIMIZATION

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

    # Import caching and optimization services
    try:
        from backend.services.redis_cache import get_cached_analysis, cache_analysis_result
        from backend.services.image_optimizer import batch_optimize_images
    except ImportError as e:
        print(f"[WARN]  Service import failed: {e}, running without optimization")
        get_cached_analysis = lambda x: None
        cache_analysis_result = lambda x, y: False
        batch_optimize_images = lambda x: x

    try:
        # STEP 1: Check Redis cache first (huge cost savings!)
        cached_result = get_cached_analysis(photo_paths[:6])
        if cached_result:
            print(f"[CACHE HIT] Returning cached analysis [OK]")
            return cached_result

        # STEP 2: Optimize images before API call (75% cost reduction!)
        print(f"[OPTIMIZE] Optimizing {len(photo_paths[:6])} images...")
        optimized_paths = batch_optimize_images(photo_paths[:6])

        # STEP 3: Prepare images for API call
        image_contents = []
        for path in optimized_paths:
            if not Path(path).exists():
                print(f"[WARN] Photo not found: {path}")
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
        
        # Create prompt for single-item clothing analysis (USER MODEL - Nov 2025)
        # ENHANCED: Natural casual tone like a real person selling on Vinted
        prompt = """Tu es quelqu'un qui vend ses vêtements sur Vinted. Écris comme une vraie personne, pas comme une boutique professionnelle. Ton naturel et décontracté, comme si tu parlais à un pote.

RÈGLES STRICTES :
- Pas d'emojis. Ton naturel et authentique.
- TITRE simple et direct (60–70 caractères max). Ex: "Hoodie Karl Lagerfeld noir et blanc L"
- Description COURTE et naturelle, 4–6 lignes max. Parle comme une vraie personne : "Je vends mon hoodie...", "Porté quelques fois", "Super état", "Nickel", "Impec".
- Pas de détails techniques compliqués (composition exacte, etc.). Juste l'essentiel.
- Évite les phrases commerciales type "qualité et style assurés", "pièce incontournable".
- Ajouter 3–5 hashtags SIMPLES et naturels (minuscules) À LA FIN.
- Mentionne les défauts simplement : "quelques traces d'usage", "léger boulochage", "bon état général".
- Sois honnête et direct : "porté plusieurs fois", "comme neuf", "quelques marques".
- Si une donnée manque, écrire "taille à vérifier" ou "mesure sur demande".
- Sortie STRICTEMENT en JSON respectant le schéma ci-dessous. N'ajoute rien d'autre.

[ALERT] VOCABULAIRE PAR CATÉGORIE :
- HAUTS (hoodie, sweat, pull, t-shirt, chemise) : poitrine, épaules, manches, dos, capuche
- BAS (jogging, pantalon, jean, short) : taille, cuisses, jambes, entrejambe, chevilles

SCHÉMA JSON DE SORTIE :
{
  "title": "string",                    // 60-90 chars, hook unique si rare/vintage
  "description": "string",              // 6-8 puces •, inclure défauts/style/saison, hashtags à la fin
  "brand": "string|null",               // ou "à préciser"
  "category": "string",                 // ex: "hoodie", "jogging", "jean"
  "size": "string|null",                // ex: "L", "M", "à préciser"
  "condition": "string",                // "Neuf avec étiquette"|"Neuf sans étiquette"|"Très bon état"|"Bon état"|"Satisfaisant"
  "color": "string",                    // ex: "noir", "bicolore"
  "materials": "string|null",           // ex: "59% coton, 32% rayonne, 9% spandex" ou "à préciser"
  "fit": "string|null",                 // ex: "coupe droite" ou null
  "style": "string|null",               // ex: "streetwear", "vintage Y2K", "casual", "sportswear" (NOUVEAU)
  "seasonality": "string|null",         // ex: "automne-hiver", "été", "toutes saisons" (NOUVEAU)
  "defects": "string|null",             // Défauts visuels précis ou "aucun défaut visible" (NOUVEAU)
  "rarity": "string|null",              // ex: "collab rare", "édition limitée", "vintage", null (NOUVEAU)
  "price": number,                      // en euros, justifié par marque/rareté/condition
  "price_justification": "string|null", // Courte explication du prix (ex: "marque premium + bon état") (NOUVEAU)
  "confidence": number                  // 0.0 à 1.0
}

EXEMPLES TON NATUREL :

HAUT (Hoodie Karl Lagerfeld) :
{
  "title": "Hoodie Karl Lagerfeld noir et blanc L",
  "description": "Je vends mon hoodie Karl Lagerfeld noir et blanc. Porté quelques fois, super état, juste un léger boulochage aux coudes mais rien de méchant. Style streetwear cool. Taille L, nickel pour l'automne-hiver. Dispo de suite ! #karllagerfeld #hoodie #streetwear #noir",
  "brand": "Karl Lagerfeld",
  "category": "hoodie",
  "size": "L",
  "condition": "Très bon état",
  "color": "bicolore",
  "materials": "coton et synthétique",
  "fit": "coupe droite",
  "style": "streetwear",
  "seasonality": "automne-hiver",
  "defects": "léger boulochage aux coudes",
  "rarity": null,
  "price": 69,
  "price_justification": "marque premium + très bon état",
  "confidence": 0.95
}

BAS (Jogging Burberry) :
{
  "title": "Jogging Burberry noir L vintage",
  "description": "Jogging Burberry noir des années 2000, logo brodé sur la cuisse. Bon état général, le cordon a un peu décoloré mais rien de grave. Style Y2K, vraiment sympa. Taille L. Envoi rapide. #burberry #jogging #vintage #y2k #noir",
  "brand": "Burberry",
  "category": "jogging",
  "size": "L",
  "condition": "Bon état",
  "color": "noir",
  "materials": "à préciser",
  "fit": "coupe droite",
  "style": "Y2K streetwear",
  "seasonality": "toutes saisons",
  "defects": "légère décoloration cordon",
  "rarity": "vintage années 2000",
  "price": 119,
  "price_justification": "marque luxe + vintage rare",
  "confidence": 0.90
}

ANALYSE VISUELLE CRITIQUE :
1. **Défauts** : Scrute CHAQUE détail – coutures effilochées? taches? bouloches? décoloration? élasticité perdue? trous? Si AUCUN défaut visible, note "aucun défaut visible".
2. **Style** : Identifie l'esthétique (streetwear, Y2K, vintage, casual, sportswear, minimaliste, grunge, preppy).
3. **Saison** : Détermine usage optimal (automne-hiver, printemps-été, toutes saisons, mi-saison).
4. **Rareté** : Détecte collaborations (Nike x Off-White, Adidas x Yeezy), éditions limitées, vintage authentique, pièces uniques.
5. **Hashtags** : Utilise mots-clés TENDANCE Vinted (#oversized, #vintage, #y2k, #rare, #streetwear, #grunge, #preppy, #90s, #2000s, #collector).
6. **Prix** : Justifie TOUJOURS le prix (marque + rareté + condition + demande marché).

Analyse les photos et génère le JSON avec ce format EXACT :"""

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
        
        print(f"[SEARCH] Analyzing {len(image_contents)} photos with GPT-4 Vision...")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4 with vision capabilities
            messages=messages,  # type: ignore
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)

        print(f"[SUCCESS] Analysis complete: {result.get('title', 'Unknown')}")
        print(f"   Category: {result.get('category')}, Price: {result.get('price')}€")

        # STEP 4: Cache the result for future use (30 day TTL)
        cache_analysis_result(photo_paths[:6], result)

        # STEP 5: Track quality metrics
        try:
            from backend.services.redis_cache import track_ai_quality_metrics
            is_valid, errors = validate_ai_result(result)
            track_ai_quality_metrics(result, is_valid)
        except Exception as e:
            print(f"[WARN]  Metrics tracking failed: {e}")

        return result

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error: {e}")
        # Return fallback result
        fallback = generate_fallback_analysis(photo_paths)

        # Track fallback usage
        try:
            from backend.services.redis_cache import track_ai_quality_metrics
            track_ai_quality_metrics(fallback, False)
        except:
            pass

        return fallback

    except Exception as e:
        print(f"[ERROR] AI analysis error: {e}")
        # Return fallback result
        fallback = generate_fallback_analysis(photo_paths)

        # Track fallback usage
        try:
            from backend.services.redis_cache import track_ai_quality_metrics
            track_ai_quality_metrics(fallback, False)
        except:
            pass

        return fallback


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
        "description": "Article en bon état visible sur photos. Matière et détails à préciser selon photos fournies. Taille à vérifier. Envoi rapide. Remise possible si achat groupé. #mode #vinted #occasion",
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
        print(f"\n[PHOTO] Analyzing group {i+1}/{len(photo_groups)} ({len(group)} photos)...")
        try:
            result = analyze_clothing_photos(group)
            result['group_index'] = i
            result['photos'] = group  # CRITICAL: Attach photos to result for draft creation
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Group {i+1} failed: {e}")
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
            print(f"[WARN] Metadata extraction failed for {path}: {e}")
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
    
    print(f"[PACKAGE] Smart grouped {len(photo_paths)} photos into {len(groups)} items (similarity-based)")
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
    print(f"[PACKAGE] Auto-batching: {total_photos} photos -> splitting into batches of {BATCH_SIZE}")
    
    all_items = []
    offset = 0
    batch_num = 1
    total_batches = (total_photos + BATCH_SIZE - 1) // BATCH_SIZE
    
    while offset < total_photos:
        batch_photos = photo_paths[offset:offset + BATCH_SIZE]
        print(f"\n[BATCH] Batch {batch_num}/{total_batches}: Analyzing photos {offset+1}-{offset+len(batch_photos)}...")
        
        try:
            batch_items = _analyze_single_batch(batch_photos, style, offset)
            all_items.extend(batch_items)
            print(f"[OK] Batch {batch_num} complete: {len(batch_items)} items detected")
        except Exception as e:
            print(f"[ERROR] Batch {batch_num} failed: {e}, using fallback")
            # Fallback: group batch photos by 7 photos per item
            fallback_groups = smart_group_photos(batch_photos, max_per_group=7)
            fallback_items = batch_analyze_photos(fallback_groups)
            all_items.extend(fallback_items)
        
        offset += BATCH_SIZE
        batch_num += 1
    
    print(f"\n[OK] Auto-batching complete: {len(all_items)} total items from {total_photos} photos")
    return all_items


def _normalize_size_field(size: str) -> str:
    """
    [FIX] NORMALISATION TAILLE - Extrait UNIQUEMENT la taille adulte finale
    
    Exemples:
    - "16Y / 165 cm (≈ XS)" -> "XS"
    - "XS (≈ 16Y)" -> "XS"  
    - "12 ans (≈ S)" -> "S"
    - "M" -> "M"
    
    Returns:
        Taille adulte simple (XS/S/M/L/XL/XXL) ou fallback
    """
    import re
    
    if not size or size.strip() == "":
        return "M"  # Fallback par défaut
    
    # Si déjà une taille simple adulte, retourner directement
    size_upper = size.strip().upper()
    simple_sizes = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]
    if size_upper in simple_sizes:
        return size_upper
    
    # Extraire la taille adulte de formats complexes (ex: "16Y / 165 cm (≈ XS)")
    # Chercher pattern: (≈ TAILLE) ou / TAILLE) ou juste TAILLE
    match = re.search(r'[≈\(]\s*([X]{0,3}[SMLX]{1,3})\s*[\)]', size.upper())
    if match:
        extracted = match.group(1)
        if extracted in simple_sizes:
            return extracted
    
    # Chercher directement une taille dans la chaîne
    for sz in simple_sizes:
        if re.search(rf'\b{sz}\b', size.upper()):
            return sz
    
    # Si "Taille non visible" ou équivalent
    if "non visible" in size.lower() or "non spécifié" in size.lower():
        return "Taille non visible"
    
    # Fallback
    return "M"


def _normalize_condition_field(condition: str) -> str:
    """
    [FIX] NORMALISATION CONDITION - Convertit en français standardisé
    
    Returns:
        Condition en français (Vinted-compatible)
    """
    if not condition:
        return "Bon état"
    
    condition_lower = condition.lower().strip()
    
    # Mapping anglais -> français
    if condition_lower in ["new with tags", "neuf avec étiquette", "neuf avec étiquettes"]:
        return "Neuf avec étiquette"
    elif condition_lower in ["new", "neuf", "neuf sans étiquette"]:
        return "Neuf sans étiquette"
    elif condition_lower in ["very good", "très bon état", "très bon"]:
        return "Très bon état"
    elif condition_lower in ["good", "bon état", "bon"]:
        return "Bon état"
    elif condition_lower in ["satisfactory", "satisfaisant", "état satisfaisant"]:
        return "Satisfaisant"
    
    # Fallback
    return "Bon état"


def _auto_polish_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    """
    [FIX] POLISSAGE AUTOMATIQUE 100% - Garantit que le brouillon est PARFAIT
    
    Corrections automatiques :
    - Supprime TOUS les emojis
    - Supprime TOUTES les phrases marketing
    - Force TOUS les champs obligatoires
    - Corrige les hashtags (3-5, à la fin)
    - Ajuste le prix si nécessaire
    - Raccourcit le titre si trop long
    - NORMALISE la taille (XS au lieu de "16Y / 165 cm (≈ XS)")
    - NORMALISE la condition en français
    
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
        print(f"[CLEAN] Emojis supprimés automatiquement")
    
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
            print(f"[CLEAN] Phrase marketing supprimée : '{phrase}'")
    
    # 2.5 VALIDER VOCABULAIRE PAR CATÉGORIE (CRITIQUE - MATCHING FLEXIBLE)
    category = draft.get("category", "").lower()
    
    # Mapping catégories -> groupes (matching par sous-chaîne pour robustesse)
    TOPS_KEYWORDS = ["hoodie", "sweat", "pull", "t-shirt", "tshirt", "tee", "chemise", 
                     "blouse", "veste", "blouson", "manteau", "doudoune", "parka", "cardigan",
                     "top", "débardeur", "gilet"]
    BOTTOMS_KEYWORDS = ["jogging", "pantalon", "jean", "short", "bermuda", "legging", 
                        "survêtement", "jogger", "cargo", "chino"]
    
    # Détection flexible : catégorie contient-elle un mot-clé ?
    is_top = any(keyword in category for keyword in TOPS_KEYWORDS)
    is_bottom = any(keyword in category for keyword in BOTTOMS_KEYWORDS)
    
    # Termes interdits par groupe (avec mapping vers remplacements contextuels)
    if is_bottom:
        # BAS : SUPPRIMER TOTALEMENT vocabulaire HAUTS
        forbidden_replacements = {
            r'\bpoitrine\b': 'cuisse',
            r'\bépaules?\b': 'taille',
            r'\bmanches?\b': 'jambes',
            r'\bcapuche\b': '',  # Supprimer complètement (illogique pour un bas)
            r'\bcol\b': '',
            r'\bdos\b': '',
            r'\bencolure\b': '',
            r'\bpoignets?\b': 'chevilles',
            r'\bbrodé poitrine\b': 'brodé cuisse',
            r'\bimprimé poitrine\b': 'imprimé cuisse',
            r'\bdétail dos\b': 'détail arrière',
            r'\bmanches longues\b': 'jambes longues',
            r'\bmanches courtes\b': 'jambes courtes'
        }
        
        for pattern, replacement in forbidden_replacements.items():
            if re.search(pattern, description_lower):
                match_text = re.search(pattern, description_lower)
                if match_text:
                    print(f"[ALERT] VOCABULAIRE INCORRECT '{match_text.group()}' dans {category} (BAS) -> '{replacement or 'supprimé'}'")
                if replacement:
                    description = re.sub(pattern, replacement, description, flags=re.IGNORECASE)
                else:
                    # Supprimer le terme + contexte autour
                    description = re.sub(rf'[,\s]*{pattern}[,\s]*', ' ', description, flags=re.IGNORECASE)
                    description = re.sub(r'\s+', ' ', description).strip()
    
    elif is_top:
        # HAUTS : SUPPRIMER TOTALEMENT vocabulaire BAS (EXHAUSTIF)
        forbidden_replacements = {
            r'\bentrejambe\b': '',
            r'\bcuisses?\b': 'manches',
            r'\bchevilles?\b': 'poignets',
            # Tous les contextes "taille" = WAIST (pas SIZE)
            r'\btaille élastique\b': 'poignets élastiques',
            r'\btaille ajustable\b': 'poignets ajustables',
            r'\btaille réglable\b': 'poignets réglables',
            r'\btaille resserrée\b': 'poignets resserrés',
            r'\btaille cintrée\b': 'coupe cintrée',
            r'\btaille stretch\b': 'tissu stretch',
            r'\bserrage à la taille\b': 'serrage aux poignets',
            r'\bceinture à la taille\b': 'bord côtelé',
            r'\bà la taille\b': 'à la taille basse',  # Edge case : peut rester si contexte bas de vêtement
            r'\btour de taille\b': 'tour de poitrine',
            r'\bpoches taille\b': 'poches poitrine',
            # Autres vocabulaire BAS
            r'\bbrodé cuisse\b': 'brodé poitrine',
            r'\bimprimé cuisse\b': 'imprimé poitrine',
            r'\bjambes longues\b': 'manches longues',
            r'\bjambes courtes\b': 'manches courtes'
        }
        
        for pattern, replacement in forbidden_replacements.items():
            if re.search(pattern, description_lower):
                match_text = re.search(pattern, description_lower)
                if match_text:
                    print(f"[ALERT] VOCABULAIRE INCORRECT '{match_text.group()}' dans {category} (HAUT) -> '{replacement or 'supprimé'}'")
                if replacement:
                    description = re.sub(pattern, replacement, description, flags=re.IGNORECASE)
                else:
                    # Supprimer le terme
                    description = re.sub(rf'[,\s]*{pattern}[,\s]*', ' ', description, flags=re.IGNORECASE)
                    description = re.sub(r'\s+', ' ', description).strip()
    
    # VÉRIFICATION FINALE : S'assurer qu'AUCUN terme interdit ne subsiste
    if is_bottom:
        # BAS : aucun vocabulaire de HAUTS ne doit survivre
        final_check = [
            r'\bpoitrine\b', r'\bépaules?\b', r'\bmanches?\b', r'\bcapuche\b', 
            r'\bcol\b', r'\bdos\b', r'\bencolure\b', r'\bpoignets?\b'
        ]
        for pattern in final_check:
            if re.search(pattern, description.lower()):
                # Dernier filet de sécurité : supprimer brutalement
                print(f"[WARN]  ALERTE : terme interdit '{pattern}' détecté après corrections -> suppression forcée")
                description = re.sub(pattern, '', description, flags=re.IGNORECASE)
                description = re.sub(r'\s+', ' ', description).strip()
    
    elif is_top:
        # HAUTS : aucun vocabulaire de BAS ne doit survivre (EXHAUSTIF : tous les contextes "taille"=WAIST)
        final_check = [
            r'\bentrejambe\b', r'\bcuisses?\b', r'\bchevilles?\b',
            # Tous les usages "taille" = WAIST (pas SIZE)
            r'\btour de taille\b', r'\btaille ajustable\b', r'\btaille élastique\b',
            r'\btaille réglable\b', r'\btaille resserrée\b', r'\btaille cintrée\b',
            r'\btaille stretch\b', r'\bserrage à la taille\b', r'\bceinture à la taille\b',
            r'\btaille \(waist\)', r'\bpoches taille\b',
            r'\bjambes?\s+(longues?|courtes?)\b'  # "jambes longues" mais pas "jambes" seul
        ]
        for pattern in final_check:
            if re.search(pattern, description.lower()):
                print(f"[WARN]  ALERTE : terme interdit '{pattern}' détecté après corrections -> suppression forcée")
                description = re.sub(pattern, '', description, flags=re.IGNORECASE)
                description = re.sub(r'\s+', ' ', description).strip()
    
    else:
        # FALLBACK CONSERVATEUR pour catégories non gérées (robes, jupes, accessoires)
        # -> Appliquer règles TOPS par défaut (plus sûr que de ne rien faire)
        if category and category not in ["vêtement", "", "autre"]:
            print(f"[INFO]  Catégorie '{category}' non classée -> application des règles TOPS par défaut")
            # Supprimer vocabulaire BAS évident (entrejambe, cuisses)
            description = re.sub(r'\bentrejambe\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\bcuisses?\b', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+', ' ', description).strip()
    
    # 3. NORMALISER ET GARANTIR CHAMPS OBLIGATOIRES
    
    # condition (JAMAIS vide + normalisation française)
    original_condition = draft.get("condition", "").strip()
    condition = _normalize_condition_field(original_condition)
    if condition != original_condition:
        print(f"[FIX] Condition normalisée : '{original_condition}' -> '{condition}'")
    draft["condition"] = condition
    
    # size (JAMAIS vide + extraction taille adulte simple)
    original_size = draft.get("size", "").strip()
    size = _normalize_size_field(original_size)
    if size != original_size:
        print(f"[FIX] Taille simplifiée : '{original_size}' -> '{size}'")
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
        print(f"[WARN]  Pas assez de hashtags ({len(hashtags)}), ajout automatique")
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
        print(f"[WARN]  Trop de hashtags ({len(hashtags)}), réduction à 5")
        hashtags = hashtags[:5]
    
    # Supprimer hashtags de la description, puis les remettre à la fin
    description_no_hashtags = re.sub(r'#\w+', '', description).strip()
    description_no_hashtags = re.sub(r'\s+', ' ', description_no_hashtags).strip()
    
    # Ajouter les hashtags à la fin
    hashtag_string = " ".join(hashtags)
    description = f"{description_no_hashtags} {hashtag_string}".strip()
    
    # 5. RACCOURCIR TITRE SI TROP LONG (≤70 chars)
    if len(title) > 70:
        print(f"[WARN]  Titre trop long ({len(title)} chars), réduction à 70")
        # Garder début + état
        title = title[:67] + "..."
    
    # 6. AJUSTER PRIX SI NÉCESSAIRE
    original_price = draft.get("price", 20)
    adjusted_price = _adjust_price_if_needed(draft)
    if adjusted_price != original_price:
        print(f"[PRICE] Prix ajusté : {original_price}€ -> {adjusted_price}€")
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
                print(f"[WARN] Photo not found: {path}")
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
        
        # Create intelligent grouping prompt with natural casual tone
        prompt = f"""Tu vends tes vêtements sur Vinted. Tu reçois {len(image_contents)} photos et tu dois les GROUPER intelligemment par pièce/vêtement, puis écrire des descriptions naturelles pour chaque groupe. Écris comme une vraie personne, pas comme une boutique pro.

RÈGLES DE GROUPEMENT CRITIQUES (anti-saucisson ET anti-mélange):
1. **UNE PIÈCE = UN ARTICLE** : Regrouper TOUTES les photos d'une même pièce/vêtement dans un seul article pour maximiser la visualisation acheteur.

2. **PLUSIEURS PIÈCES = PLUSIEURS GROUPES SÉPARÉS** (RÈGLE ABSOLUE):
   Tu DOIS créer des groupes séparés si tu détectes :
   • Marques DIFFÉRENTES (ex: Burberry ≠ Ralph Lauren -> 2 groupes)
   • Couleurs DIFFÉRENTES (ex: t-shirt noir ≠ t-shirt blanc -> 2 groupes)  
   • Coupes/styles DIFFÉRENTS (ex: hoodie ≠ t-shirt -> 2 groupes)
   • Logos/motifs DIFFÉRENTS (ex: logo Lacoste ≠ logo Polo -> 2 groupes)
   • Tailles adultes DIFFÉRENTES (ex: XS ≠ M -> 2 groupes)
   
   [RULE] INTERDIT ABSOLU : Mélanger des vêtements différents dans le même groupe (ex: t-shirt noir + t-shirt blanc = ERREUR GRAVE)

3. **JAMAIS de listing multi-pièces** : Interdiction absolue de créer "lot de 2 t-shirts" ou combiner plusieurs vêtements dans un article.

4. **Détecter les détails** : Les photos de détails/étiquettes/macros (≤2 photos isolées) doivent être fusionnées avec le groupe principal du même vêtement.

5. Les étiquettes (care labels, brand tags, size labels) DOIVENT être rattachées au vêtement principal correspondant - JAMAIS créer d'article "étiquette seule".

6. **MINIMUM 3 PHOTOS PAR ARTICLE** : Si un groupe a moins de 3 photos, essaie de trouver d'autres photos du même vêtement. Si impossible, ne crée PAS ce groupe (il sera rejeté).

CHAMPS OBLIGATOIRES (NE JAMAIS LAISSER VIDE):

**condition** (OBLIGATOIRE - JAMAIS NULL/VIDE):
  [WARN] CE CHAMP NE DOIT JAMAIS ÊTRE null, undefined, ou vide [WARN]
  Déterminer l'état selon les photos. TOUJOURS remplir ce champ.
  Valeurs autorisées UNIQUEMENT:
  • "Neuf avec étiquette" : étiquette visible sur la photo
  • "Neuf sans étiquette" : article impeccable, jamais porté
  • "Très bon état" : légères traces d'usage, propre
  • "Bon état" : usure visible mais bon état général
  • "Satisfaisant" : défauts visibles (tâches, trous, décoloration)
  
  [RULE] RÈGLE ABSOLUE : Si tu ne vois pas assez de détails pour déterminer l'état précis, tu DOIS choisir "Bon état" par défaut.
  [RULE] INTERDIT ABSOLU : Retourner null, undefined, "", ou omettre ce champ. Le JSON sera REJETÉ.

**size** (OBLIGATOIRE - JAMAIS NULL/VIDE):
  [WARN] CE CHAMP NE DOIT JAMAIS ÊTRE null, undefined, ou vide [WARN]
  [WARN] RETOURNER UNIQUEMENT LA TAILLE ADULTE NORMALISÉE (XS/S/M/L/XL/XXL) [WARN]
  
  [RULE] RÈGLES CRITIQUES - LIS EXACTEMENT L'ÉTIQUETTE (PRIORITÉ ABSOLUE):
  
  1️⃣ Si l'étiquette montre UNE TAILLE ADULTE (XS, S, M, L, XL, XXL) :
     -> Retourne CETTE taille directement : "L", "M", "XS", etc.
     -> PAS de conversion, PAS d'équivalence
     -> Exemple : étiquette dit "L" -> size: "L" (JAMAIS "XS" !)
  
  2️⃣ Si l'étiquette montre UNIQUEMENT une taille enfant (16Y, 14 ans, 165cm) :
     -> Estime la taille adulte PRUDEMMENT (16Y peut être S, M ou L selon marque!)
     -> Exemple : "16Y" seul -> size: "M" (estimation moyenne prudente)
     -> ATTENTION : NE PAS supposer automatiquement que 16Y = XS !
  
  3️⃣ Si l'étiquette montre LES DEUX (ex: "16Y / L" ou "165cm / M") :
     -> PRIVILÉGIE TOUJOURS la taille adulte : size: "L"
     -> Ignore la taille enfant dans le champ size
  
  4️⃣ Si AUCUNE taille visible sur les photos :
     -> size: "Taille non visible"
  
  ESTIMATIONS PRUDENTES (si UNIQUEMENT taille enfant visible):
  • 14Y / 152-158cm -> "S" ou "XS" (prudent: "S")
  • 16Y / 165cm -> "M" ou "L" (prudent: "M") [WARN] PAS automatiquement "XS" !
  • 18Y / 170-176cm -> "L" ou "M" (prudent: "L")
  • Si doute -> "M" (taille moyenne par défaut)
  
  FORMAT À RESPECTER ABSOLUMENT:
  [OK] BON : "L" (si étiquette montre "L")
  [OK] BON : "M" (si étiquette montre "M" ou estimation 16Y)
  [OK] BON : "XS" (si étiquette montre "XS")
  [ERROR] MAUVAIS : "16Y / 165 cm (≈ XS)" (NE JAMAIS inclure taille d'origine)
  [ERROR] MAUVAIS : "XS (≈ 16Y)" (PAS de parenthèses ni équivalences)
  [ERROR] MAUVAIS : "XS" si l'étiquette montre "L" (ERREUR GRAVE !)
  
  [RULE] RÈGLE ABSOLUE : Si aucune taille n'est visible -> retourner "Taille non visible" (texte exact)
  [RULE] INTERDIT ABSOLU : Retourner null, undefined, "", ou omettre ce champ. Le JSON sera REJETÉ.

LISTING POUR CHAQUE GROUPE:

title (≤70 chars, format SIMPLE « {{Catégorie}} {{Couleur}} {{Marque?}} {{Taille}} – {{État}} »)
  [WARN] FORMAT SIMPLIFIÉ - PAS de parenthèses, PAS d'équivalences, PAS de mesures
  
  Exemples CORRECTS:
  [OK] "T-shirt noir Burberry XS – très bon état"
  [OK] "Jogging noir Burberry XS – bon état"
  [OK] "Hoodie Karl Lagerfeld noir M – très bon état"
  
  Exemples INTERDITS:
  [ERROR] "T-shirt noir Burberry XS (≈ 16Y/165 cm) – très bon état" (PAS de parenthèses)
  [ERROR] "Jogging Burberry 16Y / 165 cm – bon état" (utiliser taille adulte)
  
  INTERDITS: emojis, superlatifs ("magnifique", "parfait"), marketing ("découvrez", "idéal pour"), parenthèses avec équivalences

description (4–6 lignes max, ton naturel et décontracté, ZÉRO emoji, ZÉRO phrases commerciales)
  Parle comme une vraie personne qui vend ses vêtements :
  - "Je vends mon...", "Porté quelques fois", "Super état", "Nickel", "Impec"
  - Mentionne l'essentiel : ce que c'est, état honnête, taille, style
  - Défauts simplement : "quelques traces", "léger boulochage", "rien de grave"
  - Pas de détails techniques compliqués (composition exacte, etc.)
  - Évite les phrases commerciales : "qualité assurée", "pièce incontournable", "style tendance"

  Exemple TON NATUREL: "Je vends mon hoodie Karl Lagerfeld noir et blanc. Porté quelques fois, super état, juste un léger boulochage aux coudes mais rien de méchant. Style streetwear cool. Taille L, nickel pour l'automne-hiver. Dispo de suite !"

  MENTIONNE HONNÊTEMENT:
  • Défauts de façon simple et directe (pas de langue de bois)
  • État général sans exagérer
  • Taille et style basique
  • Si vintage/rare, dis-le simplement

  INTERDITS: emojis, marketing ("parfait pour", "style tendance", "pièce magnifique", "qualité assurée"), superlatifs excessifs, détails techniques inutiles

hashtags (3–5 SIMPLES et naturels, À LA FIN de la description)
  Hashtags basiques et directs, pas trop compliqués
  Exemple: #karllagerfeld #hoodie #streetwear #noir
  Ou: #burberry #jogging #vintage #y2k

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
  - <40€ -> finit par 9 (ex: 19€, 29€, 39€)
  - 40–99€ -> 49/59/69/79/89/99€
  - ≥100€ -> 99/119/129/149/199€
  
  EXEMPLES CONCRETS:
  - Short Ralph Lauren bon état: 25€ × 2.0 × 0.70 = 35€ -> 39€
  - Hoodie Karl Lagerfeld très bon: 38€ × 2.2 × 0.85 = 71€ -> 69€
  - T-shirt Burberry satisfaisant: 18€ × 3.5 × 0.55 = 35€ -> 39€
  - Veste Essentials bon état: 55€ × 2.8 × 0.70 = 108€ -> 99€

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

TON NATUREL OBLIGATOIRE : Écris comme une vraie personne qui vend ses vêtements, pas comme une boutique. Utilise "Je vends mon...", "Porté quelques fois", "Super état", "Nickel". Description 4-6 lignes max : 1) ce que c'est, 2) état honnête avec défauts si besoin, 3) taille et style, 4) envoi. Pas de marketing, pas de phrases creuses.

SORTIE JSON OBLIGATOIRE (TON NATUREL):
{{
  "groups": [
    {{
      "title": "T-shirt Burberry noir XS vintage",
      "description": "Je vends mon t-shirt Burberry noir des années 2000. Porté plusieurs fois, bon état général. Le col a très légèrement décoloré mais rien de grave. Style Y2K sympa. Taille XS. Envoi rapide. #burberry #tshirt #vintage #y2k #noir",
      "price": 59,
      "brand": "Burberry",
      "size": "XS",
      "condition": "Bon état",
      "color": "Noir",
      "category": "t-shirt",
      "style": "vintage Y2K",
      "seasonality": "toutes saisons",
      "defects": "très légère décoloration col",
      "rarity": "vintage années 2000",
      "price_justification": "marque luxe + vintage",
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
        
        print(f"[AI] Analyzing {len(image_contents)} photos with GPT-4 Vision...")
        
        # Call OpenAI API with intelligent grouping
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,  # type: ignore
            max_tokens=3000,  # More tokens for multiple items
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
            
            # [FIX] POLISSAGE AUTOMATIQUE 100% (Garantit brouillons parfaits)
            group = _auto_polish_draft(group)
            
            # [OK] VALIDATION FINALE (après polissage)
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
                print(f"[ERROR] Article REJETÉ (après polissage) : {title[:50]}")
                for error in validation_errors:
                    print(f"   • {error}")
                continue  # Skip this article
            
            validated_groups.append(group)
        
        print(f"\n{'='*80}")
        print(f"[OK] VALIDATION FINALE : {len(validated_groups)}/{len(groups)} articles validés")
        print(f"{'='*80}")
        for i, group in enumerate(validated_groups, 1):
            title = group.get('title', 'N/A')
            photo_count = len(group.get('photos', []))
            condition = group.get('condition', 'N/A')
            price = group.get('price', 0)
            brand = group.get('brand', 'N/A')
            size = group.get('size', 'N/A')
            
            print(f"[{i}] {title}")
            print(f"    [PHOTO] Photos: {photo_count} | [PRICE] Prix: {price}€ | [LABEL]  Marque: {brand}")
            print(f"    [EMOJI] État: {condition} | [SIZE] Taille: {size}")
        
        return validated_groups
        
    except Exception as e:
        print(f"[ERROR] Batch analysis error: {e}")
        raise  # Let the caller handle the fallback
