import asyncio
import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated, MenuButtonWebApp, WebAppInfo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# --------- CONFIG ----------
TOKEN = os.getenv("BOT_TOKEN", "8382359692:AAG8CO0DScL8UJGfDbsXInSl1aDDbybQJT0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.awsorzqukliabaefxwvj:assalamumoleykum@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://toopsoob.vercel.app/index.html")  # ← вставить URL сайта

# --------- BOT & DISPATCHER ----------
bot = Bot(TOKEN)
dp = Dispatcher()

# --------- FASTAPI APP ----------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- DB POOL ----------
pool: asyncpg.Pool = None

# ---------- INIT DB ----------
async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as conn:
        # Основная таблица
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                count INTEGER DEFAULT 0,
                last_seen TIMESTAMP DEFAULT NOW()
            )
        """)

        # Таблица по дням (для графика)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                user_id BIGINT,
                date DATE DEFAULT CURRENT_DATE,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, date)
            )
        """)

    print("✅ БД подключена")

# ---------- GET AVATAR ----------
async def get_avatar_url(user_id: int):
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count == 0:
            return None
        file_id = photos.photos[0][0].file_id
        file = await bot.get_file(file_id)
        return f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
    except Exception as e:
        print(f"Ошибка аватара {user_id}:", e)
        return None

# ---------- API /top ----------
@app.get("/top")
async def api_top():
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, username, full_name, count
            FROM stats
            ORDER BY count DESC
            LIMIT 10
        """)

    result = []
    for i, row in enumerate(rows):
        avatar = await get_avatar_url(row["user_id"])
        result.append({
            "rank": i + 1,
            "name": row["full_name"],
            "username": row["username"],
            "count": row["count"],
            "avatar": avatar
        })
    return result

# ---------- API /user/{user_id} — личная статистика ----------
@app.get("/user/{user_id}")
async def api_user(user_id: int):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT user_id, username, full_name, count
            FROM stats WHERE user_id = $1
        """, user_id)

        if not user:
            return {"error": "Пользователь не найден"}

        # Место в топе
        rank = await conn.fetchval("""
            SELECT COUNT(*) + 1 FROM stats WHERE count > $1
        """, user["count"])

        # График за 7 дней
        week = await conn.fetch("""
            SELECT date, count FROM daily_stats
            WHERE user_id = $1
            AND date >= CURRENT_DATE - INTERVAL '6 days'
            ORDER BY date ASC
        """, user_id)

        # Сегодня
        today = await conn.fetchval("""
            SELECT count FROM daily_stats
            WHERE user_id = $1 AND date = CURRENT_DATE
        """, user_id) or 0

    avatar = await get_avatar_url(user_id)

    return {
        "user_id": user_id,
        "name": user["full_name"],
        "username": user["username"],
        "total": user["count"],
        "rank": rank,
        "avatar": avatar,
        "today": today,
        "week": [
            {"date": str(row["date"]), "count": row["count"]}
            for row in week
        ]
    }

# ---------- API /stats ----------
@app.get("/stats")
async def api_stats():
    async with pool.acquire() as conn:
        total_messages = await conn.fetchval("SELECT SUM(count) FROM stats")
        total_users = await conn.fetchval("SELECT COUNT(*) FROM stats")
    return {
        "total_messages": total_messages or 0,
        "total_users": total_users or 0
    }

# ---------- /start ----------
@dp.message(Command("start"))
async def start_cmd(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "👋 Привет!\n"
            "Добавь меня в группу — я начну считать сообщения 🚀\n\n"
            "Нажми кнопку меню снизу чтобы открыть статистику 📊"
        )

# ---------- /top в группе ----------
@dp.message(Command("top"))
async def top_cmd(message: Message):
    if message.chat.type == "private":
        return

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT full_name, count
            FROM stats
            ORDER BY count DESC
            LIMIT 10
        """)

    if not rows:
        await message.answer("📊 Пока нет статистики!")
        return

    text = "🏆 <b>Топ 10 активных участников:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{row['full_name']}</b> — {row['count']} сообщений\n"

    await message.answer(text, parse_mode="HTML")

# ---------- БОТ ДОБАВЛЕН В ГРУППУ ----------
@dp.my_chat_member()
async def bot_added(event: ChatMemberUpdated):
    if event.new_chat_member.status in ("member", "administrator"):
        await bot.send_message(
            event.chat.id,
            "✅ Привет! Я готов считать сообщения!\n"
            "Используй /top чтобы увидеть статистику 📊"
        )

# ---------- СЧЁТЧИК СООБЩЕНИЙ ----------
@dp.message()
async def count_messages(message: Message):
    if not message.from_user or message.chat.type == "private":
        return
    if message.text and message.text.startswith("/"):
        return

    user = message.from_user
    user_id = user.id
    username = user.username

    if user.first_name or user.last_name:
        full_name = user.full_name
    else:
        full_name = user.username or "Deleted User"

    async with pool.acquire() as conn:
        # Общий счётчик
        await conn.execute("""
            INSERT INTO stats (user_id, username, full_name, count, last_seen)
            VALUES ($1, $2, $3, 1, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
                count = stats.count + 1,
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                last_seen = NOW()
        """, user_id, username, full_name)

        # Дневной счётчик
        await conn.execute("""
            INSERT INTO daily_stats (user_id, date, count)
            VALUES ($1, CURRENT_DATE, 1)
            ON CONFLICT (user_id, date)
            DO UPDATE SET count = daily_stats.count + 1
        """, user_id)

# ---------- ЗАПУСК ----------
async def main():
    await init_db()

    # Кнопка меню → Mini App
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="📊 Статистика",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )

    print("✅ Бот + API запущены")
    await asyncio.gather(
        dp.start_polling(bot),
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        ).serve()
    )

if __name__ == "__main__":
    asyncio.run(main())