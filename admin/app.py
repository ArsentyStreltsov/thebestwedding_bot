from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta, timezone
import asyncio
from typing import Optional, List
from admin.database import AdminDatabase
from admin.auth import verify_password, get_password_hash, create_access_token, verify_token
from admin.config import AdminConfig
import httpx

# Московское время (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

app = FastAPI(title="Wedding Bot Admin Panel")
templates = Jinja2Templates(directory="admin/templates")

# Инициализация БД при старте
@app.on_event("startup")
async def startup():
    AdminConfig.validate()
    await AdminDatabase.create_pool()
    # Создаем таблицы, если их нет
    await init_admin_db()
    # Создаем админа по умолчанию, если его нет
    await create_default_admin()


async def init_admin_db():
    """Инициализация таблиц базы данных для админки"""
    # Создаем таблицы, которые могут отсутствовать
    await AdminDatabase.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await AdminDatabase.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_pushes (
            id SERIAL PRIMARY KEY,
            message TEXT NOT NULL,
            send_to_all BOOLEAN DEFAULT TRUE,
            target_user_ids BIGINT[],
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            is_sent BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Миграции для улучшенной логики пушей
    await AdminDatabase.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'"
    )
    await AdminDatabase.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP"
    )
    await AdminDatabase.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0"
    )
    await AdminDatabase.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS last_error TEXT"
    )
    await AdminDatabase.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS total_targets INT DEFAULT 0"
    )
    await AdminDatabase.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS success_count INT DEFAULT 0"
    )
    await AdminDatabase.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS fail_count INT DEFAULT 0"
    )
    
    # Обновляем существующие записи
    await AdminDatabase.execute("""
        UPDATE scheduled_pushes 
        SET status = CASE 
            WHEN is_sent = TRUE THEN 'sent'
            ELSE 'pending'
        END
        WHERE status IS NULL OR status = ''
    """)
    
    # Таблица логов доставки пушей
    await AdminDatabase.execute("""
        CREATE TABLE IF NOT EXISTS push_delivery_logs (
            id SERIAL PRIMARY KEY,
            push_id INT NOT NULL REFERENCES scheduled_pushes(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            duration_ms INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индексы для производительности
    await AdminDatabase.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_pending
        ON scheduled_pushes(status, scheduled_at)
    """)
    await AdminDatabase.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_logs_push
        ON push_delivery_logs(push_id)
    """)
    
    # Также создаем остальные таблицы, если их нет (для совместимости)
    await AdminDatabase.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await AdminDatabase.execute("""
        CREATE TABLE IF NOT EXISTS wishlist_items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500) NOT NULL,
            description TEXT,
            link VARCHAR(1000),
            link2 VARCHAR(1000),
            price_hint VARCHAR(255),
            order_index INTEGER DEFAULT 0,
            is_taken BOOLEAN DEFAULT FALSE,
            taken_by_user_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (taken_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
        )
    """)
    # Обновляем существующую таблицу при необходимости
    await AdminDatabase.execute(
        "ALTER TABLE wishlist_items ADD COLUMN IF NOT EXISTS price_hint VARCHAR(255)"
    )
    await AdminDatabase.execute(
        "ALTER TABLE wishlist_items ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0"
    )
    await AdminDatabase.execute(
        "ALTER TABLE wishlist_items ADD COLUMN IF NOT EXISTS link2 VARCHAR(1000)"
    )
    
    await AdminDatabase.execute("""
        CREATE TABLE IF NOT EXISTS wedding_info (
            id SERIAL PRIMARY KEY,
            section VARCHAR(100) NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


@app.on_event("shutdown")
async def shutdown():
    await AdminDatabase.close_pool()


async def create_default_admin():
    """Создание админа по умолчанию"""
    existing = await AdminDatabase.fetchrow(
        "SELECT id FROM admin_users WHERE username = $1",
        AdminConfig.ADMIN_USERNAME
    )
    if not existing:
        password_hash = get_password_hash(AdminConfig.ADMIN_PASSWORD)
        await AdminDatabase.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES ($1, $2)",
            AdminConfig.ADMIN_USERNAME,
            password_hash
        )


# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Авторизация
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = await AdminDatabase.fetchrow(
        "SELECT * FROM admin_users WHERE username = $1",
        username
    )
    
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"}
        )
    
    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    
    try:
        from jose import jwt
        payload = jwt.decode(token, AdminConfig.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
    except:
        return RedirectResponse(url="/", status_code=303)
    
    # Статистика
    users_count = await AdminDatabase.fetchval("SELECT COUNT(*) FROM users")
    wishlist_count = await AdminDatabase.fetchval("SELECT COUNT(*) FROM wishlist_items")
    pending_pushes = await AdminDatabase.fetchval(
        "SELECT COUNT(*) FROM scheduled_pushes WHERE is_sent = FALSE"
    )
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "username": username,
            "users_count": users_count,
            "wishlist_count": wishlist_count,
            "pending_pushes": pending_pushes
        }
    )


# Выход
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response


# ========== ВИШ-ЛИСТ ==========

@app.get("/wishlist", response_class=HTMLResponse)
async def wishlist_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    
    items = await AdminDatabase.fetch(
        "SELECT * FROM wishlist_items ORDER BY is_taken, order_index, created_at"
    )
    return templates.TemplateResponse(
        "wishlist.html",
        {"request": request, "items": [dict(item) for item in items]}
    )


