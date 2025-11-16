# 🔒 SECURITY & BUG AUDIT REPORT - VINTEDBOT

**Date:** 2025-11-16
**Auditor:** Claude Code Security Analysis
**Scope:** All new features from MEGA-PROMPT ULTIME session
**Status:** 🔴 **CRITICAL ISSUES FOUND - DO NOT DEPLOY YET**

---

## 📋 EXECUTIVE SUMMARY

**Total Issues Found: 28**
- 🔴 **Critical:** 8
- 🟠 **High:** 7
- 🟡 **Medium:** 9
- 🔵 **Low:** 4

**Recommendation:** **DO NOT DEPLOY** until critical and high issues are resolved.

---

## 🔴 CRITICAL ISSUES (MUST FIX)

### 1. ⚠️ MISSING DEPENDENCY - BeautifulSoup4
**File:** `backend/requirements.txt`
**Severity:** 🔴 CRITICAL
**Impact:** Application will crash on import

**Problem:**
```python
# backend/services/market_scraper.py:8
from bs4 import BeautifulSoup
```
BeautifulSoup4 is imported but NOT in requirements.txt

**Solution:**
```bash
# Add to backend/requirements.txt:
beautifulsoup4==4.12.2
```

---

### 2. 🔓 SSRF VULNERABILITY - Webhook Service
**File:** `backend/services/webhook_service.py:65`
**Severity:** 🔴 CRITICAL
**Impact:** Server-Side Request Forgery, access to internal services

**Problem:**
```python
response = await self.client.post(
    url,  # ⚠️ No validation! User can target localhost, cloud metadata, etc.
    json=payload,
    headers=request_headers
)
```

**Attack Scenario:**
```python
# Attacker creates webhook with URL:
url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
# Gets AWS credentials

url = "http://localhost:5432"
# Scans internal services
```

**Solution:**
```python
import ipaddress
from urllib.parse import urlparse

def validate_webhook_url(url: str) -> bool:
    """Validate webhook URL to prevent SSRF"""
    try:
        parsed = urlparse(url)

        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False

        # Block localhost
        if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            return False

        # Block private IPs
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False

        # Block cloud metadata
        if parsed.hostname in ['169.254.169.254', 'metadata.google.internal']:
            return False

        return True
    except:
        return False

# In send_webhook:
if not validate_webhook_url(url):
    logger.error(f"Invalid webhook URL: {url}")
    return False
```

---

### 3. 🔓 XSS VULNERABILITY - Chrome Extension
**File:** `chrome-extension/content.js:62, 87, 108`
**Severity:** 🔴 CRITICAL
**Impact:** Cross-Site Scripting, execution of malicious code

**Problem:**
```javascript
vintedBotButton.innerHTML = `
    <svg>...</svg>
    <span>Auto-fill with AI</span>  // ⚠️ No sanitization
`;

vintedBotButton.innerHTML = '<span>🤖 Generating...</span>';  // ⚠️ Direct HTML
```

**Attack Scenario:**
If AI backend returns malicious data:
```javascript
aiData = {
    title: "<img src=x onerror='alert(document.cookie)'>"
}
// Executed in user's browser
```

**Solution:**
```javascript
// Use textContent instead of innerHTML
vintedBotButton.textContent = 'Auto-fill with AI';

// Or use DOMPurify
import DOMPurify from 'dompurify';
vintedBotButton.innerHTML = DOMPurify.sanitize(content);
```

---

### 4. 📝 IMPORT MISSING - payments.py
**File:** `backend/api/v1/routers/payments.py:134`
**Severity:** 🔴 CRITICAL
**Impact:** Application crash on checkout

**Problem:**
```python
success_url = f"{os.getenv('FRONTEND_URL', ...)}"
# ⚠️ os not imported!
```

**Solution:**
```python
# Add at top of file:
import os
```

---

### 5. ⚖️ LEGAL RISK - Vinted Scraping
**File:** `backend/services/market_scraper.py`
**Severity:** 🔴 CRITICAL (Legal)
**Impact:** Terms of Service violation, potential lawsuit

**Problem:**
```python
# Scraping Vinted without permission
response = await self.client.get(f"{self.base_url}/vetements", params=params)
soup = BeautifulSoup(response.text, 'html.parser')
```

