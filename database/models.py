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
            is_taken BOOLEAN DEFAULT FALSE,
            taken_by_user_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (taken_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
        )
    """)
    
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
    
    print("База данных успешно инициализирована")
