import requests
import time
import random
import threading
import re
import json
import os

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
last_attack = {}
schedules = {}
SCHEDULE_FILE = "schedules.json"

if os.path.exists(SCHEDULE_FILE):
    with open(SCHEDULE_FILE, "r") as f:
        schedules = json.load(f)

def save_schedules():
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedules, f, indent=4)

# ----- СТРАНЫ И ТЕЛЕФОННЫЕ КОДЫ -----
COUNTRIES = {
    'us': {'code': '1', 'name': 'USA', 'phone_len': 10},
    'uk': {'code': '44', 'name': 'UK', 'phone_len': 10},
    'de': {'code': '49', 'name': 'Germany', 'phone_len': 11},
    'fr': {'code': '33', 'name': 'France', 'phone_len': 9},
    'ca': {'code': '1', 'name': 'Canada', 'phone_len': 10},
    'ru': {'code': '7', 'name': 'Russia', 'phone_len': 10},
    'ua': {'code': '380', 'name': 'Ukraine', 'phone_len': 9},
    'kz': {'code': '7', 'name': 'Kazakhstan', 'phone_len': 10},
    'pk': {'code': '92', 'name': 'Pakistan', 'phone_len': 10},
    'eg': {'code': '20', 'name': 'Egypt', 'phone_len': 9},
}

