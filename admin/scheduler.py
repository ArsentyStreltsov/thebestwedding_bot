"""
Фоновый процесс для отправки запланированных пушей
Запускается отдельно или интегрируется в основной бот
"""
import asyncio
from datetime import datetime, timezone
from admin.database import AdminDatabase
from admin.config import AdminConfig
import httpx


async def send_scheduled_pushes():
    """Проверка и отправка запланированных пушей"""
    # Проверяем, что pool инициализирован
    if AdminDatabase._pool is None:
        print("⚠️  AdminDatabase не инициализирован, scheduler не будет работать")
        return
    
    while True:
        try:
            # Получаем пушы, которые нужно отправить
            pushes = await AdminDatabase.fetch(
                """SELECT * FROM scheduled_pushes 
                   WHERE is_sent = FALSE 
                   AND (scheduled_at IS NULL OR scheduled_at <= CURRENT_TIMESTAMP)"""
            )
            
            for push in pushes:
                push_dict = dict(push)
                message = push_dict["message"]
                send_to_all = push_dict["send_to_all"]
                target_user_ids = push_dict.get("target_user_ids") or []
                
                # Получаем список пользователей
                if send_to_all:
                    users = await AdminDatabase.fetch("SELECT user_id FROM users")
                    user_ids = [u["user_id"] for u in users]
                else:
                    # Преобразуем массив PostgreSQL в список Python
                    if target_user_ids:
                        user_ids = list(target_user_ids) if isinstance(target_user_ids, (list, tuple)) else [target_user_ids]
                    else:
                        user_ids = []
                
                # Отправляем пуш
                success_count = 0
                async with httpx.AsyncClient() as client:
                    for user_id in user_ids:
                        try:
                            await client.post(
                                f"https://api.telegram.org/bot{AdminConfig.BOT_TOKEN}/sendMessage",
                                json={
                                    "chat_id": user_id,
                                    "text": message,
                                    "parse_mode": "HTML"
                                },
                                timeout=10.0
                            )
                            success_count += 1
                        except Exception as e:
                            print(f"Ошибка отправки пуша пользователю {user_id}: {e}")
                
                # Отмечаем как отправленное
                await AdminDatabase.execute(
                    "UPDATE scheduled_pushes SET is_sent = TRUE, sent_at = CURRENT_TIMESTAMP WHERE id = $1",
                    push_dict["id"]
                )
                
                print(f"Пуш {push_dict['id']} отправлен {success_count} пользователям")
            
            # Ждем 60 секунд перед следующей проверкой
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"Ошибка в scheduler: {e}")
            await asyncio.sleep(60)


if __name__ == "__main__":
    async def main():
        AdminConfig.validate()
        await AdminDatabase.create_pool()
        await send_scheduled_pushes()
    
    asyncio.run(main())
