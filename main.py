import telebot
from dotenv import load_dotenv
from handlers import handle_start, handle_callbacks, handle_messages, handle_pre_checkout, handle_successful_payment, \
    user_info
import os


def main():
    """Запускает Telegram-бота для цветочного магазина.

    Загружает конфигурацию из переменных окружения, инициализирует бота,
    регистрирует все необходимые обработчики сообщений, колбэков и платежей,
    и запускает бота в режиме long polling.
    """
    load_dotenv()
    token_tg = os.environ['TOKEN_TG']
    provider_token = os.environ.get('PROVIDER_TOKEN')
    courier_chat_id = os.environ.get('COURIER_CHAT_ID')
    florist_chat_id = os.environ.get('FLORIS_CHAT_ID')

    if not token_tg:
        print("ОШИБКА: Токен бота TOKEN_TG не найден в .env!")
        return

    if not provider_token:
        print("ОШИБКА: Токен провайдера PROVIDER_TOKEN не найден в .env! Оплата НЕ БУДЕТ РАБОТАТЬ.")

    try:
        courier_chat_id = int(courier_chat_id)
        print(f"ID курьера загружен: {courier_chat_id}")
    except ValueError:
        print("ПРЕДУПРЕЖДЕНИЕ: COURIER_CHAT_ID не найден в .env! Уведомления курьеру НЕ БУДУТ РАБОТАТЬ.")

    try:
        florist_chat_id = int(florist_chat_id)
        print(f"ID флориста загружен: {florist_chat_id}")
    except ValueError:
        print("ПРЕДУПРЕЖДЕНИЕ: FLORIST_CHAT_ID не найден в .env! Уведомления флористу НЕ БУДУТ РАБОТАТЬ.")
    bot = telebot.TeleBot(token_tg)

    handle_start(bot)
    handle_messages(bot, provider_token, florist_chat_id)
    handle_callbacks(bot, provider_token)
    handle_pre_checkout(bot),
    handle_successful_payment(bot, user_info, courier_chat_id)

    bot.polling(non_stop=True)


if __name__ == '__main__':
    main()