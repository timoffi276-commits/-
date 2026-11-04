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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    logging.info("🚀 Автоматичний моніторинг Нептуна запущено.")

    async with ClientSession() as session:
        while True:
            logging.info("🔍 Перевіряємо стан на Нептуні...")
            success = False
            
            for url in sources:
                try:
                    async with session.get(url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            raw_text = await response.text()
                            text_lower = raw_text.lower()
                            
                            # Чіткіші маркери для Ніжина та тривоги
                            has_nizhyn = "ніжин" in text_lower
                            has_alarm = "тривога" in text_lower or "активна" in text_lower or "небезпека" in text_lower
                            has_clear = "відбій" in text_lower or "скасовано" in text_lower
                            
                            if has_alarm and not has_clear:
                                current_status = "active"
                            else:
                                current_status = "clear"
                                
                            logging.info(f"🔎 Поточний визначений статус: [{current_status.upper()}] (Попередній: [{last_alert_status}])")
                            
                            # Якщо це найперша перевірка після запуску
                            if last_alert_status is None:
                                last_alert_status = current_status
                                logging.info(f"📌 Початковий статус збережено в пам'яті: {current_status}")
                            
                            # Якщо статус реально змінився
                            elif current_status != last_alert_status:
                                message_text = (
                                    "🔴 **УВАГА! Повітряна тривога в Ніжині та районі!** Пройдіть в укриття!"
                                    if current_status == "active"
                                    else "🟢 **Відбій повітряної тривоги в Ніжині та районі.** Загроза минула."
                                )
                                logging.info(f"⚡ ЗМІНА СТАТУСУ! Надсилаємо сповіщення в канал...")
                                await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
                                logging.info("✅ Сповіщення успішно надіслано в Telegram-канал!")
                                
                                # Оновлюємо статус тільки після успішної відправки
                                last_alert_status = current_status
                            else:
                                logging.info("💤 Статус без змін, сповіщення не потрібне.")
                            
                            success = True
                            break 
                        else:
                            logging.warning(f"⚠️ Нептун повернув статус: {response.status}")
                            
                except Exception as e:
                    logging.warning(f"❌ Помилка запиту до Нептуна: {e}")
                    continue
            
            if not success:
                logging.info("🛡️ [Anti-Block Mode] Сервер працює, повторимо спробу за 30 секунд...")
            
            logging.info("⏳ Очікування 30 секунд до наступної перевірки...\n")
            await asyncio.sleep(30)


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
