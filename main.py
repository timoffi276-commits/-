import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types

# Токен твого бота
TOKEN = "8924046656:AAFptNIBxDr-5MA773mF7OAdE2dJkfQEUkE"
# ID каналу @nizhyn_life (перевір, чи бот має там права адміністратора)
CHANNEL_ID = "@nizhyn_life"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Функція обробки вебхуків від Nepton IP
async def handle_webhook(request):
    try:
        data = await request.json()
        status = data.get("status", "").lower()
        logging.info(f"Отримано сигнал від Nepton IP: {status}")

        message_text = ""
        if status == "red":
            message_text = "🔴 **УВАГА! Червоний рівень небезпеки в Ніжині!** Пройдіть в укриття!"
        elif status == "yellow":
            message_text = "🟡 **Увага!** Жовтий рівень небезпеки в Ніжині."
        elif status in ["clear", "off", "green", "відбій"]:
            message_text = "🟢 **Відбій тривоги в Ніжині.** Можна покидати укриття."
        else:
            return web.json_response({"status": "ignored", "reason": "unknown status"}, status=400)

        # Надсилаємо сповіщення у канал
        await bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
        return web.json_response({"status": "success"})

    except Exception as e:
        logging.error(f"Помилка обробки вебхука: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def index(request):
    return web.Response(text="Nizhyn Alert Bot is running 24/7!")

# Налаштування асинхронного вебсервера для aiohttp
async def init_app():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_post("/webhook", handle_webhook)
    return app

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    
    # Отримуємо порт від Render або ставимо 8080 за замовчуванням для ПК
    port = int(os.environ.get("PORT", 8080))
    
    web.run_app(app, host="0.0.0.0", port=port)
