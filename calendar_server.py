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
    
    # Напоминание за 3 дня до события в 10:45 (13 мая 2026, 10:45 МСК = 07:45 UTC)
    reminder_date = "20260513T074500Z"  # 13 мая 2026, 07:45 UTC (10:45 МСК)
    
    location = "ЗАГС №4, Бутырская ул., 17, Москва"
    # Координаты ЗАГС №4 (примерные, можно уточнить)
    geo_lat = "55.8075"  # Широта
    geo_lon = "37.5894"  # Долгота
    yandex_maps_url = "https://yandex.ru/maps/-/CLtHE0NM"
    
    description = (
        "Свадьба Стрельцовых!\\n\\n"
        f"📍 Место: {location}\\n"
        f"🗺 Карты: {yandex_maps_url}\\n\\n"
        "После регистрации мы отправимся продолжать праздник в уютный ресторанчик, где мы продолжим кутить!\\n"
        "Мы ещё в процессе выбора места, но как только появится конкретика — сразу обновим информацию здесь 💫\\n\\n"
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
        f"GEO:{geo_lat};{geo_lon}\r\n"
        f"URL:{yandex_maps_url}\r\n"
        "STATUS:CONFIRMED\r\n"
        "SEQUENCE:0\r\n"
        "BEGIN:VALARM\r\n"
        "ACTION:DISPLAY\r\n"
        "DESCRIPTION:Напоминание о свадьбе\r\n"
        f"TRIGGER;VALUE=DATE-TIME:{reminder_date}\r\n"
        "END:VALARM\r\n"
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