**Issues:**
1. Violates Vinted Terms of Service
2. No robots.txt respect
3. No rate limiting (can be seen as DDoS)
4. Fake User-Agent

**Solution:**
1. **Get official API access** from Vinted
2. **Or disable this feature** until legal approval
3. Add rate limiting (max 1 request per 10 seconds)
4. Respect robots.txt
5. Add clear disclaimer to users

**Recommendation:** 🚫 **DISABLE market scraping until legal review**

---

### 6. 🔓 SQL INJECTION RISK - Admin Router
**File:** `backend/api/v1/routers/admin.py:164`
**Severity:** 🔴 CRITICAL
**Impact:** SQL Injection via f-string

**Problem:**
```python
users = await conn.fetch(f"""
    SELECT ...
    ORDER BY u.{sort_by} DESC  # ⚠️ Unsanitized user input in SQL!
    LIMIT $1 OFFSET $2
""", limit, skip)
```

**Attack Scenario:**
```python
# Attacker sends:
sort_by = "created_at; DROP TABLE users--"
# SQL becomes:
# ORDER BY u.created_at; DROP TABLE users-- DESC
```

**Solution:**
```python
# Whitelist allowed fields
ALLOWED_SORT_FIELDS = ["created_at", "last_login", "subscription_plan"]

if sort_by not in ALLOWED_SORT_FIELDS:
    sort_by = "created_at"

# Use parameterized query or whitelist mapping
SORT_MAPPING = {
    "created_at": "u.created_at",
    "last_login": "u.last_login",
    "subscription_plan": "u.subscription_plan"
}

order_clause = SORT_MAPPING[sort_by]

users = await conn.fetch(f"""
    SELECT ...
    ORDER BY {order_clause} DESC
    LIMIT $1 OFFSET $2
""", limit, skip)
```

---

### 7. 🔐 WEAK ADMIN AUTHENTICATION
**File:** `backend/api/v1/routers/admin.py:22`
**Severity:** 🔴 CRITICAL
**Impact:** Unauthorized admin access

**Problem:**
```python
admin_emails = ["admin@vintedbot.com", "support@vintedbot.com"]

if current_user.email not in admin_emails:
    raise HTTPException(...)
```

**Issues:**
1. Hardcoded admin emails
2. No database role check
3. Easy to bypass by registering with admin email
4. No audit trail

**Solution:**
```python
# Add is_admin column to users table
# Migration:
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;

# In admin.py:
async def require_admin(current_user: User = Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT is_admin FROM users WHERE id = $1",
            current_user.id
        )

        if not user or not user['is_admin']:
            logger.warning(f"Unauthorized admin access attempt: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

    return current_user
```

---

### 8. 🔧 CONFIGURATION BUG - Dockerfile Path
**File:** `fly.staging.toml:5`
**Severity:** 🔴 CRITICAL
**Impact:** Deployment will fail

**Problem:**
```toml
[build]
  dockerfile = "Dockerfile"  # ⚠️ Wrong filename!
```

We created `backend/Dockerfile.production` not `Dockerfile`

**Solution:**
```toml
[build]
  dockerfile = "backend/Dockerfile.production"
```

---

## 🟠 HIGH SEVERITY ISSUES

### 9. 🔓 TOKEN EXPOSURE - Chrome Extension
**File:** `chrome-extension/content.js:8`
**Severity:** 🟠 HIGH
**Impact:** Token accessible via console

**Problem:**
```javascript
let authToken = null;  // Global variable, accessible from console
```

**Attack Scenario:**
```javascript
// Attacker injects script or uses console:
console.log(authToken);  // Gets user's JWT token
```

**Solution:**
```javascript
// Use closure
(function() {
  let authToken = null;  // Private

  // Expose only necessary functions
  window.VintedBot = {
    init: function() { ... }
  };
})();
```

---

### 10. ♾️ INFINITE LOOP - Content Script
**File:** `chrome-extension/content.js:55`
**Severity:** 🟠 HIGH
**Impact:** Memory leak, browser freeze

**Problem:**
```javascript
if (!formContainer) {
    console.log('⚠️ Form container not found');
    setTimeout(injectAutoFillButton, 1000);  // ⚠️ Infinite recursion!
    return;
}
```

