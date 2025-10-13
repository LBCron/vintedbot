# VintedBot Connector Backend

A production-ready FastAPI backend for Vinted automation with messaging, session management, publishing queue, and Playwright worker integration.

## Features

✨ **Complete Messaging System**
- Inbox sync and thread management
- Message pagination and search
- Real-time WebSocket notifications
- Attachment uploads

🔐 **Secure Session Management**
- Encrypted cookie storage (AES-GCM)
- Session validation and lifecycle
- Multi-session support

📋 **Publish Queue & Automation**
- Manual and automated publishing modes
- Playwright worker for browser automation
- Job status tracking with logs
- Screenshot capture on errors/blocks

🛡️ **Safety Features**
- NO CAPTCHA bypass attempts
- Automatic detection and graceful failure
- Opt-in automation with preview mode
- Screenshot evidence for blocked jobs

📊 **Background Jobs**
- Inbox sync (configurable interval)
- Publish queue polling
- Scheduled price drops
- APScheduler integration

🔌 **WebSocket Support**
- Real-time message notifications
- Job status updates
- Multi-client support

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and set your preferences:
- `MOCK_MODE=true` for frontend development without real Vinted
- `ENCRYPTION_KEY` - Generate a secure 32-byte key for production
- `ALLOWED_ORIGINS` - CORS origins (use `*` for development)

### 3. Initialize Database & Seed Mock Data

```bash
python backend/scripts/seed_mock_data.py
```

### 4. Run the Server

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 5000
```

The API will be available at: `http://localhost:5000`
- **Swagger Docs**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

### 5. Run Playwright Worker (Optional)

For automated publishing:

```bash
python backend/playwright_worker.py --headless=1
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MODE` | `true` | Enable mock mode (no real Vinted calls) |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins |
| `ENCRYPTION_KEY` | (random) | 32-byte encryption key for cookies |
| `SYNC_INTERVAL_MIN` | `15` | Inbox sync interval in minutes |
| `PRICE_DROP_CRON` | `0 3 * * *` | Price drop schedule (3 AM daily) |
| `PLAYWRIGHT_HEADLESS` | `true` | Run Playwright in headless mode |
| `DATABASE_URL` | `sqlite:///...` | Database connection URL |

## API Endpoints

### Authentication
- `POST /vinted/auth/session` - Create and validate session
- `POST /vinted/auth/logout` - Delete session
- `GET /vinted/auth/sessions` - List all sessions

### Messages
- `GET /vinted/messages` - Get message threads
- `GET /vinted/messages/{thread_id}` - Get thread messages
- `POST /vinted/messages/{thread_id}/reply` - Reply to thread
- `POST /vinted/messages/send-attachment` - Upload attachment
- `POST /vinted/messages/bulk-mark-read` - Mark threads as read
- `GET /vinted/messages/notifications` - Get unread counts

### Publish Queue
- `POST /vinted/publish/queue` - Queue publish job
- `GET /vinted/publish/queue` - List jobs
- `GET /vinted/publish/queue/{job_id}` - Get job status
- `POST /vinted/publish/queue/{job_id}/cancel` - Cancel job

### Listings
- `GET /listings` - List all listings
- `GET /listings/{id}` - Get single listing
- `POST /listings` - Create listing
- `GET /listings/export/csv` - Export as CSV
- `GET /listings/export/json` - Export as JSON

### Health
- `GET /health` - System health and stats

### WebSocket
- `WS /ws/messages?session_id=<id>` - Real-time updates

## How to Import a Vinted Session Cookie

### Step 1: Export Cookie from Chrome

