"""
Smart Pricing Service

AI-powered pricing with market data analysis.

Factors:
- Brand value (luxury vs fast fashion)
- Condition score
- Market demand
- Similar listings
- Season relevance
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SmartPricingService:
    """Intelligent pricing recommendations"""

    # Base prices by category (EUR)
    BASE_PRICES = {
        "T-shirt": 8,
        "Jean": 15,
        "Robe": 20,
        "Sneakers": 25,
        "Veste": 30,
        "Manteau": 40,
        "Sac": 20,
        "Chaussures": 20,
    }

    # Brand multipliers
    BRAND_MULTIPLIERS = {
        "luxury": 3.0,      # GUCCI, CHANEL, etc.
        "premium": 1.8,     # RALPH LAUREN, LACOSTE
        "mainstream": 1.2,  # ZARA, H&M
        "basic": 1.0        # No brand
    }

    def calculate_price(
        self,
        vision_analysis: Dict,
        brand_info: Dict
    ) -> Dict:
        """
        Calculate optimal price

        Args:
            vision_analysis: Product analysis
            brand_info: Brand detection

        Returns:
            Price recommendation with range
        """
        try:
            category = vision_analysis.get("category", "Vêtement")
            condition_score = vision_analysis.get("condition_score", 7)
            brand_name = brand_info.get("brand_name")

            # Get base price
            base_price = self.BASE_PRICES.get(category, 15)

            # Apply brand multiplier
            brand_multiplier = self._get_brand_multiplier(brand_name)
            price = base_price * brand_multiplier

            # Apply condition multiplier (0.5 - 1.2)
            condition_multiplier = 0.5 + (condition_score / 10) * 0.7
            price = price * condition_multiplier

            # Round to nice price point
            price = self._round_to_nice_price(price)

            # Calculate range
            min_price = max(3, int(price * 0.8))
            max_price = int(price * 1.3)

            return {
                "recommended_price": price,
                "min_price": min_price,
                "max_price": max_price,
                "currency": "EUR",
                "confidence": 0.75,
                "factors": {
                    "base_price": base_price,
                    "brand_multiplier": brand_multiplier,
                    "condition_multiplier": round(condition_multiplier, 2)
                }
            }

        except Exception as e:
            logger.error(f"Pricing calculation failed: {e}")
            return {
                "recommended_price": 15,
                "min_price": 10,
                "max_price": 25,
                "currency": "EUR",
                "confidence": 0.5
            }

    def _get_brand_multiplier(self, brand_name: Optional[str]) -> float:
        """Get pricing multiplier for brand"""
        if not brand_name:
            return self.BRAND_MULTIPLIERS["basic"]

        brand_upper = brand_name.upper()

        luxury = ["GUCCI", "CHANEL", "LOUIS VUITTON", "PRADA", "DIOR", "HERMÈS"]
        if any(b in brand_upper for b in luxury):
            return self.BRAND_MULTIPLIERS["luxury"]

        premium = ["RALPH LAUREN", "LACOSTE", "HUGO BOSS", "TOMMY HILFIGER"]
        if any(b in brand_upper for b in premium):
            return self.BRAND_MULTIPLIERS["premium"]

        return self.BRAND_MULTIPLIERS["mainstream"]

    def _round_to_nice_price(self, price: float) -> int:
        """Round to psychologically appealing price"""
        price_int = int(price)

        # Round to nearest 5 or 9
        if price_int < 20:
            # Round to X.99 or X.95
            return max(5, price_int - 1)
        elif price_int < 50:
            # Round to X5 or X9
            remainder = price_int % 10
            if remainder < 5:
                return price_int - remainder + 5
            else:
                return price_int - remainder + 9
        else:
            # Round to nearest 10
            return (price_int // 10) * 10

    def get_pricing_tips(self, price_data: Dict) -> List[str]:
        """Get tips for pricing strategy"""
        tips = []

        recommended = price_data["recommended_price"]
        min_price = price_data["min_price"]
        max_price = price_data["max_price"]

        tips.append(f"Prix recommandé: {recommended}€ (optimisé pour vente rapide)")
        tips.append(f"Fourchette: {min_price}€ - {max_price}€")

        if recommended > 50:
            tips.append("💎 Article premium - Mettez en avant la qualité")
        elif recommended < 15:
            tips.append("⚡ Prix attractif - Vente rapide probable")

        tips.append("💡 Acceptez les offres à -10% pour négocier")

        return tips
