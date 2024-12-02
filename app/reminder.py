from app import app, db, models, football_api
import telebot
from datetime import datetime, timezone, timedelta

bot = telebot.TeleBot('5535682704:AAF-vdCVtdIi7dc2C_Hfn3WxE1YAwvE2zCE', threaded=False)

def send_remind():
    subscribes = models.Subscription.query.all()

    if subscribes:
        for subscribe in subscribes:
            match = football_api.get_team_games(subscribe.team_id)

            if match:
                team_name = match['team_name']
                match_date = match['match_date']
                offset = timedelta(hours=3)
                date_to = datetime.fromisoformat(match_date) + offset
                date_from = datetime.now(timezone.utc) + offset
                minutes_left = (date_to - date_from).total_seconds() / 60

                if (minutes_left <= subscribe.time) and (minutes_left > 0):
                    bot.send_message(int(subscribe.chat_id), f'Матч {team_name} начнётся в {date_to.hour}:{date_to.minute:02d}')