**Solution:**
```javascript
let retryCount = 0;
const MAX_RETRIES = 10;

function injectAutoFillButton() {
    if (vintedBotButton) return;

    const formContainer = document.querySelector('[data-testid="item-upload-form"]') ||
                          document.querySelector('form') ||
                          document.querySelector('.item-box');

    if (!formContainer) {
        retryCount++;
        if (retryCount < MAX_RETRIES) {
            console.log(`⚠️ Form container not found (retry ${retryCount}/${MAX_RETRIES})`);
            setTimeout(injectAutoFillButton, 1000);
        } else {
            console.error('❌ Form container not found after max retries');
        }
        return;
    }

    retryCount = 0;  // Reset on success
    // ... rest of code
}
```

---

### 11. 🔄 ASYNC/SYNC MISMATCH - Stripe Service
**File:** `backend/services/stripe_service.py`
**Severity:** 🟠 HIGH
**Impact:** Blocking calls in async context

**Problem:**
```python
async def create_customer(...) -> Optional[str]:  # Marked async
    try:
        customer = stripe.Customer.create(...)  # ⚠️ Synchronous call!
        # Blocks event loop
```

**Solution:**
```python
# Option 1: Remove async (best for Stripe SDK)
def create_customer(...) -> Optional[str]:
    try:
        customer = stripe.Customer.create(...)

# Option 2: Run in executor
import asyncio

async def create_customer(...) -> Optional[str]:
    loop = asyncio.get_event_loop()
    customer = await loop.run_in_executor(
        None,
        stripe.Customer.create,
        email,
        name,
        metadata or {}
    )
```

---

### 12. 🔒 RACE CONDITION - Customer Creation
**File:** `backend/api/v1/routers/payments.py:105-131`
**Severity:** 🟠 HIGH
**Impact:** Duplicate Stripe customers, wasted money

**Problem:**
```python
# Thread 1: SELECT
user_data = await conn.fetchrow(
    "SELECT stripe_customer_id FROM users WHERE id = $1",
    current_user.id
)

stripe_customer_id = user_data.get("stripe_customer_id") if user_data else None

# Thread 2 can create customer here too!

if not stripe_customer_id:
    stripe_customer_id = await stripe_service.create_customer(...)  # Duplicate!

    await conn.execute(
        "UPDATE users SET stripe_customer_id = $1 WHERE id = $2",
        stripe_customer_id,
        current_user.id
    )
```

**Solution:**
```python
# Use SELECT FOR UPDATE or unique constraint
async with pool.acquire() as conn:
    async with conn.transaction():
        user_data = await conn.fetchrow(
            "SELECT stripe_customer_id FROM users WHERE id = $1 FOR UPDATE",
            current_user.id
        )

        stripe_customer_id = user_data.get("stripe_customer_id") if user_data else None

        if not stripe_customer_id:
            stripe_customer_id = await stripe_service.create_customer(...)

            if not stripe_customer_id:
                raise HTTPException(...)

            await conn.execute(
                "UPDATE users SET stripe_customer_id = $1 WHERE id = $2",
                stripe_customer_id,
                current_user.id
            )
```

---

### 13. 🔓 UNRESTRICTED FILE ACCESS - Webhook Headers
**File:** `backend/services/webhook_service.py:61`
**Severity:** 🟠 HIGH
**Impact:** Header injection

**Problem:**
```python
if headers:
    request_headers.update(headers)  # ⚠️ No validation!
```

**Attack Scenario:**
```python
# Attacker sets:
headers = {
    "Host": "evil.com",  # Header injection
    "X-Forwarded-For": "trusted-ip"  # IP spoofing
}
```

**Solution:**
```python
ALLOWED_HEADER_PREFIXES = ['X-Custom-', 'X-App-']

def validate_headers(headers: Dict) -> Dict:
    """Validate and filter webhook headers"""
    safe_headers = {}
    for key, value in headers.items():
        # Only allow custom headers
        if any(key.startswith(prefix) for prefix in ALLOWED_HEADER_PREFIXES):
            # Sanitize value
            safe_headers[key] = str(value)[:500]  # Max length
    return safe_headers

# In send_webhook:
if headers:
    safe_headers = validate_headers(headers)
    request_headers.update(safe_headers)
```

