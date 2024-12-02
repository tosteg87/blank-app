from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

# создание экземпляра приложения
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from . import models

with app.app_context():
    db.create_all()

# import views
from . import pages, reminder

scheduler = APScheduler()

@scheduler.task("interval", id="do_job_1", seconds=300, misfire_grace_time=900)
def job1():
  reminder.send_remind()

scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

from . import football
