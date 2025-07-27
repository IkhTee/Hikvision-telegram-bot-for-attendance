# handlers.py
from __future__ import annotations

import re
from datetime import datetime, timedelta, date
from typing import Union

from telegram import (
    Update,
    CallbackQuery,                # ← импортирован CallbackQuery
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

import db, utils

# ───────── Conversation States ─────────
(
    REG_LANG,
    REG_NAME,
    REG_PHONE,
    REG_STUDENT,
    PROFILE,      # parent profile inline menu
    EDIT_NAME,
    EDIT_PHONE,
    EDIT_SID,
    EDIT_LANG,
    ADMIN_CODE,
    STUDENT_INFO
) = range(11)

# ───────── Localization ─────────
LOCALES = {
    "en": {
        "enter_name":       "Enter your full name:",
        "share_phone":      "Please share your phone number:",
        "enter_student":    "Enter your student ID:",
        "invalid_student":  "❌ Student ID not found. Try again:",
        "reg_complete":     "✅ Registration complete!",
        "menu_text":        "Main menu:",
        "btn_profile":      "👤 Profile",
        "btn_attendance":   "📆 Attendance",
        "btn_notif":        "🔔 Notifications",
        "notif_title":      "Notification settings:",
        "attendance_title": "Detailed last 5 weekdays:",
        "admin_menu":       "Admin menu: choose an action:",
        "logs_title":       "📊 Today’s Logs:",
        "summary_present":  "✅ Present",
        "summary_absent":   "❌ Absent",
        "summary_late":     "⏰ Late",
        "enter_sid":        "Enter student ID for details:",
        "no_events":        "No events found.",
        "export_csv":       "📥 CSV export not implemented yet.",
        "back":             "🔙 Back",
    },
    "ru": {
        "enter_name":       "Введите ваше полное имя:",
        "share_phone":      "Пожалуйста, поделитесь номером телефона:",
        "enter_student":    "Введите ID студента:",
        "invalid_student":  "❌ Студента с таким ID нет. Попробуйте снова:",
        "reg_complete":     "✅ Регистрация завершена!",
        "menu_text":        "Главное меню:",
        "btn_profile":      "👤 Профиль",
        "btn_attendance":   "📆 Посещаемость",
        "btn_notif":        "🔔 Уведомления",
        "notif_title":      "Настройки уведомлений:",
        "attendance_title": "Детально за 5 будних дней:",
        "admin_menu":       "Меню админа: выберите действие:",
        "logs_title":       "📊 Журнал за сегодня:",
        "summary_present":  "✅ Пришли",
        "summary_absent":   "❌ Отсутствуют",
        "summary_late":     "⏰ Опоздали",
        "enter_sid":        "Введите ID студента для детализации:",
        "no_events":        "События не найдены.",
        "export_csv":       "📥 Экспорт CSV ещё не реализован.",
        "back":             "🔙 Назад",
    },
    "uz": {
        "enter_name":       "To‘liq ismingizni kiriting:",
        "share_phone":      "Telefon raqamingizni ulashing:",
        "enter_student":    "Talaba ID sini kiriting:",
        "invalid_student":  "❌ Bunday ID li talaba topilmadi. Qayta urinib ko‘ring:",
        "reg_complete":     "✅ Ro‘yxatdan o‘tish yakunlandi!",
        "menu_text":        "Asosiy menyu:",
        "btn_profile":      "👤 Profil",
        "btn_attendance":   "📆 Bor‑yo‘qlik",
        "btn_notif":        "🔔 Bildirishnomalar",
        "notif_title":      "Bildirishnoma sozlamalari:",
        "attendance_title": "So‘nggi 5 ish kun detalli:",
        "admin_menu":       "Admin menyu: amalni tanlang:",
        "logs_title":       "📊 Bugungi jurnal:",
        "summary_present":  "✅ Keldi",
        "summary_absent":   "❌ Kelmadi",
        "summary_late":     "⏰ Kechikdi",
        "enter_sid":        "Talaba ID sini kiriting (detallar uchun):",
        "no_events":        "Voqealar topilmadi.",
        "export_csv":       "📥 CSV eksport hali yo‘q.",
        "back":             "🔙 Orqaga",
    }
}

# ───────── Helpers ─────────
def _chat_id_from(update_or_q: Union[Update, CallbackQuery]) -> int:
    if isinstance(update_or_q, Update):
        return update_or_q.effective_chat.id
    return update_or_q.message.chat.id  # type: ignore[attr-defined]

# ───────── Parent Inline Menu ─────────
def parent_inline(lang: str) -> InlineKeyboardMarkup:
    loc = LOCALES[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(loc["btn_profile"],    callback_data="p_profile")],
        [InlineKeyboardButton(loc["btn_attendance"], callback_data="p_att")],
        [InlineKeyboardButton(loc["btn_notif"],      callback_data="p_notif")],
    ])

