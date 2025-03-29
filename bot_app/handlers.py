import time

import telebot
from telebot import types

from keyboards import (
    first_keyboard,
    create_first_set_inline,
    order_keyboard,
    markup_keyboard
)

user_states = {}
user_info = {}

from shop.models import Order, Bouquet, User


def handle_start(bot: telebot.TeleBot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message: types.Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        username = message.from_user.username or f'tg_user_{user_id}'
        full_name = message.from_user.full_name or username

        user_obj, created = User.objects.get_or_create(
            username=username,
            defaults={
                'full_name': full_name,
                'phone': '',
                'role': None,
                'chat_id': chat_id,
                'is_active': True
            }
        )
        if not created and user_obj.chat_id != chat_id:
            user_obj.chat_id = chat_id
            user_obj.save()

        user_states.pop(user_id, None)
        user_info.pop(user_id, None)

        bot.send_message(chat_id, "Добро пожаловать в цветочный магазин!",
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(chat_id,
                         "К какому событию готовимся? Выберите один из вариантов, либо укажите свой.",
                         reply_markup=first_keyboard())


def handle_messages(bot: telebot.TeleBot, provider_token: str):
    @bot.message_handler(func=lambda message: True)
    def handler_message(message: types.Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_state = user_states.get(user_id, None)

        if current_state == 'awaiting_phone_consult':
            phone_number = message.text
            user_info.setdefault(user_id, {})['phone_consult'] = phone_number

            bot.send_message(chat_id,
                             "Флорист скоро свяжется с вами. А пока можете присмотреть что-нибудь из готовой коллекции:")
            bot.send_message(chat_id,
                             'На какую сумму рассчитываете?',
                             reply_markup=create_first_set_inline())

            florists = User.objects.filter(role='florist', is_active=True, chat_id__isnull=False)
            customer_username = message.from_user.username
            customer_contact_info = f"@{customer_username}" if customer_username else f"User ID: {user_id}"
            for florist in florists:
                bot.send_message(
                    florist.chat_id,
                    f"📞 *Запрос на консультацию!*\n\n"
                    f"👤 *Клиент:* {customer_contact_info}\n"
                    f"☎️ *Телефон:* {phone_number}\n\n"
                    f"Пожалуйста, свяжитесь с клиентом.",
                    parse_mode='Markdown'
                )

            user_states.pop(user_id, None)
            return

        elif current_state == 'awaiting_name':
            user_info[user_id]['name'] = message.text
            user_states[user_id] = 'awaiting_address'
            bot.send_message(chat_id, "Отлично! Теперь введите адрес доставки:")
            return

        elif current_state == 'awaiting_address':
            user_info[user_id]['address'] = message.text
            user_states[user_id] = 'awaiting_date'
            bot.send_message(chat_id, "Понял. Введите желаемую дату доставки (например, 25.12.2023):")
            return

        elif current_state == 'awaiting_date':
            user_info[user_id]['date'] = message.text
            user_states[user_id] = 'awaiting_time'
            bot.send_message(chat_id, "Принято. Теперь желаемое время доставки (например, 14:00-16:00):")
            return

        elif current_state == 'awaiting_time':
            user_info[user_id]['time'] = message.text

            price = user_info[user_id].get('price')
            if not price:
                bot.send_message(chat_id, "Ошибка: не найдена цена. Начните сначала /start.")
                user_states.pop(user_id, None)
                user_info.pop(user_id, None)
                return

            try:
                rub_str = price.replace('~', '')
                rub_int = int(rub_str)
            except ValueError:
                rub_int = 0

            guest_user, _ = User.objects.get_or_create(
                username=f"tg_{user_id}",
                defaults={
                    "full_name": message.from_user.first_name or "Telegram User",
                    "phone": "",
                    "role": None,
                    "is_active": True
                }
            )

            bouquet_qs = Bouquet.objects.filter(is_active=True)
            bouquet_obj = bouquet_qs.first() if bouquet_qs.exists() else None

            order_obj = Order.objects.create(
                user=guest_user,
                bouquet=bouquet_obj,
                customer_name=user_info[user_id]['name'],
                phone="",
                address=user_info[user_id]['address'],
                delivery_datetime="2025-12-25 14:00:00",
                status='new',
                total_price=rub_int,
                florist=None,
                courier=None
            )

            user_info[user_id]['order_id'] = order_obj.id

            payload = f"order_{user_id}_{price}_{int(time.time())}"
            user_info[user_id]['payload'] = payload

            if not provider_token:
                bot.send_message(chat_id, "Онлайн-оплата недоступна. Заказ сохранён, статус: new.")
                user_states.pop(user_id, None)
                return

            amount_kopecks = rub_int * 100
            invoice_title = f"Оплата букета (~{rub_int} руб.)"
            invoice_desc = f"Заказ #{order_obj.id} из магазина {bot.get_me().username}"
            prices = [types.LabeledPrice(label=f"Букет {rub_int} руб.", amount=amount_kopecks)]

            try:
                bot.send_invoice(
                    chat_id=chat_id,
                    title=invoice_title,
                    description=invoice_desc,
                    invoice_payload=payload,
                    provider_token=provider_token,
                    currency='RUB',
                    prices=prices
                )
                bot.send_message(chat_id, "Ваш заказ создан. Оплатите, чтобы завершить оформление.")
            except Exception as e:
                print(f"Ошибка send_invoice: {e}")
                bot.send_message(chat_id, "Не удалось создать счёт. Попробуйте позже.")
                order_obj.delete()

            user_states.pop(user_id, None)
            return

        if message.text == 'Назад':
            bot.send_message(chat_id, "Вы вернулись в главное меню",
                             reply_markup=first_keyboard())
        elif message.text in ("День рождения", "Свадьба", "В школу", "Без повода", "Другой повод"):
            bot.send_message(chat_id, 'На какую сумму рассчитываете?',
                             reply_markup=create_first_set_inline())
        else:
            bot.send_message(chat_id, "Пожалуйста, используйте кнопки меню или /start.")


def handle_callbacks(bot: telebot.TeleBot, provider_token: str):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call: types.CallbackQuery):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        if call.data.startswith('~'):
            price_str = call.data
            user_info.setdefault(user_id, {})['price'] = price_str

            try:
                target_price = int(price_str.replace('~', ''))
            except ValueError:
                target_price = None

            bouquet = None
            if target_price:
                bouquet = Bouquet.objects.filter(
                    is_active=True,
                    price__lte=target_price
                ).order_by('-price').first()

            if not bouquet:
                bouquet = Bouquet.objects.filter(is_active=True).order_by('price').first()

            if not bouquet or not bouquet.photo:
                bot.answer_callback_query(call.id, "Подходящий букет не найден 😥", show_alert=True)
                return

            from django.conf import settings
            photo_path = bouquet.photo.path

            caption = (
                f"{bouquet.title}\n\n"
                f"{bouquet.description}\n"
                f"💰 Цена: {bouquet.price} руб."
            )

            try:
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=caption, reply_markup=order_keyboard(price_str))
            except Exception as e:
                print(f"Ошибка отправки фото: {e}")
                bot.send_message(chat_id, "Не удалось отправить фото букета. Попробуйте позже.")
                return

            additional_text = (
                "<b>Хотите что-то еще более уникальное?</b>\n"
                "Подберите другой букет из нашей коллекции или закажите консультацию флориста."
            )
            bot.send_message(chat_id, additional_text, parse_mode='HTML', reply_markup=markup_keyboard())
            bot.answer_callback_query(call.id)

        elif call.data.startswith('order_'):
            price = call.data.split('_')[1]
            user_info[user_id] = {'price': price}
            user_states[user_id] = 'awaiting_name'
            bot.send_message(chat_id, "Для оформления заказа, укажите Ваше имя:")
            bot.answer_callback_query(call.id, "Начинаем оформление заказа...")

        elif call.data == 'consult':
            user_states[user_id] = 'awaiting_phone_consult'
            bot.send_message(chat_id, "Укажите номер телефона, и наш флорист перезвонит вам в течение 20 минут.")
            bot.answer_callback_query(call.id, text="Введите номер телефона")

        elif call.data == 'more_flowers':
            bot.answer_callback_query(call.id, "Показ каталога в процессе...", show_alert=True)
            bot.send_message(chat_id, "Пока логика каталога не реализована.")


def handle_pre_checkout(bot: telebot.TeleBot):
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def pre_checkout_query_callback(pre_checkout_query: types.PreCheckoutQuery):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            print(f"Ошибка при ответе на PreCheckoutQuery {pre_checkout_query.id}: {e}")
            try:
                bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False,
                                              error_message="Техническая ошибка при оплате.")
            except Exception as final_e:
                print(f"Не удалось ответить отказом на PreCheckoutQuery: {final_e}")


