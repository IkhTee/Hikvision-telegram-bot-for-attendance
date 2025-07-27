
# 🧠 FacePass Telegram Bot

A Telegram bot that integrates with a face recognition API to automatically log student attendance and notify parents. Built with Python, SQLite, and the `python-telegram-bot` library.

## 📌 Features
- Telegram bot for attendance management  
- Integration with a facial recognition system (simulated or real API)  
- SQLite database to store attendance records  
- Notifies parents or groups via Telegram  
- Admin-friendly design — run locally or on a server  

## 🗂 Project Structure
```
facepass_bot/
├── bot.py                # Main bot logic
├── polling.py            # Starts polling (bot runner)
├── api.py                # Real Face Recognition API interface
├── api_simulator.py      # Simulated API (for testing without hardware)
├── handlers.py           # Telegram message/command handlers
├── db.py                 # SQLite DB logic (students, attendance)
├── config.py             # Configuration file (tokens, paths)
├── attendance.db         # SQLite DB for attendance logs
├── facepass.db           # SQLite DB for registered faces
└── parents.txt           # Parent contact info (Telegram IDs)
```

## ⚙️ Setup Instructions

### 1. Install Dependencies
Make sure Python 3.8+ is installed. Then run:

```
pip install -r requirements.txt
```

If `requirements.txt` is missing:

```
pip install python-telegram-bot opencv-python flask
```

### 2. Configure the Bot
Open `config.py` and set:

```python
BOT_TOKEN = "your_telegram_bot_token"
ADMIN_CHAT_ID = 123456789  # Your Telegram user ID
API_URL = "http://localhost:5000/api/recognize"
USE_SIMULATOR = True  # Set to False for real API
```

In `parents.txt`, add Telegram usernames or chat IDs:

```
@parent1
@parent2
```

### 3. Run the Bot
To run the bot using polling mode:

```
python polling.py
```

If using simulated API:

```
python api_simulator.py
python polling.py
```

## 🧪 Simulate Face Recognition
You can test by sending a POST request:

```
curl -X POST http://localhost:5000/api/recognize      -H "Content-Type: application/json"      -d '{"student_id": "STU001", "timestamp": "2025-07-27T08:30:00"}'
```

## 🧱 Database
- `attendance.db`: Stores check-in data with timestamps  
- `facepass.db`: Stores registered face/student info  
- `db.py`: Handles all SQLite operations  

## 💻 Tech Stack
- Python 3.8+  
- SQLite  
- Telegram Bot API via `python-telegram-bot`  
- Flask (for simulation)  
- OpenCV (optional, for real-time detection)

## 🚀 Future Upgrades
- Admin dashboard to manage students  
- Live webcam-based face capture  
- Replace SQLite with cloud DB (PostgreSQL, Firebase, etc.)

## 👤 Author
**Ikhtiyor Sadulloyev**  
This project is built for education and smart automation in student attendance systems.

## 📜 License
MIT License – open for personal or academic use.
