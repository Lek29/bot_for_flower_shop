import telebot
from dotenv import load_dotenv
from heandlers import handle_start, handle_callbacks, handle_messages, handle_pre_checkout, handle_successful_payment
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

    if not token_tg:
        print("ОШИБКА: Токен бота TOKEN_TG не найден в .env!")
        return
        # Проверяем и provider_token здесь
    if not provider_token:
        print("ОШИБКА: Токен провайдера PROVIDER_TOKEN не найден в .env! Оплата НЕ БУДЕТ РАБОТАТЬ.")
        return
    bot = telebot.TeleBot(token_tg)

    handle_start(bot)
    handle_messages(bot)
    handle_callbacks(bot, provider_token)
    handle_pre_checkout(bot),
    handle_successful_payment(bot)

    bot.polling()


if __name__ == '__main__':
    main()