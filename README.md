# VintedBot API - AI-Powered Clothing Resale Assistant

An intelligent FastAPI backend system that automates the process of creating and managing clothing resale listings. The application uses AI to analyze photos and generate complete product listings with pricing suggestions, automated price management, duplicate detection, and comprehensive inventory tracking.

## Features

### 🧠 AI-Powered Listing Generation
- Upload photos (URLs or files) and automatically generate complete product listings
- Generates: title, description, brand, category, size, condition, and keywords
- Intelligent pricing suggestions with min/max/target prices and justification
- Smart mock mode when OpenAI API key is not available

### 📦 Inventory Management
- Complete CRUD operations for items
- Status tracking: draft → listed → sold → archived
- Automatic timestamps and history tracking
- JSON file-based storage for simplicity

### 🔁 Duplicate Detection
- Text similarity matching using rapidfuzz (80% threshold)
- Perceptual image hashing for visual duplicate detection
- Automatic flagging of potential duplicates

### 💸 Automated Pricing
- Daily automatic price drops (5% default) for listed items
- Price floor protection (won't drop below minimum)
- Complete price history tracking
- Price simulation endpoint for testing strategies

### 📊 Statistics & Analytics
- Total items, value, average price
- Top brands analysis
- Duplicate detection counts
- Average days since creation

### 📤 Import/Export
- CSV import/export
- Vinted-compatible CSV export
- JSON export
- PDF export with formatted tables

### 🎁 Bonus Features
- Test photoset generator (creates 5 sample listings)
- Recommendations endpoint (suggests items to relist)
- Multi-price simulation

## Quick Start

The server is already running! Visit:
- **API Documentation**: [/docs](/docs) (Swagger UI)
- **Alternative Docs**: [/redoc](/redoc) (ReDoc)
- **Root**: [/](/) (API info)

## API Endpoints

### Photo Ingestion
- `POST /ingest/photos` - Generate listing from photos
- `POST /ingest/save-draft` - Save generated draft as item

### Listings Management
- `GET /listings/all` - Get all items
- `GET /listings/{id}` - Get single item
- `PUT /listings/{id}` - Update item
- `DELETE /listings/{id}` - Delete item
- `GET /listings/status/{status}` - Get items by status

### Pricing
- `POST /pricing/simulate` - Simulate price trajectory

### Export
- `GET /export/csv` - Export as CSV
- `GET /export/vinted` - Export Vinted-compatible CSV
- `GET /export/json` - Export as JSON
- `GET /export/pdf` - Export as PDF

### Import
- `POST /import/csv` - Import from CSV

### Statistics
- `GET /stats` - Get inventory statistics
- `GET /health` - System health check

### Bonus Features
- `GET /bonus/test/photoset` - Generate 5 test listings
- `GET /bonus/recommendations` - Get relist recommendations
- `POST /bonus/simulate/multi-price` - Simulate multiple price strategies

## Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# Optional - enables real AI generation
OPENAI_API_KEY=your_openai_api_key_here
```

**Note**: If no OpenAI key is provided, the system uses intelligent mock mode with realistic data.

## Architecture

```
backend/
├── app.py                    # Main FastAPI application
├── models/
│   ├── schemas.py           # Pydantic models
│   └── db.py                # JSON database service
├── services/
│   ├── ai.py                # AI listing generation
│   ├── duplicates.py        # Duplicate detection
│   ├── pricing.py           # Price management
│   ├── stats.py             # Statistics calculation
│   └── export.py            # Export services
├── routes/
│   ├── ingest.py            # Photo ingestion routes
│   ├── listings.py          # Listing CRUD routes
│   ├── pricing.py           # Pricing routes
│   ├── export.py            # Export routes
│   ├── import_route.py      # Import routes
│   ├── stats.py             # Stats routes
│   └── bonus.py             # Bonus features
├── jobs/
│   └── scheduler.py         # APScheduler background jobs
└── data/
    ├── items.json           # Item database
    └── uploads/             # Uploaded images
```

## Background Jobs

The system runs a daily cron job (midnight) that automatically applies 5% price drops to all listed items. The scheduler starts automatically with the application.

## Console Notifications

The system provides real-time console notifications:
- 🧠 New AI draft created
- 💸 Price drops applied
- ⚠️ Duplicates detected

## Example Usage

### Generate a listing from photo URL:
```bash
curl -X POST http://localhost:5000/ingest/photos \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/shirt.jpg"]}'
```

### Get statistics:
```bash
curl http://localhost:5000/stats
```

### Export inventory as CSV:
```bash
curl http://localhost:5000/export/csv -o inventory.csv
```

## Dependencies

All dependencies are managed via uv:
- fastapi - Web framework
- uvicorn - ASGI server
- pydantic - Data validation
- apscheduler - Background jobs
- pillow - Image processing
- imagehash - Perceptual hashing
- python-dotenv - Environment management
- rapidfuzz - Text similarity
- pandas - Data processing
- reportlab - PDF generation
- python-multipart - File uploads
- requests - HTTP client

## Future Enhancements

Ready for frontend integration with Lovable.dev or other frameworks:
- Full REST API with OpenAPI documentation
- CORS enabled for all origins
- Clean, documented endpoints

## License

This project is a personal assistant tool for clothing resale automation.