1. Install a cookie export extension (e.g., "EditThisCookie" or "Cookie-Editor")
2. Go to vinted.com and log in
3. Click the extension icon
4. Find the `_vinted_fr_session` cookie (or your locale's equivalent)
5. Copy the **value** (not the name)

### Step 2: Import to Backend

```bash
curl -X POST http://localhost:5000/vinted/auth/session \
  -H "Content-Type: application/json" \
  -d '{
    "cookie_value": "<paste-your-cookie-here>",
    "note": "My main account"
  }'
```

Response:
```json
{
  "session_id": 1,
  "valid": true,
  "created_at": "2025-10-13T12:00:00"
}
```

⚠️ **IMPORTANT**: Test on a secondary account first. Automation may violate Vinted's ToS.

## Enable Automated Publishing

### Requirements
1. Valid session cookie imported
2. Playwright installed: `playwright install chromium`
3. Item prepared for publishing

### Safety Checklist
- ✅ Tested on secondary account
- ✅ CAPTCHA detection enabled (automatic)
- ✅ Screenshot capture on failures
- ✅ Rate limiting respected
- ✅ Proxy configured (if needed)

### Start Worker

```bash
# Headless mode (production)
python backend/playwright_worker.py --headless=1

# Headed mode (debugging)
python backend/playwright_worker.py --headless=0
```

The worker will:
1. Poll for queued jobs every 30 seconds
2. Load session cookies into browser
3. Navigate to Vinted
4. Check for CAPTCHA (abort if detected)
5. Execute publish action (manual preview or automated)
6. Save screenshots and logs

## Troubleshooting

### "Failed to fetch" Error

**Cause**: CORS, port mismatch, or backend down

**Solutions**:
1. Check backend is running: `curl http://localhost:5000/health`
2. Verify port 5000 is used (not 3000 or 8000)
3. Check CORS in `.env`: `ALLOWED_ORIGINS=*`
4. Try without trailing slash in URLs
5. Check browser console for actual error

### Database Errors

```bash
# Reset database
rm backend/data/db.sqlite
python backend/scripts/seed_mock_data.py
```

### Playwright Issues

```bash
# Reinstall browsers
playwright install --force chromium
```

## Example Usage

### 1. Health Check

```bash
curl -X GET http://localhost:5000/health
```

### 2. Create Session

```bash
curl -X POST http://localhost:5000/vinted/auth/session \
  -H "Content-Type: application/json" \
  -d '{"cookie_value": "your_cookie_here"}'
```

### 3. Queue Publish Job (Manual Preview)

```bash
curl -X POST http://localhost:5000/vinted/publish/queue \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": 1,
    "session_id": 1,
    "mode": "manual"
  }'
```

Response:
```json
{
  "job_id": "abc-123-def",
  "status": "queued",
  "mode": "manual"
}
```

### 4. Get Job Status

```bash
curl -X GET http://localhost:5000/vinted/publish/queue/abc-123-def
```

### 5. Get Messages

```bash
curl -X GET http://localhost:5000/vinted/messages?limit=20
```

## Legal & Safety Notice

### ⚠️ CAPTCHA & Anti-Bot Policy

This software:
- **DOES NOT** attempt to bypass CAPTCHAs
- **DOES NOT** circumvent anti-bot protections
- **WILL FAIL** gracefully when blocked
- **CAPTURES** screenshots as evidence

### Recommendations

1. **Test on secondary account** - Never use your main account for automation
2. **Respect rate limits** - Don't spam requests
3. **Manual verification** - Use "manual" mode to preview before publish
4. **Monitor logs** - Check job logs for CAPTCHA warnings
5. **Read Vinted ToS** - Ensure compliance with platform rules

### Disclaimer

This tool is for **educational and personal use only**. Users are responsible for:
- Complying with Vinted's Terms of Service
- Ensuring automation is permitted in their jurisdiction
- Any consequences from automated actions

## Architecture

```
backend/
├── app.py                  # FastAPI app, middlewares, routers
├── models.py               # SQLModel database models
├── db.py                   # Database initialization & helpers
├── vinted_connector.py     # Vinted API wrappers (mock + real)
├── playwright_worker.py    # Browser automation worker
├── jobs.py                 # APScheduler background tasks
├── routes/                 # API endpoints
│   ├── auth.py            # Session management
│   ├── messages.py        # Messaging/inbox
│   ├── publish.py         # Publish queue
│   ├── listings.py        # Listings CRUD
│   ├── offers.py          # Offers (mock)
│   ├── orders.py          # Orders (mock)
│   ├── health.py          # Health check
│   └── ws.py              # WebSocket
├── utils/                  # Utilities
│   ├── crypto.py          # AES-GCM encryption
│   ├── logger.py          # Loguru setup
│   └── validators.py      # File/URL validation
├── scripts/
│   └── seed_mock_data.py  # Database seeding
├── tests/
│   └── test_routes.py     # Pytest tests
└── data/                   # Runtime data
    ├── db.sqlite          # SQLite database
    ├── uploads/           # Uploaded files
    └── screenshots/       # Job screenshots
```

## Testing

Run tests:

```bash
pytest backend/tests/ -v
```

Expected output:
```
test_routes.py::test_health_ok PASSED
test_routes.py::test_root_endpoint PASSED
test_routes.py::test_mock_messages_list PASSED
test_routes.py::test_mock_listings PASSED
test_routes.py::test_create_session_mock PASSED
test_routes.py::test_queue_publish_job PASSED
test_routes.py::test_get_notifications PASSED
```

## Development

### Project Structure Best Practices

- **Separation of Concerns**: Routes → Services → Database
- **Type Safety**: Pydantic models for validation
- **Security**: Encrypted secrets, no raw cookie logging
- **Observability**: Request IDs, structured logging
- **Resilience**: Graceful degradation, error screenshots

### Adding New Features

1. Define models in `models.py`
2. Add DB helpers in `db.py`
3. Create route in `routes/`
4. Add tests in `tests/`
5. Update this README

## License

Personal use only. See disclaimer above.
