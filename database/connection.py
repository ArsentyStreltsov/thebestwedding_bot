import asyncpg
from typing import Optional
from config import Config


class Database:
    """Класс для работы с базой данных PostgreSQL"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def create_pool(cls) -> None:
        """Создание пула подключений к БД"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                Config.DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
    
    @classmethod
    async def close_pool(cls) -> None:
        """Закрытие пула подключений"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
    
    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Выполнение запроса без возврата результата"""
        async with cls._pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    @classmethod
    async def fetch(cls, query: str, *args) -> list:
        """Выполнение запроса с возвратом списка строк"""
        async with cls._pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    @classmethod
    async def fetchrow(cls, query: str, *args) -> Optional[dict]:
        """Выполнение запроса с возвратом одной строки"""
        async with cls._pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None
    
    @classmethod
    async def fetchval(cls, query: str, *args) -> Optional[any]:
        """Выполнение запроса с возвратом одного значения"""
        async with cls._pool.acquire() as connection:
            return await connection.fetchval(query, *args)