@app.post("/wishlist/add")
async def wishlist_add(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    link: str = Form(""),
    link2: str = Form(""),
    price_hint: str = Form(""),
    order_index: int = Form(0)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    
    # Определяем order_index, если он не задан явно
    if not order_index:
        max_order = await AdminDatabase.fetchval(
            "SELECT COALESCE(MAX(order_index), 0) FROM wishlist_items"
        )
        order_index = max_order + 1
    
    await AdminDatabase.execute(
        "INSERT INTO wishlist_items (name, description, link, link2, price_hint, order_index) "
        "VALUES ($1, $2, $3, $4, $5, $6)",
        name, description, link, link2, price_hint, order_index
    )
    return RedirectResponse(url="/wishlist", status_code=303)


@app.post("/wishlist/{item_id}/delete")
async def wishlist_delete(request: Request, item_id: int):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    
    await AdminDatabase.execute("DELETE FROM wishlist_items WHERE id = $1", item_id)
    return RedirectResponse(url="/wishlist", status_code=303)


@app.post("/wishlist/{item_id}/edit")
async def wishlist_edit(
    request: Request,
    item_id: int,
    name: str = Form(...),
    description: str = Form(""),
    link: str = Form(""),
    link2: str = Form(""),
    price_hint: str = Form(""),
    order_index: int = Form(0)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    
    await AdminDatabase.execute(
        """
        UPDATE wishlist_items
        SET name = $1,
            description = $2,
            link = $3,
            link2 = $4,
            price_hint = $5,
            order_index = $6,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $7
        """,
        name, description, link, link2, price_hint, order_index, item_id
    )
    return RedirectResponse(url="/wishlist", status_code=303)


# ========== ПУШИ ==========

@app.get("/pushes", response_class=HTMLResponse)
async def pushes_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    
    pushes = await AdminDatabase.fetch(
        "SELECT * FROM scheduled_pushes ORDER BY created_at DESC LIMIT 50"
    )
    users = await AdminDatabase.fetch("SELECT user_id, first_name, username FROM users")
    
    # Конвертируем время из UTC в московское для отображения
    pushes_list = []
    for push in pushes:
        push_dict = dict(push)
        # Конвертируем scheduled_at из UTC в московское время
        if push_dict.get("scheduled_at"):
            if isinstance(push_dict["scheduled_at"], datetime):
                if push_dict["scheduled_at"].tzinfo is None:
                    # Если время без timezone, считаем его UTC
                    utc_time = push_dict["scheduled_at"].replace(tzinfo=timezone.utc)
                else:
                    utc_time = push_dict["scheduled_at"].astimezone(timezone.utc)
                push_dict["scheduled_at"] = utc_time.astimezone(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:%S")
        # Конвертируем sent_at из UTC в московское время
        if push_dict.get("sent_at"):
            if isinstance(push_dict["sent_at"], datetime):
                if push_dict["sent_at"].tzinfo is None:
                    utc_time = push_dict["sent_at"].replace(tzinfo=timezone.utc)
                else:
                    utc_time = push_dict["sent_at"].astimezone(timezone.utc)
                push_dict["sent_at"] = utc_time.astimezone(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:%S")
        pushes_list.append(push_dict)
    
    return templates.TemplateResponse(
        "pushes.html",
        {
            "request": request,
            "pushes": pushes_list,
            "users": [dict(u) for u in users]
        }
    )


@app.post("/pushes/send")
async def push_send(
    request: Request,
    message: str = Form(...),
    send_to_all: bool = Form(False),
    target_user_ids: str = Form(""),
    scheduled_at: str = Form("")
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    
    # Парсим target_user_ids
    user_ids = []
    if not send_to_all and target_user_ids:
        user_ids = [int(uid.strip()) for uid in target_user_ids.split(",") if uid.strip().isdigit()]
    
    # Парсим scheduled_at
    scheduled_time = None
    if scheduled_at:
        try:
            # Парсим время из формы (локальное время браузера, но без timezone)
            # Предполагаем, что это московское время (UTC+3)
            local_time = datetime.fromisoformat(scheduled_at.replace('Z', ''))
            # Добавляем московский часовой пояс
            moscow_time = local_time.replace(tzinfo=MOSCOW_TZ)
            # Конвертируем в UTC для хранения в БД
            utc_time = moscow_time.astimezone(timezone.utc)
            # Убираем timezone для сохранения в БД (asyncpg требует naive datetime)
            scheduled_time = utc_time.replace(tzinfo=None)
            # Проверяем, не в прошлом ли время (в UTC)
            if scheduled_time <= datetime.utcnow():
                scheduled_time = None
        except Exception as e:
            print(f"Ошибка парсинга времени: {e}")
            scheduled_time = None
    
    # Преобразуем список в массив PostgreSQL
    user_ids_array = user_ids if user_ids else []
    
    # Если время не указано или в прошлом, ставим scheduled_at = CURRENT_TIMESTAMP
    # Scheduler заберёт и отправит немедленно
    if not scheduled_time:
        scheduled_time = None  # Будет установлено в CURRENT_TIMESTAMP на стороне БД
    
    # Всегда создаём запись в БД со статусом 'pending'
    # Scheduler заберёт и отправит (единый путь для всех пушей)
    await AdminDatabase.execute(
        """INSERT INTO scheduled_pushes (message, send_to_all, target_user_ids, scheduled_at, status)
           VALUES ($1, $2, $3, COALESCE($4, CURRENT_TIMESTAMP), 'pending')""",
        message, send_to_all, user_ids_array, scheduled_time
    )
    
    return RedirectResponse(url="/pushes", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
