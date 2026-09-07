#!/bin/bash
set -e

echo "=================================================================="
echo " Starting BIS AI Assistant (SIH 2026 - Problem Statement SIH26107)"
echo "=================================================================="

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtualenv..."
    python3 -m venv backend/venv
    ./backend/venv/bin/pip install -r backend/requirements.txt
fi

# Run initial ingestion of Indian Standards if needed
echo "Verifying BIS Standards RAG vector index..."
PYTHONPATH=. ./backend/venv/bin/python backend/app/ingestion/ingest_bis_document.py

# Start Backend Server on Port 8000
echo "Starting FastAPI Backend Server on http://localhost:8000 ..."
PYTHONPATH=. ./backend/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "Backend started with PID $BACKEND_PID."
echo "FastAPI Docs: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/api/health"

# Handle graceful shutdown
trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

wait $BACKEND_PID
