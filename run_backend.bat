@echo off
echo Starting FastAPI Backend visible to LAN physical devices...
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