def handle_successful_payment(bot: telebot.TeleBot, user_info: dict):
    @bot.message_handler(content_types=['successful_payment'])
    def successful_payment_callback(message: types.Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        payment_info = message.successful_payment
        amount = payment_info.total_amount / 100
        currency = payment_info.currency
        payload = payment_info.invoice_payload

        info = user_info.get(user_id, {})
        stored_payload = info.get('payload')
        order_id = info.get('order_id')

        if stored_payload == payload and order_id:
            try:
                order_obj = Order.objects.get(id=order_id)
                order_obj.status = 'paid'
                order_obj.save()

                name = order_obj.customer_name
                address = order_obj.address
                total_price = order_obj.total_price

                confirmation_text = (
                    f"✅ Оплата на сумму {amount} {currency} прошла успешно!\n"
                    f"Заказ #{order_id} теперь оплачен. Спасибо! 🎉\n"
                    f"Имя получателя: {name}\n"
                    f"Адрес: {address}\n"
                )
                bot.send_message(chat_id, confirmation_text)

                couriers = User.objects.filter(role='courier', is_active=True, chat_id__isnull=False)
                for courier in couriers:
                    courier_text = (
                        f"‼️ *Новый оплаченный заказ #{order_id}!* \n\n"
                        f"💰 *Сумма:* {amount} {currency}\n"
                        f"💐 *Букет:* {total_price} руб.\n"
                        f"👤 *Получатель:* {name}\n"
                        f"🏠 *Адрес:* {address}\n"
                    )
                    bot.send_message(courier.chat_id, courier_text, parse_mode='Markdown')

            except Order.DoesNotExist:
                bot.send_message(chat_id, "Ошибка: заказ не найден в базе данных.")
        else:
            bot.send_message(chat_id, "Не удалось подтвердить оплату заказа. Обратитесь в поддержку.")

        user_info.pop(user_id, None)

        bot.send_message(
            chat_id,
            f"✅ Спасибо за покупку! Ваш заказ оплачен на {amount} {currency}."
        )
