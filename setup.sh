#!/bin/bash

# Скрипт для первоначальной настройки проекта
# Использование: ./setup.sh

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚙️  Настройка проекта Telegram бота...${NC}"

# Создание виртуального окружения
if [ ! -d "venv" ] && [ ! -d "env" ]; then
    echo -e "${GREEN}📦 Создаем виртуальное окружение...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение уже существует${NC}"
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "env" ]; then
    source env/bin/activate
fi

# Установка зависимостей
echo -e "${GREEN}📦 Устанавливаем зависимости...${NC}"
pip3 install --upgrade pip
pip3 install -r requirements.txt
echo -e "${GREEN}✅ Зависимости установлены${NC}"

# Создание .env файла
if [ ! -f ".env" ]; then
    echo -e "${GREEN}📝 Создаем файл .env...${NC}"
    cat > .env << 'EOF'
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/wedding_bot_db

# Admin Configuration (для бота)
ADMIN_USER_IDS=123456789,987654321

# Admin Panel Configuration (для веб-админки)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password_here
SECRET_KEY=your-secret-key-change-this-to-random-string

# Application Settings
DEBUG=False
EOF
    echo -e "${GREEN}✅ Файл .env создан${NC}"
    echo -e "${YELLOW}⚠️  Не забудьте заполнить BOT_TOKEN и DATABASE_URL в файле .env!${NC}"
else
    echo -e "${YELLOW}⚠️  Файл .env уже существует${NC}"
fi

# Проверка Python версии
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Требуется Python 3.8 или выше. Текущая версия: $python_version${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python версия: $python_version${NC}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Настройка завершена!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📝 Следующие шаги:${NC}"
echo -e "   1. Отредактируйте файл .env и укажите:"
echo -e "      - BOT_TOKEN (получите у @BotFather)"
echo -e "      - DATABASE_URL (строка подключения к PostgreSQL)"
echo -e "   2. Запустите бота: ./run_local.sh"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
