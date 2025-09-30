#!/usr/bin/env bash
set -euo pipefail

echo "--- Starting Backend (FastAPI) first ---"
( cd backend && uvicorn main:app --reload --host 127.0.0.1 ) &

echo "--- Waiting for backend to be ready... ---"
sleep 3

echo "--- Starting Frontend (Vite) ---"
( cd webui && npm run dev )
