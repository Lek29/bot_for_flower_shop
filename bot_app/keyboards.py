import telebot
from telebot.types import InlineKeyboardButton


def first_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = telebot.types.KeyboardButton("День рождения")
    button2 = telebot.types.KeyboardButton("Свадьба")
    button3 = telebot.types.KeyboardButton("В школу")
    button4 = telebot.types.KeyboardButton("Без повода")
    button5 = telebot.types.KeyboardButton("Другой повод")

    keyboard.row(button1, button2)
    keyboard.row(button3, button4, button5)
    return keyboard


def create_first_set_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    button1 = InlineKeyboardButton('~500', callback_data='~500')
    button2 = InlineKeyboardButton('~1000', callback_data='~1000')
    button3 = InlineKeyboardButton('~2000', callback_data='~2000')
    button4 = InlineKeyboardButton('Больше', callback_data='~Больше')
    button5 = InlineKeyboardButton('Не важно', callback_data='~Не важно')

    keyboard.row(button1)
    keyboard.row(button2)
    keyboard.row(button3)
    keyboard.row(button4)
    keyboard.row(button5)
    return keyboard


def order_keyboard(price):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            f'Заказать за {price} руб.',
            callback_data=f'order_{price}'
        )
    )
    return keyboard


def markup_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Консультация флориста", callback_data="consult"),
        InlineKeyboardButton("Другие букеты", callback_data="more_flowers")
    )
    return markup