# VintedBot API - AI-Powered Clothing Resale Assistant

## Overview

VintedBot is a FastAPI-based backend system that automates the process of creating and managing clothing resale listings. The application uses AI to analyze clothing photos and generate complete product listings with pricing suggestions. It features automated price management, duplicate detection, inventory tracking, and multi-format export capabilities.

The system is designed to streamline the resale workflow by:
- Automatically generating product descriptions from images
- Suggesting optimal pricing based on condition and brand
- Detecting duplicate listings
- Managing inventory status (draft, listed, sold, archived)
- Providing scheduled price drops for unsold items
- Exporting inventory in multiple formats (CSV, JSON, PDF, Vinted-specific)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### API Framework
- **FastAPI** serves as the core web framework, providing automatic OpenAPI documentation at `/docs` and `/redoc`
- **CORS middleware** configured with regex pattern matching for Lovable.dev wildcard domains (`https://*.lovable.dev`) plus configurable additional origins from environment
- **Lifespan context manager** handles application startup/shutdown, including background scheduler initialization
- **JSONResponse wrapper** ensures consistent JSON formatting and CORS header compatibility

### Data Storage
- **File-based JSON database** (`backend/data/items.json`) stores all inventory items
- No external database required - simple JSON file acts as persistent storage
- Custom `Database` class in `backend/models/db.py` provides CRUD operations
- UUIDs used for unique item identification

### AI & Image Processing
- **Dual-mode AI service**: 
  - OpenAI integration when API key is available
  - Intelligent mock mode with realistic data generation when no API key present
- **Image hash-based duplicate detection** using perceptual hashing (pHash)
- **Text similarity matching** using rapidfuzz for title comparison (80% threshold)
- Supports both image URLs and file uploads

### Pricing Strategy
- **Three-tier pricing model**: minimum, maximum, and target prices with justification
- **Automated daily price drops** (5% default) via APScheduler background jobs
- **Price history tracking** for all adjustments with timestamps and reasons
- **Price floor protection** prevents drops below minimum suggested price
- **Simulation endpoint** allows testing price trajectories over time

### Background Jobs
- **APScheduler** manages recurring tasks
- **Daily cron job** (midnight) applies automatic price drops to all listed items
- Scheduler lifecycle tied to FastAPI application lifespan
- Job monitoring via health endpoint

### Data Models (Pydantic Schemas)
- **Item**: Core product model with full lifecycle tracking
- **ItemStatus enum**: draft → listed → sold/archived workflow
- **Condition enum**: Standardized condition levels (new with tags, very good, etc.)
- **PriceSuggestion**: Structured pricing recommendations
- **PriceHistory**: Audit trail for all price changes

### Export System
- **Multi-format support**: CSV, JSON, PDF, Vinted-specific CSV
- **ReportLab** for PDF generation with formatted tables
- **Custom field mapping** for Vinted marketplace compatibility
- Streaming responses with appropriate content-type headers

### API Routes Structure
- `/ingest` - Photo upload and AI listing generation (including save-draft endpoint)
- `/listings` - CRUD operations for inventory items (including publish endpoint)
- `/pricing` - Price simulation and management
- `/export` - Multi-format inventory exports
- `/import` - CSV import functionality
- `/stats` - Analytics and health monitoring
- `/bonus` - Recommendations and test utilities

### Lovable.dev Integration
- **CORS Configuration**: Uses `allow_origin_regex` for wildcard Lovable domain support (`https://*.lovable.dev`)
- **Additional Origins**: Configurable via `ADDITIONAL_CORS_ORIGINS` environment variable
- **OpenAPI Client Generator**: Available in `frontend/openapi_client/generate_client.py` for TypeScript client generation
- **Response Type Handling**: Properly handles JSON, CSV, and PDF responses based on content-type headers
- **Publish Endpoint**: `/listings/publish/{item_id}` for marking items as listed (route ordering optimized)
- **Integration Tests**: Comprehensive test suite in `test_lovable.py` validates all critical paths

## External Dependencies

### Core Framework
- **FastAPI** - Web framework with automatic API documentation
- **Pydantic** - Data validation and schema definition
- **Uvicorn** - ASGI server (implied, for running FastAPI)

### AI & Image Processing
- **OpenAI API** (optional) - GPT-based listing generation
- **Pillow (PIL)** - Image processing
- **imagehash** - Perceptual image hashing for duplicate detection
- **rapidfuzz** - Fast fuzzy string matching

### Background Processing
- **APScheduler** - Cron-based job scheduling for automated price drops

### Data Export
- **ReportLab** - PDF generation with tables and formatting

### HTTP & File Handling
- **requests** - HTTP client for fetching remote images
- **python-multipart** - File upload handling

### Future Integration Points
- Frontend connection ready via CORS-enabled REST API
- Lovable.dev or similar frontend frameworks can consume `/docs` OpenAPI specification
- Authentication layer can be added via FastAPI dependencies
- External marketplace APIs (Vinted, etc.) can integrate via export formats

## Recent Changes

