from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import csv
from io import StringIO

from backend.db import get_all_listings, get_listing, get_db_session
from backend.models import Listing, ListingStatus
from backend.utils.logger import logger

router = APIRouter(prefix="/listings", tags=["listings"])


class ListingCreate(BaseModel):
    title: str
    description: str
    brand: Optional[str] = None
    price: float
    photos: list[str] = []


@router.get("")
async def list_listings(limit: int = 100, offset: int = 0):
    """Get all listings"""
    listings = get_all_listings(limit=limit, offset=offset)
    
    return {
        "listings": [
            {
                "id": l.id,
                "title": l.title,
                "description": l.description,
                "brand": l.brand,
                "price": l.price,
                "status": l.status,
                "photos": l.photos,
                "created_at": l.created_at,
                "updated_at": l.updated_at
            }
            for l in listings
        ],
        "total": len(listings)
    }


@router.get("/{listing_id}")
async def get_listing_by_id(listing_id: int):
    """Get single listing"""
    listing = get_listing(listing_id)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "brand": listing.brand,
        "price": listing.price,
        "status": listing.status,
        "photos": listing.photos,
        "created_at": listing.created_at,
        "updated_at": listing.updated_at
    }


@router.post("")
async def create_listing(data: ListingCreate):
    """Create new listing"""
    with get_db_session() as db:
        listing = Listing(
            title=data.title,
            description=data.description,
            brand=data.brand,
            price=data.price,
            photos=data.photos
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        
        logger.info(f"✨ Listing {listing.id} created: {listing.title}")
        
        return {
            "id": listing.id,
            "title": listing.title,
            "status": listing.status
        }


@router.get("/export/csv")
async def export_csv():
    """Export listings as CSV"""
    listings = get_all_listings(limit=10000)
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "title", "brand", "price", "status", "created_at"])
    writer.writeheader()
    
    for l in listings:
        writer.writerow({
            "id": l.id,
            "title": l.title,
            "brand": l.brand or "",
            "price": l.price,
            "status": l.status,
            "created_at": l.created_at
        })
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=listings.csv"}
    )


@router.get("/export/json")
async def export_json():
    """Export listings as JSON"""
    listings = get_all_listings(limit=10000)
    
    data = [
        {
            "id": l.id,
            "title": l.title,
            "description": l.description,
            "brand": l.brand,
            "price": l.price,
            "status": l.status,
            "photos": l.photos,
            "created_at": str(l.created_at),
            "updated_at": str(l.updated_at)
        }
        for l in listings
    ]
    
    return StreamingResponse(
        iter([json.dumps(data, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=listings.json"}
    )
