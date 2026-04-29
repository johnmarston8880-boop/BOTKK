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
    names = ["rakesh","amit","neha","priya","vikram","ankit","divya","manoj","sonal","rajat"]
    email = f"{random.choice(names)}{random.randint(1000,9999)}@gmail.com"
    phone = f"+92{random.randint(9392823620, 9994997058)}"
    
    if is_channel:
        message_text = f"""URGENT REPORT - CHANNEL VIOLATION

Channel {target} is distributing prohibited content including child sexual abuse material (CSAM) and extremist propaganda.

This channel MUST be banned immediately.

Case ID: {random.randint(100000, 999999)}"""
    else:
        message_text = f"""URGENT REPORT - USER VIOLATION

User @{target} is distributing prohibited content including child sexual abuse material (CSAM). 

This user MUST be banned immediately.

Case ID: {random.randint(100000, 999999)}"""

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
        report_count_channel[chat_id] = report_count_channel.get(chat_id, 0)
        sent = 0
        for i in range(count):
            if stop_mass_report.get(chat_id, False):
                send_message(chat_id, f"⏹️ Остановлено на {i+1}/{count} (отправлено: {sent})")
                break
            success = send_report(target, is_channel=True)
            percent = int((i+1) / count * 100)
            if success:
                sent += 1
                report_count_channel[chat_id] = report_count_channel.get(chat_id, 0) + 1
                send_message(chat_id, f"✅ [{percent}%] Жалоба {i+1}/{count} на канал {target} ОТПРАВЛЕНА (всего: {sent})")
            else:
                send_message(chat_id, f"❌ [{percent}%] Жалоба {i+1}/{count} на канал {target} НЕ УШЛА")
            time.sleep(random.uniform(10, 30))
        send_message(chat_id, f"📊 ГОТОВО! Отправлено {sent} из {count} жалоб на канал {target}")
    else:
        report_count_user[chat_id] = report_count_user.get(chat_id, 0)
        sent = 0
        for i in range(count):
            if stop_mass_report.get(chat_id, False):
                send_message(chat_id, f"⏹️ Остановлено на {i+1}/{count} (отправлено: {sent})")
                break
            success = send_report(target, is_channel=False)
            percent = int((i+1) / count * 100)
            if success:
                sent += 1
                report_count_user[chat_id] = report_count_user.get(chat_id, 0) + 1
                send_message(chat_id, f"✅ [{percent}%] Жалоба {i+1}/{count} на @{target} ОТПРАВЛЕНА (всего: {sent})")
            else:
                send_message(chat_id, f"❌ [{percent}%] Жалоба {i+1}/{count} на @{target} НЕ УШЛА")
            time.sleep(random.uniform(10, 30))
        send_message(chat_id, f"📊 ГОТОВО! Отправлено {sent} из {count} жалоб на @{target}")
    
    mass_report_active[chat_id] = False
    stop_mass_report[chat_id] = False

print("🔥 Бот запущен. Жалобы на юзеров и каналы. /help")

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
                
                # HELP / START
                if text in ["/help", "/start"]:
                    send_message(chat_id, "✅ Команды:\n/report — одна жалоба\n/massreport — массовые (5-50)\n/status — статистика\n/stop — остановить")
                
                # REPORT
                elif text == "/report":
                    waiting_for_username[chat_id] = "single"
                    send_message(chat_id, "📢 Введи @username, ссылку на канал или @канал")
                
                # MASSREPORT
                elif text == "/massreport":
                    waiting_for_username[chat_id] = "mass"
                    send_message(chat_id, "📢 Введи цель (@username, ссылка или @канал)\nЗатем введи количество (5-50)")
                
                # STATUS
                elif text == "/status":
                    user_count = report_count_user.get(chat_id, 0)
                    channel_count = report_count_channel.get(chat_id, 0)
                    send_message(chat_id, f"📊 Статистика:\n👤 На юзеров: {user_count}\n📢 На каналы: {channel_count}\nВсего: {user_count + channel_count}")
                
                # STOP
                elif text == "/stop":
                    if mass_report_active.get(chat_id, False):
                        stop_mass_report[chat_id] = True
                        send_message(chat_id, "⏹️ Останавливаю массовую рассылку...")
                    else:
                        send_message(chat_id, "⚠️ Массовая рассылка не активна")
                
                # Обработка ввода
                elif waiting_for_username.get(chat_id) == "single":
                    username, is_channel = extract_username(text)
                    target_type = "канал" if is_channel else "юзера"
                    send_message(chat_id, f"⏳ Отправляю жалобу на {target_type} {username}...")
                    success = send_report(username, is_channel)
                    if success:
                        if is_channel:
                            report_count_channel[chat_id] = report_count_channel.get(chat_id, 0) + 1
                        else:
                            report_count_user[chat_id] = report_count_user.get(chat_id, 0) + 1
                        send_message(chat_id, f"✅ Жалоба на {target_type} {username} отправлена!")
                    else:
                        send_message(chat_id, f"❌ Ошибка при отправке на {target_type} {username}")
                    waiting_for_username[chat_id] = None
                
                elif waiting_for_username.get(chat_id) == "mass":
                    mass_report_target[chat_id] = text
                    waiting_for_username[chat_id] = "mass_count"
                    send_message(chat_id, "🔢 Введи количество жалоб (5-50)")
                
                elif waiting_for_username.get(chat_id) == "mass_count":
                    try:
                        count = int(text)
                        if 5 <= count <= 50:
                            if mass_report_active.get(chat_id, False):
                                send_message(chat_id, "⚠️ Массовая рассылка уже идет")
                            else:
                                target_raw = mass_report_target[chat_id]
                                username, is_channel = extract_username(target_raw)
                                target_type = "канал" if is_channel else "юзера"
                                mass_report_active[chat_id] = True
                                send_message(chat_id, f"🚀 Запускаю {count} жалоб на {target_type} {username}")
                                thread = threading.Thread(target=mass_report_worker, args=(chat_id, username, count, is_channel))
                                thread.start()
                        else:
                            send_message(chat_id, "❌ Введи число от 5 до 50")
                    except:
                        send_message(chat_id, "❌ Введи число")
                    waiting_for_username[chat_id] = None
                
                elif text.startswith("/"):
                    continue
                else:
                    send_message(chat_id, "Используй /help для списка команд")
        
        time.sleep(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
