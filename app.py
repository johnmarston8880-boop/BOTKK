import requests
import time
import os

TOKEN = "8137527477:AAGjVNZA7XkNvE4azSIfRnkVstodlSt_1hM"

URL = f"https://api.telegram.org/bot{TOKEN}/"

def get_updates(offset=None):
    url = URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()

def send_message(chat_id, text):
    url = URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text}
    requests.get(url, params=params)

print("Bot started")

last_update_id = 0
while True:
    updates = get_updates(last_update_id + 1)
    if updates.get("ok") and updates["result"]:
        for update in updates["result"]:
            last_update_id = update["update_id"]
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")
            if text == "/start":
                send_message(chat_id, "Bot works on Render! 🚀")
            elif text == "/report":
                send_message(chat_id, "Enter username to report")
    time.sleep(1)
