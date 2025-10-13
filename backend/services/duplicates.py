from typing import List, Tuple, Optional
from rapidfuzz import fuzz
import imagehash
from PIL import Image
import requests
from io import BytesIO
from backend.models.schemas import Item


class DuplicateDetector:
    def __init__(self, text_threshold: float = 80.0, image_threshold: int = 5):
        self.text_threshold = text_threshold
        self.image_threshold = image_threshold
    
    def check_duplicate_text(self, title: str, existing_items: List[Item]) -> Tuple[bool, Optional[Item]]:
        for item in existing_items:
            similarity = fuzz.ratio(title.lower(), item.title.lower())
            if similarity >= self.text_threshold:
                return True, item
        return False, None
    
    def compute_image_hash(self, image_url: str) -> Optional[str]:
        try:
            if image_url.startswith('http'):
                response = requests.get(image_url, timeout=10)
                img = Image.open(BytesIO(response.content))
            else:
                img = Image.open(image_url)
            
            img_hash = imagehash.phash(img)
            return str(img_hash)
        except Exception as e:
            print(f"Error computing image hash: {e}")
            return None
    
    def check_duplicate_image(self, image_hash: str, existing_items: List[Item]) -> Tuple[bool, Optional[Item]]:
        if not image_hash:
            return False, None
        
        try:
            new_hash = imagehash.hex_to_hash(image_hash)
            for item in existing_items:
                if item.image_hash:
                    existing_hash = imagehash.hex_to_hash(item.image_hash)
                    diff = new_hash - existing_hash
                    if diff <= self.image_threshold:
                        return True, item
        except Exception as e:
            print(f"Error checking image duplicate: {e}")
        
        return False, None
    
    def check_duplicates(self, title: str, image_urls: List[str], existing_items: List[Item]) -> Tuple[bool, Optional[Item]]:
        is_text_dup, text_dup_item = self.check_duplicate_text(title, existing_items)
        if is_text_dup:
            print(f"⚠️ Duplicate detected for \"{title}\"")
            return True, text_dup_item
        
        if image_urls:
            image_hash = self.compute_image_hash(image_urls[0])
            if image_hash:
                is_image_dup, image_dup_item = self.check_duplicate_image(image_hash, existing_items)
                if is_image_dup:
                    print(f"⚠️ Duplicate detected for \"{title}\" (via image)")
                    return True, image_dup_item
        
        return False, None


duplicate_detector = DuplicateDetector()
