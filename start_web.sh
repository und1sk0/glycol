#!/bin/bash
# Quick launcher for Glycol Web Server

set -e

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Default values
HOST="${GLYCOL_HOST:-127.0.0.1}"
PORT="${GLYCOL_PORT:-8666}"

echo "Starting Glycol Web Server..."
echo "Server will be available at http://${HOST}:${PORT}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the web server
python web_server.py --host "$HOST" --port "$PORT" "$@"
