"""
Comprehensive Test Suite for Vinted API Client
Tests all HTTP API functions in realistic scenarios
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.vinted_api_client import VintedAPIClient
from backend.core.session import VintedSession
from loguru import logger


async def test_bump_item():
    """Test bumping an item"""
    logger.info("🧪 TEST: Bump Item")

    # Create mock session (replace with real session for actual testing)
    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        # Test with a sample item ID (replace with real ID)
        success, error = await client.bump_item("123456789")

        if success:
            logger.success("✅ Bump test PASSED")
        else:
            logger.warning(f"⚠️ Bump test expected behavior: {error}")

    return success


async def test_follow_unfollow():
    """Test following and unfollowing a user"""
    logger.info("🧪 TEST: Follow/Unfollow User")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        test_user_id = "987654321"  # Replace with real user ID

        # Test follow
        logger.info("Testing follow...")
        follow_success, follow_error = await client.follow_user(test_user_id)

        if follow_success:
            logger.success("✅ Follow test PASSED")
        else:
            logger.warning(f"⚠️ Follow test: {follow_error}")

        # Wait a bit
        await asyncio.sleep(2)

        # Test unfollow
        logger.info("Testing unfollow...")
        unfollow_success, unfollow_error = await client.unfollow_user(test_user_id)

        if unfollow_success:
            logger.success("✅ Unfollow test PASSED")
        else:
            logger.warning(f"⚠️ Unfollow test: {unfollow_error}")

    return follow_success or unfollow_success


async def test_messaging():
    """Test sending messages with typing simulation"""
    logger.info("🧪 TEST: Send Message with Typing Simulation")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        test_conversation_id = "conv_123456"  # Replace with real conversation ID
        test_message = "Bonjour! Est-ce que l'article est toujours disponible?"

        # Test with typing simulation
        logger.info("Testing message with typing simulation...")
        success, error = await client.send_message(
            test_conversation_id,
            test_message,
            simulate_typing=True
        )

        if success:
            logger.success("✅ Messaging test PASSED")
        else:
            logger.warning(f"⚠️ Messaging test: {error}")

    return success


async def test_get_user_info():
    """Test getting user information"""
    logger.info("🧪 TEST: Get User Information")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        # Test getting current user
        logger.info("Testing get current user...")
        success, user_data, error = await client.get_current_user()

        if success:
            logger.success(f"✅ Get user test PASSED - User ID: {user_data.get('id')}")
            logger.info(f"User: {user_data.get('login')} - Items: {user_data.get('item_count')}")
        else:
            logger.warning(f"⚠️ Get user test: {error}")

    return success


async def test_get_items():
    """Test getting user's items"""
    logger.info("🧪 TEST: Get User Items")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        # First get current user ID
        success, user_data, error = await client.get_current_user()

        if not success:
            logger.error(f"❌ Cannot get user ID: {error}")
            return False

        user_id = user_data.get('id')

        # Get user's items
        logger.info(f"Testing get items for user {user_id}...")
        success, items, error = await client.get_items(user_id)

        if success:
            logger.success(f"✅ Get items test PASSED - Found {len(items)} items")

            # Show first 3 items
            for i, item in enumerate(items[:3]):
                logger.info(f"  Item {i+1}: {item.get('title')} - {item.get('price')}€")
        else:
            logger.warning(f"⚠️ Get items test: {error}")

    return success


async def test_search():
    """Test search functionality"""
    logger.info("🧪 TEST: Search Items and Users")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        # Test item search
        logger.info("Testing item search...")
        success, items, error = await client.search_items(
            query="t-shirt",
            price_from=5.0,
            price_to=20.0,
            per_page=5
        )

        if success:
            logger.success(f"✅ Item search test PASSED - Found {len(items)} items")
            for i, item in enumerate(items[:3]):
                logger.info(f"  {i+1}. {item.get('title')} - {item.get('price')}€")
        else:
            logger.warning(f"⚠️ Item search test: {error}")

        # Test user search
        logger.info("Testing user search...")
        success, users, error = await client.search_users(
            query="vintage",
            per_page=5
        )

        if success:
            logger.success(f"✅ User search test PASSED - Found {len(users)} users")
            for i, user in enumerate(users[:3]):
                logger.info(f"  {i+1}. {user.get('login')} - {user.get('item_count')} items")
        else:
            logger.warning(f"⚠️ User search test: {error}")

    return success


async def test_like_unlike():
    """Test liking and unliking items"""
    logger.info("🧪 TEST: Like/Unlike Items")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        test_item_id = "123456789"  # Replace with real item ID

        # Test like
        logger.info("Testing like...")
        like_success, like_error = await client.like_item(test_item_id)

        if like_success:
            logger.success("✅ Like test PASSED")
        else:
            logger.warning(f"⚠️ Like test: {like_error}")

        # Wait a bit
        await asyncio.sleep(1)

        # Test unlike
        logger.info("Testing unlike...")
        unlike_success, unlike_error = await client.unlike_item(test_item_id)

        if unlike_success:
            logger.success("✅ Unlike test PASSED")
        else:
            logger.warning(f"⚠️ Unlike test: {unlike_error}")

    return like_success or unlike_success


async def test_conversations():
    """Test getting conversations"""
    logger.info("🧪 TEST: Get Conversations")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    async with VintedAPIClient(session) as client:
        logger.info("Testing get conversations...")
        success, conversations, error = await client.get_conversations(per_page=10)

        if success:
            logger.success(f"✅ Get conversations test PASSED - Found {len(conversations)} conversations")

            # Show first 3 conversations
            for i, conv in enumerate(conversations[:3]):
                logger.info(f"  Conversation {i+1}: {conv.get('id')} - Last message: {conv.get('last_message', {}).get('body', 'N/A')[:50]}...")
        else:
            logger.warning(f"⚠️ Get conversations test: {error}")

    return success


async def run_all_tests():
    """Run all tests"""
    logger.info("="*60)
    logger.info("🚀 STARTING VINTED API CLIENT TEST SUITE")
    logger.info("="*60)
    logger.warning("⚠️  NOTE: Replace 'your_cookie_here' with real Vinted session cookie")
    logger.warning("⚠️  NOTE: Replace test IDs with real Vinted item/user/conversation IDs")
    logger.info("="*60)

    tests = [
        ("Get User Info", test_get_user_info),
        ("Get User Items", test_get_items),
        ("Search", test_search),
        ("Conversations", test_conversations),
        ("Bump Item", test_bump_item),
        ("Follow/Unfollow", test_follow_unfollow),
        ("Like/Unlike", test_like_unlike),
        ("Messaging", test_messaging),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info("")
        logger.info("-"*60)
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))

        # Delay between tests
        await asyncio.sleep(1)

    # Summary
    logger.info("")
    logger.info("="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status} - {test_name}")

    logger.info("-"*60)
    logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    logger.info("="*60)


if __name__ == "__main__":
    logger.info("Starting Vinted API Client tests...")
    logger.info("This test suite validates all HTTP API functions")
    logger.info("")

    asyncio.run(run_all_tests())
