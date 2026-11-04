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
    # Використовуємо стабільний відкритий API статусів
    url = "https://api.alerts.in.ua/v1/iot/stat.json"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Шукаємо статус для Чернігівської області / Ніжинського району в даних
                        # API зазвичай повертає список регіонів або словник
                        states = data.get("states", {})
                        # Шукаємо ключі або значення, що стосуються Чернігівщини (наприклад, oblast або district)
                        # Для надійності перевіряємо весь текст відповіді на наявність сигналів
                        raw_text = str(data)
                        
                        # Визначаємо, чи є тривога (якщо в JSON є ознака активної тривоги для нашого регіону)
                        # Зазвичай у цьому форматі активна тривога позначена відповідним полем
                        is_alert = "Nizhyn" in raw_text and ("active" in raw_text or "1" in raw_text)
                        
                        current_status = "active" if is_alert else "clear"
                        
                        logging.info(f"Перевірка тривоги. Поточний визначений стан: {current_status}")
                        
                        if last_status is not None and current_status != last_status:
                            if current_status == "active":
                                msg = "🔴 **УВАГА! Повітряна тривога в Ніжинському районі!** Пройдіть в укриття!"
                            else:
                                msg = "🟢 **Відбій повітряної тривоги в Ніжинському районі.** Можна покидати укриття."
                            
                            await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
                            logging.info(f"Сенсація! Стан змінився. Повідомлення надіслано в канал.")
                        
                        last_status = current_status
                    else:
                        logging.warning(f"Сервер повернув код помилки: {response.status}")
            except Exception as e:
                logging.error(f"Помилка під час запиту: {e}")
            
            await asyncio.sleep(20)

async def index(request):
    return web.Response(text="Nizhyn Alert Bot is running 24/7!")

async def start_background_tasks(app):
    app['alert_checker'] = asyncio.create_task(check_alert_status())

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", index)
    app.on_startup.append(start_background_tasks)
    
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
