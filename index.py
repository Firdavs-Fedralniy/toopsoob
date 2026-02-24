import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

TOKEN = "8382359692:AAG8CO0DScL8UJGfDbsXInSl1aDDbybQJT0"

bot = Bot(TOKEN)
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- AVATAR ----------
async def get_avatar_url(user_id: int):
    photos = await bot.get_user_profile_photos(user_id, limit=1)

    if photos.total_count == 0:
        return None

    file_id = photos.photos[0][0].file_id
    file = await bot.get_file(file_id)

    return f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"

# ---------- DB ----------
async def init_db():
    async with aiosqlite.connect("stats.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            count INTEGER
        )
        """)
        await db.commit()

# ---------- API /top ----------
@app.get("/top")
async def api_top():
    async with aiosqlite.connect("stats.db") as db:
        cursor = await db.execute(
            "SELECT user_id, username, count FROM stats ORDER BY count DESC LIMIT 10"
        )
        rows = await cursor.fetchall()

    result = []
    for user_id, name, count in rows:
        avatar = await get_avatar_url(user_id)

        result.append({
            "name": name,
            "count": count,
            "avatar": avatar
        })

    return result

# ---------- /start ----------
@dp.message(Command("start"))
async def start_cmd(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "👋 Привет!\n"
            "Добавь меня в группу — я начну считать активность 🚀"
        )

# ---------- BOT ADDED ----------
@dp.my_chat_member()
async def bot_added(event: ChatMemberUpdated):
    if event.new_chat_member.status in ("member", "administrator"):
        await bot.send_message(
            event.chat.id,
            "✅ Я готов считать сообщения!"
        )

# ---------- COUNTER ----------
@dp.message()
async def count_messages(message: Message):
    if not message.from_user or message.chat.type == "private":
        return

    if message.text and message.text.startswith("/"):
        return

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    async with aiosqlite.connect("stats.db") as db:
        await db.execute("""
        INSERT INTO stats (user_id, username, count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET count = count + 1
        """, (user_id, username))
        await db.commit()

# ---------- START ----------
async def main():
    await init_db()
    print("✅ Бот + API запущены")

    await asyncio.gather(
        dp.start_polling(bot),
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=8000)
        ).serve()
    )

if __name__ == "__main__":
    asyncio.run(main())
