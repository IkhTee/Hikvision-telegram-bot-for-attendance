# db.py

import sqlite3

DB_FILE = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Таблица событий
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        student_id TEXT,
        direction  TEXT,
        event_time TEXT
    )
    """)
    # Таблица родителей
    cur.execute("""
    CREATE TABLE IF NOT EXISTS parents (
        chat_id    INTEGER PRIMARY KEY,
        name       TEXT,
        phone      TEXT,
        student_id TEXT,
        language   TEXT,
        entry_on   INTEGER DEFAULT 1,
        exit_on    INTEGER DEFAULT 1,
        late_on    INTEGER DEFAULT 1
    )
    """)
    conn.commit()
    conn.close()

def add_event(student_id: str, direction: str, event_time: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events(student_id, direction, event_time) VALUES (?, ?, ?)",
        (student_id, direction, event_time)
    )
    conn.commit()
    conn.close()

def query_events_between(start, end):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT student_id, direction, event_time FROM events "
        "WHERE event_time BETWEEN ? AND ?",
        (start.isoformat(), end.isoformat())
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def add_parent(chat_id, name, phone, student_id, language):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        REPLACE INTO parents(chat_id, name, phone, student_id, language)
        VALUES (?, ?, ?, ?, ?)
    """, (chat_id, name, phone, student_id, language))
    conn.commit()
    conn.close()

def get_parent(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT chat_id, name, phone, student_id, language,
               entry_on, exit_on, late_on
        FROM parents WHERE chat_id = ?
    """, (chat_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "chat_id":    row[0],
        "name":       row[1],
        "phone":      row[2],
        "student_id": row[3],
        "language":   row[4],
        "entry_on":   bool(row[5]),
        "exit_on":    bool(row[6]),
        "late_on":    bool(row[7]),
    }

def update_parent_field(chat_id, field, value):
    if field not in ("name", "phone", "student_id", "language"):
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(f"UPDATE parents SET {field} = ? WHERE chat_id = ?", (value, chat_id))
    conn.commit()
    conn.close()

def toggle_notification(chat_id, field):
    if field not in ("entry_on", "exit_on", "late_on"):
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(f"UPDATE parents SET {field} = 1 - {field} WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def register_admin(chat_id, code):
    from config import ADMIN_CODES
    return code in ADMIN_CODES

def load_parents():
    """
    Возвращает список словарей:
    [{ 'chat_id':..., 'student_id':..., 'entry_on':..., 'exit_on':..., 'late_on':... }, ...]
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT chat_id, student_id, entry_on, exit_on, late_on FROM parents")
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "chat_id":    r[0],
            "student_id": r[1],
            "entry_on":   bool(r[2]),
            "exit_on":    bool(r[3]),
            "late_on":    bool(r[4]),
        }
        for r in rows
    ]
