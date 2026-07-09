# Telegram Bot

บอท Telegram สำหรับดูแลกลุ่ม:

- ลบข้อความที่มีลิงก์
- ลบข้อความแจ้งเตือนตอนมีคนเข้าหรือออกกลุ่ม

## ไฟล์ที่ต้องอัปขึ้น GitHub

- `bot.py`
- `.env.example`
- `.gitignore`
- `requirements.txt`
- `README.md`

ห้ามอัปโหลดไฟล์ `.env` เพราะมี token ลับของบอท

## ตั้งค่าบน Render

ใช้บริการแบบ `Background Worker`

ค่าแนะนำ:

- Name: `telegram-bot`
- Runtime: `Python 3`
- Build Command: เว้นว่างไว้ หรือใส่ `pip install -r requirements.txt`
- Start Command: `python bot.py`
- Instance Type: `Free`

เพิ่ม Environment Variable:

```text
TELEGRAM_BOT_TOKEN=ใส่_token_จริงตรงนี้
```

## ตั้งค่าใน Telegram group

1. เพิ่มบอทเข้า group
2. ตั้งบอทเป็น Admin
3. เปิดสิทธิ์ `Delete messages`
4. ไปที่ `@BotFather`
5. ใช้ `/setprivacy`
6. เลือกบอท
7. เลือก `Disable`
