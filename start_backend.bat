@echo off
set PYTHONIOENCODING=utf-8
set DATABASE_URL=sqlite:///backend/data/vbs.db
cd /d "C:\Users\Ronan\OneDrive\桌面\vintedbots"
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
