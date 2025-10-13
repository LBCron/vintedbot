from typing import List
from datetime import datetime
from backend.models.schemas import Item, PriceHistory, SimulationResult


class PricingService:
    def __init__(self, daily_drop_percentage: float = 5.0):
        self.daily_drop_percentage = daily_drop_percentage
    
    def apply_price_drop(self, item: Item) -> Item:
        if item.price_suggestion and item.price > item.price_suggestion.min:
            old_price = item.price
            new_price = item.price * (1 - self.daily_drop_percentage / 100)
            
            if new_price < item.price_suggestion.min:
                new_price = item.price_suggestion.min
            
            new_price = round(new_price, 2)
            
            if new_price != old_price:
                item.price_history.append(
                    PriceHistory(
                        date=datetime.now(),
                        old_price=old_price,
                        new_price=new_price,
                        reason="automatic_drop"
                    )
                )
                item.price = new_price
                item.updated_at = datetime.now()
                print(f"💸 Price drop: {item.title} from {old_price}€ → {new_price}€")
        
        return item
    
    def simulate_price_trajectory(self, initial_price: float, min_price: float, days: int) -> List[SimulationResult]:
        results = []
        current_price = initial_price
        
        for day in range(days + 1):
            results.append(
                SimulationResult(
                    day=day,
                    price=round(current_price, 2),
                    drop_percentage=0.0 if day == 0 else self.daily_drop_percentage
                )
            )
            
            if day < days:
                new_price = current_price * (1 - self.daily_drop_percentage / 100)
                if new_price < min_price:
                    current_price = min_price
                else:
                    current_price = new_price
        
        return results


pricing_service = PricingService()
