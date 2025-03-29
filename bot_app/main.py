import os
import sys
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_shop.settings')
load_dotenv()
import django
django.setup()

import telebot
from handlers import (
    handle_start,
    handle_messages,
    handle_callbacks,
    handle_pre_checkout,
    handle_successful_payment,
    user_info,
)
from shop.models import User, Order, Bouquet

def main():
    token_tg = os.getenv('TOKEN_TG')
    provider_token = os.getenv('PROVIDER_TOKEN')

    if not token_tg:
        print("❌ ОШИБКА: Токен бота TOKEN_TG не найден в .env!")
        return

    if not provider_token:
        print("⚠️  ВНИМАНИЕ: Токен провайдера оплаты не найден. Оплата не будет работать.")

    bot = telebot.TeleBot(token_tg)

    handle_start(bot)
    handle_messages(bot, provider_token)
    handle_callbacks(bot, provider_token)
    handle_pre_checkout(bot)
    handle_successful_payment(bot, user_info)

    print("✅ Бот запущен. Ожидаю команды...")
    bot.polling(non_stop=True)


if __name__ == '__main__':
    main()
