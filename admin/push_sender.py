"""Немедленная отправка пушей из админки (без фонового scheduler)."""
import asyncio
import logging
import time
from typing import List, Optional, Tuple

import httpx

from admin.database import AdminDatabase
from admin.config import AdminConfig
from utils.telegram_logger import send_to_logs_group

logger = logging.getLogger("push_sender")

CONCURRENCY = 15
HTTP_TIMEOUT = 10.0


async def get_recipients(send_to_all: bool, target_user_ids) -> List[int]:
    if send_to_all:
        users = await AdminDatabase.fetch("SELECT user_id FROM users")
        return [int(u["user_id"]) for u in users]

    if not target_user_ids:
        return []
    if isinstance(target_user_ids, (list, tuple)):
        return [int(x) for x in target_user_ids]
    return [int(target_user_ids)]


async def send_one(
    client: httpx.AsyncClient,
    user_id: int,
    message: str,
    photo_file_id: Optional[str] = None,
) -> Tuple[bool, Optional[str], int]:
    start = time.perf_counter()
    photo_file_id = (photo_file_id or "").strip() or None

    try:
        if photo_file_id:
            resp = await client.post(
                f"https://api.telegram.org/bot{AdminConfig.BOT_TOKEN}/sendPhoto",
                json={
                    "chat_id": user_id,
                    "photo": photo_file_id,
                    "caption": message,
                    "parse_mode": "HTML",
                },
                timeout=HTTP_TIMEOUT,
            )
        else:
            resp = await client.post(
                f"https://api.telegram.org/bot{AdminConfig.BOT_TOKEN}/sendMessage",
                json={"chat_id": user_id, "text": message, "parse_mode": "HTML"},
                timeout=HTTP_TIMEOUT,
            )

        duration_ms = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:500]}", duration_ms

        data = resp.json()
        if not data.get("ok"):
            return False, f"TG not ok: {str(data)[:500]}", duration_ms

        return True, None, duration_ms
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return False, str(e)[:500], duration_ms


async def process_push(push: dict) -> None:
    push_id = push["id"]
    message = push["message"]
    send_to_all = push["send_to_all"]
    target_user_ids = push.get("target_user_ids")
    photo_file_id = push.get("photo_file_id")

    await AdminDatabase.execute(
        "UPDATE scheduled_pushes SET status = 'processing' WHERE id = $1",
        push_id,
    )

    recipients = await get_recipients(send_to_all, target_user_ids)
    total = len(recipients)

    await AdminDatabase.execute(
        "UPDATE scheduled_pushes SET total_targets = $1 WHERE id = $2",
        total,
        push_id,
    )

    if total == 0:
        await AdminDatabase.execute(
            """
            UPDATE scheduled_pushes
            SET status = 'failed',
                last_error = 'No recipients',
                sent_at = CURRENT_TIMESTAMP,
                success_count = 0,
                fail_count = 0
            WHERE id = $1
            """,
            push_id,
        )
        logger.warning("Push %s: no recipients", push_id)
        return

    sem = asyncio.Semaphore(CONCURRENCY)
    success = 0
    fail = 0

    async with httpx.AsyncClient() as client:

        async def guarded_send(uid: int):
            async with sem:
                return uid, await send_one(client, uid, message, photo_file_id)

        tasks = [asyncio.create_task(guarded_send(uid)) for uid in recipients]
        for task in asyncio.as_completed(tasks):
            uid, (ok, err, duration_ms) = await task
            if ok:
                success += 1
                await AdminDatabase.execute(
                    """
                    INSERT INTO push_delivery_logs (push_id, user_id, status, duration_ms)
                    VALUES ($1, $2, 'sent', $3)
                    """,
                    push_id,
                    uid,
                    duration_ms,
                )
            else:
                fail += 1
                await AdminDatabase.execute(
                    """
                    INSERT INTO push_delivery_logs (push_id, user_id, status, error, duration_ms)
                    VALUES ($1, $2, 'failed', $3, $4)
                    """,
                    push_id,
                    uid,
                    err,
                    duration_ms,
                )

    status = "sent" if fail == 0 else ("sent_with_errors" if success > 0 else "failed")
    last_error = None if fail == 0 else f"{fail} deliveries failed (see push_delivery_logs)"

    await AdminDatabase.execute(
        """
        UPDATE scheduled_pushes
        SET status = $2,
            is_sent = TRUE,
            sent_at = CURRENT_TIMESTAMP,
            success_count = $3,
            fail_count = $4,
            last_error = $5
        WHERE id = $1
        """,
        push_id,
        status,
        success,
        fail,
        last_error,
    )

    try:
        if fail == 0:
            report = f"✅ <b>Пуш #{push_id}</b> доставлен всем <b>{total}</b> получателям."
        else:
            failed_rows = await AdminDatabase.fetch(
                """
                SELECT l.user_id, l.error, u.first_name, u.last_name, u.username
                FROM push_delivery_logs l
                LEFT JOIN users u ON u.user_id = l.user_id
                WHERE l.push_id = $1 AND l.status = 'failed'
                ORDER BY l.user_id
                """,
                push_id,
            )
            lines = []
            for r in failed_rows:
                first = r.get("first_name") or ""
                last = (r.get("last_name") or "").strip()
                name = f"{first} {last}".strip() or "—"
                username = f"@{r['username']}" if r.get("username") else "нет username"
                err = (r.get("error") or "—")[:200]
                lines.append(f"• <code>{r['user_id']}</code> {name} ({username}): {err}")
            failed_block = "\n".join(lines)
            report = (
                f"⚠️ <b>Пуш #{push_id}</b>\n\n"
                f"Всего: {total} | ✅ Доставлено: {success} | ❌ Не доставлено: {fail}\n\n"
                f"<b>Кому не доставлено:</b>\n{failed_block}"
            )
            if len(report) > 4000:
                report = report[:3970] + "\n\n… (обрезано, полный список в админке: Пуши → Лог)"
        await send_to_logs_group(report)
    except Exception as e:
        logger.error("Не удалось отправить отчёт в группу: %s", e)

    if fail > 0:
        logger.error("Push %s: %s failures out of %s", push_id, fail, total)
