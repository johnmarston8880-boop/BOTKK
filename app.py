import requests
import time
import random
import threading
import re

TOKEN = "8137527477:AAGjVNZA7XkNvE4azSIfRnkVstodlSt_1hM"
URL = f"https://api.telegram.org/bot{TOKEN}/"

waiting_for_username = {}
waiting_for_reason = {}
mass_report_active = {}
mass_report_target = {}
mass_report_reason = {}
report_count_user = {}
report_count_channel = {}
stop_mass_report = {}

REASONS = {
    "1": "🕌 Исламофобия / оскорбление религии",
    "2": "🧨 Терроризм / экстремизм",
    "3": "👶 Детская порнография / CSAM",
    "4": "💊 Наркотики / пропаганда",
    "5": "🔞 Взрослый контент без маркировки",
    "6": "💢 Разжигание ненависти / буллинг",
    "7": "🤖 Спам / мошенничество"
}

# Маты только для статуса
INSULTS = ["ебанутые ублюдки", "гниды конченые", "пиздюки долбаные", "уебаны", "твари ебучие"]

def check_target_status(target):
    try:
        if target.startswith("https://t.me/"):
            url = target
        elif target.startswith("@"):
            url = f"https://t.me/{target[1:]}"
        else:
            url = f"https://t.me/{target}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 404:
            return "dead"
        elif response.status_code == 200:
            text_lower = response.text.lower()
            if "this channel is private" in text_lower or "this group is private" in text_lower:
                return "private"
            elif "you don't have a telegram account yet" in text_lower:
                return "dead"
            else:
                return "alive"
    except:
        return "error"
    return "alive"

def get_updates(offset=None):
    url = URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json()
    except:
        return {"ok": False, "result": []}

def send_message(chat_id, text):
    url = URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text}
    try:
        requests.get(url, params=params, timeout=10)
    except:
        pass

def send_report(target, is_channel, reason_key):
    email = f"{random.choice(['user','anon','report','tg'])}{random.randint(1000,9999)}@gmail.com"
    phone = f"+7{random.randint(900, 999)}{random.randint(1111111, 9999999)}"
    time_of_report = time.strftime("%d.%m.%Y %H:%M:%S")
    
    reason_text = REASONS.get(reason_key, "Нарушение правил Telegram")
    
    message_text = f"""🚨 ЖАЛОБА НА НАРУШЕНИЕ

Цель: {"канал" if is_channel else "пользователь"} @{target}
Причина: {reason_text}
Дата и время: {time_of_report}

Требуем блокировки согласно правилам Telegram и законодательству РФ.

ID обращения: TG-{random.randint(1000,9999)}-RU
"""
    
    headers = {
        "Host": "telegram.org",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://telegram.org",
        "referer": "https://telegram.org/support"
    }
    
    try:
        s = requests.Session()
        s.get("https://telegram.org/support", headers=headers, timeout=10)
        data = f"message={message_text}&email={email}&phone={phone}&setln="
        r = s.post("https://telegram.org/support", data=data, headers=headers, timeout=15)
        if "Thanks" in r.text or "success" in r.text.lower():
            return True
        return False
    except:
        return False

def extract_username(text):
    text = text.strip()
    if text.startswith("https://t.me/"):
        parts = text.split("/")
        username = parts[-1].split("?")[0]
        return username, True
    elif text.startswith("@"):
        return text[1:], False
    else:
        return text, False

def mass_report_worker(chat_id, target, count, is_channel, reason_key):
    global report_count_user, report_count_channel, stop_mass_report
    sent = 0
    for i in range(count):
        if stop_mass_report.get(chat_id, False):
            send_message(chat_id, f"⏹️ Остановлено нахуй. Отправлено: {sent}")
            break
        success = send_report(target, is_channel, reason_key)
        percent = int((i+1) / count * 100)
        if success:
            sent += 1
            if is_channel:
                report_count_channel[chat_id] = report_count_channel.get(chat_id, 0) + 1
            else:
                report_count_user[chat_id] = report_count_user.get(chat_id, 0) + 1
            send_message(chat_id, f"💀 [{percent}%] Жалоба {i+1}/{count} | отправлено {sent} хуев")
        else:
            send_message(chat_id, f"❌ [{percent}%] Ошибка пизда: жалоба {i+1}/{count}")
        time.sleep(random.uniform(20, 90))
    send_message(chat_id, f"📊 Готово нахуй. Отправлено: {sent} жалоб")
    mass_report_active[chat_id] = False
    stop_mass_report[chat_id] = False

def show_reason_menu(chat_id, mode):
    menu = "📋 Выбери причину жалобы:\n\n"
    for key, desc in REASONS.items():
        menu += f"{key}. {desc}\n"
    menu += "\nОтправь номер (1-7)"
    send_message(chat_id, menu)
    waiting_for_reason[chat_id] = mode

print("🔥 Бот с выбором причины запущен")

