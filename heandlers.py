import telebot
from keyboards import first_keyboard, create_first_set_inline, order_keyboard, markup_keyboard


def handle_start(bot: telebot.TeleBot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        # Сбрасываем все клавиатуры
        bot.send_message(message.chat.id,
                         "Добро пожаловать в цветочный магазин!",
                         reply_markup=telebot.types.ReplyKeyboardRemove())

        bot.send_message(message.chat.id, '''К какому событию готовимся? Выберите один из вариантов, либо укажите свой.''',
            reply_markup=first_keyboard()
        )


def handle_messages(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda message: True)
    def handler_message(message):
        if message.text == 'Назад':
            bot.send_message(message.chat.id, "Вы вернулись в главное меню",
                reply_markup=first_keyboard()
            )
        elif message.text in ("День рождения", "Свадьба", "В школу", "Без повода", "Другой повод"):
            bot.send_message(message.chat.id, 'На какую сумму расчитываете?',
                             reply_markup=create_first_set_inline()
                             )


def handle_callbacks(bot: telebot.TeleBot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        if call.data == '~500':
            with open('photo/birthday_photo/на др за 500 р.jpg', 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo,
                               caption='Маленький и душевный букет, который покажет, что вы душевный и ... большой',
                               reply_markup= order_keyboard(500))
        elif call.data == '~1000':
            with open('photo/birthday_photo/др за 1000.jpg', 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo,
                               caption='Оригинальное решение. Покажет вашу страстность и щедрость',
                              reply_markup=order_keyboard(1000))
        elif call.data.startswith('order_'):
            price = call.data.split('_')[1]
            bot.send_message(call.message.chat.id,
                             f"Вы выбрали заказ букета за {price} рублей. Наш менеджер скоро свяжется с вами!"
                )

            bot.send_message(
                call.message.chat.id,
                "<b>ХОТИТЕ ЧТО-ТО ЕЩЕ БОЛЕЕ УНИКАЛЬНОЕ?</b> Подберите другой букет из нашей коллекции или закажите консультацию флориста",
                parse_mode="HTML",
                reply_markup= markup_keyboard()
            )
        elif call.data == 'consult':
            bot.send_message(
                call.message.chat.id,
                " Укажите номер телефона, и наш флорист перезвонит вам в течение 20 минут:"
            )
        elif call.data == 'more_flowers':
            bot.send_message(
                call.message.chat.id,
                "Выберите категорию букетов:",
                reply_markup=create_first_set_inline()
            )
