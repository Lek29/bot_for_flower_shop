import telebot
from telebot import types
from keyboards import first_keyboard, create_first_set_inline, order_keyboard
import time

user_states = {}
user_info = {}


def handle_start(bot: telebot.TeleBot):
    """Регистрирует обработчик команды /start.

    При получении команды /start отправляет приветственное сообщение
    и предлагает выбрать повод для букета с помощью клавиатуры.

    Args:
        bot: Экземпляр telebot.TeleBot.
    """
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id

        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_info:
            del user_info[user_id]
        #Сбрасываем все клавиатуры
        bot.send_message(message.chat.id,
                         "Добро пожаловать в цветочный магазин!",
                         reply_markup=telebot.types.ReplyKeyboardRemove())

        bot.send_message(message.chat.id, '''К какому событию готовимся? Выберите один из вариантов, либо укажите свой.''',
            reply_markup=first_keyboard()
        )


def handle_messages(bot: telebot.TeleBot, provider_token: str):
    """Регистрирует обработчик для текстовых сообщений.

    Обрабатывает нажатие кнопки 'Назад' и выбор повода для букета.
    На другие текстовые сообщения просит использовать кнопки.

    Args:
        bot: Экземпляр telebot.TeleBot.
    """
    @bot.message_handler(func=lambda message: True)
    def handler_message(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_state = user_states.get(user_id)

        if current_state == 'awaiting_name':
            user_info[user_id]['name'] = message.text
            user_states[user_id] = 'awaiting_address'
            bot.send_message(chat_id, 'Отлично! Теперь введите адрес доставки:')
        elif current_state == 'awaiting_address':
            user_info[user_id]['address'] = message.text
            user_states[user_id] = 'awaiting_date'
            bot.send_message(chat_id, "Понял. Введите желаемую дату доставки (например, 25.12.2023):")
        elif current_state == 'awaiting_date':
            user_info[user_id]['date'] = message.text
            user_states[user_id] = 'awaiting_time'
            bot.send_message(chat_id, "Принято. И последнее - желаемое время доставки (например, 14:00-16:00):")
        elif current_state == 'awaiting_time':
            user_info[user_id]['time'] = message.text

            price = user_info[user_id].get('price')

            if not price:
                bot.send_message(chat_id, "Ошибка: не найдена цена. Начните сначала /start")
                if user_id in user_states: del user_states[user_id]
                if user_id in user_info: del user_info[user_id]
                return

            try:
                amount_rub = int(price.replace('~', ''))
                amount_kopecks = amount_rub * 100
                payload = f"order_{user_id}_{price}_{int(time.time())}"
                title = f"Оплата букета ({amount_rub} руб.)"
                description = f"Заказ из магазина @{bot.get_me().username}"
                prices = [types.LabeledPrice(label=f"Букет {amount_rub} руб.", amount=amount_kopecks)]
                user_info[user_id]['payload'] = payload

                if not provider_token:
                    bot.send_message(
                        chat_id,
                    "Онлайн-оплата временно недоступна. Мы сохранили детали вашего заказа и скоро свяжемся с вами."
                    )
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
                bot.send_message(chat_id, "Ваши данные приняты. Теперь вы можете оплатить заказ.")

                del user_states[user_id]

            except ValueError:
                bot.send_message(chat_id, "Ошибка при формировании счета (цена). Попробуйте /start.")
                if user_id in user_states: del user_states[user_id]
                if user_id in user_info: del user_info[user_id]
            except Exception as e:
                print(f"Ошибка send_invoice: {e}")
                bot.send_message(chat_id, "Не удалось создать счет. Попробуйте позже.")
                if user_id in user_states:
                    del user_states[user_id]

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
            user_info.setdefault(user_id, {})['price'] = price

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
            user_info[user_id] = {'price': price}

            user_states[user_id] = 'awaiting_name'

            bot.send_message(chat_id, "Для оформления заказа, пожалуйста, введите ваше имя:")
            bot.answer_callback_query(call.id, text="Начинаем оформление заказа...")




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
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            print(f"Ошибка при ответе на PreCheckoutQuery {pre_checkout_query.id}: {e}")
            try:
                bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Техническая ошибка")
            except Exception as final_e:
                 print(f"Не удалось ответить даже отказом на PreCheckoutQuery {pre_checkout_query.id}: {final_e}")


def handle_successful_payment(bot: telebot.TeleBot, user_info: dict):
    """Регистрирует обработчик для сообщений о 'successful_payment'.

    Этот обработчик вызывается после успешного завершения платежа.
    Он извлекает информацию о платеже и отправляет подтверждение пользователю.
    Именно здесь должна быть логика выполнения оплаченного заказа.

    Args:
        bot: Экземпляр telebot.TeleBot.
    """
    @bot.message_handler(content_types=['successful_payment'])
    def successful_payment_callback(message: types.Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        payment_info = message.successful_payment
        amount = payment_info.total_amount / 100
        currency = payment_info.currency
        payload = payment_info.invoice_payload

        order_details = user_info.get(user_id)


        if order_details and order_details.get('payload') == payload:
            price = order_details.get('price', 'Не указана')
            name = order_details.get('name', 'Не указано')
            address = order_details.get('address', 'Не указан')
            date = order_details.get('date', 'Не указана')
            time = order_details.get('time', 'Не указано')

            confirmation_message = (
                f"✅ *Оплата на сумму {amount} {currency} прошла успешно!* Ваш заказ принят. Спасибо! 🎉\n\n"
                f"📝 *Детали заказа:*\n"
                f"💐 *Букет:* ~{price.replace('~', '')} руб.\n"
                f"👤 *Имя:* {name}\n"
                f"🏠 *Адрес:* {address}\n"
                f"📅 *Дата:* {date}\n"
                f"⏰ *Время:* {time}\n")

            bot.send_message(chat_id, confirmation_message, parse_mode='Markdown')

        #ГЛАВНАЯ ЛОГИКА ПОСЛЕ ОПЛАТЫ ---

        #1. Найти заказ по `payload` в вашей базе данных.
        #2. Отметить заказ как "Оплачено".

        bot.send_message(
            message.chat.id,
            f"✅ Тестовая оплата (Redsys Test) на сумму {amount} {currency} прошла успешно!\n" # Уточнили, что оплата тестовая
            f"Спасибо за покупку! 🎉\n"
        )

