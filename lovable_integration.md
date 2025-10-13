# Lovable Integration Guide

## 🎯 Overview

This guide explains how to connect your Lovable.dev frontend to the VintedBot FastAPI backend.

## 🔗 Base URL Configuration

In your Lovable project, define the API base URL as an environment variable:

```bash
# In Lovable Environment Variables
VITE_API_BASE_URL=https://your-replit-app.replit.app
```

For local development:
```bash
VITE_API_BASE_URL=http://localhost:5000
```

## 📡 API Endpoints

### Core Endpoints

| Endpoint | Method | Description | Request Body | Response |
|----------|--------|-------------|--------------|----------|
| `/health` | GET | System health status | - | `{"status": "healthy", "uptime_seconds": 123.45, "version": "1.0.0", "scheduler_jobs": 1}` |
| `/stats` | GET | Inventory statistics | - | `{"total_items": 42, "total_value": 1250.0, "avg_price": 29.76, ...}` |
| `/ingest/photos` | POST | Create draft from photos | `{"urls": ["url1", "url2"]}` | Draft object with AI-generated data |
| `/ingest/save-draft` | POST | Save draft as item | Draft object | Item object with ID |
| `/listings/all` | GET | Get all listings | - | Array of items |
| `/listings/{id}` | GET | Get single item | - | Item object |
| `/listings/{id}` | PUT | Update item | Item object | Updated item |
| `/listings/{id}` | DELETE | Delete item | - | `{"message": "Item deleted successfully"}` |
| `/listings/publish/{id}` | POST | Mark as published | - | Updated item with status="listed" |
| `/listings/status/{status}` | GET | Get items by status | - | Array of items |

### Export Endpoints

| Endpoint | Method | Description | Response Type |
|----------|--------|-------------|---------------|
| `/export/csv` | GET | Export as CSV | text/csv |
| `/export/vinted` | GET | Export Vinted CSV | text/csv |
| `/export/json` | GET | Export as JSON | application/json |
| `/export/pdf` | GET | Export as PDF | application/pdf |

### Import Endpoint

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/import/csv` | POST | Import from CSV | File upload | `{"message": "...", "items": [...]}` |

### Pricing & Bonus

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/pricing/simulate` | POST | Simulate price drops | `{"initial_price": 50, "min_price": 20, "days": 30}` | Array of simulation results |
| `/bonus/test/photoset` | GET | Generate 5 test listings | - | Array of 5 drafts |
| `/bonus/recommendations` | GET | Get relist suggestions | - | Array of recommended items |

## 💻 Frontend Integration Examples

### Fetch API (TypeScript/JavaScript)

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL;

// Get health status
async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  const data = await response.json();
  return data;
}

// Create listing from photo
async function createListing(photoUrls: string[]) {
  const response = await fetch(`${API_BASE}/ingest/photos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ urls: photoUrls }),
  });
  const draft = await response.json();
  return draft;
}

// Get all listings
async function getAllListings() {
  const response = await fetch(`${API_BASE}/listings/all`);
  const items = await response.json();
  return items;
}

// Publish an item
async function publishItem(itemId: string) {
  const response = await fetch(`${API_BASE}/listings/publish/${itemId}`, {
    method: 'POST',
  });
  const item = await response.json();
  return item;
}

// Get statistics
async function getStats() {
  const response = await fetch(`${API_BASE}/stats`);
  const stats = await response.json();
  return stats;
}
```

### Axios (Alternative)

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get stats
const stats = await api.get('/stats');

// Create listing
const draft = await api.post('/ingest/photos', {
  urls: ['https://example.com/photo.jpg'],
});

// Publish item
const published = await api.post(`/listings/publish/${itemId}`);
```

## 🔐 CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:3000`
- `http://localhost:5173` (Vite default)
- `https://*.lovable.dev`
- `https://*.lovable.app`

CORS headers include:
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`
- `Access-Control-Allow-Credentials: true`

## 📋 Data Models

### Item
```typescript
interface Item {
  id: string;
  title: string;
  description: string;
  brand?: string;
  category?: string;
  size?: string;
  condition?: "new_with_tags" | "new_without_tags" | "very_good" | "good" | "satisfactory";
  price: number;
  price_suggestion?: {
    min: number;
    max: number;
    target: number;
    justification: string;
  };
  keywords: string[];
  image_urls: string[];
  status: "draft" | "listed" | "sold" | "archived";
  possible_duplicate: boolean;
  estimated_sale_score?: number;
  created_at: string;
  updated_at: string;
}
```

### Draft
```typescript
interface Draft {
  title: string;
  description: string;
  brand?: string;
  category_guess?: string;
  condition?: string;
  size_guess?: string;
  keywords: string[];
  price_suggestion: {
    min: number;
    max: number;
    target: number;
    justification: string;
  };
  image_urls: string[];
  possible_duplicate: boolean;
  estimated_sale_score?: number;
}
```

## 🧪 Testing

Run the integration test suite:
```bash
python test_lovable.py
```

Or test individual endpoints:
```bash
# Health check
curl https://your-app.replit.app/health

# Get stats
curl https://your-app.replit.app/stats

# Create listing
curl -X POST https://your-app.replit.app/ingest/photos \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/photo.jpg"]}'
```

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `https://your-app.replit.app/docs`
- **ReDoc**: `https://your-app.replit.app/redoc`

## ✅ Pre-Launch Checklist

- [ ] Environment variable `VITE_API_BASE_URL` is set in Lovable
- [ ] Backend is deployed and accessible via public URL
- [ ] CORS origins include your Lovable domain
- [ ] All endpoints return proper JSON responses
- [ ] Integration tests pass (`python test_lovable.py`)
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] Frontend can fetch from `/stats` successfully

## 🚀 Quick Start

1. **Deploy Backend**: Ensure your Replit backend is running on port 5000
2. **Set Environment Variable**: In Lovable, add `VITE_API_BASE_URL=https://your-app.replit.app`
3. **Test Connection**: Make a test request to `/health` from your frontend
4. **Start Building**: Use the endpoints above to build your UI

## 💡 Tips

- Always handle loading and error states in your frontend
- Use TypeScript interfaces for type safety
- Implement retry logic for network failures
- Cache frequently accessed data (stats, listings)
- Show user feedback for all async operations

---

✅ **Your VintedBot backend is now ready for Lovable.dev integration!**

For support, check the [API Documentation](https://your-app.replit.app/docs) or review the test file `test_lovable.py`.
