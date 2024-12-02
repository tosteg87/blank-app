from app import db

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    chat_id = db.Column(db.String(120))
    team_id = db.Column(db.Integer)
    time = db.Column(db.Integer)

#    def __repr__(self):
#        return {self.chat_id, self.team_id, self.time}
