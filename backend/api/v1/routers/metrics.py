"""
Prometheus metrics endpoint for VintedBot API
Exposes /metrics for Prometheus scraping
"""

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Exposes all metrics registered in backend.core.metrics
    
    Usage:
        curl http://localhost:5000/metrics
    
    Prometheus config:
        scrape_configs:
          - job_name: 'vintedbot'
            static_configs:
              - targets: ['localhost:5000']
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
