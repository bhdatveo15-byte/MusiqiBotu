import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from aiohttp import web

# --- TOKENLƏR ---
API_TOKEN = '8593665005:AAF8_5IkhYudcJa3ysqzLjK7XcGCktTd-3M' 
ADMIN_ID = 6254213843

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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

# --- YÜKLƏMƏ HİSSƏSİ ---
@dp.message(F.text & ~F.text.startswith('/'))
async def download_music(message: types.Message):
    query = message.text
    msg = await message.answer(f"🔍 '{query}' axtarılır...")

    # YENİ TƏNZİMLƏMƏLƏR
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'cookiefile': 'cookies.txt',  # <-- KUKİNİ GERİ QAYTARDIQ
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'quiet': True,
        'nocheckcertificate': True,
        # Brauzeri təqlid etmək üçün:
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        loop = asyncio.get_event_loop()
        filename, error_text = await loop.run_in_executor(None, lambda: real_download(ydl_opts, query))
        
        if filename:
            await message.answer_audio(FSInputFile(filename), caption=f"🎧 {filename[:-4]}\nBot: @Baku_musicc_bot")
            os.remove(filename) 
            await msg.delete()
        else:
            await msg.edit_text(f"❌ Xəta baş verdi (YouTube blokladı):\n{error_text}")

    except Exception as e:
        await msg.edit_text(f"❌ Sistem Xətası: {str(e)}")

def real_download(opts, query):
    with YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if 'entries' in info:
                info = info['entries'][0]
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return filename, None 
        except Exception as e:
            return None, str(e)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"Salam {message.from_user.first_name}! 👋\nMahnı adını yazın, yükləyim.")

async def main():
    init_db()
    await asyncio.gather(start_server(), dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass