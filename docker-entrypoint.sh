#!/bin/bash
set -e

# Start backend
echo "Starting FinanceAI backend on port ${BACKEND_PORT:-8001}..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${BACKEND_PORT:-8001} &

# Start frontend
echo "Starting FinanceAI frontend on port ${FRONTEND_PORT:-3000}..."
cd /app/web
node server.js &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