---

### 14. 📦 UNCLOSED HTTP CLIENTS
**File:** `backend/services/webhook_service.py:26`, `market_scraper.py:27`
**Severity:** 🟠 HIGH
**Impact:** Resource leak, connection exhaustion

**Problem:**
```python
def __init__(self):
    self.client = httpx.AsyncClient(timeout=self.timeout)
    # ⚠️ Never closed! Connections leak
```

**Solution:**
```python
# Option 1: Add close method
async def close(self):
    await self.client.aclose()

# Option 2: Use as context manager
async with httpx.AsyncClient() as client:
    response = await client.post(url, ...)

# Option 3: Global client with lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_http_client():
    client = httpx.AsyncClient()
    try:
        yield client
    finally:
        await client.aclose()
```

---

### 15. 🔍 INFORMATION DISCLOSURE - Logs
**Files:** Multiple
**Severity:** 🟠 HIGH
**Impact:** Sensitive data in logs

**Problem:**
```python
logger.info(f"✅ Created Stripe customer: {customer.id}")
logger.info(f"📨 Webhook sent: {event} to {url}")  # URL may contain secrets
logger.error(f"❌ Failed to create customer: {e}")  # Exception may contain PII
```

**Solution:**
```python
# Use structured logging with sanitization
def sanitize_for_log(data: str) -> str:
    """Remove sensitive data from logs"""
    # Redact email addresses
    data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', data)
    # Redact tokens
    data = re.sub(r'(Bearer|token|key)[\s:=]+[A-Za-z0-9_-]+', r'\1 [REDACTED]', data, flags=re.I)
    return data

logger.info(f"Created Stripe customer", extra={"customer_id": customer.id[:8] + "***"})
logger.info(f"Webhook sent", extra={"event": event, "host": urlparse(url).hostname})
```

---

## 🟡 MEDIUM SEVERITY ISSUES

### 16. 🔢 NO RATE LIMITING - Webhooks
**File:** `backend/services/webhook_service.py`
**Severity:** 🟡 MEDIUM
**Impact:** DOS of external services

**Solution:**
```python
from collections import defaultdict
from time import time

class WebhookRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_per_minute = 10

    async def check_rate_limit(self, user_id: str) -> bool:
        now = time()
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < 60
        ]

        if len(self.requests[user_id]) >= self.max_per_minute:
            return False

        self.requests[user_id].append(now)
        return True
```

---

### 17. ❌ MISSING ERROR HANDLING - querySelectorAll
**File:** `chrome-extension/content.js:129-131`
**Severity:** 🟡 MEDIUM
**Impact:** Logic error

**Problem:**
```javascript
const imageElements = document.querySelectorAll('[data-testid="item-photo"]') ||
                      document.querySelectorAll('.item-photo img') ||
                      document.querySelectorAll('input[type="file"]');
// ⚠️ querySelectorAll NEVER returns null, always NodeList (even if empty)
// So || never triggers
```

**Solution:**
```javascript
let imageElements = document.querySelectorAll('[data-testid="item-photo"]');
if (imageElements.length === 0) {
    imageElements = document.querySelectorAll('.item-photo img');
}
if (imageElements.length === 0) {
    imageElements = document.querySelectorAll('input[type="file"]');
}
```

---

### 18. 🔐 HARDCODED BACKEND URL
**Files:** `chrome-extension/content.js:7`, `popup.js:6`
**Severity:** 🟡 MEDIUM
**Impact:** Difficult to switch between staging/production

**Solution:**
```javascript
// In manifest.json, add:
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  },
  "web_accessible_resources": [{
    "resources": ["config.json"],
    "matches": ["<all_urls>"]
  }]
}

// Create config.json:
{
  "backend_url": "https://vintedbot-staging.fly.dev",
  "environment": "staging"
}

// In code:
const config = await fetch(chrome.runtime.getURL('config.json')).then(r => r.json());
const BACKEND_URL = config.backend_url;
```

---

### 19. ⏱️ NO TIMEOUT - Extension Fetch
**Files:** `chrome-extension/content.js`, `popup.js`
**Severity:** 🟡 MEDIUM
**Impact:** Hanging requests

