#!/bin/bash
set -euo pipefail

APP_DIR="/home/botapp/thebestwedding_bot"
BOT_SERVICE="thebestwedding-bot"
ADMIN_SERVICE="thebestwedding-admin"

echo "🚀 Ручной деплой на сервере: $BOT_SERVICE + $ADMIN_SERVICE"
echo "========================================================"

cd "$APP_DIR"

if [ -d ".git" ]; then
    git pull origin main
else
    echo "⚠️  Репозиторий не клонирован — используйте rsync или git clone"
fi

sudo -u botapp bash -c "
    cd '$APP_DIR'
    source venv/bin/activate
    pip install -r requirements.txt -q
"

systemctl restart "$BOT_SERVICE"
systemctl restart "$ADMIN_SERVICE"
systemctl is-active "$BOT_SERVICE"
systemctl is-active "$ADMIN_SERVICE"
echo "✅ Деплой завершён"
