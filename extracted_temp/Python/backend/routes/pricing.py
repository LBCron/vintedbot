from fastapi import APIRouter
from typing import List
from backend.models.schemas import PriceSimulation, SimulationResult
from backend.services.pricing import pricing_service

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.post("/simulate", response_model=List[SimulationResult])
async def simulate_pricing(simulation: PriceSimulation):
    return pricing_service.simulate_price_trajectory(
        initial_price=simulation.initial_price,
        min_price=simulation.min_price,
        days=simulation.days
    )
