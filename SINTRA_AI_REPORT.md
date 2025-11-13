# VintedBot: Comprehensive Technical Report for Sintra AI

## 1. Project Overview

**VintedBot** is a sophisticated, AI-powered automation platform designed for the Vinted marketplace. It empowers users to streamline their selling process by automating tedious tasks, from listing creation to user interaction. The platform's core feature is its ability to take raw photos of clothing and automatically generate complete, optimized Vinted listings using AI.

### Key Features:

*   **AI-Powered Listing Generation:** Utilizes GPT-4 Vision to analyze product images and automatically generate titles, descriptions, prices, categories, and other relevant details.
*   **Advanced Analytics Dashboard:** Provides users with detailed insights into their sales performance, including heatmaps, top/bottom performing listings, and category-wise analysis. This is a unique feature not found in competing bots.
*   **Intelligent Automation:**
    *   **Auto-Bump:** Automatically re-lists items to keep them at the top of search results.
    *   **Auto-Follow/Unfollow:** Engages with other users by automatically following them and unfollowing those who don't follow back.
    *   **Auto-Messages:** Sends templated messages to new followers or users who like an item, with human-like typing simulation.
*   **Multi-Account Management:** Allows users to manage multiple Vinted accounts from a single interface.
*   **Secure and Robust:** Implements various security and anti-detection measures to protect user accounts and data.
*   **Subscription-Based Model:** Integrates with Stripe for handling user subscriptions and different tiers of service.

## 2. Technical Architecture

VintedBot employs a modern, decoupled architecture with a Python-based backend and a React-based frontend.

*   **Backend:** A powerful FastAPI application that serves a RESTful API, manages the database, handles automation tasks, and communicates with external services like OpenAI and Stripe.
*   **Frontend:** A responsive and user-friendly single-page application (SPA) built with React and TypeScript, providing a rich user interface for interacting with the backend services.
*   **Database:** A combination of SQLite for local development and PostgreSQL for production, with SQLAlchemy and SQLModel for data modeling and querying.
*   **Task Scheduling:** An APScheduler instance runs in the background to execute recurring tasks like auto-bumping and inbox synchronization.
*   **Browser Automation:** Playwright is used to interact with the Vinted website in a human-like manner.

## 3. Backend Details

### 3.1. Core Technologies

*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Web Server:** Uvicorn
*   **Database:**
    *   SQLAlchemy with asyncpg for asynchronous PostgreSQL access.
    *   SQLModel for Pydantic-based ORM.
    *   SQLite for local development and fallback.
*   **Caching:** Redis with `hiredis` for performance.
*   **Authentication:**
    *   JWT (JSON Web Tokens) for securing API endpoints.
    *   `python-jose` and `pyjwt` for token creation and validation.
    *   Argon2 for password hashing.
*   **Security:**
    *   `cryptography` for AES-256 encryption of sensitive data like Vinted session cookies.
    *   Rate limiting on API endpoints to prevent abuse.
    *   CORS configured to allow specific origins.

### 3.2. Key Dependencies

*   **`fastapi`:** The core web framework.
*   **`sqlalchemy[asyncio]` & `asyncpg`:** For asynchronous database interaction.
*   **`sqlmodel`:** For data modeling.
*   **`playwright`:** For browser automation and interaction with Vinted.
*   **`openai`:** To connect to the OpenAI API (GPT-4 Vision) for AI-powered analysis.
*   **`anthropic`:** For Claude API integration (used in monitoring and auto-fix).
*   **`stripe`:** For payment processing and subscription management.
*   **`apscheduler`:** For scheduling and running background jobs.
*   **`sentry-sdk`:** For error tracking and monitoring.
*   **`prometheus-client`:** For exposing application metrics.
*   **`httpx`:** Asynchronous HTTP client for making requests to external services.
*   **`pillow` & `imagehash`:** For image processing and perceptual hashing to detect duplicate images.

### 3.3. API Endpoints

The API is versioned, with the main endpoints under `/api/v1`. Here's a summary of the key routes:

*   **Authentication (`/auth`):** `POST /register`, `POST /login`, `GET /me`
*   **Billing (`/billing`):** `POST /checkout`, `POST /portal`, `POST /webhook`
*   **Bulk Operations (`/bulk`):** `POST /photos/analyze`, `GET /jobs/{job_id}`, `GET /drafts`, `PATCH /drafts/{id}`, `POST /drafts/{id}/publish`
*   **Analytics (`/analytics`):** `GET /dashboard`, `POST /events/view`, `POST /events/like`
*   **Automation (`/automation`):** `GET /rules`, `POST /bump/configure`, `POST /follow/configure`
*   **Accounts (`/accounts`):** For managing multiple Vinted accounts.
*   **Admin (`/admin`):** For super-admin functionalities.

