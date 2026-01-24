from database.connection import Database


async def init_db() -> None:
    """Инициализация таблиц базы данных"""
    
    # Таблица пользователей
    await Database.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица товаров виш-листа
    await Database.execute("""
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
    # На случай уже существующей таблицы — добавляем недостающие колонки
    await Database.execute(
        "ALTER TABLE wishlist_items ADD COLUMN IF NOT EXISTS price_hint VARCHAR(255)"
    )
    await Database.execute(
        "ALTER TABLE wishlist_items ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0"
    )
    await Database.execute(
        "ALTER TABLE wishlist_items ADD COLUMN IF NOT EXISTS link2 VARCHAR(1000)"
    )
    
    # Таблица полезной информации
    await Database.execute("""
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
    
    # Таблица для будущих викторин
    await Database.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица вопросов викторины
    await Database.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id SERIAL PRIMARY KEY,
            quiz_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            options JSONB NOT NULL,
            correct_answer INTEGER NOT NULL,
            order_index INTEGER DEFAULT 0,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица ответов пользователей на викторины
    await Database.execute("""
        CREATE TABLE IF NOT EXISTS quiz_answers (
            id SERIAL PRIMARY KEY,
            quiz_id INTEGER NOT NULL,
            user_id BIGINT NOT NULL,
            question_id INTEGER NOT NULL,
            answer INTEGER NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица запланированных пушей
    await Database.execute("""
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
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS last_error TEXT"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS total_targets INT DEFAULT 0"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS success_count INT DEFAULT 0"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS fail_count INT DEFAULT 0"
    )
    
    # Обновляем существующие записи: если is_sent=TRUE, ставим status='sent'
    await Database.execute("""
        UPDATE scheduled_pushes 
        SET status = CASE 
            WHEN is_sent = TRUE THEN 'sent'
            ELSE 'pending'
        END
        WHERE status IS NULL OR status = ''
    """)
    
    # Таблица логов доставки пушей
    await Database.execute("""
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
    await Database.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_pending
        ON scheduled_pushes(status, scheduled_at)
    """)
    await Database.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_logs_push
        ON push_delivery_logs(push_id)
    """)
    
    # Миграции для улучшенной логики пушей
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS attempts INT DEFAULT 0"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS last_error TEXT"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS total_targets INT DEFAULT 0"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS success_count INT DEFAULT 0"
    )
    await Database.execute(
        "ALTER TABLE scheduled_pushes ADD COLUMN IF NOT EXISTS fail_count INT DEFAULT 0"
    )
    
    # Таблица логов доставки пушей
    await Database.execute("""
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
    await Database.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_pending
        ON scheduled_pushes(status, scheduled_at)
    """)
    await Database.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_logs_push
        ON push_delivery_logs(push_id)
    """)
    
    # Таблица админов для веб-админки
    await Database.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # База данных успешно инициализирована
