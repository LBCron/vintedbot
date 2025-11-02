# VintedBot API - AI-Powered Clothing Resale Assistant

## Overview
VintedBot is a FastAPI-based backend system designed to automate and streamline the process of creating and managing clothing resale listings, primarily for platforms like Vinted. It leverages AI to analyze clothing photos, generate comprehensive product listings with pricing suggestions, and manage inventory. The system features automated price adjustments, duplicate detection, and multi-format export capabilities, aiming to simplify the resale workflow and optimize listing creation.

## User Preferences
Preferred communication style: Simple, everyday language (French speaker).
Zero failed drafts requirement - all drafts must pass strict validation before creation.

## System Architecture

### API Framework
- **FastAPI** provides the core web framework, including automatic OpenAPI documentation.
- **CORS middleware** is configured to allow requests from `https://*.lovable.dev` and other configurable origins.
- **Lifespan context manager** handles application startup and shutdown, including scheduler initialization.
- **JSONResponse wrapper** ensures consistent JSON formatting and CORS compatibility.

### Data Storage (SQLite - October 2025)
- **SQLite Storage Backend** (`backend/core/storage.py`) - 100% local, zero cost, survives VM restarts:
  - **File**: `backend/data/vbs.db` (persistent on Replit VM)
  - **Tables**:
    - `drafts`: All generated drafts with quality gate tracking (title, description, price, brand, size, photos, status, flags)
    - `listings`: Active Vinted listings with vinted_id and listing_url
    - `publish_log`: Publication audit trail with idempotency protection (prevents duplicate publishes)
    - `photo_plans`: Photo analysis plans (migrated from PostgreSQL)
    - `bulk_jobs`: Legacy ingest job tracking
  - **TTL Auto-Purge**: Daily vacuum_and_prune job (02:00) removes old drafts (30d) and logs (90d)
  - **Export/Import**: GET /export/drafts returns ZIP, POST /import/drafts restores from ZIP/JSON
  - **Zero Dependencies**: No external database required (PostgreSQL only used for legacy features)
- **File-based JSON database** (`backend/data/items.json`) serves as the persistent storage for all inventory items (legacy).
- A custom `Database` class handles CRUD operations, using UUIDs for unique item identification.

### AI & Image Processing
- **Dual-mode AI service**: Integrates with OpenAI (GPT-4o Vision) for photo analysis and listing generation when an API key is available, and provides an intelligent mock mode otherwise.
- **HEIC/HEIF→JPEG Auto-Conversion**: All HEIC/HEIF images are automatically converted to JPEG before OpenAI Vision API calls (via `encode_image_to_base64()`)
- **Auto-Batching Intelligence (October 2025)**: Handles UNLIMITED photos via automatic batching
  - ≤25 photos → Single GPT-4 Vision analysis (all photos together)
  - >25 photos → Auto-splits into batches of 25, analyzes each separately, merges results
  - Example: 144 photos → 6 batches → ~20-28 articles detected with ALL their photos
  - Fallback mode: 7 photos minimum per article for complete visualization
- **Multi-Item Detection via GPT-4 Vision**: `smart_analyze_and_group_photos()` analyzes ALL photos intelligently to detect multiple distinct items (e.g., 5 items detected from 38 photos)
- **Smart AI Grouping**: Analyzes and groups multiple photos by visual similarity to create single listings, identifying unique characteristics and providing confidence scores.
- **Strict AI Prompt System (November 2025)**:
  - **ZERO emojis, ZERO marketing phrases** ("parfait pour", "style tendance", "casual chic", "look", "découvrez", "idéal")
  - **ZERO superlatifs** ("magnifique", "prestigieuse", "haute qualité", "parfait", "tendance")
  - **Hashtag Rules**: EXACTLY 3-5 hashtags, ALWAYS at end of description
  - **Title Format SIMPLIFIÉ**: ≤70 chars, format "Catégorie Couleur Marque Taille – État" (NO parentheses, NO measurements)
    - Example: "Jogging noir Burberry XS – bon état" (NOT "Jogging Burberry 16Y / 165 cm (≈ XS)")
  - **Description Structure**: 5-8 factual lines (what it is, condition, material, size info, measurements needed, shipping)
  - **Size Normalization (SIMPLIFIÉ - Nov 2025)**: 
    - AI returns ONLY adult size in 'size' field (XS/S/M/L/XL)
    - Child/teen sizes (16Y, 165cm) automatically converted to adult equivalent WITHOUT details
    - Backend post-processing: `_normalize_size_field()` extracts final size from complex formats
    - Example AI output: `"size": "XS"` (NOT "16Y / 165 cm (≈ XS)")
  - **MANDATORY Fields (November 2025)**: 
    - **condition**: ALWAYS filled, auto-normalized to French via `_normalize_condition_field()`
    - **size**: ALWAYS filled, auto-simplified to adult size via `_normalize_size_field()`
    - AI is instructed to NEVER leave these fields null/empty/undefined
  - **Auto-Polish Function (Nov 2025)**: `_auto_polish_draft()` guarantees 100% publish-ready drafts
    - Strips ALL emojis from title + description
    - Removes ALL marketing phrases ("parfait pour", "idéal", "magnifique", etc.)
    - Normalizes condition to French standard values
    - Simplifies size to adult equivalent only (XS not "16Y/165cm (≈XS)")
    - Adjusts hashtags to 3-5 (adds missing or removes extras)
    - Truncates title to ≤70 chars if needed
    - Auto-adjusts prices with brand multipliers
