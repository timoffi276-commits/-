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
    
    sources = [
        "https://neptun.in.ua/"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    logging.info("🚀 Фоновий моніторинг повітряних тривог для Ніжина запущено.")

    async with ClientSession() as session:
        while True:
            logging.info("🔍 Починаємо новий цикл перевірки Нептуна...")
            success = False
            
            for url in sources:
                try:
                    logging.info(f"🌐 Надсилаємо запит до Нептуна: {url}")
                    async with session.get(url, headers=headers, timeout=10) as response:
                        logging.info(f"📥 Отримано відповідь від Нептуна із кодом статусу: {response.status}")
                        
                        if response.status == 200:
                            raw_text = await response.text()
                            text_lower = raw_text.lower()
                            
                            # Шукаємо згадки саме Ніжина або району та статус тривоги
                            is_nizhyn_mentioned = "ніжин" in text_lower
                            has_alarm = "тривога" in text_lower or "активна" in text_lower or "небезпека" in text_lower
                            has_clear = "відбій" in text_lower or "скасовано" in text_lower
                            
                            # Якщо згадується Ніжин і є тривога (і немає відбою)
                            if is_nizhyn_mentioned and has_alarm and not has_clear:
                                current_status = "active"
                            else:
                                current_status = "clear"
                                
                            logging.info(f"🔎 Результат аналізу для Ніжина: визначено статус -> [{current_status.upper()}]")
                            
                            if last_alert_status is None:
                                last_alert_status = current_status
                                logging.info(f"📌 Початковий статус встановлено в пам'яті: {current_status}")
                            elif current_status != last_alert_status:
                                message_text = (
                                    "🔴 **УВАГА! Повітряна тривога в Ніжині та районі!** Пройдіть в укриття!"
                                    if current_status == "active"
                                    else "🟢 **Відбій повітряної тривоги в Ніжині та районі.** Загроза минула."
                                )
                                logging.info(f"⚡ Статус змінився з [{last_alert_status}] на [{current_status}]! Надсилаємо сповіщення в канал...")
                                await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
                                logging.info("✅ Сповіщення успішно надіслано в Telegram-канал!")
                            else:
                                logging.info("💤 Статус не змінився, повідомлення не надсилаємо.")
                            
                            last_alert_status = current_status
                            success = True
                            break 
                        else:
                            logging.warning(f"⚠️ Нептун повернув неочікуваний статус: {response.status}")
                            
                except Exception as e:
                    logging.warning(f"❌ Помилка під час запиту до Нептуна: {e}")
                    continue
            
            if not success:
                logging.info("🛡️ [Anti-Block Mode] Нептун тимчасово недоступний, тримаємо сервер активним...")
            
            logging.info("⏳ Очікування 30 секунд до наступної перевірки...\n")
            await asyncio.sleep(30)


async def handle_root_ping(request):
    return web.Response(text="Nizhyn Alert Bot with Neptun integration is running 24/7! 🚀", content_type="text/plain")


async def setup_background_loop(app):
    app['alert_task'] = asyncio.create_task(check_alert_status())


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", handle_root_ping)
    app.on_startup.append(setup_background_loop)
    
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Запуск веб-сервера на порті {port}...")
    web.run_app(app, host="0.0.0.0", port=port)
