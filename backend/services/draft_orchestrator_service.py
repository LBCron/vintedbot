"""
Draft Creation Orchestrator

Coordinates all AI services to create complete, optimized drafts from photos.

Pipeline:
1. Enhanced Vision Analysis (GPT-4o)
2. Brand Detection (OCR)
3. Content Generation (Title, Description, Hashtags)
4. Smart Pricing
5. Draft Assembly
"""
import logging
import asyncio
from typing import Dict, List, Optional
from pathlib import Path

from backend.services.enhanced_vision_service import EnhancedVisionService
from backend.services.brand_detection_service import BrandDetectionService
from backend.services.draft_content_generator import DraftContentGenerator
from backend.services.smart_pricing_service import SmartPricingService

logger = logging.getLogger(__name__)


class DraftOrchestratorService:
    """Orchestrates complete draft creation pipeline"""

    def __init__(self):
        self.vision_service = EnhancedVisionService()
        self.brand_service = BrandDetectionService()
        self.content_generator = DraftContentGenerator()
        self.pricing_service = SmartPricingService()

    async def create_draft_from_photos(
        self,
        photo_paths: List[str],
        style: str = "casual_friendly",
        language: str = "fr",
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Complete pipeline: photos → optimized draft

        Args:
            photo_paths: List of product photo paths
            style: Description style
            language: Content language
            user_preferences: Optional user preferences

        Returns:
            Complete draft data ready for Vinted
        """
        try:
            logger.info(f"Starting draft creation for {len(photo_paths)} photos")

            # STEP 1: Vision Analysis (parallel for all photos)
            vision_tasks = [
                self.vision_service.analyze_product_photo(path)
                for path in photo_paths
            ]
            vision_results = await asyncio.gather(*vision_tasks)

            # Use first photo as primary
            primary_analysis = vision_results[0]
            logger.info(f"Vision: {primary_analysis.get('category')} - {primary_analysis.get('condition')}")

            # STEP 2: Brand Detection (on first photo)
            brand_info = self.brand_service.detect_brand(photo_paths[0])
            logger.info(f"Brand: {brand_info.get('brand_name', 'None')} (conf: {brand_info.get('confidence', 0)}%)")

            # STEP 3: Content Generation (parallel)
            title_task = self.content_generator.generate_title(
                primary_analysis, brand_info, language
            )
            desc_task = self.content_generator.generate_description(
                primary_analysis, brand_info, style, language
            )
            hashtags_task = self.content_generator.generate_hashtags(
                primary_analysis, brand_info
            )

            title, description, hashtags = await asyncio.gather(
                title_task, desc_task, hashtags_task
            )

            logger.info(f"Content: Title={title[:50]}...")

            # STEP 4: Smart Pricing
            pricing = self.pricing_service.calculate_price(
                primary_analysis, brand_info
            )
            logger.info(f"Pricing: {pricing['recommended_price']}€")

            # STEP 5: Assemble Draft
            draft = {
                "title": title,
                "description": description,
                "price": pricing["recommended_price"],
                "price_range": {
                    "min": pricing["min_price"],
                    "max": pricing["max_price"]
                },
                "category": primary_analysis.get("category"),
                "subcategory": primary_analysis.get("subcategory"),
                "brand": brand_info.get("brand_name"),
                "brand_confidence": brand_info.get("confidence", 0),
                "condition": primary_analysis.get("condition"),
                "condition_score": primary_analysis.get("condition_score"),
                "colors": primary_analysis.get("colors", []),
                "materials": primary_analysis.get("materials", []),
                "size": primary_analysis.get("size_label"),
                "gender": primary_analysis.get("gender"),
                "season": primary_analysis.get("season"),
                "style": primary_analysis.get("style", []),
                "hashtags": hashtags,
                "defects": primary_analysis.get("defects", []),
                "photo_count": len(photo_paths),
                "photo_quality": primary_analysis.get("photo_quality"),
                "ai_generated": True,
                "generation_metadata": {
                    "description_style": style,
                    "language": language,
                    "vision_model": "gpt-4o",
                    "brand_detection": brand_info.get("method"),
                    "pricing_confidence": pricing.get("confidence")
                }
            }

            logger.info(f"✅ Draft created successfully: {draft['title']}")
            return draft

        except Exception as e:
            logger.error(f"Draft creation failed: {e}", exc_info=True)
            raise

    async def analyze_multiple_photos(
        self,
        photo_paths: List[str]
    ) -> Dict:
        """
        Analyze photos to detect multiple items (for auto-grouping)

        Args:
            photo_paths: List of photo paths

        Returns:
            Grouping analysis
        """
        try:
            # Detect items in each photo
            tasks = [
                self.vision_service.detect_multiple_items(path)
                for path in photo_paths
            ]
            results = await asyncio.gather(*tasks)

            # Calculate total items
            total_items = sum(r.get("item_count", 1) for r in results)

            # Suggest grouping
            if total_items == len(photo_paths):
                grouping = "one_item_per_photo"
            elif total_items > len(photo_paths):
                grouping = "multiple_items_detected"
            else:
                grouping = "unclear"

            return {
                "photo_count": len(photo_paths),
                "detected_items": total_items,
                "grouping_strategy": grouping,
                "auto_group_possible": grouping == "one_item_per_photo",
                "photo_analyses": results
            }

        except Exception as e:
            logger.error(f"Photo analysis failed: {e}")
            return {
                "photo_count": len(photo_paths),
                "detected_items": len(photo_paths),
                "grouping_strategy": "one_item_per_photo",
                "auto_group_possible": True
            }
