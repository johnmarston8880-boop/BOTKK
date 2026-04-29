
import requests
import time

TOKEN = "8137527477:AAGjVNZA7XkNvE4azSIfRnkVstodlSt_1hM"
URL = f"https://api.telegram.org/bot{TOKEN}/"

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

print("🔥 Бот запущен")

last_id = 0
while True:
    try:
        updates = get_updates(last_id + 1)
        if updates.get("ok") and updates["result"]:
            for update in updates["result"]:
                last_id = update["update_id"]
                
                # ИГНОРИРУЕМ ВСЁ, КРОМЕ ТЕКСТОВЫХ СООБЩЕНИЙ
                if "message" not in update:
                    continue
                if "text" not in update["message"]:
                    continue
                
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]
                
                if text == "/start":
                    send_message(chat_id, "✅ Бот работает!")
                elif text == "/report":
                    send_message(chat_id, "📢 Введи @username")
        time.sleep(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
