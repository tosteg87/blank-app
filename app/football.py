from app import app, db, models
import logging
import time
import json
from urllib.parse import parse_qs
import telebot
from flask import abort, request
from . import football_api
from sqlalchemy import and_

logging.basicConfig(level=logging.INFO,
                    filename="py_log.log",
                    filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")

secret = "AAFptTVEoPltHwMRmRo2ZiG2sAetXc-96eU"
bot = telebot.TeleBot('5535682704:AAF-vdCVtdIi7dc2C_Hfn3WxE1YAwvE2zCE', threaded=False)

#bot.remove_webhook()
#time.sleep(1)
#bot.set_webhook(url="https://footbalreminder.onrender.com/tghook{}".format(secret))

@app.route('/tghook{}'.format(secret), methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        request_body_dict = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return 'ok'
    else:
        return abort(403)


@bot.message_handler(commands=['start'])
def send_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    countries_list = football_api.get_countries()
    chunks_list = list(chunk_dict(countries_list, 10))
    count_page = len(chunks_list)

    countries_buttons = []

    for name in chunks_list[0].keys():
        countries_buttons.append(
            telebot.types.InlineKeyboardButton(
                text=name, callback_data=f't=select&ct=countries&name={name}'))
    markup.add(*countries_buttons)

    if (count_page > 1):
        markup.add(
            telebot.types.InlineKeyboardButton(
                text='Вперёд', callback_data='t=page&cp=1&ct=countries'))

    bot.send_message(message.chat.id, 'Выберите страну', reply_markup=markup)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_string = []
    help_string.append("*Football subscriber*.\n\n")
    help_string.append("/start - start subscribe\n")
    help_string.append("/help - show help")
    bot.send_message(message.chat.id,
                     "".join(help_string),
                     parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data:
        data = parse_qs(call.data)
        message = call.message

        if data['t'][0] == 'page':
            current_page = int(data['cp'][0])

            match data['ct'][0]:
                case 'countries':
                    markup = countries_page_buttons(current_page)
                    bot.edit_message_text('Выберите страну',
                                          chat_id=message.chat.id,
                                          message_id=message.message_id,
                                          reply_markup=markup)

                case 'leagues':
                    markup = leagues_page_buttons(current_page,
                                                  data['name'][0])
                    bot.edit_message_text('Выберите лигу',
                                          chat_id=message.chat.id,
                                          message_id=message.message_id,
                                          reply_markup=markup)
        elif data['t'][0] == 'select':
            type = data['ct'][0]

            match type:
                case 'countries':
                    country = data['name'][0]
                    markup = telebot.types.InlineKeyboardMarkup()
                    leagues_list = football_api.get_leagues(country)
                    chunks_list = list(chunks(leagues_list, 10))
                    count_page = len(chunks_list)
                    
                    leagues_buttons = []

                    for league in chunks_list[0]:
                        league_id = league['id']
                        league_name = league['name']

                        leagues_buttons.append(
                            telebot.types.InlineKeyboardButton(
                                text=league_name,
                                callback_data=
                                f't=select&ct=leagues&league_id={league_id}'))
                    
                    markup.add(*leagues_buttons)

                    if (count_page > 1):
                        markup.add(
                            telebot.types.InlineKeyboardButton(
                                text='Вперёд',
                                callback_data=
                                f't=page&cp=1&ct=leagues&name={country}'))

                    bot.delete_message(message.chat.id, message.message_id)
                    bot.send_message(message.chat.id,
                                     'Выберите лигу',
                                     reply_markup=markup)

                case 'leagues':
                    league_id = data['league_id'][0]
                    teams = football_api.get_teams(league_id)

                    bot.delete_message(message.chat.id, message.message_id)

                    if teams:
                        markup = telebot.types.InlineKeyboardMarkup()
                        teams_buttons = []

                        for team_id, team_name in teams.items():
                            teams_buttons.append(telebot.types.InlineKeyboardButton(text=team_name, callback_data=f't=select&ct=team&team_id={team_id}'))
                        markup.add(*teams_buttons)
                    
                        bot.send_message(message.chat.id, 'Выберите команду', reply_markup=markup)
                    else:
                        bot.send_message(message.chat.id, 'Команды не найдены')
                
                case 'team':
                    team_id = data['team_id'][0]
                    team_name = football_api.get_team_name(team_id)

                    bot.delete_message(message.chat.id, message.message_id)

                    exist_subscription = models.Subscription.query.filter(models.Subscription.chat_id == message.chat.id, models.Subscription.team_id == team_id).all()
                    
                    if (exist_subscription):
                        bot.send_message(message.chat.id, f'{team_name} уже добавлена в отслеживаемые')
                    else:
                        s = models.Subscription(chat_id=message.chat.id, team_id=team_id, time=10)
                        db.session.add(s)
                        db.session.commit()
                    
                        bot.send_message(message.chat.id, f'{team_name} добавлена в отслеживаемые')

def countries_page_buttons(current_page):
    markup = telebot.types.InlineKeyboardMarkup()
    countries_list = football_api.get_countries()
    chunks_list = list(chunk_dict(countries_list, 10))
    count_page = len(chunks_list)

    countries_buttons = []
    prev_next_buttons = create_paginations(current_page, count_page,
                                           'countries')

    for name in chunks_list[current_page].keys():
        countries_buttons.append(
            telebot.types.InlineKeyboardButton(
                text=name, callback_data=f't=select&ct=countries&name={name}'))

    markup.add(*countries_buttons)
    markup.add(*prev_next_buttons)

    return markup


def leagues_page_buttons(current_page, country):
    markup = telebot.types.InlineKeyboardMarkup()
    leagues_list = football_api.get_leagues(country)
    chunks_list = list(chunks(leagues_list, 10))
    count_page = len(chunks_list)

    leagues_buttons = []
    prev_next_buttons = create_paginations(current_page, count_page, 'leagues', country)

    for league in chunks_list[current_page]:
        league_id = league['id']
        league_name = league['name']

        leagues_buttons.append(
            telebot.types.InlineKeyboardButton(
                text=league_name,
                callback_data=
                f't=select&ct=leagues&league_id={league_id}&name={country}'))

    markup.add(*leagues_buttons)
    markup.add(*prev_next_buttons)

    return markup


def create_paginations(current_page, count_page, list_type, country = ''):
    prev_next_buttons = []

    if country:
        country = f'&name={country}'

    if current_page == 0 and count_page > 1:
        prev_next_buttons.append(
            telebot.types.InlineKeyboardButton(
                text='Вперёд',
                callback_data=f't=page&cp={current_page + 1}&ct={list_type}{country}'))
    elif current_page + 1 == count_page:
        prev_next_buttons.append(
            telebot.types.InlineKeyboardButton(
                text='Назад',
                callback_data=f't=page&cp={current_page - 1}&ct={list_type}{country}'))
    else:
        prev_next_buttons.append(
            telebot.types.InlineKeyboardButton(
                text='Назад',
                callback_data=f't=page&cp={current_page - 1}&ct={list_type}{country}'))
        prev_next_buttons.append(
            telebot.types.InlineKeyboardButton(
                text='Вперёд',
                callback_data=f't=page&cp={current_page + 1}&ct={list_type}{country}'))

    return prev_next_buttons


def chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def chunk_dict(d, size):
    items = list(d.items())
    chunks = [items[i:i + size] for i in range(0, len(items), size)]
    return [dict(chunk) for chunk in chunks]


#bot.infinity_polling()
