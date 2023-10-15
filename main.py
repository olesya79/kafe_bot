from datetime import datetime

import pytz
import telebot
from telebot import types

from bot_settings import DATABASE
from bot_settings import Parms
from bot_settings import SETTINGS
from db_methods import Dirs
from db_methods import add_button_press_in_db
from db_methods import add_msg_in_db
from db_methods import create_or_update_doc_data
from db_methods import dirs
from db_methods import generate_message
from db_methods import generate_rating_message
from db_methods import get_menu_data
from db_methods import get_menu_position
from db_methods import get_top_buttons
from db_methods import get_top_messages
from db_methods import get_top_users_by_time
from firestore_client import FirestoreClient
from menu import CATS_DIR
from menu import MENU_DIR
from menu import MenuInfo
from menu import Scope
from telegram_token import bot_token

# https://t.me/men28_bot
bot = telebot.TeleBot(bot_token)
client = FirestoreClient()


@bot.message_handler(commands=['start'])
def start_bot(message):
    bot.send_message(message.chat.id, f'Привет {message.from_user.full_name}',
                     reply_markup=create_markup(CATS_DIR[Scope.categories]))


@bot.message_handler(commands=['help'])
def help(message):
    start = '/start - Команда для получения меню'
    admin_buttons = '/admin_buttons - Команда для получения информации о кнопках'
    admin_messages = '/admin_messages - Команда для получения рейтинга пльзователей по оставленным сообщениям'
    admin_time = f'/admin_time - Команда для получения информации за {SETTINGS[Parms.time_range]} последних дней'
    msg = f'Для того чтобы оставить своё пожелание кафе, просто напишите в чат сообщение (лимит сообщений: {SETTINGS[Parms.message_limit]})'
    bot.send_message(
        chat_id=message.chat.id,
        text='\n'.join([x for x in [start, admin_buttons, admin_messages, admin_time, msg]])
    )


@bot.message_handler(commands=['admin_buttons'])
def admin_buttons_bot(message):
    info = get_top_buttons(client)
    top_taps = info[dirs[Dirs.button_taps]]
    top_users = info[dirs[Dirs.user_buttons]]
    msg = generate_rating_message(top_taps, "кнопок", SETTINGS[Parms.top_buttons_range])
    msg += '\n\n'
    msg += generate_rating_message(top_users, 'пользователей по нажатию кнопок', SETTINGS[Parms.top_users_range])
    bot.send_message(
        chat_id=message.chat.id,
        text=msg,
        parse_mode=SETTINGS[Parms.parse_mode]
    )


@bot.message_handler(commands=['admin_messages'])
def admin_buttons_bot(message):
    info = get_top_messages(client)
    top_users = info[dirs[Dirs.user_messages]]
    msg = generate_rating_message(top_users, 'пользователей по оставленным сообщениям',
                                  SETTINGS[Parms.top_messages_range])
    bot.send_message(
        chat_id=message.chat.id,
        text=msg,
        parse_mode=SETTINGS[Parms.parse_mode]
    )


@bot.message_handler(commands=['admin_time'])
def admin_time_users(message):
    info = get_top_users_by_time(client)
    top_users_message = info[dirs[Dirs.user_messages]]
    top_users_button = info[dirs[Dirs.user_buttons]]
    top_buttons = info[dirs[Dirs.button_taps]]
    msg = generate_rating_message(top_users_message, 'пользователей по оставленным сообщениям',
                                  SETTINGS[Parms.top_messages_range], SETTINGS[Parms.time_range])
    msg += '\n\n'
    msg += generate_rating_message(top_users_button, "пользователей по нажатию кнопок",
                                   SETTINGS[Parms.top_users_range], SETTINGS[Parms.time_range])
    msg += '\n\n'
    msg += generate_rating_message(top_buttons, "кнопок", SETTINGS[Parms.top_buttons_range], SETTINGS[Parms.time_range])
    bot.send_message(
        chat_id=message.chat.id,
        text=msg,
        parse_mode=SETTINGS[Parms.parse_mode]
    )


def create_markup(keyboard_name: str):
    actual_keyboard = get_menu_data(client, keyboard_name)
    keyboard = types.InlineKeyboardMarkup()
    for pos in actual_keyboard:
        callback_data = f"{keyboard_name};{pos[MENU_DIR[MenuInfo.id]]};{pos[MENU_DIR[MenuInfo.name]]}"
        keyboard.add(types.InlineKeyboardButton(text=pos[MENU_DIR[MenuInfo.name]], callback_data=callback_data))
    if keyboard_name != CATS_DIR[Scope.categories]:
        keyboard.add(types.InlineKeyboardButton(text='Домой', callback_data='home;0;Домой'))
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_actions(call):
    user = call.from_user.username
    time = datetime.now(pytz.timezone('Europe/Moscow'))
    parms = call.data.split(';')
    button_doc = create_or_update_doc_data(client, DATABASE[Parms.buttons], user,
                                           add_button_press_in_db(parms[2], time))
    if button_doc is not None:
        client.add_info_in_array(DATABASE[Parms.collection], DATABASE[Parms.buttons], user,
                                 add_button_press_in_db(parms[2], time))
    if int(parms[1]) == 0:
        bot.send_message(
            chat_id=call.message.chat.id,
            text='Вы вернулись к выбору категорий',
            reply_markup=create_markup(CATS_DIR[Scope.categories]),
        )
        return
    button = get_menu_position(get_menu_data(client, parms[0]), int(parms[1]))
    bot.send_message(
        chat_id=call.from_user.id,
        text=generate_message(button),
        reply_markup=create_markup(button[MENU_DIR[MenuInfo.next_position]]),
        parse_mode=SETTINGS[Parms.parse_mode]
    )


@bot.message_handler(content_types=['text'])
def add_message_in_db(message):
    user = message.from_user.username
    time = datetime.now(pytz.timezone('Europe/Moscow'))
    messages = create_or_update_doc_data(client, DATABASE[Parms.messages], user, add_msg_in_db(message.text, time))
    if messages is None:
        return
    if len(messages[user]) <= SETTINGS[Parms.message_limit]:
        client.add_info_in_array(DATABASE[Parms.collection], DATABASE[Parms.messages],
                                 user, add_msg_in_db(message.text, time))
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text='Лимит сообщений исчерпан'
        )


if __name__ == '__main__':
    bot.polling(non_stop=True, interval=0)
