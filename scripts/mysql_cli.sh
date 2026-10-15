#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOCKET="$PROJECT_DIR/mysql_data/mysql.sock"
PORT=3307

if [ -S "$SOCKET" ]; then
    /opt/homebrew/bin/mysql -u root -S "$SOCKET" "$@"
else
    /opt/homebrew/bin/mysql -u root -h 127.0.0.1 -P $PORT "$@"
fi
