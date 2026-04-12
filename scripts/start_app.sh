#!/bin/zsh
set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$BASE_DIR/../.venv/bin/python"

"$BASE_DIR/scripts/start_mysql.sh"
cd "$BASE_DIR"
"$VENV_PYTHON" manage.py migrate
"$VENV_PYTHON" manage.py seed_data
"$VENV_PYTHON" manage.py runserver localhost:8000
