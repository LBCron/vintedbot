from pydantic import BaseModel
from typing import List, Optional


class MediaOut(BaseModel):
    id: int
    url: str
    width: int
    height: int
    mime: str


class DraftPhotoOut(BaseModel):
    media: MediaOut
    order_index: int


class DraftOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    price_suggested: Optional[float] = None
    photos: List[DraftPhotoOut]