async def show_parent_menu(update_or_q, context: ContextTypes.DEFAULT_TYPE):
    chat_id = _chat_id_from(update_or_q)
    p = db.get_parent(chat_id)
    if not p:
        return
    loc = LOCALES[p["language"]]
    await context.bot.send_message(chat_id, loc["menu_text"], reply_markup=parent_inline(p["language"]))

# ======================================================================
#  REGISTRATION
# ======================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O‘zbek",  callback_data="lang_uz")],
    ])
    await update.message.reply_text("Choose your language:", reply_markup=kb)
    return REG_LANG

async def reg_set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_", 1)[1]
    context.user_data["lang"] = lang

    chat_id = q.message.chat.id
    db.add_parent(chat_id, name="", phone="", student_id="", language=lang)

    await q.edit_message_text(LOCALES[lang]["enter_name"])
    return REG_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    name = update.message.text.strip()
    context.user_data["name"] = name
    db.update_parent_field(chat_id, "name", name)

    lang = context.user_data["lang"]
    loc = LOCALES[lang]
    contact_kb = ReplyKeyboardMarkup(
        [[KeyboardButton(text="📱 " + loc["share_phone"], request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(loc["share_phone"], reply_markup=contact_kb)
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    phone = update.message.contact.phone_number if update.message.contact else update.message.text.strip()
    context.user_data["phone"] = phone
    db.update_parent_field(chat_id, "phone", phone)

    lang = context.user_data["lang"]
    loc = LOCALES[lang]
    await update.message.reply_text(loc["enter_student"], reply_markup=ReplyKeyboardRemove())
    return REG_STUDENT

async def reg_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    sid = update.message.text.strip()
    lang = context.user_data["lang"]
    loc = LOCALES[lang]

    valid = {s["student_id"] for s in utils.load_students()}
    if sid not in valid:
        await update.message.reply_text(loc["invalid_student"])
        return REG_STUDENT

    db.update_parent_field(chat_id, "student_id", sid)
    await update.message.reply_text(loc["reg_complete"])
    await show_parent_menu(update, context)
    return ConversationHandler.END

# ======================================================================
#  PARENT MENU CALLBACKS
# ======================================================================
async def parent_profile_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    chat_id = q.message.chat.id
    p = db.get_parent(chat_id)
    if not p:
        await q.edit_message_text("Profile not found.")
        return ConversationHandler.END

    loc = LOCALES[p["language"]]
    text = (
        f"Name:    {p['name'] or '—'}\n"
        f"Phone:   {p['phone'] or '—'}\n"
        f"Student ID: {p['student_id'] or '—'}\n"
        f"Language:   {p['language']}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Name",       callback_data="edit_name"),
         InlineKeyboardButton("📱 Phone",      callback_data="edit_phone")],
        [InlineKeyboardButton("🆔 Student ID", callback_data="edit_sid"),
         InlineKeyboardButton("🌐 Language",   callback_data="edit_lang")],
        [InlineKeyboardButton(loc["back"],     callback_data="back_parent")],
    ])
    await q.edit_message_text(text, reply_markup=kb)
    return PROFILE

async def parent_attendance_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    return await attendance_command(q, context)

async def parent_notif_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    return await notif_menu(q, context)

# ======================================================================
#  PROFILE EDIT
# ======================================================================
async def profile_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    action = q.data
    if action == "back_parent":
        return await show_parent_menu(q, context)

    field = action.split("_",1)[1]  # name|phone|sid|lang
    if field != "lang":
        context.user_data["edit_field"] = "student_id" if field=="sid" else field

    if field == "lang":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
             InlineKeyboardButton("🇺🇿 O‘zbek",  callback_data="lang_uz")],
        ])
        await q.edit_message_text("Select language:", reply_markup=kb)
        return EDIT_LANG

    prompts = {
        "name":  "Enter new name:",
        "phone": "Enter new phone:",
        "sid":   "Enter new student ID:",
    }
    await q.edit_message_text(prompts[field])
    return {"name":EDIT_NAME, "phone":EDIT_PHONE, "sid":EDIT_SID}[field]

