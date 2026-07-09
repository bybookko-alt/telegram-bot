import json
import os
import re
import time
import urllib.parse
import urllib.request


LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|@\w+|[a-z0-9-]+\.[a-z]{2,})",
    re.IGNORECASE,
)


def load_env(path=".env"):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def telegram_request(token, method, payload=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def send_message(token, chat_id, text):
    return telegram_request(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
        },
    )


def delete_message(token, chat_id, message_id):
    return telegram_request(
        token,
        "deleteMessage",
        {
            "chat_id": chat_id,
            "message_id": message_id,
        },
    )


def get_chat_title(message):
    chat = message.get("chat", {})
    return chat.get("title") or chat.get("username") or str(chat.get("id", "unknown"))


def get_updates(token, offset=None):
    params = {
        "timeout": 50,
        "allowed_updates": json.dumps(["message"]),
    }
    if offset is not None:
        params["offset"] = offset

    query = urllib.parse.urlencode(params)
    return telegram_request(token, f"getUpdates?{query}")


def has_link(message):
    text = message.get("text") or message.get("caption") or ""
    if LINK_PATTERN.search(text):
        return True

    for entity in message.get("entities", []) + message.get("caption_entities", []):
        if entity.get("type") in {"url", "text_link", "mention"}:
            return True

    return False


def is_join_or_leave_message(message):
    return bool(message.get("new_chat_members") or message.get("left_chat_member"))


def try_delete_message(token, chat_id, message_id, chat_title, reason):
    print(f"{reason}. Deleting message_id={message_id} in chat={chat_title}.")
    try:
        delete_message(token, chat_id, message_id)
        print("Message deleted.")
    except Exception as error:
        print(f"Could not delete message: {error}")


def handle_message(token, message):
    chat_id = message["chat"]["id"]
    message_id = message["message_id"]
    text = message.get("text", "")
    chat_type = message["chat"].get("type", "private")
    chat_title = get_chat_title(message)

    print(f"Message received: chat={chat_title} type={chat_type} text={text[:80]!r}")

    if chat_type in {"group", "supergroup"} and is_join_or_leave_message(message):
        try_delete_message(token, chat_id, message_id, chat_title, "Join/leave notice detected")
        return

    if chat_type in {"group", "supergroup"} and has_link(message):
        try_delete_message(token, chat_id, message_id, chat_title, "Link detected")
        return

    if text == "/start":
        send_message(
            token,
            chat_id,
            "สวัสดีครับ! บอท tonngtan พร้อมใช้งานแล้ว\nถ้าอยู่ในกลุ่มและเป็นแอดมิน บอทจะลบข้อความที่มีลิงก์ให้ครับ",
        )
    elif text == "/help":
        send_message(
            token,
            chat_id,
            "คำสั่งที่ใช้ได้:\n/start - เริ่มใช้งานบอท\n/help - ดูคำสั่ง\n\nในกลุ่ม: บอทจะลบข้อความที่มีลิงก์ เช่น https://, www., t.me หรือ @username",
        )
    elif text:
        send_message(token, chat_id, f"คุณพิมพ์ว่า: {text}")
    else:
        send_message(token, chat_id, "ตอนนี้บอทรองรับข้อความตัวอักษรก่อนครับ")


def main():
    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN. Create a .env file first.")

    print("Bot is running. Press Ctrl+C to stop.")
    offset = None

    while True:
        try:
            updates = get_updates(token, offset)
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    handle_message(token, message)
        except KeyboardInterrupt:
            print("\nBot stopped.")
            break
        except Exception as error:
            print(f"Temporary error: {error}")
            time.sleep(5)


if __name__ == "__main__":
    main()
