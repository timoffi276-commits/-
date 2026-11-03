# main.py

import asyncio
import json
import logging
import requests
from aiogram import Bot
from config import BOT_TOKEN, ALERT_GROUP

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=BOT_TOKEN)

NEPTUN_URL = "https://neptun.in.ua/api/v1/alerts"

last_alert_state = None


async def check_alerts_loop():
    global last_alert_state
    logging.info("Служба моніторингу тривог Neptun API запущена для Ніжинського району...")

    while True:
        try:
            response = requests.get(NEPTUN_URL, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Отримуємо список районів з поля "raions"
                raions_list = data.get("raions", [])
                
                # Шукаємо Ніжинський район у списку активних тривог за назвою або ключом
                nizhyn_active = False
                for item in raions_list:
                    if isinstance(item, dict):
                        name = item.get("name", "").lower()
                        key = item.get("key", "").lower()
                        
                        # Перевіряємо, чи це Ніжинський район
                        if "ніжин" in name or "nizhyn" in key:
                            nizhyn_active = True
                            break

                if last_alert_state is None:
                    last_alert_state = nizhyn_active
                    logging.info(f"Початковий стан для Ніжинського району: {'ТРИВОГА 🚨' if nizhyn_active else 'НЕМАЄ ТРИВОГИ 🟢'}")

                elif nizhyn_active != last_alert_state:
                    last_alert_state = nizhyn_active
                    
                    if nizhyn_active:
                        message = (
                            "🚨 **ПОВІТРЯНА ТРИВОГА!**\n\n"
                            "У Ніжинському районі оголошено повітряну тривогу!\n\n"
                            "Прямуйте в укриття!"
                        )
                        logging.info("Увага: Тривога в Ніжинському районі! Надсилаємо сповіщення...")
                    else:
                        message = (
                            "🟢 **ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ**\n\n"
                            "У Ніжинському районі повітряна тривога завершена."
                        )
                        logging.info("Відбій тривоги в Ніжинському районі. Надсилаємо сповіщення...")

                    await bot.send_message(chat_id=ALERT_GROUP, text=message, parse_mode="Markdown")
            else:
                logging.warning(f"Неочікуваний HTTP статус від NEPTUN API: {response.status_code}")

        except Exception as e:
            logging.error(f"Помилка: {e}")

        await asyncio.sleep(5)


async def main():
    asyncio.create_task(check_alerts_loop())
    await bot.delete_webhook(drop_pending_updates=True)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинено.")