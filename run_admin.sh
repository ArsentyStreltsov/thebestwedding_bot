#!/bin/bash

# Скрипт для локального запуска админ-панели
# Использование: ./run_admin.sh

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🖥️  Запуск админ-панели...${NC}"

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}📝 Создайте файл .env на основе .env.example${NC}"
    exit 1
fi

# Проверка наличия обязательных переменных для админки
if ! grep -q "ADMIN_PASSWORD=" .env || grep -q "ADMIN_PASSWORD=your_admin_password_here" .env; then
    echo -e "${RED}❌ ADMIN_PASSWORD не настроен в .env файле!${NC}"
    echo -e "${YELLOW}📝 Укажите пароль для админки в файле .env${NC}"
    exit 1
fi

if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=your-secret-key" .env; then
    echo -e "${RED}❌ SECRET_KEY не настроен в .env файле!${NC}"
    echo -e "${YELLOW}📝 Укажите SECRET_KEY в файле .env${NC}"
    echo -e "${YELLOW}   Можно сгенерировать: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"${NC}"
    exit 1
fi

# Проверка наличия DATABASE_URL
if ! grep -q "DATABASE_URL=" .env || grep -q "DATABASE_URL=postgresql://user:password" .env; then
    echo -e "${RED}❌ DATABASE_URL не настроен в .env файле!${NC}"
    echo -e "${YELLOW}📝 Укажите строку подключения к PostgreSQL в файле .env${NC}"
    exit 1
fi

# Проверка наличия BOT_TOKEN
if ! grep -q "BOT_TOKEN=" .env || grep -q "BOT_TOKEN=your_bot_token_here" .env; then
    echo -e "${RED}❌ BOT_TOKEN не настроен в .env файле!${NC}"
    echo -e "${YELLOW}📝 Укажите токен бота в файле .env${NC}"
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
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Зависимости не установлены${NC}"
    echo -e "${GREEN}📦 Устанавливаем зависимости...${NC}"
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Зависимости установлены${NC}"
fi

# Запуск админки
echo -e "${GREEN}🚀 Запускаем админ-панель...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Админка будет доступна по адресу: http://localhost:8000${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 admin/main.py