async def save_profile_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    field = context.user_data.get("edit_field")
    if field:
        db.update_parent_field(chat_id, field, update.message.text.strip())
    await update.message.reply_text("✅ Updated!", reply_markup=ReplyKeyboardRemove())
    return await parent_profile_cb(update, context)

async def edit_lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = q.data.split("_",1)[1]
    db.update_parent_field(q.message.chat.id, "language", lang)
    return await parent_profile_cb(update, context)

# ======================================================================
#  ATTENDANCE
# ======================================================================
async def attendance_command(update_or_q, context: ContextTypes.DEFAULT_TYPE):
    chat_id = _chat_id_from(update_or_q)
    p = db.get_parent(chat_id)
    if not p: return
    sid = p["student_id"]
    loc = LOCALES[p["language"]]

    days, d = [], date.today()
    while len(days) < 5:
        if d.weekday() < 5: days.append(d)
        d -= timedelta(days=1)
    days.reverse()

    rows = [
        "Date        |  In  | Out  | Status",
        "------------|------|------|-------",
    ]
    for day in days:
        start = datetime.combine(day, datetime.min.time())
        end   = datetime.combine(day, datetime.max.time())
        evs = [e for e in db.query_events_between(start, end) if e[0]==sid]
        if not evs:
            rows.append(f"{day} |  —   |  —   | ❌")
        else:
            ins  = min([e[2][11:16] for e in evs if e[1]=="Kirdi"], default="—")
            outs = max([e[2][11:16] for e in evs if e[1]=="Chiqdi"], default="—")
            rows.append(f"{day} | {ins:>5}| {outs:>5}| ✅")

    text = f"{loc['attendance_title']}\n```text\n" + "\n".join(rows) + "\n```"
    if isinstance(update_or_q, Update):
        await update_or_q.message.reply_text(text, parse_mode="Markdown")
    else:
        await update_or_q.edit_message_text(text, parse_mode="Markdown")

# ======================================================================
#  NOTIFICATIONS
# ======================================================================
async def notif_menu(update_or_q, context: ContextTypes.DEFAULT_TYPE):
    chat_id = _chat_id_from(update_or_q)
    p = db.get_parent(chat_id)
    if not p: return
    loc = LOCALES[p["language"]]

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{'🟢' if p['entry_on'] else '🔴'} Entry",
                callback_data="toggle_entry_on"
            ),
            InlineKeyboardButton(
                f"{'🟢' if p['exit_on']  else '🔴'} Exit",
                callback_data="toggle_exit_on"
            ),
            InlineKeyboardButton(
                f"{'🟢' if p['late_on']  else '🔴'} Late",
                callback_data="toggle_late_on"
            ),
        ],
        [InlineKeyboardButton(loc["back"], callback_data="back_parent")],
    ])

    if isinstance(update_or_q, Update):
        await update_or_q.message.reply_text(loc["notif_title"], reply_markup=kb)
    else:
        await update_or_q.edit_message_text(loc["notif_title"], reply_markup=kb)
    return PROFILE

async def notif_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    fld = q.data.split("_",1)[1]
    db.toggle_notification(q.message.chat.id, fld)
    return await notif_menu(q, context)

# ======================================================================
#  ADMIN FLOW
# ======================================================================
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter admin code:")
    return ADMIN_CODE

async def admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.register_admin(update.message.chat.id, update.message.text.strip()):
        await show_admin_menu(update, context)
    else:
        await update.message.reply_text("❌ Wrong admin code.")
    return ConversationHandler.END

