import telebot
from telebot import types
from keyboards import first_keyboard, create_first_set_inline, order_keyboard


def handle_start(bot: telebot.TeleBot):
    """Регистрирует обработчик команды /start.

    При получении команды /start отправляет приветственное сообщение
    и предлагает выбрать повод для букета с помощью клавиатуры.

    Args:
        bot: Экземпляр telebot.TeleBot.
    """
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
    """Регистрирует обработчик для текстовых сообщений.

    Обрабатывает нажатие кнопки 'Назад' и выбор повода для букета.
    На другие текстовые сообщения просит использовать кнопки.

    Args:
        bot: Экземпляр telebot.TeleBot.
    """
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


def handle_callbacks(bot: telebot.TeleBot, provider_token: str):
    """Регистрирует обработчик для всех callback-запросов от инлайн-кнопок.

    Обрабатывает выбор ценовой категории (отправляет фото и кнопку заказа),
    нажатие кнопки заказа (инициирует оплату через send_invoice),
    запрос консультации и выбор других букетов.

    Args:
        bot: Экземпляр telebot.TeleBot.
        provider_token: Токен платежного провайдера, загруженный из .env.
    """
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        if call.data.startswith('~'):
            price = call.data
            photo_path = None
            caption = "Описание букета."

            if price == '~500':
                photo_path = 'photo/birthday_photo/на др за 500 р.jpg'
                caption = 'Маленький и душевный букет.'
            elif price == '~1000':
                photo_path = 'photo/birthday_photo/др за 1000.jpg'
                caption = 'Оригинальное решение.'

            if photo_path:
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=caption,
                                    reply_markup=order_keyboard(price))
                    bot.answer_callback_query(call.id)
            else:
                    bot.answer_callback_query(call.id, "Фото для этой цены не найдено.", show_alert=True)

        elif call.data.startswith('order_'):
            price = call.data.split('_')[1]
            try:
                amount_rub = int(price.replace('~', ''))
                amount_kopecks = amount_rub * 100
                payload = f"bouquet_{price}_{user_id}"
                title = f"Оплата букета ({amount_rub} руб.)"
                description = f"Заказ из магазина @{bot.get_me().username}"
                prices = [types.LabeledPrice(label=f"Букет {amount_rub} руб.", amount=amount_kopecks)]

                if not provider_token:
                    print("ОШИБКА: Токен провайдера не найден!")
                    bot.answer_callback_query(call.id, "Ошибка настройки оплаты.", show_alert=True)
                    return

                bot.send_invoice(
                    chat_id=chat_id,
                    title=title,
                    description=description,
                    invoice_payload=payload,
                    provider_token=provider_token,
                    currency='RUB',
                    prices=prices
                )
                bot.answer_callback_query(call.id, text="Создан счет на оплату.")

            except ValueError:
                print(f"Неверный формат цены в коллбэке: {call.data}")
                bot.answer_callback_query(call.id, "Ошибка цены.", show_alert=True)
            except Exception as e:
                print(f"Ошибка при отправке инвойса: {e}")
                bot.answer_callback_query(call.id, "Не удалось создать счет.", show_alert=True)


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


def handle_pre_checkout(bot: telebot.TeleBot):
    """Регистрирует обработчик для PreCheckoutQuery.

    Этот обработчик вызывается Telegram перед попыткой списания средств.
    Он должен подтвердить ('ok=True') или отклонить ('ok=False') платеж
    в течение 10 секунд. В данной версии всегда подтверждает платеж.

    Args:
        bot: Экземпляр telebot.TeleBot.
    """
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def pre_checkout_query_callback(pre_checkout_query: types.PreCheckoutQuery):
        # print(f"PreCheckoutQuery: {pre_checkout_query.id}")
        # Просто подтверждаем для теста
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            print(f"Ошибка при ответе на PreCheckoutQuery {pre_checkout_query.id}: {e}")
            try:
                bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Техническая ошибка")
            except Exception as final_e:
                 print(f"Не удалось ответить даже отказом на PreCheckoutQuery {pre_checkout_query.id}: {final_e}")


def handle_successful_payment(bot: telebot.TeleBot):
    """Регистрирует обработчик для сообщений о 'successful_payment'.

    Этот обработчик вызывается после успешного завершения платежа.
    Он извлекает информацию о платеже и отправляет подтверждение пользователю.
    Именно здесь должна быть логика выполнения оплаченного заказа.

    Args:
        bot: Экземпляр telebot.TeleBot.
    """
    @bot.message_handler(content_types=['successful_payment'])
    def successful_payment_callback(message: types.Message):
        payment_info = message.successful_payment
        amount = payment_info.total_amount / 100
        currency = payment_info.currency
        payload = payment_info.invoice_payload

        # print(f"SuccessfulPayment: user={message.from_user.id}, amount={amount} {currency}, payload={payload}")
        #ГЛАВНАЯ ЛОГИКА ПОСЛЕ ОПЛАТЫ ---
        # ИМЕННО ЗДЕСЬ НУЖНО ДЕЙСТВОВАТЬ!
        # 1. Найти заказ по `payload` в вашей базе данных.
        # 2. Отметить заказ как "Оплачено".

        # Отправляем подтверждение пользователю
        bot.send_message(
            message.chat.id,
            f"✅ Тестовая оплата (Redsys Test) на сумму {amount} {currency} прошла успешно!\n" # Уточнили, что оплата тестовая
            f"Спасибо за покупку! 🎉\n"
            f"(Payload: `{payload}`)"
        )

