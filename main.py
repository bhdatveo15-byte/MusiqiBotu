import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from pytubefix import Search
from aiohttp import web

# --- TOKENLƏR ---
API_TOKEN = '8593665005:AAF8_5IkhYudcJa3ysqzLjK7XcGCktTd-3M' 
ADMIN_ID = 6254213843

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- SERVER (Botun yatmaması üçün) ---
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

# --- YÜKLƏMƏ HİSSƏSİ (PYTUBEFIX) ---
@dp.message(F.text & ~F.text.startswith('/'))
async def download_music(message: types.Message):
    query = message.text
    msg = await message.answer(f"🔍 '{query}' axtarılır... (Yeni metod)")

    try:
        loop = asyncio.get_event_loop()
        # Yükləməni arxa planda edirik
        filename, title = await loop.run_in_executor(None, lambda: real_download(query))
        
        if filename:
            await msg.edit_text("📤 Yüklənir, göndərilir...")
            # Telegram-a audio kimi göndəririk
            await message.answer_audio(FSInputFile(filename), caption=f"🎧 {title}\nBot: @Baku_musicc_bot")
            
            # Faylı silirik
            if os.path.exists(filename):
                os.remove(filename)
            await msg.delete()
        else:
            await msg.edit_text("❌ Mahnı tapılmadı.")

    except Exception as e:
        await msg.edit_text(f"❌ Xəta baş verdi: {str(e)}")

def real_download(query):
    try:
        # Pytubefix ilə axtarış
        s = Search(query)
        if not s.videos:
            return None, None
            
        yt = s.videos[0] # İlk nəticəni götürürük
        title = yt.title
        
        # Audio axınını tapırıq (m4a formatı Telegram üçün uyğundur)
        ys = yt.streams.get_audio_only()
        
        # Fayl adı yaradırıq
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_title}.m4a"
        
        # Yükləyirik
        ys.download(filename=filename)
        return filename, title
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"Salam {message.from_user.first_name}! 👋\nBiz sistemi yenilədik. Mahnı adını yazın!")

async def main():
    init_db()
    await asyncio.gather(start_server(), dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass