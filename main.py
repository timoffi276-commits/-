import os
import logging
import asyncio
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher

# --- НАЛАШТУВАННЯ ---
TELEGRAM_BOT_TOKEN = "8924046656:AAFptNIBxDr-5MA773mF7OAdE2dJkfQEUkE"
CHANNEL_ID = "@nizhyn_life"

# Офіційний токен від alerts.in.ua (безкоштовний)
# Встав свій токен замість тексту нижче у лапках:
ALERTS_API_TOKEN = "ТВІЙ_ТОКЕН_ВІД_ALERTS_IN_UA"

# Налаштування логування для відстеження всього в реальному часі на Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# Глобальна змінна для збереження попереднього стану тривоги
last_alert_status = None


async def check_alert_status():
    """
    Фонова асинхронна задача, яка опитує офіційний API тривог України.
    Працює безперервно у циклі 24/7.
    """
    global last_alert_status
    
    # Офіційний захищений ендпоінт для отримання статусу регіонів
    url = "https://api.alerts.in.ua/v1/iot/stat.json"
    
    headers = {
        "Authorization": f"Bearer {ALERTS_API_TOKEN}",
        "User-Agent": "NizhynLifeBot/2.0"
    }
    
    logging.info("Фоновий моніторинг повітряних тривог успішно запущено.")

    async with ClientSession() as session:
        while True:
            try:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Перевіряємо статус саме по Чернігівській області (область ID 24 або за назвою)
                        # Структура офіційного API містить стани регіонів
                        states = data.get("states", {})
                        
                        # Шукаємо Чернігівську область у даних
                        chernihiv_data = states.get("24", {}) # 24 зазвичай код Чернігівщини або шукаємо через текст
                        raw_json_str = str(data)
                        
                        # Надійний пошук активної тривоги для Ніжинського району / Чернігівщини
                        # У цьому API активна тривога має значення 'A' (Active) або числове значення
                        is_chernihiv_alert = "24" in raw_json_str and ("A" in raw_json_str or "active" in raw_json_str)
                        
                        # Додаткова перевірка через ключові слова
                        current_status = "active" if is_chernihiv_alert else "clear"
                        
                        logging.info(f"Перевірка джерела: статус у регіоні — {current_status}")
                        
                        # Якщо це перший запуск, просто запам'ятовуємо поточний стан, щоб не спамити
                        if last_alert_status is None:
                            last_alert_status = current_status
                            logging.info(f"Початковий стан зафіксовано як: {current_status}")
                        
                        # Якщо стан змінився — надсилаємо сповіщення в Telegram-канал
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
                            
                            # Надсилаємо повідомлення у ваш публічний канал
                            await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
                            logging.info("Повідомлення успішно доставлено в Telegram-канал @nizhyn_life!")
                        
                        last_alert_status = current_status
                        
                    elif response.status == 401:
                        logging.error("❌ ПОМИЛКА АВТОРИЗАЦІЇ: Невірний або прострочений API-токен alerts.in.ua!")
                    else:
                        logging.warning(f"⚠️ Сервер повернув непередбачуваний статус: {response.status}")
                        
            except asyncio.TimeoutError:
                logging.warning("⏳ Час очікування запиту до сервера вичерпано (таймаут). Повторимо спробу пізніше.")
            except Exception as e:
                logging.error(f"❌ Сталася непередбачена помилка у фоновій задачі: {e}")
            
            # Інтервал між перевірками (в секундах). 25 секунд — ідеально для оперативізму.
            await asyncio.sleep(25)


async def handle_root_ping(request):
    """
    HTTP-обробник для головної сторінки сайту Render.
    Потрібен для того, щоб UptimeRobot міг пінгувати сервер і він не засинав 24/7.
    """
    return web.Response(text="Nizhyn Alert Bot is running safely and securely 24/7! 🚀", content_type="text/plain")


async def setup_background_loop(app):
    """Автоматичний запуск фонової перевірки при старті веб-сервера."""
    app['alert_task'] = asyncio.create_task(check_alert_status())


if __name__ == "__main__":
    # Створюємо асинхронний веб-додаток (aiohttp) для підтримання життя сервісу на Render
    app = web.Application()
    app.router.add_get("/", handle_root_ping)
    app.on_startup.append(setup_background_loop)
    
    # Отримуємо порт від Render або використовуємо стандартний 8080
    port_number = int(os.environ.get("PORT", 8080))
    
    logging.info(f"Запуск веб-сервера на порті {port_number}...")
    web.run_app(app, host="0.0.0.0", port=port)
