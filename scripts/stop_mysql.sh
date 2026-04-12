#!/bin/zsh
set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$BASE_DIR/mysql-run/mysql.pid"

if [ -f "$PID_FILE" ]; then
  kill "$(cat "$PID_FILE")"
  rm -f "$PID_FILE"
  echo "MySQL stopped."
else
  echo "No MySQL PID file found."
fi
