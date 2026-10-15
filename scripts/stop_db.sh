#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_DIR/mysql_data"
PID_FILE="$DATA_DIR/mysqld.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Stopping local MySQL server (PID: $PID)..."
    kill "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo "Local MySQL stopped."
else
    echo "PID file not found. Is local MySQL running?"
fi