### Publish Queue API Fixed (October 14, 2025)
- ✅ **Publish queue endpoint**: `GET /vinted/publish/queue` now returns Lovable-compatible format (direct array)
- ✅ **Job actions added**: retry, run, pause, delete endpoints for queue management
- ✅ **Fast response**: <2ms average, no more timeouts
- ✅ **Field mapping**: `scheduled_at` (not schedule_at), `screenshot` (not screenshot_path), status/mode as strings
- ✅ **All job endpoints working**:
  - `GET /vinted/publish/queue` - List all jobs
  - `GET /vinted/publish/queue/{job_id}` - Get job details
  - `POST /vinted/publish/queue/{job_id}/cancel` - Cancel job
  - `POST /vinted/publish/queue/{job_id}/retry` - Retry failed job
  - `POST /vinted/publish/queue/{job_id}/run` - Manually trigger queued job
  - `POST /vinted/publish/queue/{job_id}/pause` - Pause running job
  - `DELETE /vinted/publish/queue/{job_id}` - Delete job

### Mobile Photo Upload Fix (October 14, 2025)
- ✅ **Multi-photo upload endpoint**: `/vinted/photos/upload` now accepts 1-20 images simultaneously
- ✅ **Lovable-compatible format**: Returns `{"photos": [{"temp_id", "url", "filename"}]}` as expected by frontend
- ✅ **Mobile-friendly**: Accepts JPG, PNG, WEBP up to 15MB per photo
- ✅ **Rate limiting**: 10 requests/minute protection
- ✅ **Static file serving**: `/temp_photos` endpoint serves uploaded images

### Vinted Automation System (October 13, 2025)
- ✅ **Playwright-based automation**: Full Vinted listing creation and publication
- ✅ **Encrypted session vault**: Fernet encryption for cookie/user-agent storage (`backend/data/session.enc`)
- ✅ **Photo upload pipeline**: Multipart upload with temp storage at `/temp_photos` (rate limited 10/min)
- ✅ **Two-phase workflow**: 
  - Phase A (prepare): Fill form, upload photos, detect captcha → returns `confirm_token`
  - Phase B (publish): Click publish button using token (30min TTL)
- ✅ **Dry-run by default**: All operations safe unless `dry_run: false` explicitly set
- ✅ **Captcha detection**: Graceful handling with `needs_manual: true` response (no bypass attempts)
- ✅ **Rate limiting**: 5 requests/min on publish endpoint
- ✅ **Idempotency support**: `Idempotency-Key` header prevents duplicate publications
- ✅ **Complete documentation**: `VINTED_API_TESTS.md` (cURL tests) + `LOVABLE_PROMPT.md` (frontend integration)
- ✅ **New endpoints**:
  - `POST /vinted/auth/session` - Save encrypted session
  - `GET /vinted/auth/check` - Verify authentication
  - `POST /vinted/photos/upload` - Upload listing photos
  - `POST /vinted/listings/prepare` - Prepare draft (Phase A)
  - `POST /vinted/listings/publish` - Publish listing (Phase B)
- ✅ **Dependencies added**: playwright, cryptography
- ✅ **Architect validated**: None-guards fixed, /temp_photos mounted, all critical paths functional

### Multipart Upload Endpoint (October 13, 2025)
- ✅ **Production-ready image upload**: POST /api/v1/ingest/upload accepts 1-20 images
- ✅ **Image processing pipeline**: Auto-corrects EXIF orientation, resizes to 1600px max, JPEG quality 80, strips GPS/EXIF data
- ✅ **Security & validation**: Rate limiting (10/min), file size limit (15MB/413), MIME validation (415), proper error codes
- ✅ **Database models**: Media, Draft, DraftPhoto for tracking uploads and draft listings
- ✅ **Idempotent storage**: SHA256-based filenames prevent duplicates
- ✅ **Local media serving**: Files served from /media endpoint with static file mount
- ✅ **Comprehensive tests**: 8 test cases covering happy paths, oversize files, invalid MIME, validation errors
- ✅ **New dependencies**: pydantic-settings, filetype, boto3, tenacity, slowapi, pytest-asyncio

### Project Restoration (October 13, 2025)
- ✅ **Restored from ZIP backup**: Successfully extracted and reorganized project structure
- ✅ **Python 3.11 environment**: Configured with uv package manager
- ✅ **Dependencies installed**: All required packages installed via pyproject.toml
- ✅ **Workflow configured**: FastAPI server running on port 5000 with automatic startup
- ✅ **Deployment ready**: Configured for Replit VM deployment with Always On capability
- ✅ **Public API URL**: https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev

### Development Setup
1. **Package Manager**: Using uv for dependency management (faster than pip)
2. **Environment Variables**: .env file created from .env.example template
3. **Port Configuration**: Bound to 0.0.0.0:5000 for Replit compatibility
4. **CORS**: Pre-configured for Lovable.dev integration
5. **Background Scheduler**: APScheduler running with 1 cron job for daily price drops

### Deployment Configuration
- **Type**: Reserved VM (for Always On capability)
- **Run Command**: `uvicorn backend.app:app --host 0.0.0.0 --port 5000`
- **Port**: 5000 (Replit standard)
- **Environment**: Production-ready with health monitoring

### Lovable.dev Integration
To connect a Lovable.dev frontend, use this environment variable:
```
VITE_API_BASE_URL=https://b3358a26-d290-4c55-82fc-cc0ad63fac5b-00-29ghky26cw3zi.janeway.replit.dev
```

**CORS Configuration (October 14, 2025):**
- Backend configured with regex pattern to accept all Lovable domains:
  - `*.lovableproject.com` (current Lovable frontend domain)
  - `*.lovable.dev` 
  - `*.lovable.app`
- Pattern: `r"https://.*\.lovable(project\.com|\.dev|\.app)"`
- Mock mode disabled: `MOCK_MODE=False` for real Vinted authentication