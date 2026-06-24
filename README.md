# Telegram Bot для свадьбы

ТЕСТ ДЕПЛОЯ АВТОМАТИЧЕСКИ

Бот для общения с гостями свадьбы, управления виш-листом и предоставления полезной информации.

## Функционал

- 💍 **Информация о свадьбе** - дата, место проведения, добавление в календарь
- 👰‍♀️ **Дресс-код** - рекомендации по нарядам
- 🎁 **Виш-лист** - просмотр подарков, отметка забранных товаров
- 📋 **Дисклеймер** - информация о традициях и пожеланиях
- 🎥 **Видео-приглашение** - видео "Save the date"

## Быстрый старт

### Настройка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip3 install -r requirements.txt
```

3. Скопируйте `.env.example` в `.env` и заполните переменные.

## Запуск

### Локальная разработка (с ngrok)

Бот работает через webhook. Для локальной разработки используйте ngrok:

```bash
# Автоматический запуск (рекомендуется)
./run_local_webhook.sh

# Или вручную:
# 1. Запустите ngrok: ngrok http 8002
# 2. Добавьте в .env.local: WEBHOOK_HOST=https://your-ngrok-url.ngrok.io
# 3. Запустите бота: python3 main.py
```

### Продакшн (Hetzner)

Полная инструкция по переносу: [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md)

Кратко:
- Webhook-бот: `main.py` (systemd `thebestwedding-bot`, порт `8002`)
- Админка: `python -m admin.main` (systemd `thebestwedding-admin`, порт `8003`)
- Пуши отправляются **сразу из админки** — отдельного scheduler/worker нет
- Деплой: `git push origin main` → GitHub Actions

## База данных

Бот использует PostgreSQL. При первом запуске автоматически создаются необходимые таблицы:
- `users` - пользователи бота
- `wishlist_items` - товары виш-листа
- `scheduled_pushes` - история рассылок
- `admin_users` - пользователи админ-панели

## Структура проекта

```
thebestwedding_bot/
├── main.py              # Точка входа (webhook)
├── config.py            # Конфигурация
├── database/            # Работа с БД
├── handlers/            # Обработчики сообщений
├── keyboards/           # Клавиатуры
├── admin/               # Админ-панель
│   ├── app.py
│   ├── push_sender.py   # Немедленная отправка пушей
│   └── templates/
├── scripts/deploy-server.sh
├── .github/workflows/deploy.yml
├── docs/MIGRATION_GUIDE.md
└── requirements.txt
```

## Деплой на GitHub

```bash
./deploy.sh "описание изменений"
# или
git push origin main
```

⚠️ **Важно**: `.env` и `.env.local` не должны попадать в git (они в `.gitignore`).

## Админ-панель

Веб-интерфейс для управления ботом: виш-лист и рассылки.

### Локальный запуск

```bash
python3 -m admin.main
# http://localhost:8003
```

### Функционал

- **Виш-лист**: добавление, редактирование, удаление товаров
- **Пуши**: немедленная отправка всем или выборочно (с фото и логом доставки)

### Авторизация

- `ADMIN_USERNAME` (по умолчанию: `admin`)
- `ADMIN_PASSWORD` (обязательно)
- `SECRET_KEY` для JWT

## Безопасность

⚠️ Никогда не коммитьте `.env` в репозиторий.
