# utils.py
import json

def load_students():
    with open("students.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_students(students):
    with open("students.json", "w", encoding="utf-8") as f:
        json.dump(students, f, indent=2, ensure_ascii=False)

def register_parent(chat_id, code):
    students = load_students()
    for student in students:
        if (student["registration_code"] == code
            and student.get("telegram_chat_id") is None):
            student["telegram_chat_id"] = chat_id
            save_students(students)
            return student["name"]
    return None
