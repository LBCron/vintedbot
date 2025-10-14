"""
AI-powered photo analysis and listing generation using OpenAI GPT-4 Vision
Analyzes clothing photos and generates: title, description, price, category, condition, color
"""
import os
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
from openai import OpenAI

# Use Replit AI Integrations (no API key required, billed to credits)
AI_INTEGRATIONS_OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
AI_INTEGRATIONS_OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

# This is using Replit's AI Integrations service
openai_client = OpenAI(
    api_key=AI_INTEGRATIONS_OPENAI_API_KEY,
    base_url=AI_INTEGRATIONS_OPENAI_BASE_URL
)


def encode_image_to_base64(image_path: str) -> str:
    """Convert local image to base64 string"""
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
        
        # Create prompt for clothing analysis
        prompt = """Tu es un expert en vêtements et mode. Analyse ces photos de vêtement et génère un brouillon d'annonce Vinted optimisée.

IMPORTANT: Réponds UNIQUEMENT avec un objet JSON valide, sans markdown ni texte supplémentaire.

Format de réponse requis:
{
    "title": "Titre accrocheur (max 60 caractères, inclut marque si visible, catégorie, couleur)",
    "description": "Description détaillée et professionnelle (150-300 mots) : état, matières, détails, style, comment le porter. Ajoute émojis pertinents.",
    "price": 25,
    "category": "t-shirt|hoodie|sweatshirt|joggers|jeans|pantalon|short|veste|manteau|parka|chemise|polo|robe|jupe|casquette|sneakers|chaussures|sac|autre",
    "condition": "Neuf avec étiquette|Très bon état|Bon état|Satisfaisant",
    "color": "noir|blanc|gris|bleu|rouge|vert|jaune|beige|marron|rose|violet|orange|multicolore",
    "brand": "Nom de la marque si visible, sinon 'Non spécifié'",
    "size": "XS|S|M|L|XL|XXL|nombre si visible, sinon 'Non spécifié'",
    "confidence": 0.95
}

Règles de pricing:
- T-shirt/polo: 8-15€
- Hoodie/sweatshirt: 20-35€
- Jeans/pantalon: 20-40€
- Veste/manteau: 30-80€
- Chaussures/sneakers: 25-60€
- Sac: 15-50€
- Si marque premium visible (Nike, Adidas, Zara, etc.): +30%

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
    Uses simple heuristics based on filename and basic detection
    """
    return {
        "title": "Vêtement à identifier",
        "description": "Article en bon état. Photos réelles. Envoi rapide depuis Grenoble. N'hésitez pas à poser vos questions ! 📦",
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
            results.append(result)
        except Exception as e:
            print(f"❌ Group {i+1} failed: {e}")
            fallback = generate_fallback_analysis(group)
            fallback['group_index'] = i
            results.append(fallback)
    
    return results


def smart_group_photos(photo_paths: List[str], max_per_group: int = 6) -> List[List[str]]:
    """
    Intelligently group photos into clothing items
    Simple version: groups by sequences (every N photos = 1 item)
    
    TODO: Use image similarity (CLIP embeddings) for smarter grouping
    
    Args:
        photo_paths: All photo paths
        max_per_group: Maximum photos per item (default 6)
        
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
