from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.schemas import Item, ItemStatus
from backend.models.db import db

router = APIRouter(prefix="/listings", tags=["Listings"])


@router.get("/all", response_model=List[Item])
async def get_all_listings():
    return db.get_all()


@router.get("/{item_id}", response_model=Item)
async def get_listing(item_id: str):
    item = db.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=Item)
async def update_listing(item_id: str, item: Item):
    updated_item = db.update(item_id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@router.delete("/{item_id}")
async def delete_listing(item_id: str):
    success = db.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}


@router.get("/status/{status}", response_model=List[Item])
async def get_listings_by_status(status: ItemStatus):
    return db.get_by_status(status)
