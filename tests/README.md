# VintedBot Test Suite

Enterprise-grade test suite with 80%+ coverage target.

## Quick Start

```bash
# Install test dependencies
pip install -r backend/requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/services/test_stripe_service.py

# Run specific test
pytest tests/unit/services/test_stripe_service.py::TestStripeService::test_create_checkout_session_success
```

## Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── services/           # Service layer tests
│   │   ├── test_stripe_service.py (12 tests)
│   │   ├── test_webhook_service.py (12 tests)
│   │   └── test_ml_pricing_service.py (14 tests)
│   └── routers/            # API router tests
│       ├── test_payments_router.py (5 tests)
│       └── test_admin_router.py (8 tests)
├── integration/            # Integration tests
└── e2e/                    # End-to-end tests
```

## Current Coverage

**51 Unit Tests** covering critical paths:
- ✅ Stripe payment flows
- ✅ Webhook delivery & SSRF protection
- ✅ ML price prediction & validation
- ✅ Payment API endpoints
- ✅ Admin API & SQL injection protection

**Target:** 80%+ coverage

## Test Categories

### Security Tests

Critical security tests included:
- SSRF protection (webhooks)
- SQL injection prevention (admin router)
- Input validation (all services)
- Output sanitization (ML service)

Run security tests only:
```bash
pytest -m security
```

### Performance Tests

TODO: Add performance/load tests

### Integration Tests

TODO: Add integration tests for:
- Complete Stripe payment flow
- Webhook end-to-end delivery
- Database migrations

## CI/CD Integration

Tests run automatically on:
- Every commit (GitHub Actions)
- Pull requests
- Before deployment

## Writing Tests

### Example Test

```python
import pytest
from backend.services.my_service import my_service

class TestMyService:
    @pytest.mark.asyncio
    async def test_my_function(self, mock_db_pool):
        """Test description"""
        result = await my_service.my_function()
        
        assert result is not None
        assert result["success"] is True
```

### Fixtures

Common fixtures available in `conftest.py`:
- `mock_db_pool` - Mock database connection
- `mock_user` - Mock user object
- `mock_admin_user` - Mock admin user
- `mock_stripe` - Mock Stripe API
- `mock_httpx_client` - Mock HTTP client

## Troubleshooting

**Tests fail with database errors:**
```bash
# Set test database URL
export DATABASE_URL="postgresql://test:test@localhost/vintedbot_test"
```

**Import errors:**
```bash
# Make sure backend is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

**Slow tests:**
```bash
# Skip slow tests
pytest -m "not slow"
```
