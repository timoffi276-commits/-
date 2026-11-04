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
                            
                            # Логуємо невелику частину тексту зі сторінки для контролю
                            logging.info(f"📄 Зчитано символів з сайту: {len(raw_text)}")
                            
                            # Перевіряємо наявність маркерів тривоги чи активного стану на сторінці
                            # (Можемо шукати класи стилів або специфічні слова, які з'являються при тривозі)
                            has_active_class = "alarm" in text_lower or "danger" in text_lower or "red" in text_lower or "активна" in text_lower
                            has_nizhyn = "ніжин" in text_lower
                            
                            # Якщо сайт загалом сигналізує про небезпеку
                            if has_active_class and ("тривога" in text_lower or "небезпека" in text_lower):
                                current_status = "active"
                            else:
                                current_status = "clear"
                                
                            logging.info(f"🔎 Поточний визначений статус: [{current_status.upper()}]")
                            
                            if last_alert_status is None:
                                last_alert_status = current_status
                                logging.info(f"📌 Початковий статус збережено: {current_status}")
                            elif current_status != last_alert_status:
                                message_text = (
                                    "🔴 **УВАГА! Повітряна тривога в Ніжині та районі!** Пройдіть в укриття!"
                                    if current_status == "active"
                                    else "🟢 **Відбій повітряної тривоги в Ніжині та районі.** Загроза минула."
                                )
                                logging.info(f"⚡ ЗМІНА СТАТУСУ з [{last_alert_status}] на [{current_status}]! Надсилаємо в канал...")
                                await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
                                logging.info("✅ Сповіщення успішно надіслано!")
                            else:
                                logging.info("💤 Статус без змін.")
                            
                            last_alert_status = current_status
                            success = True
                            break 
                        else:
                            logging.warning(f"⚠️ Нептун повернув статус: {response.status}")
                            
                except Exception as e:
                    logging.warning(f"❌ Помилка запиту: {e}")
                    continue
            
            if not success:
                logging.info("🛡️ [Anti-Block Mode] Повторна спроба через 30 секунд...")
            
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
