import os
import logging
import asyncio
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher

# --- НАЛАШТУВАННЯ ---
TELEGRAM_BOT_TOKEN = "8924046656:AAFptNIBxDr-5MA773mF7OAdE2dJkfQEUkE"
CHANNEL_ID = "@nizhyn_life"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

last_alert_status = None


async def check_alert_status():
    global last_alert_status
    # Використовуємо відкритий і безкоштовний публічний ендпоінт мапи тривог
    url = "https://ubilling.net.ua/aerial/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    logging.info("Фоновий моніторинг повітряних тривог запущено.")

    async with ClientSession() as session:
        while True:
            try:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.text()
                        
                        # Перевіряємо статус по Чернігівській області (сторінка містить таблицю або статус регіонів)
                        is_chernihiv_alert = "Чернігівська" in data and ("1" in data or "active" in data)
                        current_status = "active" if is_chernihiv_alert else "clear"
                        
                        logging.info(f"Стан тривоги в регіоні: {current_status}")
                        
                        if last_alert_status is None:
                            last_alert_status = current_status
                            logging.info(f"Початковий стан зафіксовано як: {current_status}")
                        
                        elif current_status != last_alert_status:
                            if current_status == "active":
                                message_text = (
                                    "🔴 **УВАГА! Повітряна тривога в Ніжинському районі!**\n"
                                    "Негайно пройдіть в укриття!"
                                )
                                logging.info("⚠️ ЗМІНА СТАНУ: Розпочалася повітряна тривога!")
                            else:
                                message_text = (
                                    "🟢 **Відбій повітряної тривоги в Ніжинському районі.**\n"
                                    "Загроза минула, можна покидати укриття."
                                )
                                logging.info("✅ ЗМІНА СТАНУ: Відбій тривоги!")
                            
                            await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
                            logging.info("Повідомлення успішно доставлено в Telegram-канал @nizhyn_life!")
                        
                        last_alert_status = current_status
                    else:
                        logging.warning(f"Сервер повернув статус: {response.status}")
                        
            except Exception as e:
                logging.error(f"Помилка у фоновій задачі: {e}")
            
            await asyncio.sleep(25)


async def handle_root_ping(request):
    return web.Response(text="Nizhyn Alert Bot is running 24/7! 🚀", content_type="text/plain")


async def setup_background_loop(app):
    app['alert_task'] = asyncio.create_task(check_alert_status())


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", handle_root_ping)
    app.on_startup.append(setup_background_loop)
    
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Запуск веб-сервера на порті {port}...")
    web.run_app(app, host="0.0.0.0", port=port)
