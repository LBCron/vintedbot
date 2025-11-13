FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Playwright dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libglib2.0-0 \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (dependencies already installed above)
RUN playwright install chromium

# Copy application code as backend module
# This maintains the import structure (from backend.X import Y)
RUN mkdir -p /app/backend
COPY . /app/backend/

# Create data directory
RUN mkdir -p /app/backend/data

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application with proper module path
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8001"]
