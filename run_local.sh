#!/bin/bash

# Скрипт для локального запуска бота
# Использование: ./run_local.sh

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Запуск Telegram бота локально...${NC}"

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}📝 Создайте файл .env на основе .env.example${NC}"
    echo -e "${YELLOW}   Пример: cp .env.example .env${NC}"
    exit 1
fi

# Проверка наличия BOT_TOKEN в .env
if ! grep -q "BOT_TOKEN=" .env || grep -q "BOT_TOKEN=your_bot_token_here" .env; then
    echo -e "${RED}❌ BOT_TOKEN не настроен в .env файле!${NC}"
    echo -e "${YELLOW}📝 Укажите ваш токен бота в файле .env${NC}"
    exit 1
fi

# Проверка наличия DATABASE_URL в .env
if ! grep -q "DATABASE_URL=" .env || grep -q "DATABASE_URL=postgresql://user:password" .env; then
    echo -e "${RED}❌ DATABASE_URL не настроен в .env файле!${NC}"
    echo -e "${YELLOW}📝 Укажите строку подключения к PostgreSQL в файле .env${NC}"
    exit 1
fi

# Проверка наличия виртуального окружения
if [ ! -d "venv" ] && [ ! -d "env" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено${NC}"
    read -p "Создать виртуальное окружение? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}📦 Создаем виртуальное окружение...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
    fi
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo -e "${GREEN}🔌 Активируем виртуальное окружение...${NC}"
    source venv/bin/activate
elif [ -d "env" ]; then
    echo -e "${GREEN}🔌 Активируем виртуальное окружение...${NC}"
    source env/bin/activate
fi

# Проверка установленных зависимостей
if ! python3 -c "import aiogram" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Зависимости не установлены${NC}"
    echo -e "${GREEN}📦 Устанавливаем зависимости...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Зависимости установлены${NC}"
fi

# Проверка подключения к базе данных
echo -e "${BLUE}🔍 Проверяем подключение к базе данных...${NC}"
if python3 -c "
import asyncio
from config import Config
from database.connection import Database

async def check_db():
    try:
        Config.validate()
        await Database.create_pool()
        await Database.fetchval('SELECT 1')
        print('✅ Подключение к БД успешно')
        await Database.close_pool()
        return True
    except Exception as e:
        print(f'❌ Ошибка подключения к БД: {e}')
        return False

asyncio.run(check_db())
" 2>/dev/null; then
    echo -e "${GREEN}✅ База данных доступна${NC}"
else
    echo -e "${RED}❌ Не удалось подключиться к базе данных${NC}"
    echo -e "${YELLOW}📝 Проверьте настройки DATABASE_URL в .env${NC}"
    exit 1
fi

# Запуск бота
echo -e "${GREEN}🚀 Запускаем бота...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 main.py
