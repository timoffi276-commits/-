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
    
    # Список резервних джерел для надійності
    sources = [
        "https://ubilling.net.ua/aerial/",
        "https://emapa.fra1.cdn.digitaloceanspaces.com/alerts.json"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    logging.info("Фоновий моніторинг повітряних тривог із підтримкою резервних джерел запущено.")

    async with ClientSession() as session:
        while True:
            success = False
            
            for url in sources:
                try:
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.text()
                            
                            is_chernihiv_alert = "Чернігівська" in data and ("active" in data or "1" in data)
                            current_status = "active" if is_chernihiv_alert else "clear"
                            
                            logging.info(f"Успішна перевірка через джерело [{url}]. Статус: {current_status}")
                            
                            if last_alert_status is None:
                                last_alert_status = current_status
                            elif current_status != last_alert_status:
                                if current_status == "active":
                                    message_text = "🔴 **УВАГА! Повітряна тривога в Ніжинському районі!** Пройдіть в укриття!"
                                else:
                                    message_text = "🟢 **Відбій повітряної тривоги в Ніжинському районі.** Загроза минула."
                                
                                await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
                                logging.info("Сповіщення про зміну статусу надіслано в Telegram-канал!")
                            
                            last_alert_status = current_status
                            success = True
                            break 
                except Exception:
                    continue
            
            if not success:
                logging.warning("Всі джерела тимчасово недоступні, повторимо спробу пізніше...")
            
            await asyncio.sleep(30)


async def handle_root_ping(request):
    return web.Response(text="Nizhyn Alert Bot is running 24/7 with Multi-Source Failover! 🚀", content_type="text/plain")


async def setup_background_loop(app):
    app['alert_task'] = asyncio.create_task(check_alert_status())


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", handle_root_ping)
    app.on_startup.append(setup_background_loop)
    
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Запуск веб-сервера на порті {port}...")
    web.run_app(app, host="0.0.0.0", port=port)
