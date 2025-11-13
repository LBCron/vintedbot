"""
Sprint 1 Phase 3: Sophisticated Description Generator

Generate optimized descriptions in 5 different styles:
1. Casual: Friendly, conversational tone
2. Professional: Formal, detailed, trustworthy
3. Minimal: Short, essential info only
4. Storytelling: Narrative approach, emotional connection
5. Urgency: FOMO-driven, time-sensitive

Plus SEO optimization and templating system.
"""
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import re
from loguru import logger


class DescriptionStyle(Enum):
    """Available description styles"""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    MINIMAL = "minimal"
    STORYTELLING = "storytelling"
    URGENCY = "urgency"


@dataclass
class SEOKeywords:
    """SEO keywords for Vinted optimization"""
    primary: List[str]  # Main keywords (brand, category)
    secondary: List[str]  # Related keywords
    hashtags: List[str]  # Popular hashtags (3-5)


@dataclass
class GeneratedDescription:
    """A generated description"""
    text: str
    style: DescriptionStyle
    char_count: int
    word_count: int
    hashtags: List[str]
    seo_score: float  # 0-100
    readability_score: float  # 0-100


class DescriptionGenerator:
    """
    Sophisticated description generator with multiple styles

    Features:
    - 5 distinct writing styles
    - SEO optimization for Vinted search
    - Keyword integration
    - Hashtag generation (3-5 relevant tags)
    - Character limit compliance (Vinted: 1000 chars)
    - Template support
    - A/B testing metadata
    """

    MAX_LENGTH = 1000  # Vinted description limit

    def __init__(self):
        self.seo_keywords_db = self._load_seo_keywords()
        self.templates = self._load_templates()

    def generate(
        self,
        item_data: Dict,
        style: DescriptionStyle = DescriptionStyle.CASUAL,
        include_seo: bool = True,
        include_hashtags: bool = True,
        custom_notes: Optional[str] = None
    ) -> GeneratedDescription:
        """
        Generate description for an item

        Args:
            item_data: Dict with title, brand, category, condition, size, color, etc.
            style: Description style to use
            include_seo: Whether to include SEO keywords
            include_hashtags: Whether to add hashtags
            custom_notes: Optional custom notes to include

        Returns:
            Generated description with metadata
        """
        logger.info(f"[DESC-GEN] Generating {style.value} description")

        # Extract item info
        title = item_data.get("title", "Article")
        brand = item_data.get("brand", "")
        category = item_data.get("category", "")
        condition = item_data.get("condition", "Bon état")
        size = item_data.get("size", "")
        color = item_data.get("color", "")
        price = item_data.get("price", 0)

        # Generate SEO keywords
        seo = self._generate_seo_keywords(brand, category, color) if include_seo else None

        # Generate base description based on style
        if style == DescriptionStyle.CASUAL:
            text = self._generate_casual(item_data, seo)
        elif style == DescriptionStyle.PROFESSIONAL:
            text = self._generate_professional(item_data, seo)
        elif style == DescriptionStyle.MINIMAL:
            text = self._generate_minimal(item_data, seo)
        elif style == DescriptionStyle.STORYTELLING:
            text = self._generate_storytelling(item_data, seo)
        elif style == DescriptionStyle.URGENCY:
            text = self._generate_urgency(item_data, seo)
        else:
            text = self._generate_casual(item_data, seo)

        # Add custom notes if provided
        if custom_notes:
            text += f"\n\n{custom_notes}"

        # Generate hashtags
        hashtags = self._generate_hashtags(brand, category, color, size) if include_hashtags else []

        # Add hashtags to description
        if hashtags:
            text += "\n\n" + " ".join(hashtags)

        # Ensure within character limit
        if len(text) > self.MAX_LENGTH:
            # Truncate and add ellipsis
            text = text[:self.MAX_LENGTH - 3] + "..."

        # Calculate scores
        seo_score = self._calculate_seo_score(text, seo) if seo else 50.0
        readability_score = self._calculate_readability_score(text)

        # Count chars and words
        char_count = len(text)
        word_count = len(text.split())

        description = GeneratedDescription(
            text=text,
            style=style,
            char_count=char_count,
            word_count=word_count,
            hashtags=hashtags,
            seo_score=seo_score,
            readability_score=readability_score
        )

        logger.info(
            f"[DESC-GEN] Generated {word_count} words, "
            f"SEO score: {seo_score:.1f}, "
            f"Readability: {readability_score:.1f}"
        )

        return description

    def _generate_casual(self, item_data: Dict, seo: Optional[SEOKeywords]) -> str:
        """Generate casual, friendly description"""
        brand = item_data.get("brand", "")
        title = item_data.get("title", "Article")
        condition = item_data.get("condition", "Bon état")
        size = item_data.get("size", "")
        color = item_data.get("color", "")

        parts = [
            f"Salut ! 👋",
            f"",
            f"Je vends ce super {title.lower()} {f'de chez {brand}' if brand else ''} !",
            f"",
        ]

        # Condition
        if "neuf" in condition.lower():
            parts.append(f"État : {condition} - jamais porté, encore avec l'étiquette ! 🏷️")
        elif "comme neuf" in condition.lower():
            parts.append(f"État : {condition} - quasi neuf, porté une ou deux fois max ! ✨")
        else:
            parts.append(f"État : {condition} - en super condition ! 👌")

        parts.append("")

        # Size and color
        details = []
        if size:
            details.append(f"Taille {size}")
        if color:
            details.append(f"couleur {color}")
        if details:
            parts.append(f"📏 {' - '.join(details)}")
            parts.append("")

        # Call to action
        parts.extend([
            "N'hésite pas si tu as des questions ! 💬",
            "Envoi rapide et soigné 📦",
            "",
            "À bientôt ! 😊"
        ])

        return "\n".join(parts)

    def _generate_professional(self, item_data: Dict, seo: Optional[SEOKeywords]) -> str:
        """Generate professional, detailed description"""
        brand = item_data.get("brand", "")
        title = item_data.get("title", "Article")
        category = item_data.get("category", "")
        condition = item_data.get("condition", "Bon état")
        size = item_data.get("size", "")
        color = item_data.get("color", "")

        parts = [
            f"{title}",
            ""
        ]

        if brand:
            parts.append(f"Marque: {brand}")

        # Specifications
        specs = []
        if category:
            specs.append(f"Catégorie: {category}")
        if size:
            specs.append(f"Taille: {size}")
        if color:
            specs.append(f"Couleur: {color}")
        if condition:
            specs.append(f"État: {condition}")

        if specs:
            parts.append("")
            parts.extend(specs)

        # Description
        parts.extend([
            "",
            "Description:",
            f"Article {f'de marque {brand}' if brand else 'de qualité'} en {condition.lower()}.",
            "Photos récentes représentant fidèlement l'article.",
            "",
            "Informations pratiques:",
            "• Envoi sous 48h après paiement",
            "• Emballage soigné et sécurisé",
            "• Paiement sécurisé via Vinted",
            "• Réponse rapide aux messages",
            "",
            "Pour toute question, n'hésitez pas à me contacter.",
            "Merci de votre visite !"
        ])

        return "\n".join(parts)

    def _generate_minimal(self, item_data: Dict, seo: Optional[SEOKeywords]) -> str:
        """Generate minimal, concise description"""
        brand = item_data.get("brand", "")
        title = item_data.get("title", "Article")
        condition = item_data.get("condition", "Bon état")
        size = item_data.get("size", "")
        color = item_data.get("color", "")

        parts = [title]

        details = []
        if brand:
            details.append(brand)
        if size:
            details.append(f"Taille {size}")
        if color:
            details.append(color)

        if details:
            parts.append(" • ".join(details))

        parts.append(condition)
        parts.append("")
        parts.append("Envoi rapide 📦")

        return "\n".join(parts)

    def _generate_storytelling(self, item_data: Dict, seo: Optional[SEOKeywords]) -> str:
        """Generate narrative, emotional description"""
        brand = item_data.get("brand", "")
        title = item_data.get("title", "Article")
        condition = item_data.get("condition", "Bon état")
        category = item_data.get("category", "")

        # Create narrative based on category
        if "robe" in category.lower() or "dress" in category.lower():
            story = "Cette magnifique pièce a été mon coup de cœur, mais il est temps de lui trouver une nouvelle maison. "
        elif "jean" in category.lower() or "pantalon" in category.lower():
            story = "Ce vêtement intemporel mérite une seconde vie dans votre garde-robe. "
        elif "pull" in category.lower() or "sweat" in category.lower():
            story = "Doux et confortable, ce vêtement a été mon allié cocooning. "
        else:
            story = "Cet article unique a fait partie de ma garde-robe, mais je souhaite maintenant lui offrir une nouvelle vie. "

        parts = [
            f"✨ {title} ✨",
            "",
            story,
            "",
            f"État : {condition}",
            ""
        ]

        if brand:
            parts.append(f"Marque authentique {brand} - qualité garantie.")
            parts.append("")

        parts.extend([
            "Pourquoi vous allez l'adorer :",
            "• Pièce unique qui se démarque",
            "• Qualité et style réunis",
            "• Parfait pour créer des looks originaux",
            "",
            "Donnez-lui une seconde chance d'être aimé ! 💚",
            "",
            "Envoi avec soin et rapidité. 📦"
        ])

        return "\n".join(parts)

    def _generate_urgency(self, item_data: Dict, seo: Optional[SEOKeywords]) -> str:
        """Generate urgent, FOMO-driven description"""
        brand = item_data.get("brand", "")
        title = item_data.get("title", "Article")
        condition = item_data.get("condition", "Bon état")
        price = item_data.get("price", 0)

        parts = [
            f"🔥 OFFRE LIMITÉE 🔥",
            "",
            f"{title}",
            ""
        ]

        if brand:
            parts.append(f"Marque premium : {brand}")
            parts.append("")

        parts.extend([
            f"État : {condition}",
            "",
            "⏰ NE MANQUEZ PAS CETTE OPPORTUNITÉ !",
            ""
        ])

        if price and price > 0:
            parts.append(f"Prix exceptionnel : {price}€")
            parts.append("")

        parts.extend([
            "Pourquoi craquer maintenant :",
            "✓ Article très demandé",
            "✓ Stock limité (dernier exemplaire)",
            "✓ Prix imbattable",
            "✓ Envoi immédiat dès réception du paiement",
            "",
            "🚀 Premier arrivé, premier servi !",
            "",
            "Les articles de cette qualité partent vite...",
            "Faites vite avant qu'il ne soit trop tard ! ⚡",
            "",
            "Questions? Réponse ultra-rapide garantie! 💬"
        ])

        return "\n".join(parts)

    def _generate_seo_keywords(self, brand: str, category: str, color: str) -> SEOKeywords:
        """Generate SEO keywords for Vinted search"""
        primary = []
        secondary = []

        # Brand as primary keyword
        if brand:
            primary.append(brand.lower())

        # Category as primary keyword
        if category:
            primary.append(category.lower())

        # Color as secondary
        if color:
            secondary.append(color.lower())

        # Add common related terms
        if category:
            cat_lower = category.lower()
            if "jean" in cat_lower:
                secondary.extend(["denim", "pantalon"])
            elif "pull" in cat_lower:
                secondary.extend(["sweater", "tricot"])
            elif "robe" in cat_lower:
                secondary.extend(["dress", "tenue"])

        return SEOKeywords(
            primary=primary,
            secondary=secondary,
            hashtags=[]  # Will be generated separately
        )

    def _generate_hashtags(self, brand: str, category: str, color: str, size: str) -> List[str]:
        """Generate 3-5 relevant hashtags"""
        hashtags = []

        # Brand hashtag
        if brand:
            hashtags.append(f"#{brand.replace(' ', '')}")

        # Category hashtag
        if category:
            cat_clean = category.replace(" ", "").replace("-", "")
            hashtags.append(f"#{cat_clean}")

        # Color hashtag (if distinctive)
        if color and color.lower() not in ["noir", "blanc", "gris", "black", "white", "gray"]:
            hashtags.append(f"#{color.replace(' ', '')}")

        # Size hashtag (if specific)
        if size:
            size_clean = size.replace(" ", "").upper()
            hashtags.append(f"#{size_clean}")

        # Add popular generic hashtags to reach 3-5
        popular = ["#mode", "#fashion", "#vintedFrance", "#bonPlan", "#secondMain"]
        for tag in popular:
            if len(hashtags) >= 5:
                break
            if tag not in hashtags:
                hashtags.append(tag)

        return hashtags[:5]  # Max 5 hashtags

    def _calculate_seo_score(self, text: str, seo: Optional[SEOKeywords]) -> float:
        """Calculate SEO score based on keyword presence"""
        if not seo:
            return 50.0

        score = 0.0
        text_lower = text.lower()

        # Primary keywords (worth 40 points total)
        for keyword in seo.primary:
            if keyword in text_lower:
                score += 40 / max(len(seo.primary), 1)

        # Secondary keywords (worth 30 points total)
        for keyword in seo.secondary:
            if keyword in text_lower:
                score += 30 / max(len(seo.secondary), 1)

        # Length bonus (worth 30 points)
        if len(text) >= 200:
            score += 30
        elif len(text) >= 100:
            score += 15

        return min(score, 100.0)

    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score (simplified)"""
        # Count sentences, words, characters
        sentences = len([s for s in re.split(r'[.!?]', text) if s.strip()])
        words = len(text.split())
        chars = len(text.replace(" ", "").replace("\n", ""))

        if sentences == 0 or words == 0:
            return 50.0

        # Average word length
        avg_word_length = chars / words

        # Average sentence length
        avg_sentence_length = words / sentences

        # Score (simplified Flesch formula concept)
        # Ideal: short words (4-6 chars), medium sentences (15-20 words)
        score = 100.0

        # Penalize very long words
        if avg_word_length > 7:
            score -= (avg_word_length - 7) * 5
        # Penalize very short words
        elif avg_word_length < 3:
            score -= (3 - avg_word_length) * 10

        # Penalize very long sentences
        if avg_sentence_length > 25:
            score -= (avg_sentence_length - 25) * 2
        # Penalize very short sentences
        elif avg_sentence_length < 10:
            score -= (10 - avg_sentence_length) * 1

        return max(min(score, 100.0), 0.0)

    def _load_seo_keywords(self) -> Dict:
        """Load SEO keywords database (simplified)"""
        return {
            "categories": {
                "jean": ["denim", "pantalon", "pants"],
                "robe": ["dress", "tenue"],
                "pull": ["sweater", "tricot", "knit"],
                "t-shirt": ["tee", "top"],
                "veste": ["jacket", "coat", "blazer"]
            }
        }

    def _load_templates(self) -> Dict:
        """Load description templates"""
        return {
            "casual": {
                "intro": ["Salut ! 👋", "Hey ! 🙂", "Hello ! 😊"],
                "closing": ["À bientôt !", "Bisous ! 😘", "Merci ! 🙏"]
            },
            "professional": {
                "intro": ["Bonjour,", "Bonsoir,"],
                "closing": ["Cordialement,", "Bien cordialement,", "Merci de votre visite."]
            }
        }