async def show_admin_menu(update_or_q, context: ContextTypes.DEFAULT_TYPE):
    chat_id = _chat_id_from(update_or_q)
    parent = db.get_parent(chat_id)
    lang   = parent["language"] if parent else "en"
    loc    = LOCALES[lang]

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Today’s Logs", callback_data="summary")],
        [InlineKeyboardButton("👤 Student Info", callback_data="student_info")],
        [InlineKeyboardButton("📥 Export CSV",   callback_data="export")],
    ])
    await context.bot.send_message(chat_id, loc["admin_menu"], reply_markup=kb)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    action = q.data
    chat_id = q.message.chat.id
    parent = db.get_parent(chat_id)
    lang = parent["language"] if parent else "en"
    loc = LOCALES[lang]

    if action == "back_admin":
        return await show_admin_menu(q, context)

    if action == "summary":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("1d: P/A/L",  callback_data="summary_1"),
             InlineKeyboardButton("7d: P/A/L",  callback_data="summary_7"),
             InlineKeyboardButton("30d: P/A/L", callback_data="summary_30")],
            [InlineKeyboardButton(loc["back"], callback_data="back_admin")],
        ])
        return await q.edit_message_text(loc["logs_title"], reply_markup=kb)

    m = re.fullmatch(r"summary_(\d+)", action)
    if m:
        days = int(m.group(1))
        end = datetime.now()
        start = end - timedelta(days=days-1)
        evs = db.query_events_between(start, end)
        all_ids = {s["student_id"] for s in utils.load_students()}

        present = {r[0] for r in evs if r[1] == "Kirdi"}
        absent = all_ids - present
        cutoff = end.replace(hour=9, minute=30, second=0, microsecond=0)
        late = {r[0] for r in evs if r[1]=="Kirdi" and datetime.fromisoformat(r[2]) > cutoff}

        text = (
            f"{loc['summary_present']}: {', '.join(sorted(present)) or '—'}\n\n"
            f"{loc['summary_absent']}:  {', '.join(sorted(absent)) or '—'}\n\n"
            f"{loc['summary_late']}:    {', '.join(sorted(late)) or '—'}"
        )
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton(loc["back"], callback_data="back_admin")]])
        return await q.edit_message_text(text, reply_markup=back_kb)

    if action == "student_info":
        await q.edit_message_text(loc["enter_sid"])
        return STUDENT_INFO

    if action == "export":
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton(loc["back"], callback_data="back_admin")]])
        return await q.edit_message_text(loc["export_csv"], reply_markup=back_kb)

async def handle_student_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    sid = update.message.text.strip()
    parent = db.get_parent(chat_id) or {}
    lang = parent.get("language", "en")
    loc = LOCALES[lang]

    rows = [r for r in db.query_events_between(datetime(1970,1,1), datetime.now()) if r[0]==sid]
    if not rows:
        text = loc["no_events"]
    else:
        lines = [f"{r[2][11:16]} — {'Entry' if r[1]=='Kirdi' else 'Exit'}" for r in rows]
        text = f"History for {sid}:\n" + "\n".join(lines)

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(loc["back"], callback_data="back_admin")]])
    )
    return ConversationHandler.END

def get_handlers():
    return [
        # registration
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                REG_LANG:    [CallbackQueryHandler(reg_set_lang, pattern="^lang_")],
                REG_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
                REG_PHONE:   [MessageHandler(filters.CONTACT | filters.TEXT, reg_phone)],
                REG_STUDENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_student)],
            },
            fallbacks=[]
        ),

        # parent inline menu
        CallbackQueryHandler(parent_profile_cb,    pattern="^p_profile$"),
        CallbackQueryHandler(parent_attendance_cb, pattern="^p_att$"),
        CallbackQueryHandler(parent_notif_cb,      pattern="^p_notif$"),

        # profile edit
        ConversationHandler(
            entry_points=[CallbackQueryHandler(profile_edit_callback, pattern="^(edit_|back_parent)$")],
            states={
                EDIT_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, save_profile_edit)],
                EDIT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_profile_edit)],
                EDIT_SID:   [MessageHandler(filters.TEXT & ~filters.COMMAND, save_profile_edit)],
                EDIT_LANG:  [CallbackQueryHandler(edit_lang_choice, pattern="^lang_")],
            },
            fallbacks=[]
        ),

        # notifications
        CallbackQueryHandler(notif_toggle, pattern="^toggle_"),

        # attendance via typing 📆
        MessageHandler(filters.Regex(r"^📆"), attendance_command),

        # admin
        ConversationHandler(
            entry_points=[CommandHandler("admin", admin_start)],
            states={ADMIN_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_login)]},
            fallbacks=[]
        ),
        CallbackQueryHandler(admin_callback,
            pattern=r"^(summary|summary_\d+|student_info|export|back_admin)$"
        ),
        ConversationHandler(
            entry_points=[CallbackQueryHandler(lambda u,c: None, pattern="^student_info$")],
            states={STUDENT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_student_info)]},
            fallbacks=[CallbackQueryHandler(lambda u,c: show_admin_menu(u,c), pattern="^back_admin$")]
        ),
    ]
