# VintedBot Frontend

Complete React frontend for VintedBot with AI-powered automation features.

## Features

- 🔐 **Authentication** - JWT-based login/register
- 📤 **Upload** - Drag-drop photo upload with AI analysis
- 📝 **Drafts** - Manage and edit auto-generated listings
- 📊 **Analytics** - Performance dashboard with heatmaps (PREMIUM)
- 🤖 **Automation** - Auto-bump, auto-follow, auto-messages (PREMIUM)
- 👥 **Multi-Account** - Manage multiple Vinted accounts (PREMIUM)
- ⚙️ **Settings** - Profile and subscription management

## Tech Stack

- **React 18** + TypeScript
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first styling
- **React Router** - Client-side routing
- **Axios** - HTTP client with interceptors
- **Lucide React** - Beautiful icons
- **Recharts** - Analytics charts

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env` file:

```
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will run on **http://localhost:5000**

### 4. Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client with JWT interceptor
│   │   └── client.ts
│   ├── components/       # Reusable components
│   │   ├── Layout.tsx
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── QuotaCard.tsx
│   │   ├── DraftCard.tsx
│   │   ├── StatsCard.tsx
│   │   └── HeatmapChart.tsx
│   ├── pages/            # All application pages
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Upload.tsx
│   │   ├── Drafts.tsx
│   │   ├── DraftEdit.tsx
│   │   ├── Analytics.tsx
│   │   ├── Automation.tsx
│   │   ├── Accounts.tsx
│   │   └── Settings.tsx
│   ├── contexts/         # React contexts
│   │   └── AuthContext.tsx
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Integration

### Authentication

```typescript
import { authAPI } from './api/client';

// Register
await authAPI.register({ email, password, name });

// Login
await authAPI.login({ email, password });

// Get user profile
await authAPI.getMe();
```

### Upload Photos

```typescript
import { bulkAPI } from './api/client';

const formData = new FormData();
files.forEach(file => formData.append('files', file));

const response = await bulkAPI.uploadPhotos(formData);
const jobId = response.data.job_id;
```

### Track Progress

```typescript
const job = await bulkAPI.getJob(jobId);
console.log(job.data.progress_percent); // 0-100
```

## Authentication Flow

1. User registers or logs in
2. Backend returns JWT token
3. Frontend stores token in localStorage
4. Axios interceptor adds token to all requests
5. Protected routes check authentication status

## Quota Management

All API endpoints check quotas automatically. When a quota is exceeded, the backend returns HTTP 429 with upgrade message.

## Mobile Responsiveness

- Touch-friendly buttons (min 44px height)
- Responsive grid layouts
- Hamburger menu on mobile
- TailwindCSS breakpoints (sm:, md:, lg:)

## Premium Features

### Analytics Dashboard

- Total views, likes, messages
- Performance heatmap (best posting times)
- Top/bottom performing listings
- Category performance breakdown

### Automation

- **Auto-Bump**: Repost listings automatically
- **Auto-Follow**: Grow followers automatically
- **Auto-Messages**: Send personalized offers to likers

### Multi-Account

- Manage multiple Vinted accounts
- Switch between accounts
- Separate sessions per account

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Port Configuration

- Frontend: Port 5000 (Vite dev server)
- Backend: Port 8000 (FastAPI)
- Proxy: All `/auth`, `/bulk`, `/analytics`, etc. → Backend

## Troubleshooting

### CORS Errors

Make sure backend CORS is configured:

```python
origins = ["http://localhost:5000"]
app.add_middleware(CORSMiddleware, allow_origins=origins)
```

### Token Expiration

JWT tokens expire after 7 days. If you get 401 errors, log in again.

### Upload Fails

Check quotas in Settings page. Free plan has limits on AI analyses and storage.

## License

Proprietary - VintedBot
