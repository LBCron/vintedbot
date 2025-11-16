"""
Market Scraper Service
Scrapes Vinted for competitive pricing and market trends
"""
import httpx
from typing import Dict, List, Optional
from loguru import logger
from bs4 import BeautifulSoup
import re
from datetime import datetime


class MarketScraperService:
    """
    Service for scraping Vinted market data

    Features:
    - Find similar items by category/brand
    - Extract pricing trends
    - Analyze sold vs active listings
    - Calculate market statistics
    """

    def __init__(self):
        self.base_url = "https://www.vinted.fr"
        self.timeout = httpx.Timeout(15.0)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    async def search_similar_items(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        color: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search for similar items on Vinted

        Args:
            category: Item category
            brand: Brand name
            size: Size
            color: Color
            limit: Max results to return

        Returns:
            List of similar items with pricing
        """
        logger.info(f"🔍 Searching Vinted: category={category}, brand={brand}, size={size}")

        # Build search URL
        search_url = f"{self.base_url}/vetements"

        params = {}

        if brand:
            params['brand_ids[]'] = brand  # Would need brand ID mapping
        if category:
            params['catalog_ids[]'] = category  # Would need category ID mapping
        if size:
            params['size_ids[]'] = size
        if color:
            params['color_ids[]'] = color

        params['per_page'] = limit

        try:
            response = await self.client.get(search_url, params=params)

            if response.status_code != 200:
                logger.warning(f"Search failed: {response.status_code}")
                return []

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            items = []

            # Find item cards (Vinted's structure)
            item_cards = soup.find_all('div', {'class': re.compile(r'feed-grid__item')})

            for card in item_cards[:limit]:
                try:
                    item_data = self._parse_item_card(card)
                    if item_data:
                        items.append(item_data)
                except Exception as e:
                    logger.debug(f"Failed to parse item card: {e}")
                    continue

            logger.info(f"✅ Found {len(items)} similar items")
            return items

        except Exception as e:
            logger.error(f"❌ Market scraping error: {e}")
            return []

    def _parse_item_card(self, card) -> Optional[Dict]:
        """
        Parse an item card element

        Args:
            card: BeautifulSoup element

        Returns:
            Item data dict or None
        """
        try:
            # Extract title
            title_elem = card.find('h3') or card.find('div', {'class': 'feed-grid__item-title'})
            title = title_elem.text.strip() if title_elem else None

            # Extract price
            price_elem = card.find('div', {'class': re.compile(r'.*price.*')})
            price_text = price_elem.text.strip() if price_elem else None

            price = None
            if price_text:
                # Extract number from price (e.g., "25,00 €" -> 25.0)
                match = re.search(r'([\d,]+)', price_text)
                if match:
                    price = float(match.group(1).replace(',', '.'))

            # Extract brand
            brand_elem = card.find('div', {'class': re.compile(r'.*brand.*')})
            brand = brand_elem.text.strip() if brand_elem else None

            # Extract size
            size_elem = card.find('div', {'class': re.compile(r'.*size.*')})
            size = size_elem.text.strip() if size_elem else None

            # Extract status (sold or active)
            sold = card.find('div', {'class': re.compile(r'.*sold.*')}) is not None

            # Extract URL
            link_elem = card.find('a')
            url = f"{self.base_url}{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else None

            if not title or price is None:
                return None

            return {
                "title": title,
                "price": price,
                "brand": brand,
                "size": size,
                "sold": sold,
                "url": url,
                "scraped_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None

    async def get_market_statistics(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        size: Optional[str] = None
    ) -> Dict:
        """
        Get market statistics for similar items

        Args:
            category: Item category
            brand: Brand name
            size: Size

        Returns:
            Market statistics
        """
        items = await self.search_similar_items(
            category=category,
            brand=brand,
            size=size,
            limit=100
        )

        if not items:
            return {
                "total_items": 0,
                "avg_price": 0,
                "min_price": 0,
                "max_price": 0,
                "median_price": 0,
                "sold_count": 0,
                "active_count": 0,
                "sell_through_rate": 0
            }

        prices = [item['price'] for item in items if item['price'] is not None]
        sold_items = [item for item in items if item['sold']]
        active_items = [item for item in items if not item['sold']]

        if not prices:
            return {
                "total_items": len(items),
                "avg_price": 0,
                "min_price": 0,
                "max_price": 0,
                "median_price": 0,
                "sold_count": len(sold_items),
                "active_count": len(active_items),
                "sell_through_rate": 0
            }

        # Calculate statistics
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)

        # Median
        sorted_prices = sorted(prices)
        median_price = sorted_prices[len(sorted_prices) // 2]

        # Sell-through rate
        total = len(sold_items) + len(active_items)
        sell_through_rate = (len(sold_items) / total * 100) if total > 0 else 0

        return {
            "total_items": len(items),
            "avg_price": round(avg_price, 2),
            "min_price": round(min_price, 2),
            "max_price": round(max_price, 2),
            "median_price": round(median_price, 2),
            "sold_count": len(sold_items),
            "active_count": len(active_items),
            "sell_through_rate": round(sell_through_rate, 2)
        }

    async def get_price_recommendations(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        condition: Optional[str] = None
    ) -> Dict:
        """
        Get pricing recommendations based on market data

        Args:
            category: Item category
            brand: Brand name
            size: Size
            condition: Item condition

        Returns:
            Price recommendations
        """
        stats = await self.get_market_statistics(
            category=category,
            brand=brand,
            size=size
        )

        if stats['total_items'] == 0:
            return {
                "recommended_price": None,
                "min_price": None,
                "max_price": None,
                "confidence": 0,
                "message": "No market data available"
            }

        # Recommend median price (more stable than average)
        recommended = stats['median_price']

        # Adjust for condition
        if condition:
            condition_multipliers = {
                "neuf_avec_etiquette": 1.2,  # New with tags
                "neuf_sans_etiquette": 1.1,  # New without tags
                "tres_bon_etat": 1.0,  # Very good
                "bon_etat": 0.85,  # Good
                "satisfaisant": 0.7  # Satisfactory
            }

            multiplier = condition_multipliers.get(condition, 1.0)
            recommended = recommended * multiplier

        # Price range
        min_rec = recommended * 0.9
        max_rec = recommended * 1.15

        # Confidence based on sample size
        confidence = min(stats['total_items'] / 50 * 100, 100)

        return {
            "recommended_price": round(recommended, 2),
            "min_price": round(min_rec, 2),
            "max_price": round(max_rec, 2),
            "confidence": round(confidence, 1),
            "market_stats": stats,
            "message": f"Based on {stats['total_items']} similar items"
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
market_scraper = MarketScraperService()
