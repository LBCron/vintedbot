# OpenAPI Client for Lovable.dev

## Auto-Generated Files

- `types.ts` - TypeScript interfaces and types
- `client.ts` - API client with all endpoints
- `openapi.json` - Full OpenAPI specification

## Usage in Lovable

Import the types and client in your Lovable frontend:

```typescript
import { api } from './openapi_client/client';
import { Item, Draft, Stats } from './openapi_client/types';

// Use the API client
const stats = await api.get_stats();
const listings = await api.get_all_listings();
const draft = await api.ingest_photos({ urls: ['https://example.com/photo.jpg'] });
```

## Regenerate

To regenerate after API changes:

```bash
python frontend/openapi_client/generate_client.py
```
