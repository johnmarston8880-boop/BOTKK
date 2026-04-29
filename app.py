
import requests
import time
import random

TOKEN = "8137527477:AAGjVNZA7XkNvE4azSIfRnkVstodlSt_1hM"
URL = f"https://api.telegram.org/bot{TOKEN}/"

# Ожидаем юзернейм после /report
waiting_for_username = {}

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

def send_report(target_username, chat_id):
    """Отправляет жалобу через telegram.org/support"""
    
    # Генерация случайных данных
    names = ["rakesh","amit","neha","priya","vikram","ankit","divya","manoj","sonal","rajat"]
    email = f"{random.choice(names)}{random.randint(1000,9999)}@gmail.com"
    phone = f"+92{random.randint(9392823620, 9994997058)}"
    
    # Шаблон жалобы (жёсткий, чтобы гарантированно сработало)
    message_text = f"""URGENT REPORT - VIOLATION OF TELEGRAM TERMS

User @{target_username} is distributing prohibited content including child sexual abuse material (CSAM). 

Screenshots and evidence have been saved. 

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
        # Сначала получаем куки
        s = requests.Session()
        s.get("https://telegram.org/support", headers=headers, timeout=10)
        
        # Отправляем жалобу
        data = f"message={message_text}&email={email}&phone={phone}&setln="
        r = s.post("https://telegram.org/support", data=data, headers=headers, timeout=15)
        
        if "Thanks" in r.text or "success" in r.text.lower():
            send_message(chat_id, f"✅ Жалоба на @{target_username} отправлена!")
            return True
        else:
            send_message(chat_id, f"❌ Ошибка при отправке жалобы на @{target_username}")
            return False
    except Exception as e:
        send_message(chat_id, f"⚠️ Ошибка: {e}")
        return False

print("🔥 Бот запущен с функцией отправки жалоб")

last_id = 0
while True:
    try:
        updates = get_updates(last_id + 1)
        if updates.get("ok") and updates["result"]:
            for update in updates["result"]:
                last_id = update["update_id"]
                
                if "message" not in update:
                    continue
                if "text" not in update["message"]:
                    continue
                
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"].strip()
                
                # Обработка команд
                if text == "/start":
                    send_message(chat_id, "✅ Бот работает!\n/report — отправить жалобу")
                
                elif text == "/report":
                    waiting_for_username[chat_id] = True
                    send_message(chat_id, "📢 Введи @username цели")
                
                elif text.startswith("/"):
                    # Игнорируем другие команды
                    continue
                
                elif waiting_for_username.get(chat_id):
                    # Это юзернейм после команды /report
                    if text.startswith("@"):
                        username = text[1:]
                        send_message(chat_id, f"⏳ Отправляю жалобу на @{username}...")
                        send_report(username, chat_id)
                        waiting_for_username[chat_id] = False
                    else:
                        send_message(chat_id, "❌ Юзернейм должен начинаться с @")
                        waiting_for_username[chat_id] = False
                
                else:
                    send_message(chat_id, "Используй /report")
                    
        time.sleep(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
