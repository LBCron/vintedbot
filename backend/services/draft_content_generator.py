"""
Draft Content Generator Service

Generates SEO-optimized titles, descriptions, and hashtags for Vinted listings.

Features:
- 3 description styles (casual_friendly, professional, trendy)
- SEO-optimized titles
- Smart hashtags based on trends
- Multilingual support (FR/EN)
- Defect highlighting
"""
import logging
import asyncio
from typing import Dict, List, Optional
from backend.core.openai_client import get_openai_client

logger = logging.getLogger(__name__)


class DraftContentGenerator:
    """AI-powered content generation for drafts"""

    def __init__(self):
        self.client = get_openai_client()

    async def generate_description(
        self,
        vision_analysis: Dict,
        brand_info: Dict,
        style: str = "casual_friendly",
        language: str = "fr"
    ) -> str:
        """
        Generate product description with specified style

        Args:
            vision_analysis: Vision analysis results
            brand_info: Brand detection results
            style: casual_friendly | professional | trendy
            language: fr | en

        Returns:
            Generated description
        """
        if not self.client.is_configured:
            return self._fallback_description(vision_analysis, language)

        try:
            # Build context from analysis
            category = vision_analysis.get("category", "Vêtement")
            condition = vision_analysis.get("condition", "Bon état")
            colors = ", ".join(vision_analysis.get("colors", ["Non spécifié"]))
            materials = ", ".join(vision_analysis.get("materials", []))
            defects = vision_analysis.get("defects", [])
            brand = brand_info.get("brand_name", "Sans marque")

            style_guides = {
                "casual_friendly": {
                    "fr": "Style décontracté et amical avec emojis 😊. Chaleureux, personnel, encourageant. Max 150 mots.",
                    "en": "Casual and friendly style with emojis 😊. Warm, personal, encouraging. Max 150 words."
                },
                "professional": {
                    "fr": "Style professionnel et descriptif. Formel, précis, sans emojis. Max 150 mots.",
                    "en": "Professional and descriptive style. Formal, precise, no emojis. Max 150 words."
                },
                "trendy": {
                    "fr": "Style branché et moderne 🔥. Utilise le langage des réseaux sociaux, emojis tendance. Max 150 mots.",
                    "en": "Trendy and modern style 🔥. Uses social media language, trending emojis. Max 150 words."
                }
            }

            style_guide = style_guides.get(style, style_guides["casual_friendly"])[language]

            prompt = f"""Generate a {language.upper()} product description for Vinted.

Product info:
- Category: {category}
- Brand: {brand}
- Condition: {condition}
- Colors: {colors}
- Materials: {materials}
- Defects: {len(defects)} defect(s)

Style: {style_guide}

Requirements:
- Highlight key features
- Mention condition honestly
{"- Note defects clearly" if defects else ""}
- SEO keywords naturally included
- Engaging and sales-oriented
- Accurate to product analysis

Description:"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )

            description = response.choices[0].message.content.strip()
            logger.info(f"Generated {style} description in {language}")
            return description

        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return self._fallback_description(vision_analysis, language)

    async def generate_title(
        self,
        vision_analysis: Dict,
        brand_info: Dict,
        language: str = "fr"
    ) -> str:
        """
        Generate SEO-optimized title

        Args:
            vision_analysis: Vision analysis results
            brand_info: Brand detection results
            language: fr | en

        Returns:
            Optimized title (max 100 chars)
        """
        if not self.client.is_configured:
            return self._fallback_title(vision_analysis, brand_info, language)

        try:
            category = vision_analysis.get("category", "Vêtement")
            brand = brand_info.get("brand_name", "")
            colors = vision_analysis.get("colors", [])
            size = vision_analysis.get("size_label", "")
            condition = vision_analysis.get("condition", "")

            prompt = f"""Generate a SEO-optimized Vinted title in {language.upper()}.

Product:
- Category: {category}
- Brand: {brand}
- Colors: {", ".join(colors[:2])}
- Size: {size}
- Condition: {condition}

Requirements:
- Max 100 characters
- Include brand if present
- Include primary color
- Include category
- SEO keywords
- Attractive and clickable

Title:"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.5
            )

            title = response.choices[0].message.content.strip()
            # Ensure max length
            if len(title) > 100:
                title = title[:97] + "..."

            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return self._fallback_title(vision_analysis, brand_info, language)

    async def generate_hashtags(
        self,
        vision_analysis: Dict,
        brand_info: Dict,
        max_tags: int = 10
    ) -> List[str]:
        """
        Generate smart hashtags based on trends and product

        Args:
            vision_analysis: Vision analysis results
            brand_info: Brand detection results
            max_tags: Maximum number of hashtags

        Returns:
            List of hashtags
        """
        try:
            category = vision_analysis.get("category", "")
            brand = brand_info.get("brand_name", "")
            colors = vision_analysis.get("colors", [])
            style = vision_analysis.get("style", [])
            season = vision_analysis.get("season", "")

            # Build base hashtags
            hashtags = []

            # Category
            if category:
                hashtags.append(f"#{category.replace(' ', '')}")

            # Brand
            if brand:
                hashtags.append(f"#{brand.replace(' ', '')}")

            # Colors
            for color in colors[:2]:
                hashtags.append(f"#{color.replace(' ', '')}")

            # Style
            for style_tag in style[:2]:
                hashtags.append(f"#{style_tag.replace(' ', '')}")

            # Season
            if season and season != "Toutes saisons":
                hashtags.append(f"#{season}")

            # Trending tags
            trending = ["#Vinted", "#SecondHand", "#Sustainable", "#Fashion"]
            hashtags.extend(trending[:max_tags - len(hashtags)])

            return hashtags[:max_tags]

        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return ["#Vinted", "#Fashion", "#SecondHand"]

    def _fallback_description(self, vision_analysis: Dict, language: str) -> str:
        """Fallback description when AI unavailable"""
        category = vision_analysis.get("category", "Vêtement")
        condition = vision_analysis.get("condition", "Bon état")

        if language == "fr":
            return f"{category} en {condition}. Article de qualité à petit prix !"
        else:
            return f"{category} in {condition}. Quality item at a great price!"

    def _fallback_title(self, vision_analysis: Dict, brand_info: Dict, language: str) -> str:
        """Fallback title when AI unavailable"""
        category = vision_analysis.get("category", "Item")
        brand = brand_info.get("brand_name", "")

        if brand:
            return f"{brand} {category}"
        return category
