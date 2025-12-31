import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from aiohttp import web

# --- BURANI DƏYİŞİN ---
API_TOKEN = '8593665005:AAF8_5IkhYudcJa3ysqzLjK7XcGCktTd-3M' 
ADMIN_ID = 6254213843

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- VERİLƏNLƏR BAZASI ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
    except: pass
    finally: conn.close()

def get_all_users_info():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- SERVER ---
async def health_check(request):
    return web.Response(text="Bot is active!")

async def start_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- KOMANDALAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    name = message.from_user.username if message.from_user.username else message.from_user.first_name
    add_user(message.from_user.id, name)
    await message.answer(f"Salam {message.from_user.first_name}! 👋\nBot Render-də işləyir!")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        users = get_all_users_info()
        msg = f"📊 **Statistika ({len(users)} nəfər):**\n\n"
        for i, user in enumerate(users, 1):
            msg += f"{i}. {user[1]}\n"
        await message.answer(msg, parse_mode="Markdown")

@dp.message(F.text)
async def download_music(message: types.Message):
    name = message.from_user.username if message.from_user.username else message.from_user.first_name
    add_user(message.from_user.id, name)
    
    query = message.text
    msg = await message.answer(f"🔍 '{query}' axtarılır...")
    
    # Kuki faylını bura əlavə etdik
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'cookiefile': 'cookies.txt',  # <-- ƏSAS DƏYİŞİKLİK BURADADIR
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'quiet': True
    }

    try:
        loop = asyncio.get_event_loop()
        filename = await loop.run_in_executor(None, lambda: real_download(ydl_opts, query))
        if filename:
            await message.answer_audio(FSInputFile(filename), caption=f"🎧 {filename[:-4]}")
            os.remove(filename) 
            await msg.delete()
        else:
            await msg.edit_text("❌ Tapılmadı.")
    except Exception as e:
        await msg.edit_text(f"❌ Xəta: {str(e)}")

def real_download(opts, query):
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        if 'entries' in info: info = info['entries'][0]
        return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

async def main():
    init_db()
    await asyncio.gather(start_server(), dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass