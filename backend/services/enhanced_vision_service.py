"""
Enhanced Vision Analysis Service with GPT-4o

Advanced photo analysis for draft creation:
- Detailed product identification
- Color, material, pattern detection
- Condition assessment
- Brand visibility detection
- Defect identification
- Style and category suggestions
"""
import logging
import base64
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
from backend.core.openai_client import get_openai_client

logger = logging.getLogger(__name__)


class EnhancedVisionService:
    """Enhanced vision analysis using GPT-4o for maximum accuracy"""

    def __init__(self):
        self.client = get_openai_client()

    async def analyze_product_photo(self, image_path: str) -> Dict:
        """
        Comprehensive product analysis with GPT-4o

        Args:
            image_path: Path to product image

        Returns:
            Detailed analysis including category, colors, materials, condition, defects
        """
        if not self.client.is_configured:
            logger.error("OpenAI client not configured")
            return self._fallback_analysis()

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Enhanced prompt for comprehensive analysis
            prompt = """Analyze this product photo in extreme detail for a Vinted listing.

Provide a comprehensive JSON analysis with:

{
  "category": "category name (e.g., 'T-shirt', 'Jean', 'Sneakers')",
  "subcategory": "specific type (e.g., 'Slim fit jeans', 'Running shoes')",
  "gender": "Homme/Femme/Unisexe/Enfant",
  "colors": ["primary color", "secondary color"],
  "materials": ["main material", "other materials"],
  "patterns": ["pattern type"] or [],
  "brand_visible": true/false,
  "brand_name": "detected brand name or null",
  "brand_confidence": 0-100,
  "condition": "Neuf avec étiquette/Très bon état/Bon état/Satisfaisant",
  "condition_score": 1-10,
  "defects": [
    {
      "type": "type of defect",
      "severity": "minor/moderate/major",
      "location": "where on the item",
      "description": "detailed description"
    }
  ],
  "style": ["style keywords like 'vintage', 'streetwear', 'casual'"],
  "season": "Été/Automne/Hiver/Printemps/Toutes saisons",
  "size_visible": true/false,
  "size_label": "detected size or null",
  "features": ["notable features like 'pockets', 'hood', 'zipper'"],
  "photo_quality": {
    "lighting": "good/poor",
    "angle": "front/side/back/detail",
    "background": "clean/cluttered",
    "focus": "sharp/blurry"
  },
  "recommendations": ["suggestions to improve listing"]
}

Be extremely detailed and accurate. Look for brand logos, tags, labels, defects, stains, wear patterns."""

            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Latest vision model
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": "high"  # High detail for better analysis
                            }
                        }
                    ]
                }],
                response_format={"type": "json_object"},
                max_tokens=1500,
                temperature=0.3
            )

            result = eval(response.choices[0].message.content)
            logger.info(f"Vision analysis complete: {result.get('category')} - {result.get('condition')}")
            return result

        except asyncio.TimeoutError:
            logger.error("Vision analysis timed out")
            return self._fallback_analysis()
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return self._fallback_analysis()

    async def batch_analyze_photos(self, image_paths: List[str]) -> List[Dict]:
        """
        Analyze multiple photos in parallel

        Args:
            image_paths: List of image file paths

        Returns:
            List of analysis results
        """
        tasks = [self.analyze_product_photo(path) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Photo {i} analysis failed: {result}")
                valid_results.append(self._fallback_analysis())
            else:
                valid_results.append(result)

        return valid_results

    async def detect_multiple_items(self, image_path: str) -> Dict:
        """
        Detect if photo contains multiple items (for auto-grouping)

        Args:
            image_path: Path to image

        Returns:
            Detection result with item count and suggestions
        """
        if not self.client.is_configured:
            return {"item_count": 1, "items": [], "auto_group_possible": False}

        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            prompt = """How many distinct clothing/fashion items are in this photo?

Respond in JSON:
{
  "item_count": number of items,
  "items": [
    {"type": "item type", "position": "location in photo"}
  ],
  "auto_group_possible": true if items can be grouped together,
  "grouping_suggestion": "how to group items"
}"""

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }],
                response_format={"type": "json_object"},
                max_tokens=500
            )

            return eval(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Multi-item detection failed: {e}")
            return {"item_count": 1, "items": [], "auto_group_possible": False}

    def _fallback_analysis(self) -> Dict:
        """Fallback when vision AI unavailable"""
        return {
            "category": "Vêtement",
            "subcategory": "Non spécifié",
            "gender": "Unisexe",
            "colors": ["Non détecté"],
            "materials": ["Non détecté"],
            "patterns": [],
            "brand_visible": False,
            "brand_name": None,
            "brand_confidence": 0,
            "condition": "Bon état",
            "condition_score": 7,
            "defects": [],
            "style": [],
            "season": "Toutes saisons",
            "size_visible": False,
            "size_label": None,
            "features": [],
            "photo_quality": {
                "lighting": "good",
                "angle": "front",
                "background": "clean",
                "focus": "sharp"
            },
            "recommendations": ["AI vision not available - manual review recommended"],
            "fallback": True
        }
