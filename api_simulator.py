# api_simulator.py

import time
from telegram import Bot
from config import BOT_TOKEN
from utils import load_students
import db

bot = Bot(token=BOT_TOKEN)

def simulate_student_event(student_id: str, direction: str = "Keldi"):
    """
    direction: "Keldi" или "Chiqdi"
    """
    # текущее время
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    # сохраняем в БД
    db.add_event(student_id, direction, ts)

    # пробегаемся по списку студентов из JSON
    students = load_students()
    for st in students:
        # ищем тех, чей ID совпал
        if st["student_id"] != student_id:
            continue
        chat_id = st.get("telegram_chat_id")
        if not chat_id:
            # если родитель ещё не привязал чат
            continue

        # подтягиваем настройки уведомлений из БД
        parent = db.get_parent(chat_id)
        if not parent:
            continue

        # фильтры по включённым типам уведомлений
        if direction == "Keldi" and not parent["entry_on"]:
            continue
        if direction == "Chiqdi" and not parent["exit_on"]:
            continue

        text = f"🎓 {st['name']} ({student_id})\n⏰ {ts}\n➡️ {direction}"
        bot.send_message(chat_id=chat_id, text=text)
        print("Sent to", chat_id)

if __name__ == "__main__":
    # Примеры вызова
    simulate_student_event("20201234", "Keldi")
    time.sleep(2)
    simulate_student_event("20201234", "Chiqdi")
