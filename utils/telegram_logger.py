"""
Утилита для отправки важных логов в Telegram группу
"""
import asyncio
import logging
import httpx
import threading
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения HTTP клиента
_http_client: Optional[httpx.AsyncClient] = None
_sync_http_client: Optional[httpx.Client] = None


async def init_telegram_logger():
    """Инициализация HTTP клиента для отправки сообщений"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=10.0)
    
    global _sync_http_client
    if _sync_http_client is None:
        _sync_http_client = httpx.Client(timeout=10.0)


async def close_telegram_logger():
    """Закрытие HTTP клиента"""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
    
    global _sync_http_client
    if _sync_http_client:
        _sync_http_client.close()
        _sync_http_client = None


def send_to_logs_group_sync(message: str) -> bool:
    """
    Синхронная версия отправки сообщения в группу (для использования в logging handler)
    """
    if not Config.LOGS_GROUP_ID:
        return False
    
    global _sync_http_client
    if not _sync_http_client:
        _sync_http_client = httpx.Client(timeout=10.0)
    
    try:
        url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage"
        response = _sync_http_client.post(
            url,
            json={
                "chat_id": Config.LOGS_GROUP_ID,
                "text": message,
                "parse_mode": "HTML"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("ok", False)
        return False
    except Exception:
        return False


async def send_to_logs_group(message: str) -> bool:
    """
    Отправляет сообщение в группу для логов
    
    Args:
        message: Текст сообщения для отправки
        
    Returns:
        True если отправка успешна, False в противном случае
    """
    if not Config.LOGS_GROUP_ID:
        logger.debug("LOGS_GROUP_ID не установлен, пропускаем отправку")
        return False
    
    if not _http_client:
        await init_telegram_logger()
    
    try:
        url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage"
        response = await _http_client.post(
            url,
            json={
                "chat_id": Config.LOGS_GROUP_ID,
                "text": message,
                "parse_mode": "HTML"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                logger.debug(f"Сообщение успешно отправлено в группу {Config.LOGS_GROUP_ID}")
                return True
            else:
                error_desc = data.get("description", "Unknown error")
                logger.error(f"Не удалось отправить сообщение в группу: {error_desc}. Response: {data}")
                return False
        else:
            logger.error(f"Ошибка HTTP при отправке в группу: {response.status_code}, response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в группу: {e}", exc_info=True)
        return False


class TelegramGroupHandler(logging.Handler):
    """Кастомный handler для отправки ошибок в Telegram группу"""
    
    def emit(self, record: logging.LogRecord):
        """Отправляет только ERROR и CRITICAL логи в группу"""
        if record.levelno >= logging.ERROR:
            try:
                message = self.format(record)
                # Отправляем в отдельном потоке, чтобы не блокировать основной поток
                def send_in_thread():
                    send_to_logs_group_sync(f"❌ <b>Ошибка в боте:</b>\n\n<code>{message}</code>")
                
                thread = threading.Thread(target=send_in_thread, daemon=True)
                thread.start()
            except Exception:
                # Игнорируем ошибки при отправке логов, чтобы не создавать бесконечный цикл
                pass
