"""
Vinted HTTP API Client
Direct HTTP communication with Vinted API (faster and more reliable than Playwright)
"""
import httpx
import random
import time
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
from backend.core.session import VintedSession


class VintedAPIClient:
    """
    HTTP-based Vinted API client
    Uses direct API calls instead of browser automation
    """

    BASE_URL = "https://www.vinted.com"
    API_BASE = "https://www.vinted.com/api/v2"

    def __init__(self, session: VintedSession):
        """
        Initialize API client with session

        Args:
            session: VintedSession with cookie and user_agent
        """
        self.session = session
        self.client = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=30.0,
            follow_redirects=True
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with session cookies"""
        return {
            'User-Agent': self.session.user_agent,
            'Cookie': self.session.cookie,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.vinted.com',
            'Referer': 'https://www.vinted.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Random human-like delay"""
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)

    # ======================
    # BUMP (Item Promotion)
    # ======================

    async def bump_item(self, item_id: str) -> Tuple[bool, Optional[str]]:
        """
        Bump (promote) an item to bring it to top of search results
        Vinted API endpoint: POST /api/v2/items/{item_id}/push_up

        Args:
            item_id: Item ID to bump

        Returns:
            (success, error_message)
        """
        try:
            logger.info(f"[PROCESS] Bumping item {item_id}...")

            # Endpoint for bumping items
            url = f"{self.API_BASE}/items/{item_id}/push_up"

            response = await self.client.post(url)

            if response.status_code == 200:
                logger.info(f"[OK] Successfully bumped item {item_id}")
                return (True, None)
            elif response.status_code == 402:
                # Payment required - free bumps exhausted
                return (False, "Free bumps exhausted - payment required")
            elif response.status_code == 429:
                return (False, "Rate limited - too many bumps")
            else:
                logger.error(f"[ERROR] Bump failed: {response.status_code} - {response.text}")
                return (False, f"Bump failed: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"[ERROR] Bump error: {e}")
            return (False, f"Bump error: {str(e)}")

    async def get_items(self, user_id: str, per_page: int = 20) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Get user's items/listings

        Args:
            user_id: Vinted user ID
            per_page: Items per page

        Returns:
            (success, items_list, error_message)
        """
        try:
            url = f"{self.API_BASE}/users/{user_id}/items"
            params = {"per_page": per_page}

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                return (True, items, None)
            else:
                return (False, None, f"Failed to get items: HTTP {response.status_code}")

        except Exception as e:
            return (False, None, f"Get items error: {str(e)}")

    # ======================
    # FOLLOW / UNFOLLOW
    # ======================

    async def follow_user(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Follow a Vinted user
        Vinted API endpoint: POST /api/v2/users/{user_id}/follow

        Args:
            user_id: Vinted user ID to follow

        Returns:
            (success, error_message)
        """
        try:
            logger.info(f"👥 Following user {user_id}...")

            url = f"{self.API_BASE}/users/{user_id}/follow"

            response = await self.client.post(url)

            if response.status_code == 200:
                logger.info(f"[OK] Successfully followed user {user_id}")
                return (True, None)
            elif response.status_code == 422:
                return (False, "Already following this user")
            elif response.status_code == 429:
                return (False, "Rate limited - too many follows")
            else:
                logger.error(f"[ERROR] Follow failed: {response.status_code}")
                return (False, f"Follow failed: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"[ERROR] Follow error: {e}")
            return (False, f"Follow error: {str(e)}")

    async def unfollow_user(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Unfollow a Vinted user
        Vinted API endpoint: DELETE /api/v2/users/{user_id}/follow

        Args:
            user_id: Vinted user ID to unfollow

        Returns:
            (success, error_message)
        """
        try:
            logger.info(f"👋 Unfollowing user {user_id}...")

            url = f"{self.API_BASE}/users/{user_id}/follow"

            response = await self.client.delete(url)

            if response.status_code == 200:
                logger.info(f"[OK] Successfully unfollowed user {user_id}")
                return (True, None)
            elif response.status_code == 422:
                return (False, "Not following this user")
            else:
                logger.error(f"[ERROR] Unfollow failed: {response.status_code}")
                return (False, f"Unfollow failed: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"[ERROR] Unfollow error: {e}")
            return (False, f"Unfollow error: {str(e)}")

    async def get_followers(self, user_id: str, page: int = 1) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Get user's followers

        Args:
            user_id: Vinted user ID
            page: Page number

        Returns:
            (success, followers_list, error_message)
        """
        try:
            url = f"{self.API_BASE}/users/{user_id}/followers"
            params = {"page": page, "per_page": 20}

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                followers = data.get('users', [])
                return (True, followers, None)
            else:
                return (False, None, f"Failed to get followers: HTTP {response.status_code}")

        except Exception as e:
            return (False, None, f"Get followers error: {str(e)}")

    # ======================
    # MESSAGES
    # ======================

    async def send_message(
        self,
        conversation_id: str,
        message: str,
        simulate_typing: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a message in a conversation
        Vinted API endpoint: POST /api/v2/conversations/{conversation_id}/messages

        Args:
            conversation_id: Conversation ID
            message: Message text
            simulate_typing: Simulate human typing delay

        Returns:
            (success, error_message)
        """
        try:
            logger.info(f"💬 Sending message to conversation {conversation_id}...")

            # Simulate typing if requested
            if simulate_typing:
                # Calculate typing time based on message length (50-150ms per character)
                typing_ms = len(message) * random.randint(50, 150)
                await asyncio.sleep(typing_ms / 1000)

            url = f"{self.API_BASE}/conversations/{conversation_id}/messages"

            payload = {
                "body": message
            }

            response = await self.client.post(url, json=payload)

            if response.status_code == 200:
                logger.info(f"[OK] Message sent successfully")
                return (True, None)
            elif response.status_code == 429:
                return (False, "Rate limited - too many messages")
            else:
                logger.error(f"[ERROR] Send message failed: {response.status_code}")
                return (False, f"Send failed: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"[ERROR] Send message error: {e}")
            return (False, f"Send error: {str(e)}")

    async def get_conversations(self, page: int = 1, per_page: int = 20) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Get user's conversations

        Args:
            page: Page number
            per_page: Conversations per page

        Returns:
            (success, conversations_list, error_message)
        """
        try:
            url = f"{self.API_BASE}/conversations"
            params = {"page": page, "per_page": per_page}

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                return (True, conversations, None)
            else:
                return (False, None, f"Failed to get conversations: HTTP {response.status_code}")

        except Exception as e:
            return (False, None, f"Get conversations error: {str(e)}")

    async def mark_conversation_read(self, conversation_id: str) -> Tuple[bool, Optional[str]]:
        """
        Mark conversation as read

        Args:
            conversation_id: Conversation ID

        Returns:
            (success, error_message)
        """
        try:
            url = f"{self.API_BASE}/conversations/{conversation_id}/read"

            response = await self.client.post(url)

            if response.status_code == 200:
                return (True, None)
            else:
                return (False, f"Mark read failed: HTTP {response.status_code}")

        except Exception as e:
            return (False, f"Mark read error: {str(e)}")

    # ======================
    # USER PROFILE
    # ======================

    async def get_current_user(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Get current authenticated user info

        Returns:
            (success, user_data, error_message)
        """
        try:
            url = f"{self.API_BASE}/users/current"

            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                user = data.get('user', {})
                return (True, user, None)
            else:
                return (False, None, f"Failed to get user: HTTP {response.status_code}")

        except Exception as e:
            return (False, None, f"Get user error: {str(e)}")

    async def get_user(self, user_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Get user profile by ID

        Args:
            user_id: Vinted user ID

        Returns:
            (success, user_data, error_message)
        """
        try:
            url = f"{self.API_BASE}/users/{user_id}"

            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                user = data.get('user', {})
                return (True, user, None)
            else:
                return (False, None, f"Failed to get user: HTTP {response.status_code}")

        except Exception as e:
            return (False, None, f"Get user error: {str(e)}")

    # ======================
    # SEARCH
    # ======================

    async def search_users(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Search for users

        Args:
            query: Search query
            page: Page number
            per_page: Results per page

        Returns:
            (success, users_list, error_message)
        """
        try:
            url = f"{self.API_BASE}/users/search"
            params = {
                "search_text": query,
                "page": page,
                "per_page": per_page
            }

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                return (True, users, None)
            else:
                return (False, None, f"Search failed: HTTP {response.status_code}")

        except Exception as e:
            return (False, None, f"Search error: {str(e)}")

    async def search_items(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        size_id: Optional[int] = None,
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Search for items with filters

        Args:
            query: Search query
            category_id: Category ID filter
            brand_id: Brand ID filter
            size_id: Size ID filter
            price_from: Min price filter
            price_to: Max price filter
            page: Page number
            per_page: Results per page

        Returns:
            (success, items_list, error_message)
        """
        try:
            url = f"{self.API_BASE}/catalog/items"

            params = {
                "page": page,
                "per_page": per_page
            }

            if query:
                params["search_text"] = query
            if category_id:
                params["catalog_ids[]"] = category_id
            if brand_id:
                params["brand_ids[]"] = brand_id
            if size_id:
                params["size_ids[]"] = size_id
            if price_from is not None:
                params["price_from"] = price_from
            if price_to is not None:
                params["price_to"] = price_to

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                return (True, items, None)
            else:
                return (False, None, f"Search failed: HTTP {response.status_code}")

        except Exception as e:
            return (False, None, f"Search error: {str(e)}")

    # ======================
    # LIKES / FAVORITES
    # ======================

    async def like_item(self, item_id: str) -> Tuple[bool, Optional[str]]:
        """
        Like (favorite) an item

        Args:
            item_id: Item ID to like

        Returns:
            (success, error_message)
        """
        try:
            logger.info(f"❤️ Liking item {item_id}...")

            url = f"{self.API_BASE}/items/{item_id}/like"

            response = await self.client.post(url)

            if response.status_code == 200:
                logger.info(f"[OK] Successfully liked item {item_id}")
                return (True, None)
            elif response.status_code == 422:
                return (False, "Already liked this item")
            else:
                return (False, f"Like failed: HTTP {response.status_code}")

        except Exception as e:
            return (False, f"Like error: {str(e)}")

    async def unlike_item(self, item_id: str) -> Tuple[bool, Optional[str]]:
        """
        Unlike (unfavorite) an item

        Args:
            item_id: Item ID to unlike

        Returns:
            (success, error_message)
        """
        try:
            url = f"{self.API_BASE}/items/{item_id}/like"

            response = await self.client.delete(url)

            if response.status_code == 200:
                return (True, None)
            else:
                return (False, f"Unlike failed: HTTP {response.status_code}")

        except Exception as e:
            return (False, f"Unlike error: {str(e)}")

    # ======================
    # LISTING MANAGEMENT (Sprint 1 Feature 1B)
    # ======================

    async def get_listing(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific listing

        Args:
            item_id: Vinted item ID

        Returns:
            Listing data dict or None if not found
        """
        try:
            logger.info(f"[API] Fetching listing {item_id}...")

            url = f"{self.API_BASE}/items/{item_id}"

            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                item = data.get('item', {})
                logger.info(f"[OK] Successfully fetched listing {item_id}")
                return item
            elif response.status_code == 404:
                logger.warning(f"Listing {item_id} not found (404)")
                return None
            else:
                logger.error(f"Failed to fetch listing {item_id}: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching listing {item_id}: {e}")
            return None

    async def update_listing(
        self,
        item_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update a listing on Vinted

        Args:
            item_id: Vinted item ID
            update_data: Dict with fields to update (title, description, price, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[API] Updating listing {item_id}...")

            url = f"{self.API_BASE}/items/{item_id}"

            # Build update payload
            payload = {}

            if 'title' in update_data:
                payload['title'] = update_data['title']
            if 'description' in update_data:
                payload['description'] = update_data['description']
            if 'price' in update_data:
                payload['price'] = update_data['price']
            if 'brand' in update_data:
                payload['brand_title'] = update_data['brand']
            if 'size' in update_data:
                payload['size_title'] = update_data['size']
            if 'condition' in update_data:
                payload['status'] = update_data['condition']
            if 'color' in update_data:
                payload['color'] = update_data['color']

            # Human delay before update
            await self.human_delay(500, 1500)

            response = await self.client.put(url, json=payload)

            if response.status_code == 200:
                logger.info(f"[OK] Successfully updated listing {item_id}")
                return True
            elif response.status_code == 403:
                logger.error(f"Forbidden to update listing {item_id} (not owner?)")
                return False
            elif response.status_code == 404:
                logger.error(f"Listing {item_id} not found")
                return False
            else:
                logger.error(f"Failed to update listing {item_id}: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error updating listing {item_id}: {e}")
            return False

    async def get_user_listings(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 100
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Get all listings for a user (authenticated user or specific user_id)

        Args:
            user_id: User ID (None = authenticated user)
            status: Filter by status ('active', 'sold', 'inactive')
            per_page: Results per page

        Returns:
            (success, items_list, error_message)
        """
        try:
            if user_id:
                url = f"{self.API_BASE}/users/{user_id}/items"
            else:
                url = f"{self.API_BASE}/items"  # Authenticated user's items

            params = {
                "per_page": per_page
            }

            if status:
                params["status"] = status

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                logger.info(f"[OK] Fetched {len(items)} listings")
                return (True, items, None)
            else:
                return (False, None, f"Failed to fetch listings: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"Error fetching user listings: {e}")
            return (False, None, f"Error: {str(e)}")

