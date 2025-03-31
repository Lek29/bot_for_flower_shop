import time
import os

from django.db.models.functions import Random
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

from shop.models import Bouquet

FLORIST_CHAT_ID = os.getenv('FLORIST_CHAT_ID')
COURIER_CHAT_ID = os.getenv('COURIER_CHAT_ID')


def handle_start(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        user_states.pop(user_id, None)
        user_info.pop(user_id, None)

        bot.send_message(
            chat_id,
            "Добро пожаловать в цветочный магазин!",
            reply_markup=telebot.types.ReplyKeyboardRemove()
        )
        bot.send_message(
            chat_id,
            "К какому событию готовимся? Выберите один из вариантов, либо укажите свой.",
            reply_markup=first_keyboard()
        )


def handle_messages(bot, provider_token):
    @bot.message_handler(func=lambda message: True)
    def handler_message(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_state = user_states.get(user_id, None)

        if current_state == 'awaiting_custom_occasion':
            user_info[user_id] = {}
            user_info[user_id]['custom_occasion'] = message.text or 'Без повода'
            user_info[user_id]['occasion'] = 'Без повода'
            user_states[user_id] = 'awaiting_price_selection'

            bot.send_message(
                chat_id,
                "На какую сумму рассчитываете?",
                reply_markup=create_first_set_inline()
            )
            return

        if current_state == 'awaiting_phone_consult':
            phone_number = message.text
            user_info.setdefault(user_id, {})['phone_consult'] = phone_number

            bot.send_message(
                chat_id,
                "Флорист скоро свяжется с вами. А пока можете присмотреть что-нибудь из готовой коллекции:"
            )
            bot.send_message(
                chat_id,
                'На какую сумму рассчитываете?',
                reply_markup=create_first_set_inline()
            )

            if FLORIST_CHAT_ID:
                try:
                    florist_chat_id = int(FLORIST_CHAT_ID)
                    customer_username = message.from_user.username
                    customer_contact_info = f"@{customer_username}" if customer_username else f"User ID: {user_id}"
                    bot.send_message(
                        florist_chat_id,
                        f"📞 *Запрос на консультацию!*\n\n"
                        f"👤 *Клиент:* {customer_contact_info}\n"
                        f"☎️ *Телефон:* {phone_number}\n\n"
                        f"Пожалуйста, свяжитесь с клиентом.",
                        parse_mode='Markdown'
                    )
                except ValueError:
                    print("Ошибка: FLORIST_CHAT_ID не является целым числом.")

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
            bot.send_message(chat_id, "Понял. Введите желаемую дату доставки (например, 25.12.2025):")
            return

        elif current_state == 'awaiting_date':
            user_info[user_id]['date'] = message.text
            user_states[user_id] = 'awaiting_time'
            bot.send_message(chat_id, "Принято. Теперь желаемое время доставки (например, 14:00-16:00):")
            return

        elif current_state == 'awaiting_time':
            user_info[user_id]['time'] = message.text

            price = user_info[user_id].get('price')
            bouquet_id = user_info[user_id].get('bouquet_id')

            if not price or not bouquet_id:
                bot.send_message(chat_id, "Ошибка: не найдена цена или букет. Начните сначала /start.")
                user_states.pop(user_id, None)
                user_info.pop(user_id, None)
                return

            if not provider_token:
                bot.send_message(chat_id, "Онлайн-оплата недоступна. Заказ сформирован без оплаты.")
                user_states.pop(user_id, None)
                return

            order_id = int(time.time())
            user_info[user_id]['order_id'] = order_id
            payload = f"order_{user_id}_{price}_{order_id}"
            user_info[user_id]['payload'] = payload

            try:
                bouquet_obj = Bouquet.objects.get(id=bouquet_id)
                invoice_title = f"Оплата букета: {bouquet_obj.title}"
                invoice_desc = f"Заказ #{order_id} из магазина @{bot.get_me().username}"
            except Bouquet.DoesNotExist:
                invoice_title = "Оплата букета"
                invoice_desc = f"Заказ #{order_id} из магазина @{bot.get_me().username}"

            try:
                amount_in_kop = int(price) * 100
                bot.send_invoice(
                    chat_id=chat_id,
                    title=invoice_title,
                    description=invoice_desc,
                    invoice_payload=payload,
                    provider_token=provider_token,
                    currency='RUB',
                    prices=[types.LabeledPrice(label="Букет", amount=amount_in_kop)]
                )
                bot.send_message(chat_id, "Ваш заказ создан. Оплатите, чтобы завершить оформление.")
            except Exception as e:
                print(f"Ошибка send_invoice: {e}")
                bot.send_message(chat_id, "Не удалось создать счёт. Попробуйте позже.")

            user_states.pop(user_id, None)
            return

        if message.text == 'Назад':
            bot.send_message(
                chat_id,
                "Вы вернулись в главное меню",
                reply_markup=first_keyboard()
            )

        elif message.text in ("День рождения", "Свадьба", "В школу", "Без повода"):
            user_info[user_id] = {'occasion': message.text}
            user_states[user_id] = 'awaiting_price_selection'
            bot.send_message(
                chat_id,
                'На какую сумму рассчитываете?',
                reply_markup=create_first_set_inline()
            )

        elif message.text == "Другой повод":
            user_states[user_id] = 'awaiting_custom_occasion'
            bot.send_message(chat_id, "Укажите, пожалуйста, повод:")

        else:
            bot.send_message(chat_id, "Пожалуйста, используйте кнопки меню или /start.")


def handle_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        if call.data.startswith('~'):
            price_str = call.data.replace('~', '')
            user_info.setdefault(user_id, {})
            user_info[user_id]['price'] = price_str

            occasion = user_info[user_id].get('occasion', '')

            qs = Bouquet.objects.filter(is_active=True)
            if occasion:
                qs = qs.filter(occasion__iexact=occasion)

            try:
                if price_str.isdigit():
                    price_value = int(price_str)
                    qs = qs.filter(price__lte=price_value).order_by('-price')
                    bouquet = qs.first()
                elif price_str == 'Больше':
                    qs = qs.filter(price__gt=2000).order_by('price')
                    bouquet = qs.first()
                elif price_str == 'Не важно':
                    bouquet = qs.order_by(Random()).first()
                else:
                    bouquet = None

                if bouquet:
                    user_info[user_id]['bouquet_id'] = bouquet.id
                    with open(bouquet.photo.path, 'rb') as photo:
                        caption = f"{bouquet.description}\n\nЦена: {bouquet.price} руб."
                        bot.send_photo(chat_id, photo, caption=caption, reply_markup=order_keyboard(bouquet.price))

                    additional_text = (
                        "<b>Хотите что-то еще более уникальное?</b>\n"
                        "Подберите другой букет из нашей коллекции или закажите консультацию флориста."
                    )
                    bot.send_message(chat_id, additional_text, parse_mode='HTML', reply_markup=markup_keyboard())
                else:
                    bot.answer_callback_query(
                        call.id,
                        "Букетов не найдено под выбранные критерии.",
                        show_alert=True
                    )
            except Exception as e:
                print(f"Ошибка при выборе букета: {e}")
                bot.answer_callback_query(call.id, "Ошибка при выборе букета.", show_alert=True)

        elif call.data.startswith('order_'):
            parts = call.data.split('_')
            if len(parts) == 2:
                price_value = parts[1]
                user_info[user_id]['price'] = price_value

            user_states[user_id] = 'awaiting_name'
            bot.send_message(chat_id, "Для оформления заказа, укажите Ваше имя:")
            bot.answer_callback_query(call.id, "Начинаем оформление заказа...")

        elif call.data == 'consult':
            user_states[user_id] = 'awaiting_phone_consult'
            bot.send_message(chat_id, "Укажите номер телефона, и наш флорист перезвонит вам в течение 20 минут.")
            bot.answer_callback_query(call.id, "Введите номер телефона")

        elif call.data == 'more_flowers':
            last_id = user_info.get(user_id, {}).get('bouquet_id')
            last_price_str = user_info.get(user_id, {}).get('price')
            occasion = user_info[user_id].get('occasion', '')

            if not last_id or not last_price_str:
                bot.answer_callback_query(call.id, "Сначала выберите какой-нибудь букет", show_alert=True)
                return

            try:
                last_bouquet = Bouquet.objects.get(id=last_id, is_active=True)
            except Bouquet.DoesNotExist:
                bot.answer_callback_query(call.id, "Текущий букет недоступен", show_alert=True)
                return

            try:
                p_last = int(last_price_str) if last_price_str.isdigit() else last_bouquet.price
            except ValueError:
                p_last = last_bouquet.price

            p_min = max(0, p_last - 200)
            p_max = p_last + 200

            qs = Bouquet.objects.filter(is_active=True)
            if occasion:
                qs = qs.filter(occasion__iexact=occasion)

            qs = qs.filter(price__gte=p_min, price__lte=p_max).exclude(id=last_bouquet.id)
            new_bouquet = qs.order_by(Random()).first()
            if not new_bouquet:
                bot.answer_callback_query(
                    call.id,
                    "В диапазоне ±200 руб больше нет букетов. Попробуйте другую категорию.",
                    show_alert=True
                )
                return

            user_info[user_id]['bouquet_id'] = new_bouquet.id
            user_info[user_id]['price'] = str(new_bouquet.price)

            try:
                with open(new_bouquet.photo.path, 'rb') as photo:
                    caption = f"{new_bouquet.description}\n\nЦена: {new_bouquet.price} руб."
                    bot.send_photo(chat_id, photo, caption=caption, reply_markup=order_keyboard(new_bouquet.price))
            except Exception as e:
                print(f"Ошибка открытия фото {e}")
                bot.send_message(chat_id, "Не удалось открыть фото букета.")

            additional_text = (
                "<b>Хотите что-то еще более уникальное?</b>\n"
                "Подберите другой букет из нашей коллекции или закажите консультацию флориста."
            )
            bot.send_message(chat_id, additional_text, parse_mode='HTML', reply_markup=markup_keyboard())
            bot.answer_callback_query(call.id)


def handle_pre_checkout(bot):
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def pre_checkout_query_callback(pre_checkout_query):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            print(f"Ошибка при ответе на PreCheckoutQuery {pre_checkout_query.id}: {e}")
            try:
                bot.answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=False,
                    error_message="Техническая ошибка при оплате."
                )
            except Exception as final_e:
                print(f"Не удалось ответить отказом на PreCheckoutQuery: {final_e}")


def handle_successful_payment(bot):
    @bot.message_handler(content_types=['successful_payment'])
    def successful_payment_callback(message):
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
            name = info.get('name', 'Не указано')
            address = info.get('address', 'Не указано')
            date_val = info.get('date', 'Не указано')
            time_val = info.get('time', 'Не указано')
            bouquet_id = info.get('bouquet_id')
            bouquet_price = info.get('price', 0)

            confirmation_text = (
                f"✅ Оплата на сумму {amount} {currency} прошла успешно!\n"
                f"Заказ #{order_id} теперь оплачен. Спасибо! 🎉\n\n"
                f"Имя получателя: {name}\n"
                f"Адрес: {address}\n"
                f"Дата: {date_val} | Время: {time_val}\n"
                f"Сумма: {bouquet_price} руб.\n"
            )
            bot.send_message(chat_id, confirmation_text)

            if COURIER_CHAT_ID:
                try:
                    courier_chat_id = int(COURIER_CHAT_ID)
                    courier_text = (
                        f"‼️ *Новый оплаченный заказ #{order_id}!* \n\n"
                        f"💰 *Сумма:* {amount} {currency}\n"
                        f"💐 *Цена букета:* {bouquet_price} руб.\n"
                        f"👤 *Получатель:* {name}\n"
                        f"🏠 *Адрес:* {address}\n"
                        f"📅 *Дата:* {date_val}\n"
                        f"⏰ *Время:* {time_val}\n"
                    )
                    bot.send_message(courier_chat_id, courier_text, parse_mode='Markdown')
                except ValueError:
                    print("Ошибка: COURIER_CHAT_ID не является целым числом.")

        else:
            bot.send_message(chat_id, "Не удалось подтвердить оплату заказа. Обратитесь в поддержку.")

        user_info.pop(user_id, None)
        bot.send_message(
            chat_id,
            f"✅ Спасибо за покупку! Ваш заказ оплачен на {amount} {currency}."
        )
