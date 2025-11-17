import os
import httpx
from typing import List, Dict, Optional
from datetime import datetime
from backend.utils.logger import logger

# SECURITY FIX: Default to "false" to prevent accidental bypass in production
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
VINTED_BASE_URL = "https://www.vinted.com/api/v2"


async def fetch_inbox(cookie: str, limit: int = 50) -> List[Dict]:
    """Fetch inbox/conversations from Vinted"""
    
    if MOCK_MODE:
        logger.info("MOCK MODE: Returning fake inbox data")
        return [
            {
                "thread_id": "thread_1",
                "participants": ["user_123", "user_456"],
                "snippet": "Hey, is this item still available?",
                "unread_count": 2,
                "last_message_at": datetime.utcnow().isoformat()
            },
            {
                "thread_id": "thread_2",
                "participants": ["user_123", "user_789"],
                "snippet": "Thanks for the quick response!",
                "unread_count": 0,
                "last_message_at": datetime.utcnow().isoformat()
            }
        ]
    
    # Real implementation
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VINTED_BASE_URL}/inbox/conversations",
                headers={"Cookie": cookie},
                params={"per_page": limit},
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("conversations", [])
            else:
                logger.error(f"Fetch inbox failed: {response.status_code}")
                return []

    # SECURITY FIX Bug #69: Replace generic Exception with specific httpx exceptions
    except httpx.TimeoutException as e:
        logger.error(f"Fetch inbox timeout: {e}")
        return []
    except httpx.ConnectError as e:
        logger.error(f"Fetch inbox connection error: {e}")
        return []
    except (httpx.HTTPError, ValueError, KeyError) as e:
        logger.error(f"Fetch inbox error: {e}")
        return []


async def fetch_thread_messages(cookie: str, thread_id: str, page: int = 1) -> List[Dict]:
    """Fetch messages for a specific thread"""
    
    if MOCK_MODE:
        logger.info(f"MOCK MODE: Returning fake messages for thread {thread_id}")
        return [
            {
                "id": 1,
                "sender": "user_456",
                "body": "Hey, is this item still available?",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": 2,
                "sender": "me",
                "body": "Yes, it's still available!",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    # Real implementation
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VINTED_BASE_URL}/inbox/conversations/{thread_id}/messages",
                headers={"Cookie": cookie},
                params={"page": page},
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [])
            else:
                logger.error(f"Fetch thread messages failed: {response.status_code}")
                return []

    # SECURITY FIX Bug #69: Replace generic Exception with specific httpx exceptions
    except httpx.TimeoutException as e:
        logger.error(f"Fetch thread messages timeout: {e}")
        return []
    except httpx.ConnectError as e:
        logger.error(f"Fetch thread messages connection error: {e}")
        return []
    except (httpx.HTTPError, ValueError, KeyError) as e:
        logger.error(f"Fetch thread messages error: {e}")
        return []


async def prepare_publish_payload(item_data: Dict) -> Dict:
    """Prepare payload for publishing an item"""
    
    if MOCK_MODE:
        logger.info("MOCK MODE: Returning mock publish payload")
        return {
            "title": item_data.get("title", "Mock Item"),
            "price": item_data.get("price", 10.0),
            "description": item_data.get("description", "Mock description"),
            "photos": item_data.get("photos", [])
        }
    
    # Real implementation would format the payload according to Vinted's API
    return {
        "title": item_data.get("title"),
        "price": item_data.get("price"),
        "description": item_data.get("description"),
        "brand_id": item_data.get("brand_id"),
        "size_id": item_data.get("size_id"),
        "catalog_id": item_data.get("catalog_id"),
        "color_ids": item_data.get("color_ids", []),
        "photo_ids": item_data.get("photo_ids", [])
    }


async def validate_session_cookie(cookie: str) -> bool:
    """Validate if session cookie is still valid"""
    
    if MOCK_MODE:
        return True
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VINTED_BASE_URL}/users/current",
                headers={"Cookie": cookie},
                timeout=10.0
            )
            return response.status_code == 200

    # SECURITY FIX Bug #69: Replace generic Exception with specific httpx exceptions
    except httpx.TimeoutException as e:
        logger.error(f"Cookie validation timeout: {e}")
        return False
    except httpx.ConnectError as e:
        logger.error(f"Cookie validation connection error: {e}")
        return False
    except httpx.HTTPError as e:
        logger.error(f"Cookie validation error: {e}")
        return False
