#!/bin/bash

# Скрипт для локального запуска бота с webhook через ngrok
# Использование: ./run_local_webhook.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск Telegram бота с webhook через ngrok...${NC}"

# Проверка наличия .env.local файла
if [ ! -f ".env.local" ]; then
    echo -e "${RED}❌ Файл .env.local не найден!${NC}"
    echo -e "${YELLOW}📝 Создайте файл .env.local на основе .env${NC}"
    exit 1
fi

# Проверка наличия ngrok
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok не установлен!${NC}"
    echo -e "${YELLOW}📝 Установите ngrok:${NC}"
    echo -e "${YELLOW}   macOS: brew install ngrok${NC}"
    echo -e "${YELLOW}   Или скачайте с https://ngrok.com/download${NC}"
    exit 1
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo -e "${BLUE}🔌 Активируем виртуальное окружение...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено. Создайте его: python3 -m venv venv${NC}"
    exit 1
fi

# Запуск ngrok в фоне
echo -e "${BLUE}🌐 Запускаем ngrok на порту 8001...${NC}"
ngrok http 8001 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Ждём немного, чтобы ngrok запустился
sleep 3

# Получаем URL из ngrok
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1)

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ Не удалось получить URL от ngrok${NC}"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ ngrok запущен: ${NGROK_URL}${NC}"

# Обновляем .env.local с URL ngrok
if grep -q "WEBHOOK_HOST=" .env.local; then
    # Заменяем существующий WEBHOOK_HOST
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|WEBHOOK_HOST=.*|WEBHOOK_HOST=${NGROK_URL}|" .env.local
    else
        # Linux
        sed -i "s|WEBHOOK_HOST=.*|WEBHOOK_HOST=${NGROK_URL}|" .env.local
    fi
else
    # Добавляем WEBHOOK_HOST
    echo "WEBHOOK_HOST=${NGROK_URL}" >> .env.local
fi

echo -e "${GREEN}✅ WEBHOOK_HOST обновлён в .env.local${NC}"

# Функция для очистки при выходе
cleanup() {
    echo -e "\n${YELLOW}🛑 Останавливаем ngrok...${NC}"
    kill $NGROK_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Очистка завершена${NC}"
}

trap cleanup EXIT INT TERM

# Запуск бота
echo -e "${BLUE}🤖 Запускаем бота...${NC}"
python3 main.py
