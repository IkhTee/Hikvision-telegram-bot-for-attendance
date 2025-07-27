# bot.py

import threading
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import db
from config import BOT_TOKEN
from handlers import get_handlers
import polling

# Флаг для остановки симуляции (если нужна)
stop_simulation = threading.Event()

def start_simulation_loop():
    from api_simulator import simulate_student_event

    while not stop_simulation.is_set():
        # Здесь можно подставить любой student_id из students.json
        simulate_student_event("20201234", direction="Keldi")
        time.sleep(5)

    print("Simulation loop stopped")

async def stop_sim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_simulation.set()
    await update.message.reply_text("🛑 Simulation stopped")

async def stop_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    polling.stop()
    await update.message.reply_text("🛑 Polling stopped")

def main():
    # 1) Инициализируем базу
    db.init_db()

    # 2) Запускаем polling в отдельном потоке
    polling_thread = threading.Thread(target=polling.run_polling, daemon=True)
    polling_thread.start()

    # 3) Запускаем симуляцию (опционально)
    sim_thread = threading.Thread(target=start_simulation_loop, daemon=True)
    sim_thread.start()

    # 4) Собираем и запускаем Telegram-бота
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем все хэндлеры
    for handler in get_handlers():
        app.add_handler(handler)

    # Команда для остановки симуляции
    app.add_handler(CommandHandler("stop_sim", stop_sim))
    # Команда для остановки polling
    app.add_handler(CommandHandler("stop_poll", stop_poll))

    print("Bot started…")
    app.run_polling()

if __name__ == "__main__":
    main()
