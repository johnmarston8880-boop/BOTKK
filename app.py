import requests
import time
import sys

TOKEN = "8137527477:AAGjVNZA7XkNvE4azSIfRnkVstodlSt_1hM"

URL = f"https://api.telegram.org/bot{TOKEN}/"

def get_updates(offset=None):
    url = URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json()
    except Exception as e:
        print(f"Error in get_updates: {e}")
        return {"ok": False, "result": []}

def send_message(chat_id, text):
    url = URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text}
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print(f"Error in send_message: {e}")

print("Bot started!")

last_id = 0
while True:
    updates = get_updates(last_id + 1)
    if updates.get("ok") and updates["result"]:
        for update in updates["result"]:
            last_id = update["update_id"]
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")
            if text == "/start":
                send_message(chat_id, "✅ Bot works on Railway!")
            elif text == "/report":
                send_message(chat_id, "📢 Enter username to report")
    time.sleep(1)