**Solution:**
```javascript
async function fetchWithTimeout(url, options = {}, timeout = 10000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw error;
    }
}

// Use:
const response = await fetchWithTimeout(`${BACKEND_URL}/drafts/ai-generate`, {
    method: 'POST',
    headers: {...},
    body: JSON.stringify(...)
}, 15000);  // 15 second timeout
```

---

### 20. 🗃️ MISSING DATABASE COLUMNS
**File:** `backend/api/v1/routers/payments.py`
**Severity:** 🟡 MEDIUM
**Impact:** Database errors on deploy

**Problem:**
Code assumes these columns exist:
- `users.stripe_customer_id`
- `users.stripe_subscription_id`
- `users.subscription_plan`
- `users.subscription_status`
- `webhooks` table

**Solution:**
Create migration:
```sql
-- migrations/add_stripe_columns.sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(50) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'active';

CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    events TEXT[],
    secret TEXT,
    headers JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_triggered TIMESTAMP,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0
);

CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX idx_webhooks_active ON webhooks(active) WHERE active = TRUE;
```

---

### 21. 🧠 ML MODEL NOT TRAINED
**File:** `backend/services/ml_pricing_service.py`
**Severity:** 🟡 MEDIUM
**Impact:** ML pricing won't work initially

**Problem:**
Model file doesn't exist on first deploy, falls back to rule-based pricing.

**Solution:**
1. Add training data seeding
2. Train initial model with sample data
3. Or clearly document ML requires data collection first

```python
# Add to deployment script:
async def seed_ml_model():
    """Train initial ML model with sample data"""
    sample_data = [
        {'category': 'vetements', 'brand': 'Zara', 'condition': 'bon_etat', 'price': 15.0},
        # ... 50+ samples
    ]

    await ml_pricing_service.train_model(sample_data)
    logger.info("✅ ML model trained with seed data")
```

---

### 22. 🔍 NO INPUT VALIDATION - Webhook Registration
**File:** `backend/api/v1/routers/webhooks.py`
**Severity:** 🟡 MEDIUM
**Impact:** Invalid webhooks in database

**Problem:**
No validation on webhook URL format, headers, secret length.

**Solution:**
```python
class CreateWebhookRequest(BaseModel):
    url: HttpUrl  # ✅ Already validated by Pydantic
    events: Optional[List[str]] = None
    secret: Optional[str] = Field(None, min_length=16, max_length=128)
    headers: Optional[Dict[str, str]] = Field(None, max_properties=10)

    @validator('events')
    def validate_events(cls, v):
        if v:
            for event in v:
                if len(event) > 100:
                    raise ValueError('Event name too long')
        return v

    @validator('headers')
    def validate_headers(cls, v):
        if v:
            for key, value in v.items():
                if len(key) > 100 or len(value) > 500:
                    raise ValueError('Header too long')
        return v
```

---

### 23. 📊 NO PAGINATION - Admin Users List
**File:** `backend/api/v1/routers/admin.py:164`
**Severity:** 🟡 MEDIUM
**Impact:** Performance issues with many users

**Problem:**
Pagination implemented but no max limit enforced.

**Solution:**
```python
@router.get("/users", response_model=List[UserStatsResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),  # ✅ Max 100
    sort_by: str = "created_at",
    admin: User = Depends(require_admin)
):
    # ... existing code
```

---

### 24. 🔄 NO RETRY LOGIC - Stripe Calls
**File:** `backend/services/stripe_service.py`
**Severity:** 🟡 MEDIUM
**Impact:** Transient failures not handled

**Solution:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def create_customer_with_retry(...):
    return await create_customer(...)
