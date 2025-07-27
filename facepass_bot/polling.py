# polling.py
# Опрос API турникета и отправка уведомлений родителям

import time
import requests
import db
import utils
from telegram import Bot
from config import BOT_TOKEN
from datetime import datetime

# Инициализируем бот и БД
bot = Bot(token=BOT_TOKEN)
db.init_db()

def handle_event(student_id: str, direction: str, timestamp: str = None):
    """
    Сохраняет событие в БД и отправляет сообщение родителю.
    """
    # 1) Сохраняем событие
    db.add_event(student_id, direction)

    # 2) Готовим и отправляем сообщение
    ts = timestamp or datetime.now().strftime("%H:%M:%S")
    students = utils.load_students()
    for s in students:
        if s["student_id"] == student_id and s.get("telegram_chat_id"):
            msg = (
                f"🎓 {s['name']}\n"
                f"⏰ {ts}\n"
                f"➡️ {direction}"
            )
            bot.send_message(chat_id=s["telegram_chat_id"], text=msg)
            print(f"Уведомление отправлено: {s['name']} — {direction} в {ts}")
            break

def run_polling():
    """
    Основной цикл: опрашивает API каждые 5 секунд,
    получает новые события и обрабатывает их.
    """
    API_URL = "https://api.univer.example/events" 
    last_ts = None
    print("Запуск polling. Ожидание событий...")

    while True:
        params = {"since": last_ts} if last_ts else {}
        try:
            resp = requests.get(API_URL, params=params, timeout=10)
            resp.raise_for_status()
            events = resp.json()  # list of dicts: {"student_id","direction","timestamp"}

            for ev in events:
                handle_event(ev["student_id"], ev["direction"], ev.get("timestamp"))
                last_ts = ev.get("timestamp", last_ts)

        except Exception as e:
            print(f"Ошибка polling: {e}")

        time.sleep(5)


if __name__ == "__main__":
    run_polling()
# polling.py
# Опрос API турникета и отправка уведомлений родителям

import threading
import time
import requests
import db
import utils
from telegram import Bot
from config import BOT_TOKEN
from datetime import datetime

# Флажок для остановки polling
stop_polling = threading.Event()

# Инициализируем бота и БД
bot = Bot(token=BOT_TOKEN)
db.init_db()

def handle_event(student_id: str, direction: str, timestamp: str = None):
    """
    Сохраняет событие в БД и отправляет сообщение родителю.
    """
    ts_iso = timestamp or datetime.now().isoformat()
    db.add_event(student_id, direction, ts_iso)

    ts = datetime.fromisoformat(ts_iso).strftime("%H:%M:%S")
    students = utils.load_students()
    for s in students:
        if s["student_id"] == student_id and s.get("telegram_chat_id"):
            msg = (
                f"🎓 {s['name']}\n"
                f"⏰ {ts}\n"
                f"➡️ {direction}"
            )
            bot.send_message(chat_id=s["telegram_chat_id"], text=msg)
            print(f"Уведомление отправлено: {s['name']} — {direction} в {ts}")
            break

def run_polling():
    """
    Основной цикл: опрашивает API каждые 5 секунд,
    получает новые события и обрабатывает их.
    """
    API_URL = "https://api.univer.example/events"
    last_ts = None
    print("Запуск polling. Ожидание событий...")

    while not stop_polling.is_set():
        params = {"since": last_ts} if last_ts else {}
        try:
            resp = requests.get(API_URL, params=params, timeout=10)
            resp.raise_for_status()
            events = resp.json()  # [{"student_id","direction","timestamp"}, …]

            for ev in events:
                handle_event(ev["student_id"], ev["direction"], ev.get("timestamp"))
                last_ts = ev.get("timestamp", last_ts)

        except Exception as e:
            print(f"Ошибка polling: {e}")

        # Пауза с проверкой флажка каждую секунду
        for _ in range(5):
            if stop_polling.is_set():
                break
            time.sleep(1)

    print("Polling loop stopped")

def stop():
    """Остановить polling."""
    stop_polling.set()

if __name__ == "__main__":
    run_polling()
