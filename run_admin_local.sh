#!/usr/bin/env bash

# Скрипт для запуска локальной админки.
# Использует те же переменные окружения и БД, что и бот.
#
# Использование:
#   ./run_admin_local.sh

set -euo pipefail

cd "$(dirname "$0")"

# Активируем виртуальное окружение, если оно есть
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

python3 -m admin.main

