"""
Простой веб-сервер для отдачи .ics файла для Apple Calendar
Запускается отдельно или может быть интегрирован в основной бот
"""
from flask import Flask, Response
from datetime import datetime
import os

app = Flask(__name__)


def generate_ics_file():
    """Генерирует .ics файл для события свадьбы"""
    # Параметры события
    title = "Свадьба Стрельцовых!"
    # Дата: 16 мая 2026, 10:45 по Москве (UTC+3) = 07:45 UTC
    start_date = "20260516T074500Z"  # 16 мая 2026, 07:45 UTC (10:45 МСК)
    end_date = "20260516T084500Z"    # 16 мая 2026, 08:45 UTC (11:45 МСК)
    
    location = "ЗАГС №4, Бутырская ул., 17, Москва"
    
    description = (
        "Свадьба Стрельцовых!\\n\\n"
        f"📍 Место: {location}\\n\\n"
        "После регистрации мы отправимся продолжать праздник в уютный ресторанчик!\\n\\n"
        "Очень ждём встречи! ✨"
    )
    
    # Формируем .ics файл
    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Wedding Bot//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:wedding-streltsov-20260516@wedding-bot\r\n"
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\r\n"
        f"DTSTART:{start_date}\r\n"
        f"DTEND:{end_date}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{description}\r\n"
        f"LOCATION:{location}\r\n"
        "STATUS:CONFIRMED\r\n"
        "SEQUENCE:0\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    
    return ics_content


@app.route('/wedding.ics')
def wedding_calendar():
    """Endpoint для получения .ics файла свадьбы"""
    ics_content = generate_ics_file()
    
    response = Response(
        ics_content,
        mimetype='text/calendar',
        headers={
            'Content-Disposition': 'attachment; filename=wedding.ics',
            'Content-Type': 'text/calendar; charset=utf-8'
        }
    )
    
    return response


@app.route('/health')
def health():
    """Health check endpoint для Railway"""
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
