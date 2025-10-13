from typing import List
from collections import Counter
from datetime import datetime
from backend.models.schemas import Item, StatsResponse


class StatsService:
    def calculate_stats(self, items: List[Item]) -> StatsResponse:
        if not items:
            return StatsResponse(
                total_items=0,
                total_value=0.0,
                avg_price=0.0,
                top_brands=[],
                duplicates_detected=0,
                avg_days_since_creation=0.0
            )
        
        total_items = len(items)
        total_value = sum(item.price for item in items)
        avg_price = total_value / total_items if total_items > 0 else 0.0
        
        brands = [item.brand for item in items if item.brand]
        brand_counts = Counter(brands)
        top_brands = [brand for brand, _ in brand_counts.most_common(5)]
        
        duplicates_detected = sum(1 for item in items if item.possible_duplicate)
        
        now = datetime.now()
        days_since_creation = [
            (now - item.created_at).days 
            for item in items 
            if isinstance(item.created_at, datetime)
        ]
        avg_days = sum(days_since_creation) / len(days_since_creation) if days_since_creation else 0.0
        
        return StatsResponse(
            total_items=total_items,
            total_value=round(total_value, 2),
            avg_price=round(avg_price, 2),
            top_brands=top_brands,
            duplicates_detected=duplicates_detected,
            avg_days_since_creation=round(avg_days, 2)
        )


stats_service = StatsService()
