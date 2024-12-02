from app import app, db, models, football_api
from flask import render_template, request
import telebot
from datetime import datetime, timezone, timedelta

bot = telebot.TeleBot('5535682704:AAF-vdCVtdIi7dc2C_Hfn3WxE1YAwvE2zCE', threaded=False)

@app.route('/')
def home():
  content = ''
  #models.Subscription.query.delete()
  #db.session.commit()

  subscribes = models.Subscription.query.all()

  if subscribes:
    for subscribe in subscribes:
      match = football_api.get_team_games(subscribe.team_id)
      content += f'{subscribe.team_id}'

      if match:
        team_name = match['team_name']
        match_date = match['match_date']
        content += f'{team_name} - {match_date}'

  return content

@app.route('/test', methods=["GET", "POST"])
def test_page():
    user = request.args.get('name')
    return render_template('hello.html', user_name=user)