- **Hashtag Generation**: GPT-4 Vision automatically generates 3-5 relevant hashtags at END of description for better visibility
- **Robust Fallback**: If GPT-4 fails (JSON error, API timeout), `batch_analyze_photos()` ensures photos are preserved in fallback results
- **Image hash-based duplicate detection** (pHash) and **text similarity matching** (rapidfuzz) are used to prevent redundant listings.
- **AI Chat Endpoint**: `/ai/chat` provides a conversational assistant for resale advice.

### Pricing Strategy
- Implements a **three-tier pricing model** (minimum, maximum, target) with AI-driven suggestions.
- **Automated daily price drops** (5% default) are managed by APScheduler, with price floor protection.
- **Price history tracking** records all adjustments.

### Background Jobs
- **APScheduler** manages recurring tasks, such as daily automated price drops.
- Scheduler lifecycle is integrated with the FastAPI application lifespan.

### Data Models (Pydantic Schemas)
- Core models include `Item`, `ItemStatus` (draft, listed, sold, archived), `Condition`, `PriceSuggestion`, and `PriceHistory`.
- Additional models for bulk operations, drafts, and job management.
- **DraftItem Frontend Compatibility (October 2025)**: Added default values for `condition="Bon état"` and `confidence=0.8` to prevent validation errors when legacy drafts are missing these fields. Ensures seamless Lovable.dev frontend integration.

### Export System
- Supports **multi-format exports**: CSV, JSON, PDF (using ReportLab), and Vinted-specific CSV with custom field mapping.
- Provides streaming responses with appropriate content-type headers.

### API Routes Structure
- Dedicated routers for:
    - `/ingest`: Photo upload and AI listing generation.
    - `/listings`: CRUD operations for inventory items.
    - `/pricing`: Price simulation and management.
    - `/export`: Inventory exports.
    - `/import`: CSV import functionality.
    - `/stats`: Analytics and health monitoring.
    - `/bulk`: Multi-photo analysis and draft creation.
        - `/bulk/photos/analyze`: Frontend-compatible photo analysis (returns job_id, plan_id, estimated_items)
            - `auto_grouping=false`: Force single-item (all photos = 1 article)
            - `auto_grouping=true` AND ≤80 photos: Single-item by default
            - `auto_grouping=true` AND >80 photos: Multi-item (GPT-4 Vision clustering)
        - `/bulk/jobs/{job_id}`: Job status polling (reads from PostgreSQL photo_plans)
        - `/bulk/plan`: Create grouping plan with anti-saucisson rules (AI Vision clustering)
        - `/bulk/generate`: Generate validated drafts from plan (strict validation: title≤70, hashtags 3-5)
            - GPT-4 automatically generates 3-5 hashtags in description
        - `/bulk/ingest`: Smart single/multi-item detection and processing
        - `/bulk/drafts/{draft_id}/photos` (NEW Nov 2025): Upload additional photos to existing draft
        - `/bulk/drafts/{draft_id}/publish` (FIXED Nov 2025): Robust photo path resolution prevents "Not Found" errors
    - `/vinted`: Vinted-specific automation (session management, photo upload, listing prepare/publish).