# ----- ЗАГРУЗКА ПРОКСИ (опционально) -----
def load_proxies():
    try:
        with open('proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies if proxies else None
    except FileNotFoundError:
        return None

PROXY_LIST = load_proxies()
if PROXY_LIST:
    print(f"[+] Загружено {len(PROXY_LIST)} прокси")
else:
    print("[!] Файл proxies.txt не найден или пуст. Работаю без прокси.")

# ----- ПРИЧИНЫ ЖАЛОБ -----
REASONS = {
    "1": "🕌 Исламофобия / оскорбление религии",
    "2": "🧨 Терроризм / экстремизм",
    "3": "👶 Детская порнография / CSAM",
    "4": "💊 Наркотики / пропаганда",
    "5": "🔞 Взрослый контент без маркировки",
    "6": "💢 Разжигание ненависти / буллинг",
    "7": "🤖 Спам / мошенничество"
}

INSULTS = ["ебанутые ублюдки", "гниды конченые", "пиздюки долбаные", "уебаны", "твари ебучие"]

# ----- ФУНКЦИЯ ОТПРАВКИ ЖАЛОБЫ С РОТАЦИЕЙ СТРАН И ПРОКСИ -----
def send_report(target, is_channel, reason_key):
    country_code = random.choice(list(COUNTRIES.keys()))
    country_info = COUNTRIES[country_code]
    phone_number = ''.join([str(random.randint(0,9)) for _ in range(country_info['phone_len'])])
    full_phone = f"+{country_info['code']}{phone_number}"
    email = f"{random.choice(['anon','user','report','citizen'])}{random.randint(100,999)}@{random.choice(['gmail.com','proton.me','yahoo.com'])}"
    violation = REASONS.get(reason_key, "Violation of Telegram ToS")
    
    message_text = f"""🚨 СРОЧНАЯ ЖАЛОБА НА НАРУШЕНИЕ

Цель: {"канал" if is_channel else "пользователь"} @{target}
Причина: {violation}
Страна отправителя: {country_info['name']}

Прошу проверить и заблокировать. Доказательства прилагаются.

Дата: {time.strftime('%d.%m.%Y %H:%M:%S')}
ID: TG-{random.randint(1000,9999)}
"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    session = requests.Session()
    proxy = None
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        session.proxies = {"http": proxy, "https": proxy}
        print(f"[*] Использую прокси: {proxy}")
    try:
        session.get("https://telegram.org/support", headers=headers, timeout=15)
        data = f"message={message_text}&email={email}&phone={full_phone}&setln="
        r = session.post("https://telegram.org/support", data=data, headers=headers, timeout=15)
        if "Thanks" in r.text or "success" in r.text.lower():
            return True
        return False
    except Exception as e:
        print(f"Ошибка при использовании {proxy}: {e}")
        return False

# ----- ОСТАЛЬНЫЕ ФУНКЦИИ (без изменений) -----
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

# ----- ФОНОВАЯ ЗАДАЧА ДЛЯ РАСПИСАНИЙ -----
def schedule_checker():
    while True:
        now = time.time()
        to_remove = []
        for chat_id, tasks in schedules.items():
            for task in tasks[:]:
                if task["next_run"] <= now:
                    send_message(int(chat_id), f"⏰ Автоматический запуск: {task['count']} жалоб на {task['target']} (причина: {REASONS[task['reason']]})")
                    thread = threading.Thread(target=mass_report_worker, args=(int(chat_id), task['target'], task['count'], task['is_channel'], task['reason']))
                    thread.start()
                    if task["interval"] == "daily":
                        task["next_run"] = now + 86400
                    elif task["interval"] == "hourly":
                        task["next_run"] = now + 3600
                    else:
                        to_remove.append((chat_id, task))
            for chat_id, task in to_remove:
                schedules[chat_id].remove(task)
                if not schedules[chat_id]:
                    del schedules[chat_id]
        save_schedules()
        time.sleep(60)

threading.Thread(target=schedule_checker, daemon=True).start()

# ----- ОСНОВНОЙ ЦИКЛ БОТА -----
print("🔥 HIGHLANDER с прокси и ротацией стран запущен")

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
                    send_message(chat_id, "⚡ Команды:\n/report — одна жалоба\n/massreport — массовые 5-50\n/doomsday — СУДНЫЙ ДЕНЬ 10-100\n/check — проверить статус\n/status — статистика\n/stop — остановить\n/repeat — повторить последнюю атаку\n/schedule — поставить на расписание")
                
                elif text == "/report":
                    show_reason_menu(chat_id, "single")
                
                elif text == "/massreport":
                    show_reason_menu(chat_id, "mass")
                
                elif text == "/doomsday":
                    show_reason_menu(chat_id, "doomsday")
                
                elif text == "/repeat":
                    last = last_attack.get(chat_id)
                    if not last:
                        send_message(chat_id, "❌ Нет предыдущей атаки.")
                    else:
                        send_message(chat_id, f"🔄 Повтор: {last['target']}, {REASONS[last['reason']]}, {last['count']} жалоб")
                        thread = threading.Thread(target=mass_report_worker, args=(chat_id, last['target'], last['count'], last['is_channel'], last['reason']))
                        thread.start()
                
                elif text == "/schedule":
                    waiting_for_username[chat_id] = "schedule_target"
                    send_message(chat_id, "📅 Введи цель (@username или ссылка)")
                
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
                
                # ---------- ОБРАБОТЧИКИ СОСТОЯНИЙ ----------
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
                        last_attack[chat_id] = {"target": username, "is_channel": is_channel, "reason": reason, "count": 1}
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
                                last_attack[chat_id] = {"target": username, "is_channel": is_channel, "reason": reason, "count": count}
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
                                last_attack[chat_id] = {"target": username, "is_channel": is_channel, "reason": reason, "count": count}
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
                        msg = f"💀💀💀 СНЕСЕН НАХУЙ, {insult}! 💀💀💀\n{username} удалён."
                    elif status == "private":
                        msg = f"⚠️ ЦЕЛЬ СКРЫТА! {username} стал приватным."
                    elif status == "alive":
                        msg = f"🟢 ЦЕЛЬ ЖИВА, {random.choice(INSULTS)}. {username} ещё существует."
                    else:
                        msg = f"❌ Ошибка проверки."
                    send_message(chat_id, msg)
                    waiting_for_username[chat_id] = None
                
                elif waiting_for_username.get(chat_id) == "schedule_target":
                    mass_report_target[chat_id] = text
                    waiting_for_username[chat_id] = "schedule_reason"
                    send_message(chat_id, "📋 Выбери причину жалобы (отправь номер 1-7):\n" + "\n".join([f"{k}. {v}" for k,v in REASONS.items()]))
                
                elif waiting_for_username.get(chat_id) == "schedule_reason":
                    if text in REASONS:
                        mass_report_reason[chat_id] = text
                        waiting_for_username[chat_id] = "schedule_count"
                        send_message(chat_id, "🔢 Введи количество (5-100)")
                    else:
                        send_message(chat_id, "❌ Введи номер от 1 до 7")
                
                elif waiting_for_username.get(chat_id) == "schedule_count":
                    try:
                        count = int(text)
                        if 5 <= count <= 100:
                            waiting_for_username[chat_id] = "schedule_interval"
                            mass_report_target[str(chat_id)+"_count"] = count
                            send_message(chat_id, "⏱ Введи интервал: daily (каждый день) или hourly (каждый час)")
                        else:
                            send_message(chat_id, "❌ От 5 до 100")
                    except:
                        send_message(chat_id, "❌ Введи число")
                
                elif waiting_for_username.get(chat_id) == "schedule_interval":
                    interval = text.lower()
                    if interval in ["daily", "hourly"]:
                        target_raw = mass_report_target[chat_id]
                        username, is_channel = extract_username(target_raw)
                        reason = mass_report_reason.get(chat_id, "1")
                        count = mass_report_target.get(str(chat_id)+"_count", 50)
                        if str(chat_id) not in schedules:
                            schedules[str(chat_id)] = []
                        schedules[str(chat_id)].append({
                            "target": username,
                            "is_channel": is_channel,
                            "reason": reason,
                            "count": count,
                            "interval": interval,
                            "next_run": time.time() + (86400 if interval == "daily" else 3600)
                        })
                        save_schedules()
                        send_message(chat_id, f"✅ Поставлено на расписание: {count} жалоб на @{username} каждые {interval}.")
                        waiting_for_username[chat_id] = None
                    else:
                        send_message(chat_id, "❌ Введи daily или hourly")
                
                elif text.startswith("/"):
                    continue
                else:
                    send_message(chat_id, "❓ /help")
        
        time.sleep(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
