"""
Auto-Pricing Intelligence Engine
AI-driven dynamic pricing based on market analysis and demand
"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import statistics
from loguru import logger


class PricingStrategy(Enum):
    QUICK_SALE = "quick_sale"          # Prix compétitif pour vente rapide
    MAXIMIZE_PROFIT = "maximize_profit"  # Prix optimal pour max profit
    MATCH_MARKET = "match_market"      # S'aligner sur le marché
    DYNAMIC = "dynamic"                # Ajustement automatique selon performance


@dataclass
class PriceRecommendation:
    """Recommandation de prix avec confidence"""
    min_price: float
    optimal_price: float
    max_price: float
    confidence: str  # 'low', 'medium', 'high'
    reasoning: List[str]
    market_average: Optional[float]
    competitor_prices: List[float]
    demand_score: float  # 0-100
    estimated_days_to_sell: int

    def to_dict(self) -> Dict:
        return {
            'min_price': round(self.min_price, 2),
            'optimal_price': round(self.optimal_price, 2),
            'max_price': round(self.max_price, 2),
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'market_average': round(self.market_average, 2) if self.market_average else None,
            'competitor_prices': [round(p, 2) for p in self.competitor_prices],
            'demand_score': round(self.demand_score, 1),
            'estimated_days_to_sell': self.estimated_days_to_sell
        }


class PricingEngine:
    """
    Core pricing engine

    Factors considered:
    - Brand premium (Zara, H&M vs luxury brands)
    - Condition (Neuf, Très bon état, etc.)
    - Category demand (trending items)
    - Seasonal factors
    - Competition analysis
    - Historical sell-through rate
    - Time on market
    """

    # Brand multipliers (premium brands get higher prices)
    BRAND_MULTIPLIERS = {
        # Luxury
        'gucci': 2.5, 'prada': 2.3, 'louis vuitton': 2.8, 'chanel': 3.0,
        'hermès': 3.5, 'dior': 2.5, 'balenciaga': 2.2, 'saint laurent': 2.4,

        # Premium
        'maje': 1.8, 'sandro': 1.8, 'ba&sh': 1.7, 'the kooples': 1.6,
        'ted baker': 1.5, 'all saints': 1.5, 'cos': 1.4,

        # Fast fashion premium
        'zara': 1.2, 'mango': 1.2, '& other stories': 1.3,

        # Fast fashion
        'h&m': 1.0, 'uniqlo': 1.0, 'topshop': 1.0, 'bershka': 0.9,
        'pull&bear': 0.9, 'stradivarius': 0.9,

        # Default
        'default': 1.0
    }

    # Condition multipliers
    CONDITION_MULTIPLIERS = {
        'Neuf avec étiquette': 0.95,    # 95% of new price
        'Neuf sans étiquette': 0.85,
        'Très bon état': 0.70,
        'Bon état': 0.50,
        'Satisfaisant': 0.30
    }

    def __init__(self):
        from backend.core.storage import get_store
        self.store = get_store()

    async def get_price_recommendation(
        self,
        brand: str,
        category: str,
        condition: str,
        original_price: Optional[float] = None,
        strategy: PricingStrategy = PricingStrategy.MATCH_MARKET,
        user_id: Optional[str] = None
    ) -> PriceRecommendation:
        """
        Get AI-powered price recommendation

        Process:
        1. Analyze market prices for similar items
        2. Apply brand/condition multipliers
        3. Factor in demand and seasonality
        4. Calculate optimal price range
        5. Provide confidence score and reasoning
        """
        logger.info(f"🔍 Analyzing pricing for {brand} - {category} ({condition})")

        reasoning = []

        # 1. Get brand multiplier
        brand_lower = brand.lower() if brand else 'default'
        brand_multiplier = self.BRAND_MULTIPLIERS.get(brand_lower, 1.0)

        if brand_multiplier > 1.5:
            reasoning.append(f"✨ Premium brand '{brand}' detected (+{int((brand_multiplier-1)*100)}%)")

        # 2. Get condition multiplier
        condition_multiplier = self.CONDITION_MULTIPLIERS.get(
            condition,
            0.60  # Default to "Bon état"
        )
        reasoning.append(f"📦 Condition: {condition} ({int(condition_multiplier*100)}% of new price)")

        # 3. Analyze market prices for this category
        market_prices = await self._get_market_prices(category, brand)

        if market_prices:
            market_avg = statistics.mean(market_prices)
            market_median = statistics.median(market_prices)
            reasoning.append(f"📊 Market average: €{market_avg:.2f} (based on {len(market_prices)} similar items)")
        else:
            # Fallback to estimated base price if no market data
            market_avg = self._estimate_base_price(category, brand)
            market_median = market_avg
            reasoning.append(f"⚠️ Limited market data, using estimated baseline")

        # 4. Calculate base price
        if original_price:
            base_price = original_price * condition_multiplier
            reasoning.append(f"💰 Original price: €{original_price:.2f} → €{base_price:.2f} after condition")
        else:
            base_price = market_avg

        # 5. Apply brand premium
        base_price *= brand_multiplier

        # 6. Analyze demand
        demand_score = await self._calculate_demand_score(category, brand)
        reasoning.append(f"📈 Demand score: {demand_score:.0f}/100")

        # 7. Apply strategy adjustments
        if strategy == PricingStrategy.QUICK_SALE:
            # 10-15% below market for quick sale
            optimal_price = market_median * 0.85
            min_price = market_median * 0.70
            max_price = market_median * 0.95
            reasoning.append("⚡ Quick sale strategy: priced 15% below market")
            days_to_sell = 7

        elif strategy == PricingStrategy.MAXIMIZE_PROFIT:
            # 5-10% above market if demand is high
            if demand_score > 70:
                optimal_price = market_median * 1.05
                max_price = market_median * 1.15
            else:
                optimal_price = market_median
                max_price = market_median * 1.10
            min_price = market_median * 0.90
            reasoning.append("💎 Profit maximization: priced at or above market")
            days_to_sell = 30

        elif strategy == PricingStrategy.MATCH_MARKET:
            # Match market median
            optimal_price = market_median
            min_price = market_median * 0.85
            max_price = market_median * 1.10
            reasoning.append("🎯 Market matching: aligned with competitors")
            days_to_sell = 14

        else:  # DYNAMIC
            # Adaptive based on demand
            if demand_score > 80:
                optimal_price = market_median * 1.05  # High demand = price up
                reasoning.append("🔥 High demand detected: pricing above market")
            elif demand_score < 40:
                optimal_price = market_median * 0.90  # Low demand = price down
                reasoning.append("❄️ Low demand: competitive pricing")
            else:
                optimal_price = market_median
                reasoning.append("⚖️ Moderate demand: market pricing")

            min_price = optimal_price * 0.85
            max_price = optimal_price * 1.15
            days_to_sell = int(30 - (demand_score / 5))  # 10-30 days

        # 8. Determine confidence
        confidence = self._calculate_confidence(len(market_prices), demand_score)

        # 9. Ensure minimum viability (Vinted fees = 5% + €0.70)
        vinted_fee_percent = 0.05
        vinted_fee_fixed = 0.70

        min_viable_price = (vinted_fee_fixed + 1.0) / (1 - vinted_fee_percent)  # At least €1 net

        if min_price < min_viable_price:
            min_price = min_viable_price
            reasoning.append(f"⚠️ Adjusted min price to cover Vinted fees (€{min_viable_price:.2f})")

        # Ensure logical ordering
        min_price = min(min_price, optimal_price * 0.85)
        max_price = max(max_price, optimal_price * 1.15)

        return PriceRecommendation(
            min_price=min_price,
            optimal_price=optimal_price,
            max_price=max_price,
            confidence=confidence,
            reasoning=reasoning,
            market_average=market_avg if market_prices else None,
            competitor_prices=sorted(market_prices[:10]) if market_prices else [],
            demand_score=demand_score,
            estimated_days_to_sell=days_to_sell
        )

    async def _get_market_prices(self, category: str, brand: str) -> List[float]:
        """
        Get market prices for similar items

        TODO: Implement Vinted scraping or use historical data
        For now, return mock data based on patterns
        """
        # Mock implementation - should scrape Vinted or use DB
        # In production, this would query:
        # 1. Historical sold items in same category/brand
        # 2. Current listings from competitors
        # 3. Vinted search results

        # Simulate market prices based on category
        category_lower = category.lower() if category else ''
        brand_lower = brand.lower() if brand else ''

        base_prices = {
            'robe': [15, 18, 20, 22, 25, 28, 30],
            'pull': [12, 15, 18, 20, 22, 25],
            'jean': [20, 25, 28, 30, 35, 40],
            'veste': [30, 35, 40, 45, 50, 55],
            'chaussures': [25, 30, 35, 40, 45, 50, 60],
            't-shirt': [8, 10, 12, 15, 18, 20],
            'sac': [20, 25, 30, 35, 40, 50, 60]
        }

        # Find matching category
        for key, prices in base_prices.items():
            if key in category_lower:
                # Apply brand multiplier
                multiplier = self.BRAND_MULTIPLIERS.get(brand_lower, 1.0)
                return [p * multiplier for p in prices]

        # Default
        return [15.0, 18.0, 20.0, 22.0, 25.0, 28.0, 30.0]

    def _estimate_base_price(self, category: str, brand: str) -> float:
        """Estimate base price when no market data available"""
        # Simple estimation based on category
        category_lower = category.lower() if category else ''

        if 'robe' in category_lower or 'dress' in category_lower:
            base = 22.0
        elif 'jean' in category_lower or 'pantalon' in category_lower:
            base = 25.0
        elif 'veste' in category_lower or 'manteau' in category_lower:
            base = 40.0
        elif 'chaussures' in category_lower or 'shoes' in category_lower:
            base = 35.0
        elif 't-shirt' in category_lower or 'top' in category_lower:
            base = 12.0
        elif 'pull' in category_lower or 'sweater' in category_lower:
            base = 18.0
        elif 'sac' in category_lower or 'bag' in category_lower:
            base = 30.0
        else:
            base = 20.0

        # Apply brand multiplier
        brand_lower = brand.lower() if brand else 'default'
        multiplier = self.BRAND_MULTIPLIERS.get(brand_lower, 1.0)

        return base * multiplier

    async def _calculate_demand_score(self, category: str, brand: str) -> float:
        """
        Calculate demand score (0-100) based on:
        - Category popularity
        - Brand popularity
        - Seasonal factors
        - Recent sales velocity

        TODO: Implement with real data from Vinted trends
        """
        score = 50.0  # Base score

        # Category popularity
        category_lower = category.lower() if category else ''
        popular_categories = ['robe', 'jean', 'basket', 'pull', 'veste']

        if any(cat in category_lower for cat in popular_categories):
            score += 15

        # Brand popularity
        brand_lower = brand.lower() if brand else ''
        if brand_lower in ['zara', 'h&m', 'mango', 'nike', 'adidas']:
            score += 10
        elif brand_lower in self.BRAND_MULTIPLIERS and self.BRAND_MULTIPLIERS[brand_lower] > 2.0:
            score += 20  # Luxury brands = high demand

        # Seasonal factors (simplified)
        month = datetime.now().month

        # Summer items (June-August)
        if 6 <= month <= 8:
            if any(word in category_lower for word in ['robe', 't-shirt', 'short', 'sandale']):
                score += 15

        # Winter items (November-February)
        elif month >= 11 or month <= 2:
            if any(word in category_lower for word in ['manteau', 'pull', 'veste', 'boots']):
                score += 15

        return min(100.0, max(0.0, score))

    def _calculate_confidence(self, market_data_points: int, demand_score: float) -> str:
        """Calculate confidence level based on data availability"""
        if market_data_points >= 10 and demand_score > 60:
            return 'high'
        elif market_data_points >= 5 or demand_score > 40:
            return 'medium'
        else:
            return 'low'

    async def enable_dynamic_pricing(
        self,
        item_id: str,
        min_acceptable_price: float,
        adjustment_frequency_days: int = 7
    ):
        """
        Enable dynamic pricing for an item

        Auto-adjusts price every X days based on performance:
        - If many views but no likes → price is too high
        - If many likes but no sale → slightly reduce price
        - If no views → significantly reduce price or improve listing
        """
        # TODO: Implement in DB
        # Store dynamic pricing settings for item
        # Create cron job to adjust prices
        logger.info(f"📊 Dynamic pricing enabled for item {item_id}")
        return {
            'enabled': True,
            'min_price': min_acceptable_price,
            'adjustment_frequency': adjustment_frequency_days,
            'next_adjustment': (datetime.now() + timedelta(days=adjustment_frequency_days)).isoformat()
        }