### UI/UX and Design
- **Style Customization**: AI-generated descriptions can be customized (minimal, streetwear, classique).
- **Lovable.dev Integration**: CORS configured for seamless frontend integration, with an OpenAPI client generator available.
- **Mobile-Friendly**: Multi-photo upload endpoints accept various image formats and handle HEIC conversion.

### Vinted Automation
- **Playwright-based automation** for Vinted listing creation and publication.
- Utilizes **encrypted session vault** for secure storage of cookies/user-agents.
- Implements a **two-phase workflow** (prepare and publish) with captcha detection and dry-run capabilities.
- Supports **idempotency** to prevent duplicate publications.

### Production Safeguards & Optimizations (October 2025)
- **Smart Estimation Algorithm**: Frontend shows realistic counts via `max(1, photo_count // 5)` instead of hardcoded "1 article" (18 photos → "3-4 articles estimés")
- **Smart Single-Item Detection**: `/bulk/ingest` and `/bulk/plan` auto-detect when ≤80 photos represent a single item (configurable via `SINGLE_ITEM_DEFAULT_MAX_PHOTOS=80`)
- **Anti-Saucisson Grouping** (`/bulk/plan`): AI Vision clustering with label detection (care labels, brand tags, size labels). Clusters ≤2 photos auto-merge to largest cluster. Never creates label-only articles.
- **Strict Draft Validation** (`/bulk/generate`): 
  - Validates title≤70 chars, hashtags 3-5, NO emojis, NO marketing phrases, all required fields present
  - Sets `flags.publish_ready=true` only after ALL validations pass
  - `DraftItem` schema includes `flags: PublishFlags` and `missing_fields: List[str]` for validation tracking
  - Skips invalid items with clear error messages (zero failed drafts)
- **Realistic Pricing System (October 2025)**:
  - Premium brands (Ralph Lauren, **Karl Lagerfeld**, Diesel, Tommy Hilfiger, Lacoste, Hugo Boss): ×2.0 to ×2.5 multiplier
  - Luxury brands (Burberry, Dior, Gucci, LV, Prada): ×3.0 to ×5.0 multiplier
  - Streetwear (Fear of God Essentials, Supreme, Off-White): ×2.5 to ×3.5 multiplier
  - Example: Short Ralph Lauren bon état = 39€ (not 19€), Hoodie Karl Lagerfeld très bon = 69€
- **Label Auto-Attachment**: AI Vision automatically detects care labels, brand tags, and size labels, then attaches them to the main clothing item (never creates label-only articles)
- **Size Normalization**: Child/teen sizes (16Y, 165cm) auto-converted to adult size equivalents (XS/S/M) with confidence tracking
- **Publication Validation**: `/vinted/listings/prepare` enforces strict validations (title ≤70 chars, 3-5 hashtags, price_suggestion.min|target|max, flags.publish_ready=true) and returns `{ok:false, reason:"NOT_READY"}` on failure
- **Idempotency Protection**: `/vinted/listings/publish` requires `Idempotency-Key` header to prevent duplicate publications
- **Production Mode Enabled**: `dry_run=false` by default - all publications are REAL (not simulations)
- **Secure Logging**: All logs redact sensitive data (cookies, user-agents) - only metadata (lengths, status, latency) is logged
- **Safe Defaults**: All production features enabled via `SAFE_DEFAULTS=true` environment variable

## External Dependencies

### Core Framework & Data Validation
- **FastAPI**: Web framework.
- **Pydantic**: Data validation and settings management.
- **Uvicorn**: ASGI server.

### AI & Image Processing
- **OpenAI API**: GPT-based listing generation and smart grouping.
- **Pillow (PIL)**: Image processing and manipulation.
- **imagehash**: Perceptual hashing for duplicate image detection.
- **rapidfuzz**: Fast fuzzy string matching for text similarity.
- **pillow-heif**: HEIC/HEIF image format support.

### Background Processing
- **APScheduler**: For cron-based job scheduling.

### Data Export
- **ReportLab**: PDF generation.

### HTTP & File Handling
- **requests**: HTTP client.
- **python-multipart**: File upload handling.
- **filetype**: File type detection.
- **boto3**: (Potentially for S3 or cloud storage, though local storage is primary).
- **tenacity**: Retry mechanism.
- **slowapi**: Rate limiting.

### Vinted Automation
- **playwright**: Browser automation.
- **cryptography**: For encryption of session data.