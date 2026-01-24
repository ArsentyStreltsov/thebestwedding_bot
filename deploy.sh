#!/usr/bin/env bash

# Простой скрипт для деплоя изменений на GitHub.
# Использование:
#   ./deploy.sh "сообщение коммита"
# или просто ./deploy.sh и затем ввести сообщение с клавиатуры.

set -euo pipefail

cd "$(dirname "$0")"

if git diff --quiet && git diff --cached --quiet; then
  echo "Нет изменений для коммита."
  exit 0
fi

if [ "$#" -gt 0 ]; then
  COMMIT_MESSAGE="$*"
else
  echo "Введите сообщение коммита:"
  read -r COMMIT_MESSAGE
fi

if [ -z "$COMMIT_MESSAGE" ]; then
  echo "Сообщение коммита пустое, выходим."
  exit 1
fi

echo "Добавляем изменения..."
git add -A

echo "Создаём коммит..."
git commit -m "$COMMIT_MESSAGE"

echo "Отправляем на origin main..."
git push origin main

echo "Готово ✅"

