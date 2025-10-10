#!/usr/bin/env bash
set -euo pipefail

echo "--- Ensuring backend virtualenv exists and activating it ---"
if [ ! -d "backend/.venv" ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv backend/.venv
  else
    python -m venv backend/.venv
  fi
fi

if [ -f "backend/.venv/bin/activate" ]; then
  . backend/.venv/bin/activate
elif [ -f "backend/.venv/Scripts/activate" ]; then
  . backend/.venv/Scripts/activate
fi

compute_hash() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v md5sum >/dev/null 2>&1; then
    md5sum "$1" | awk '{print $1}'
  elif command -v certutil >/dev/null 2>&1; then
    certutil -hashfile "$1" SHA256 | sed -n '2p' | tr -d ' \r\n'
  else
    echo ""
  fi
}

echo "--- Installing Python dependencies if needed ---"
REQ_FILE="backend/requirements.txt"
REQ_HASH_FILE="backend/.venv/.requirements_hash"
if [ -f "$REQ_FILE" ]; then
  REQ_HASH=$(compute_hash "$REQ_FILE")
  PREV_HASH=""
  if [ -f "$REQ_HASH_FILE" ]; then
    PREV_HASH=$(cat "$REQ_HASH_FILE")
  fi
  if [ "$REQ_HASH" != "$PREV_HASH" ]; then
    echo "Installing/updating Python packages..."
    pip install -r "$REQ_FILE"
    if [ -n "$REQ_HASH" ]; then
      echo "$REQ_HASH" > "$REQ_HASH_FILE"
    fi
  else
    echo "Python dependencies up-to-date, skipping pip install."
  fi
else
  echo "No requirements.txt found, skipping pip install."
fi

echo "--- Installing frontend dependencies if needed ---"
NODE_PKG="webui/package.json"
NODE_HASH_FILE="webui/.node_deps_hash"
if [ -f "$NODE_PKG" ]; then
  PKG_HASH=$(compute_hash "$NODE_PKG")
  PREV_PKG_HASH=""
  if [ -f "$NODE_HASH_FILE" ]; then
    PREV_PKG_HASH=$(cat "$NODE_HASH_FILE")
  fi
  if [ ! -d "webui/node_modules" ] || [ "$PKG_HASH" != "$PREV_PKG_HASH" ]; then
    echo "Installing/updating frontend packages..."
    ( cd webui && npm install )
    if [ -n "$PKG_HASH" ]; then
      echo "$PKG_HASH" > "$NODE_HASH_FILE"
    fi
  else
    echo "Frontend dependencies up-to-date, skipping npm install."
  fi
else
  echo "No webui/package.json found, skipping npm install."
fi

echo "--- Starting Backend (FastAPI) first ---"
( cd backend && uvicorn main:app --reload --host 127.0.0.1 ) &

echo "--- Waiting for backend to be ready... ---"
sleep 3

echo "--- Starting Frontend (Vite) ---"
( cd webui && npm run dev )