### 3.4. Background Jobs

The `APScheduler` runs the following jobs:

1.  **Inbox Sync:** Every 15 minutes.
2.  **Publish Poll:** Every 30 seconds.
3.  **Price Drop:** Daily at 3 AM.
4.  **Vacuum & Prune:** Daily at 2 AM (database maintenance).
5.  **Clean Temp Photos:** Every 6 hours.
6.  **Automation Executor:** Every 5 minutes (for auto-bump, auto-follow, etc.).

## 4. Frontend Details

### 4.1. Core Technologies

*   **Language:** TypeScript
*   **Framework:** React 18
*   **Build Tool:** Vite
*   **Styling:**
    *   TailwindCSS for utility-first styling.
    *   `clsx` for conditional class names.
    *   `postcss` and `autoprefixer` for CSS processing.
*   **Routing:** `react-router-dom` for client-side routing.
*   **State Management:** React Context API (`AuthContext`, `ThemeContext`).
*   **API Communication:** `axios` for making HTTP requests to the backend.

### 4.2. Key Dependencies

*   **`react` & `react-dom`:** The core React library.
*   **`react-router-dom`:** For routing.
*   **`axios`:** For API communication.
*   **`recharts`:** For creating charts and graphs in the analytics dashboard.
*   **`framer-motion`:** For animations and transitions.
*   **`react-hot-toast`:** For displaying notifications.
*   **`react-dropzone`:** For drag-and-drop file uploads.
*   **`@headlessui/react`:** For unstyled, accessible UI components.
*   **`lucide-react`:** For icons.

### 4.3. Application Structure

*   **`main.tsx`:** The application entry point, which sets up routing and context providers.
*   **`App.tsx`:** The root component that defines the application's routes and layout.
*   **`pages/`:** Contains the main pages of the application (e.g., `Dashboard.tsx`, `Login.tsx`, `Analytics.tsx`).
*   **`components/`:** Contains reusable React components.
*   **`contexts/`:** Contains React context providers for managing global state (e.g., `AuthContext.tsx`).
*   **`api/`:** Contains the API client and functions for interacting with the backend.
*   **`ProtectedRoute.tsx`:** A higher-order component that protects routes from unauthenticated access.

## 5. Database Schema

The database consists of 17 tables, including:

*   **`users`:** Stores user account information.
*   **`vinted_accounts`:** Stores multiple Vinted accounts per user.
*   **`listings`:** Stores information about Vinted listings.
*   **`drafts`:** Stores listings that are not yet published.
*   **`bulk_jobs`:** Tracks the status of AI analysis jobs.
*   **`analytics_events`:** Logs events like views, likes, and messages for analytics.
*   **`automation_rules`:** Stores user-defined automation rules.
*   **`message_templates`:** Stores templates for automated messages.

## 6. Security & Anti-Detection Measures

### Anti-Detection:

*   **Human-like Interaction:** Simulates human behavior with random delays between actions and character-by-character typing in messages.
*   **Robust Selectors:** Uses multiple CSS selectors to interact with Vinted elements, making it less prone to breaking after website updates.
*   **Intelligent Captcha Handling:** Designed to minimize the chances of triggering captchas, for example, by using a draft mode.

### Security:

*   **Secure Authentication:** Uses JWTs with short expiration times and secure password hashing (Argon2).
*   **Data Encryption:** Encrypts sensitive information like Vinted session cookies using AES-256.
*   **Input Validation:** Uses Pydantic for strict data validation on all API inputs.
*   **Rate Limiting:** Protects the API from brute-force attacks and abuse.

## 7. Configuration

The application is configured using environment variables, typically stored in a `.env` file. Key variables include:

*   `OPENAI_API_KEY`: For accessing the OpenAI API.
*   `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, etc.: For Stripe integration.
*   `ALLOWED_ORIGINS`: To configure CORS.
*   `DATABASE_URL`: To connect to the PostgreSQL database.

## 8. Setup and Running

### Backend:

1.  Install Python dependencies: `pip install -r backend/requirements.txt`
2.  Set up environment variables (e.g., `OPENAI_API_KEY`).
3.  Run the backend server: `uvicorn backend.app:app --host 0.0.0.0 --port 8000`

### Frontend:

1.  Navigate to the `frontend` directory: `cd frontend`
2.  Install Node.js dependencies: `bun install` (or `npm install`)
3.  Run the frontend development server: `bun run dev` (or `npm run dev`)

This report provides a comprehensive overview of the VintedBot project. Please let me know if you require further details on any specific part of the application.
