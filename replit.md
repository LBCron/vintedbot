# VintedBot API - AI-Powered Clothing Resale Assistant

## Overview
VintedBot is a FastAPI-based backend system designed to automate and streamline the process of creating and managing clothing resale listings, primarily for platforms like Vinted. It leverages AI to analyze clothing photos, generate comprehensive product listings with pricing suggestions, and manage inventory. The system features automated price adjustments, duplicate detection, and multi-format export capabilities, aiming to simplify the resale workflow and optimize listing creation.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### API Framework
- **FastAPI** provides the core web framework, including automatic OpenAPI documentation.
- **CORS middleware** is configured to allow requests from `https://*.lovable.dev` and other configurable origins.
- **Lifespan context manager** handles application startup and shutdown, including scheduler initialization.
- **JSONResponse wrapper** ensures consistent JSON formatting and CORS compatibility.

### Data Storage
- **File-based JSON database** (`backend/data/items.json`) serves as the persistent storage for all inventory items, eliminating the need for an external database.
- A custom `Database` class handles CRUD operations, using UUIDs for unique item identification.

### AI & Image Processing
- **Dual-mode AI service**: Integrates with OpenAI (GPT-4o Vision) for photo analysis and listing generation when an API key is available, and provides an intelligent mock mode otherwise.
- **Smart AI Grouping**: Analyzes and groups multiple photos by visual similarity to create single listings, identifying unique characteristics and providing confidence scores.
- **Image hash-based duplicate detection** (pHash) and **text similarity matching** (rapidfuzz) are used to prevent redundant listings.
- Supports both image URLs and direct file uploads, including automatic HEIC/HEIF conversion to JPG.
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
        - `/bulk/plan`: Create grouping plan with anti-saucisson rules (AI Vision clustering)
        - `/bulk/generate`: Generate validated drafts from plan (strict validation: title≤70, hashtags 3-5)
        - `/bulk/ingest`: Smart single/multi-item detection and processing
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
- **Smart Single-Item Detection**: `/bulk/ingest` and `/bulk/plan` auto-detect when ≤80 photos represent a single item (configurable via `SINGLE_ITEM_DEFAULT_MAX_PHOTOS=80`)
- **Anti-Saucisson Grouping** (`/bulk/plan`): AI Vision clustering with label detection (care labels, brand tags, size labels). Clusters ≤2 photos auto-merge to largest cluster. Never creates label-only articles.
- **Strict Draft Validation** (`/bulk/generate`): Only creates drafts if publish_ready=true, missing_fields=0, title≤70, hashtags 3-5. Returns clear error otherwise (zero failed drafts).
- **Label Auto-Attachment**: AI Vision automatically detects care labels, brand tags, and size labels, then attaches them to the main clothing item (never creates label-only articles)
- **Publication Validation**: `/vinted/listings/prepare` enforces strict validations (title ≤70 chars, 3-5 hashtags, price_suggestion.min|target|max, flags.publish_ready=true) and returns `{ok:false, reason:"NOT_READY"}` on failure
- **Idempotency Protection**: `/vinted/listings/publish` requires `Idempotency-Key` header to prevent duplicate publications
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