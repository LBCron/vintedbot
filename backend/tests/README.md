# Vinted API Test Suite

Comprehensive test suite for validating all HTTP API functions in realistic scenarios.

## 🧪 Tests Included

1. **Get User Info** - Validates fetching current user profile
2. **Get User Items** - Tests retrieving user's listings
3. **Search** - Tests item and user search functionality
4. **Conversations** - Validates conversation retrieval
5. **Bump Item** - Tests item promotion to top of search
6. **Follow/Unfollow** - Tests user following/unfollowing
7. **Like/Unlike** - Tests item favoriting
8. **Messaging** - Tests sending messages with typing simulation

## 🚀 Running Tests

### Prerequisites

You need a valid Vinted session cookie. To obtain it:

1. Login to Vinted.fr in your browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies → https://www.vinted.fr
4. Copy the entire cookie string (all cookies combined)

### Running the Test Suite

```bash
# From project root
cd backend
python tests/test_vinted_api.py
```

### Configuration

Edit `test_vinted_api.py` and replace:

```python
session = VintedSession(
    cookie="your_cookie_here",  # ← Replace with real cookie
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)
```

Also update test IDs:
- `test_item_id` - Real Vinted item ID
- `test_user_id` - Real Vinted user ID
- `test_conversation_id` - Real conversation ID

## 📊 Expected Output

```
============================================================
🚀 STARTING VINTED API CLIENT TEST SUITE
============================================================
⚠️  NOTE: Replace 'your_cookie_here' with real Vinted session cookie
============================================================

------------------------------------------------------------
🧪 TEST: Get User Information
Testing get current user...
✅ Get user test PASSED - User ID: 12345678
User: johndoe - Items: 42

------------------------------------------------------------
🧪 TEST: Get User Items
Testing get items for user 12345678...
✅ Get items test PASSED - Found 42 items
  Item 1: Nike Air Max - 45.00€
  Item 2: Adidas T-Shirt - 15.00€
  Item 3: Vintage Jacket - 60.00€

...

============================================================
📊 TEST SUMMARY
============================================================
✅ PASSED - Get User Info
✅ PASSED - Get User Items
✅ PASSED - Search
✅ PASSED - Conversations
⚠️ FAILED - Bump Item (expected - requires free bumps)
✅ PASSED - Follow/Unfollow
✅ PASSED - Like/Unlike
✅ PASSED - Messaging
------------------------------------------------------------
Total: 7/8 tests passed (87.5%)
============================================================
```

## ⚠️ Important Notes

### Rate Limiting

- Tests include delays between API calls (1-2 seconds)
- Don't run tests too frequently to avoid rate limiting
- Vinted may throttle requests if they detect unusual activity

### Expected Failures

Some tests may fail with expected errors:

- **Bump Item**: May fail with "Free bumps exhausted" (HTTP 402) - this is normal
- **Follow User**: May fail with "Already following" (HTTP 422) - this is normal
- **Like Item**: May fail with "Already liked" (HTTP 422) - this is normal

These are NOT bugs - they indicate the API is working correctly.

### Authentication

If all tests fail with authentication errors:
1. Check that your cookie is valid and not expired
2. Ensure cookie includes all necessary values (session, csrf token, etc.)
3. Try logging out and logging back in to get a fresh cookie

## 🔧 Debugging

### Enable Verbose Logging

The test suite uses `loguru` for logging. To see more details:

```python
logger.add("test_results.log", level="DEBUG")
```

### Test Individual Functions

You can run individual tests by commenting out others in `run_all_tests()`:

```python
tests = [
    ("Get User Info", test_get_user_info),  # Only run this test
    # ("Get User Items", test_get_items),  # Commented out
    # ... rest commented
]
```

## 📈 Performance Benchmarks

Expected performance (with HTTP API):

- Get User Info: ~300-500ms
- Get Items: ~400-600ms
- Search: ~500-800ms
- Bump Item: ~400-600ms
- Follow/Unfollow: ~300-500ms
- Send Message: ~500ms + typing simulation time

**Note**: Typing simulation adds 50-150ms per character to message sending (realistic human-like behavior).

## 🛡️ Security

- Never commit your Vinted cookie to version control
- Cookies should be stored securely (use `.env` files with `.gitignore`)
- Rotate cookies regularly for security
- Use test accounts for development, not production accounts

## 📝 Adding New Tests

To add a new test:

1. Create a new async function following the pattern:

```python
async def test_my_feature():
    """Test my new feature"""
    logger.info("🧪 TEST: My Feature")

    session = VintedSession(
        cookie="your_cookie_here",
        user_agent="..."
    )

    async with VintedAPIClient(session) as client:
        # Your test logic here
        success, data, error = await client.my_function()

        if success:
            logger.success("✅ Test PASSED")
        else:
            logger.warning(f"⚠️ Test: {error}")

    return success
```

2. Add it to the `tests` list in `run_all_tests()`:

```python
tests = [
    # ... existing tests
    ("My Feature", test_my_feature),
]
```

## 🤝 Contributing

When adding new API functions to `VintedAPIClient`, always add corresponding tests to this suite.

## 📚 Related Documentation

- See `backend/core/vinted_api_client.py` for API client implementation
- See `backend/api/v1/routers/automation.py` for automation endpoints
- See main README.md for overall project documentation
