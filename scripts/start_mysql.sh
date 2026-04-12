#!/bin/zsh
set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$BASE_DIR/mysql-data"
RUN_DIR="$BASE_DIR/mysql-run"
TMP_DIR="$BASE_DIR/mysql-tmp"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/mysql.log"
SOCKET_FILE="$RUN_DIR/mysql.sock"
PID_FILE="$RUN_DIR/mysql.pid"
MYSQLD_BIN="/opt/anaconda3/bin/mysqld"
MYSQL_BIN="/opt/anaconda3/bin/mysql"
MYSQL_SHARE="/opt/anaconda3/share/mysql"

mkdir -p "$DATA_DIR" "$RUN_DIR" "$TMP_DIR" "$LOG_DIR"

if [ ! -f "$DATA_DIR/auto.cnf" ]; then
  "$MYSQLD_BIN" --initialize-insecure --basedir=/opt/anaconda3 --datadir="$DATA_DIR" --lc-messages-dir="$MYSQL_SHARE"
fi

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "MySQL is already running."
else
  nohup "$MYSQLD_BIN" \
    --basedir=/opt/anaconda3 \
    --datadir="$DATA_DIR" \
    --socket="$SOCKET_FILE" \
    --pid-file="$PID_FILE" \
    --skip-networking \
    --lc-messages-dir="$MYSQL_SHARE" \
    --tmpdir="$TMP_DIR" > "$LOG_FILE" 2>&1 &
fi

for _ in {1..20}; do
  if [ -S "$SOCKET_FILE" ]; then
    break
  fi
  sleep 1
done

"$MYSQL_BIN" --socket="$SOCKET_FILE" -u root -e "CREATE DATABASE IF NOT EXISTS smart_resource_allocation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS 'resource_admin'@'localhost' IDENTIFIED BY 'resource123'; GRANT ALL PRIVILEGES ON *.* TO 'resource_admin'@'localhost'; FLUSH PRIVILEGES;"

echo "MySQL is ready on socket: $SOCKET_FILE"
