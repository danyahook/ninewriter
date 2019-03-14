#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telebot as tb
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from sqlalchemy import PrimaryKeyConstraint


NINE_WRITER = None
NINE_WRITER_WORLD = None
TEST_WRITER_1 = -1001399496717
TEST_WRITER_2 = -1001100854769


base = declarative_base()
engine = sa.create_engine("sqlite:////sqlite/nine.db")
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker())(bind=engine)


class UserModel(base):
    __tablename__ = "users"
    __table_args__ = (
        PrimaryKeyConstraint('tele_id', 'order', 'send_to'),
    )
    tele_id = sa.Column(sa.Integer)
    order = sa.Column(sa.String)
    send_to = sa.Column(sa.Integer)


# reload(sys)  # Reload does the trick!
# sys.setdefaultencoding('UTF8')

# ip = '104.248.114.3'
# port = '8080'

# apihelper.proxy = {
#  'https': 'https://{}:{}'.format(ip, port)
# }


def isint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def create_bot(api):
    bot = tb.TeleBot(api)

    @bot.message_handler(commands=['start','restart'])
    def handler_login(message):
        user_btn = tb.types.ReplyKeyboardMarkup(True)
        user_btn.row('💼 Менеджер')
        bot.send_message(message.from_user.id, "...", reply_markup=user_btn)

    @bot.message_handler(func=lambda message: message.text == '💼 Менеджер')
    def password_login(message):
        bot.send_message(message.from_user.id, "Введите пароль: ")

    @bot.message_handler(func=lambda message: message.text == '11223344')
    def main_menu(message):
        user = session.query(UserModel).filter_by(tele_id=message.from_user.id).first()
        if user is None:
            user_start = UserModel(tele_id=message.from_user.id, order="none", send_to=0)
            session.add(user_start)
        else:
            user.order = "none"
        session.commit()
        user_btn = tb.types.ReplyKeyboardMarkup(True)
        user_btn.row('📝 Заказ в @ninewriter')
        user_btn.row('📝 Заказ в @ninewriterwords')
        bot.send_message(message.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)

    @bot.message_handler(func=lambda message: message.text == '📝 Заказ в @ninewriter' or message.text == '📝 Заказ в @ninewriterwords')
    def choice_point(message):
        user = session.query(UserModel).filter_by(tele_id=message.from_user.id).first()
        if message.text == '📝 Заказ в @ninewriter':
            user.send_to = TEST_WRITER_1
        elif message.text == '📝 Заказ в @ninewriterwords':
            user.send_to = TEST_WRITER_2
        session.commit()
        user_btn = tb.types.ReplyKeyboardMarkup(True)
        user_btn.row('🖍 Заполнить заказ')
        user_btn.row('🔙 Назад', '📬 Отправить заказ в работу')
        bot.send_message(message.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)

    @bot.message_handler(func=lambda message: message.text == '🖍 Заполнить заказ')
    def text_take(message):
        user_rep = tb.types.ForceReply()
        bot.send_message(message.from_user.id, "Текст заказа:", reply_markup=user_rep)

    @bot.message_handler(func=lambda message: message.text == '🔙 Назад')
    def text_take(message):
        user = session.query(UserModel).filter_by(tele_id=message.from_user.id).first()
        if user is None:
            user_start = UserModel(tele_id=message.from_user.id, order="none")
            session.add(user_start)
        else:
            user.order = "none"
        session.commit()
        user_btn = tb.types.ReplyKeyboardMarkup(True)
        user_btn.row('📝 Заказ в @ninewriter')
        user_btn.row('📝 Заказ в @ninewriterwords')
        bot.send_message(message.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)

    @bot.message_handler(func=lambda message: message.text == '📬 Отправить заказ в работу')
    def text_take(message):
        user = session.query(UserModel).filter_by(tele_id=message.from_user.id).first()
        print(user.order)
        if user.order == "none":
            order_text = 'Поле не заполнено!'
        else:
            order_text = user.order
        session.commit()
        keyboard = tb.types.InlineKeyboardMarkup()
        callback_button = tb.types.InlineKeyboardButton(text="Отправить заказ!", callback_data="send")
        keyboard.add(callback_button)
        bot.send_message(message.from_user.id, order_text, reply_markup=keyboard)

    @bot.message_handler(func=lambda message: message.reply_to_message is not None)
    def handler_reorder(message):
        if message.reply_to_message.text == "Текст заказа:":
            user = session.query(UserModel).filter_by(tele_id=message.from_user.id).first()
            user.order = message.text
            session.commit()
            user_btn = tb.types.ReplyKeyboardMarkup(True)
            user_btn.row('🖍 Заполнить заказ')
            user_btn.row('🔙 Назад', '📬 Отправить заказ в работу')
            bot.send_message(message.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        if call.data == "send":
            user = session.query(UserModel).filter_by(tele_id=call.from_user.id).first()
            if user.order != "none":
                send_text = user.order
                user.order = "none"
                keyboard = tb.types.InlineKeyboardMarkup()
                callback_button = tb.types.InlineKeyboardButton(text="Take the order!", callback_data=user.tele_id)
                keyboard.add(callback_button)
                bot.send_message(user.send_to, send_text, reply_markup=keyboard)
                user_btn = tb.types.ReplyKeyboardMarkup(True)
                user_btn.row('📝 Заказ в @ninewriter')
                user_btn.row('📝 Заказ в @ninewriterwords')
                bot.send_message(call.from_user.id, "Выберите пункт меню: ", reply_markup=user_btn)
                bot.answer_callback_query(callback_query_id=call.id, show_alert=True,
                                          text="Заказ отправлен!")
            elif user.order == "none":
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                          text="Текст не введен!")
            session.commit()
        if isint(call.data) is True:
            try:
                message_text = call.message.text
                bot.send_message(chat_id=call.data,
                                 text=message_text + '\n-----------\n<b>⤵️Ваш заказ взял</b>\n\n🌐 <a href="tg://user?id={}">Ссылка на профиль</a>'.
                                 format(call.from_user.id),
                                 parse_mode='HTML')
                bot.send_message(chat_id=call.from_user.id,
                                 text=message_text + '\n-----------\n<b>⤵️Вы взяли заказ от</b>\n\n🌐 <a href="tg://user?id={}">Ссылка на профиль</a>'.
                                 format(call.data),
                                 parse_mode='HTML')
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                          text="Этот заказ уже взят!")

    return bot


def main():
    api_token = "TOKEN"
    bot = create_bot(api_token)
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()