last_id = 0
while True:
    try:
        updates = get_updates(last_id + 1)
        if updates.get("ok") and updates["result"]:
            for update in updates["result"]:
                last_id = update["update_id"]
                if "message" not in update or "text" not in update["message"]:
                    continue
                
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"].strip()
                
                if text in ["/help", "/start"]:
                    send_message(chat_id, "⚡ Команды:\n/report — одна жалоба\n/massreport — массовые 5-50\n/doomsday — СУДНЫЙ ДЕНЬ 10-100\n/check — проверить статус\n/status — статистика\n/stop — остановить")
                
                elif text == "/report":
                    show_reason_menu(chat_id, "single")
                
                elif text == "/massreport":
                    show_reason_menu(chat_id, "mass")
                
                elif text == "/doomsday":
                    show_reason_menu(chat_id, "doomsday")
                
                elif text == "/check":
                    waiting_for_username[chat_id] = "check_target"
                    send_message(chat_id, "🔍 Введи цель для проверки")
                
                elif text == "/status":
                    user_count = report_count_user.get(chat_id, 0)
                    channel_count = report_count_channel.get(chat_id, 0)
                    send_message(chat_id, f"📊 Статистика:\n👤 Юзеров: {user_count}\n📢 Каналов: {channel_count}\nВсего: {user_count + channel_count}")
                
                elif text == "/stop":
                    if mass_report_active.get(chat_id, False):
                        stop_mass_report[chat_id] = True
                        send_message(chat_id, "⏹️ Останавливаю нахуй...")
                    else:
                        send_message(chat_id, "⚠️ Нет активной атаки")
                
                elif waiting_for_reason.get(chat_id) in ["single", "mass", "doomsday"]:
                    if text in REASONS:
                        mode = waiting_for_reason[chat_id]
                        waiting_for_reason[chat_id] = None
                        waiting_for_username[chat_id] = mode
                        mass_report_reason[chat_id] = text
                        send_message(chat_id, f"✅ Причина: {REASONS[text]}\n📢 Введи цель (@username или ссылка)")
                    else:
                        send_message(chat_id, "❌ Введи номер от 1 до 7")
                
                elif waiting_for_username.get(chat_id) == "single":
                    username, is_channel = extract_username(text)
                    reason = mass_report_reason.get(chat_id, "1")
                    target_type = "канал" if is_channel else "юзера"
                    send_message(chat_id, f"⏳ Жалоба на {target_type} {username}...")
                    success = send_report(username, is_channel, reason)
                    if success:
                        if is_channel:
                            report_count_channel[chat_id] = report_count_channel.get(chat_id, 0) + 1
                        else:
                            report_count_user[chat_id] = report_count_user.get(chat_id, 0) + 1
                        send_message(chat_id, f"✅ Жалоба на {target_type} {username} отправлена!")
                    else:
                        send_message(chat_id, f"❌ Ошибка отправки")
                    waiting_for_username[chat_id] = None
                
                elif waiting_for_username.get(chat_id) == "mass":
                    mass_report_target[chat_id] = text
                    waiting_for_username[chat_id] = "mass_count"
                    send_message(chat_id, "🔢 Введи количество (5-50)")
                
                elif waiting_for_username.get(chat_id) == "mass_count":
                    try:
                        count = int(text)
                        if 5 <= count <= 50:
                            if mass_report_active.get(chat_id, False):
                                send_message(chat_id, "⚠️ Атака уже идёт")
                            else:
                                target_raw = mass_report_target[chat_id]
                                username, is_channel = extract_username(target_raw)
                                target_type = "канал" if is_channel else "юзера"
                                reason = mass_report_reason.get(chat_id, "1")
                                mass_report_active[chat_id] = True
                                send_message(chat_id, f"🚀 {count} жалоб на {target_type} {username} (причина: {REASONS[reason]})")
                                thread = threading.Thread(target=mass_report_worker, args=(chat_id, username, count, is_channel, reason))
                                thread.start()
                        else:
                            send_message(chat_id, "❌ От 5 до 50")
                    except:
                        send_message(chat_id, "❌ Введи число")
                    waiting_for_username[chat_id] = None
                
                elif waiting_for_username.get(chat_id) == "doomsday":
                    mass_report_target[chat_id] = text
                    waiting_for_username[chat_id] = "doomsday_count"
                    send_message(chat_id, "🔢 Введи количество (10-100)")
                
                elif waiting_for_username.get(chat_id) == "doomsday_count":
                    try:
                        count = int(text)
                        if 10 <= count <= 100:
                            if mass_report_active.get(chat_id, False):
                                send_message(chat_id, "⚠️ Атака уже идёт")
                            else:
                                target_raw = mass_report_target[chat_id]
                                username, is_channel = extract_username(target_raw)
                                target_type = "канал" if is_channel else "юзера"
                                reason = mass_report_reason.get(chat_id, "1")
                                mass_report_active[chat_id] = True
                                send_message(chat_id, f"💀💀💀 СУДНЫЙ ДЕНЬ НАХУЙ 💀💀💀\n{count} жалоб на {target_type} {username} (причина: {REASONS[reason]})")
                                thread = threading.Thread(target=mass_report_worker, args=(chat_id, username, count, is_channel, reason))
                                thread.start()
                        else:
                            send_message(chat_id, "❌ От 10 до 100")
                    except:
                        send_message(chat_id, "❌ Введи число")
                    waiting_for_username[chat_id] = None
                
                elif waiting_for_username.get(chat_id) == "check_target":
                    username, is_channel = extract_username(text)
                    status = check_target_status(username)
                    if status == "dead":
                        insult = random.choice(INSULTS)
                        msg = f"💀💀💀 СНЕСЕН НАХУЙ, {insult}! 💀💀💀\n{username} удалён или заблокирован."
                    elif status == "private":
                        msg = f"⚠️ ЦЕЛЬ СКРЫТА! {username} стал приватным. Повтори атаку."
                    elif status == "alive":
                        msg = f"🟢 ЦЕЛЬ СУЧКА ЖИВА, {random.choice(INSULTS)}. {username} ещё существует."
                    else:
                        msg = f"❌ Не удалось проверить {username}."
                    send_message(chat_id, msg)
                    waiting_for_username[chat_id] = None
                
                elif text.startswith("/"):
                    continue
                else:
                    send_message(chat_id, "❓ /help")
        
        time.sleep(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
