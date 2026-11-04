import os
import logging
import asyncio
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher

TOKEN = "8924046656:AAFptNIBxDr-5MA773mF7OAdE2dJkfQEUkE"
CHANNEL_ID = "@nizhyn_life"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Зберігаємо останній відомий стан тривоги
last_status = None

async def check_alert_status():
    global last_status
    url = "https://neptun.in.ua/api/alerts" # або прямий URL джерела
    
    async with ClientSession() as session:
        while True:
            try:
                # Опитуємо джерело кожні 30 секунд
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Припускаємо, що флан статусу лежить у полі status для Ніжина
                        current_status = data.get("nizhyn", "").lower()
                        
                        # Якщо стан змінився — надсилаємо сповіщення
                        if current_status != last_status and current_status != "":
                            last_status = current_status
                            
                            if current_status in ["red", "active", "1"]:
                                msg = "🔴 **УВАГА! Повітряна тривога в Ніжині!** Пройдіть в укриття!"
                            elif current_status in ["green", "clear", "off", "0"]:
                                msg = "🟢 **Відбій повітряної тривоги в Ніжині.** Можна покидати укриття."
                            else:
                                msg = None

                            if msg:
                                await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
                                logging.info(f"Надіслано сповіщення: {current_status}")
            except Exception as e:
                logging.error(f"Помилка під час опитування джерела: {e}")
            
            # Чекаємо 30 секунд перед наступною перевіркою
            await asyncio.sleep(30)

async def index(request):
    return web.Response(text="Nizhyn Alert Bot is running 24/7!")

async def start_background_tasks(app):
    app['alert_checker'] = asyncio.create_task(check_alert_status())

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", index)
    
    # Запускаємо фонову перевірку при старті сервера
    app.on_startup.append(start_background_tasks)
    
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
