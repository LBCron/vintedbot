import json
import os
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import Item, ItemStatus
import uuid


class Database:
    def __init__(self, file_path: str = "backend/data/items.json"):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    def _read(self) -> List[dict]:
        with open(self.file_path, 'r') as f:
            return json.load(f)
    
    def _write(self, items: List[dict]):
        with open(self.file_path, 'w') as f:
            json.dump(items, f, indent=2, default=str)
    
    def get_all(self) -> List[Item]:
        items_data = self._read()
        return [Item(**item) for item in items_data]
    
    def get_by_id(self, item_id: str) -> Optional[Item]:
        items = self.get_all()
        for item in items:
            if item.id == item_id:
                return item
        return None
    
    def create(self, item: Item) -> Item:
        if not item.id:
            item.id = str(uuid.uuid4())
        item.created_at = datetime.now()
        item.updated_at = datetime.now()
        
        items = self._read()
        items.append(item.model_dump(mode='json'))
        self._write(items)
        return item
    
    def update(self, item_id: str, item: Item) -> Optional[Item]:
        items = self._read()
        for i, existing_item in enumerate(items):
            if existing_item['id'] == item_id:
                item.updated_at = datetime.now()
                items[i] = item.model_dump(mode='json')
                self._write(items)
                return item
        return None
    
    def delete(self, item_id: str) -> bool:
        items = self._read()
        new_items = [item for item in items if item['id'] != item_id]
        if len(new_items) < len(items):
            self._write(new_items)
            return True
        return False
    
    def get_by_status(self, status: ItemStatus) -> List[Item]:
        items = self.get_all()
        return [item for item in items if item.status == status]


db = Database()
