        token,
        "sendMessage",
        payload,
    )


def send_photo(token, chat_id, photo_url, caption, reply_markup=None, message_thread_id=None):
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
    }
    if message_thread_id:
        payload["message_thread_id"] = int(message_thread_id)
    if reply_markup:
        payload["reply_markup"] = reply_markup

    return telegram_request(token, "sendPhoto", payload)


def get_welcome_buttons():
    buttons = []
    for number in range(1, 4):
        text = os.environ.get(f"WELCOME_BUTTON_{number}_TEXT")
        url = os.environ.get(f"WELCOME_BUTTON_{number}_URL")
        if text and url:
            buttons.append([{"text": text, "url": url}])

    if not buttons:
        return None

    return {"inline_keyboard": buttons}


def send_welcome_message(token, chat_id, message):
    target_chat_id = os.environ.get("WELCOME_TARGET_CHAT_ID", chat_id)
    target_thread_id = os.environ.get("WELCOME_TARGET_THREAD_ID")
    welcome_message = os.environ.get(
        "WELCOME_MESSAGE",
        "ยินดีต้อนรับสมาชิกใหม่ครับ กรุณาอ่านกฎของกลุ่มก่อนโพสต์ข้อความ",
    )
    members = message.get("new_chat_members", [])
    names = [member.get("first_name", "member") for member in members]
    if names:
        welcome_message = f"{welcome_message}\n\nสมาชิกใหม่: {', '.join(names)}"

    photo_url = os.environ.get("WELCOME_PHOTO_URL")
    buttons = get_welcome_buttons()
    if photo_url:
        return send_photo(token, target_chat_id, photo_url, welcome_message, buttons, target_thread_id)

    return send_message(token, target_chat_id, welcome_message, target_thread_id)


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


def is_join_message(message):
    return bool(message.get("new_chat_members"))


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
        if is_join_message(message):
            try:
                send_welcome_message(token, chat_id, message)
                print("Welcome message sent.")
            except Exception as error:
                print(f"Could not send welcome message: {error}")
        return

    if chat_type in {"group", "supergroup"} and has_link(message):
        try_delete_message(token, chat_id, message_id, chat_title, "Link detected")
        return

    if chat_type in {"group", "supergroup"}:
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
