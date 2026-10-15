#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_DIR/mysql_data"
SOCKET="$DATA_DIR/mysql.sock"
PID_FILE="$DATA_DIR/mysqld.pid"
LOG_FILE="$DATA_DIR/mysqld.log"
PORT=3307

if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "Local MySQL is already running (PID: $(cat "$PID_FILE"), Port: $PORT)."
    exit 0
fi

echo "Starting local project MySQL server on port $PORT..."
/opt/homebrew/bin/mysqld \
    --datadir="$DATA_DIR" \
    --socket="$SOCKET" \
    --port=$PORT \
    --pid-file="$PID_FILE" \
    --log-error="$LOG_FILE" &

# Wait for socket to become available
for i in {1..30}; do
    if [ -S "$SOCKET" ]; then
        echo "Local MySQL started successfully! (Socket: $SOCKET, Port: $PORT)"
        exit 0
    fi
    sleep 0.2
done

echo "MySQL started, but socket check timed out. Check $LOG_FILE"