```

---

## 🔵 LOW SEVERITY ISSUES

### 25. 📝 MISSING TYPE HINTS - Some Functions
**Files:** Various
**Severity:** 🔵 LOW
**Impact:** Code readability

---

### 26. 🎨 CSS SELECTOR BRITTLENESS
**File:** `chrome-extension/content.js`, `market_scraper.py`
**Severity:** 🔵 LOW
**Impact:** Breaks when Vinted changes HTML

**Solution:** More robust selectors, fallbacks

---

### 27. 🔊 EXCESSIVE LOGGING
**Files:** Multiple
**Severity:** 🔵 LOW
**Impact:** Log spam in production

**Solution:** Use appropriate log levels (DEBUG for details, INFO for important events)

---

### 28. 💾 NO MEMORY LIMITS - VM Config
**File:** `fly.staging.toml:57`
**Severity:** 🔵 LOW
**Impact:** 512MB may be insufficient for ML

**Solution:**
```toml
[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024  # Increase to 1GB for ML models
```

---

## ✅ REQUIRED FIXES BEFORE DEPLOYMENT

### CRITICAL (Must Fix):
1. ✅ Add `beautifulsoup4==4.12.2` to requirements.txt
2. ✅ Fix SSRF in webhook_service.py (add URL validation)
3. ✅ Fix XSS in content.js (use textContent)
4. ✅ Add `import os` to payments.py
5. ✅ **Disable market scraping** or get legal approval
6. ✅ Fix SQL injection in admin.py (whitelist sort fields)
7. ✅ Implement database role-based admin auth
8. ✅ Fix Dockerfile path in fly.staging.toml

### HIGH (Should Fix):
9. ✅ Fix token exposure in Chrome extension
10. ✅ Add max retries to content.js
11. ✅ Fix async/sync mismatch in Stripe service
12. ✅ Add transaction lock for customer creation
13. ✅ Validate webhook headers
14. ✅ Close HTTP clients properly
15. ✅ Sanitize logs

### MEDIUM (Recommended):
16-24: Address as time permits

### LOW:
25-28: Nice to have

---

## 🛠️ QUICK FIX SCRIPT

Here's a script to apply critical fixes:

```bash
#!/bin/bash
# fix-critical-issues.sh

echo "🔧 Applying critical security fixes..."

# 1. Add missing dependency
echo "beautifulsoup4==4.12.2  # HTML parsing for market data" >> backend/requirements.txt

# 2. Add missing import
sed -i '9a import os' backend/api/v1/routers/payments.py

# 3. Fix Dockerfile path
sed -i 's/dockerfile = "Dockerfile"/dockerfile = "backend\/Dockerfile.production"/' fly.staging.toml

# 4. Increase VM memory
sed -i 's/memory_mb = 512/memory_mb = 1024/' fly.staging.toml

echo "✅ Critical fixes applied!"
echo "⚠️  Manual fixes still required:"
echo "  - SSRF validation in webhook_service.py"
echo "  - XSS fixes in content.js"
echo "  - SQL injection fix in admin.py"
echo "  - Admin authentication system"
echo "  - Market scraping legal review"
```

---

## 🎯 DEPLOYMENT CHECKLIST

Before deploying:

- [ ] Apply all CRITICAL fixes (1-8)
- [ ] Apply HIGH severity fixes (9-15)
- [ ] Run security scan: `bandit -r backend/`
- [ ] Test all new endpoints manually
- [ ] Create database migration for new columns
- [ ] Configure environment variables:
  - [ ] STRIPE_SECRET_KEY
  - [ ] STRIPE_PUBLISHABLE_KEY
  - [ ] STRIPE_WEBHOOK_SECRET
  - [ ] STRIPE_STARTER_PRICE_ID
  - [ ] STRIPE_PRO_PRICE_ID
  - [ ] STRIPE_ENTERPRISE_PRICE_ID
  - [ ] FRONTEND_URL
- [ ] Test Chrome extension locally
- [ ] Review Vinted Terms of Service
- [ ] Legal approval for market scraping
- [ ] Set up monitoring/alerting
- [ ] Backup database before deploy

---

## 📞 QUESTIONS FOR USER

1. **Legal**: Do we have permission to scrape Vinted? Should we disable this feature?
2. **Admin**: How should admin users be designated? Email list or database role?
3. **Stripe**: Do you have Stripe account set up with price IDs?
4. **Database**: Can I create the required migration files?
5. **ML**: Should we train the ML model with sample data or wait for real data?

---

**Status:** 🔴 **DO NOT DEPLOY UNTIL CRITICAL ISSUES RESOLVED**

**Estimated Fix Time:** 4-6 hours for critical issues

**Next Steps:**
1. Fix critical security issues
2. Create database migrations
3. Test thoroughly
4. Re-audit
5. Deploy to staging
6. Monitor for 24h
7. Deploy to production

---

*Report generated by Claude Code Security Analysis*
*Date: 2025-11-16*
