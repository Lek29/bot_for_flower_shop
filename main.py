import telebot
from dotenv import load_dotenv
from heandlers import handle_start, handle_callbacks, handle_messages
import os


def main():
    load_dotenv()
    token_tg = os.environ['TOKEN_TG']

    bot = telebot.TeleBot(token_tg)

    handle_start(bot)
    handle_messages(bot)
    handle_callbacks(bot)

    bot.polling()


if __name__ == '__main__':
    main()