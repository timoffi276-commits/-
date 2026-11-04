import os
import logging
import asyncio
from aiohttp import web, ClientSession
from aiogram import Bot

# --- НАЛАШТУВАННЯ ---
TELEGRAM_BOT_TOKEN = "8924046656:AAFptNIBxDr-5MA773mF7OAdE2dJkfQEUkE"
CHANNEL_ID = "@nizhyn_life"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
last_alert_status = None


async def check_alert_status():
    global last_alert_status
    
    # Використовуємо надійний відкритий ендпоінт мапи тривог
    sources = [
        "https://emapa.fra1.cdn.digitaloceanspaces.com/alerts.json",
        "https://ubilling.net.ua/aerial/"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    logging.info("🚀 Фоновий моніторинг повітряних тривог запущено і готовий до роботи.")

    async with ClientSession() as session:
        while True:
            logging.info("🔍 Починаємо новий цикл перевірки джерел тривоги...")
            success = False
            
            for url in sources:
                try:
                    logging.info(f"🌐 Пробуємо надіслати запит до джерела: {url}")
                    async with session.get(url, headers=headers, timeout=10) as response:
                        logging.info(f"📥 Отримано відповідь від {url} із кодом статусу: {response.status}")
                        
                        if response.status == 200:
                            try:
                                json_data = await response.json()
                                raw_text = str(json_data)
                                logging.info(f"📄 Дані з {url} успішно прочитані як JSON.")
                            except Exception:
                                raw_text = await response.text()
                                logging.info(f"📄 Дані з {url} прочитані як звичайний текст.")
                            
                            is_chernihiv_alert = ("Чернігівська" in raw_text or "Chernihiv" in raw_text or "Ніжин" in raw_text) and ("active" in raw_text or "1" in raw_text or "true" in raw_text.lower())
                            current_status = "active" if is_chernihiv_alert else "clear"
                            
                            logging.info(f"🔎 Результат аналізу для [{url}]: визначено статус -> [{current_status.upper()}]")
                            
                            if last_alert_status is None:
                                last_alert_status = current_status
                                logging.info(f"📌 Початковий статус успішно встановлено в пам'яті: {current_status}")
                            elif current_status != last_alert_status:
                                message_text = (
                                    "🔴 **УВАГА! Повітряна тривога в Ніжинському районі!** Пройдіть в укриття!"
                                    if current_status == "active"
                                    else "🟢 **Відбій повітряної тривоги в Ніжинському районі.** Загроза минула."
                                )
                                logging.info(f"⚡ УВАГА! Статус змінився з [{last_alert_status}] на [{current_status}]! Надсилаємо сповіщення в канал...")
                                await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
                                logging.info("✅ Сповіщення успішно надіслано в Telegram-канал!")
                            else:
                                logging.info(f"💤 Статус не змінився (залишився {current_status}), повідомлення не надсилаємо.")
                            
                            last_alert_status = current_status
                            success = True
                            break 
                        else:
                            logging.warning(f"⚠️ Джерело {url} повернуло неочікуваний статус: {response.status}")
                            
                except Exception as e:
                    logging.warning(f"❌ Помилка під час запиту до {url}: {e}")
                    continue
            
            if not success:
                logging.info("🛡️ [Anti-Block Mode] Сервер працює стабільно, очікуємо наступного циклу...")
            
            logging.info("⏳ Очікування 30 секунд до наступної перевірки...\n")
            await asyncio.sleep(30)


async def handle_root_ping(request):
    return web.Response(text="Nizhyn Alert Bot is running 24/7! Ready for presentation! 🚀", content_type="text/plain")


async def setup_background_loop(app):
    app['alert_task'] = asyncio.create_task(check_alert_status())


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", handle_root_ping)
    app.on_startup.append(setup_background_loop)
    
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Запуск веб-сервера на порті {port}...")
    web.run_app(app, host="0.0.0.0", port=port)
