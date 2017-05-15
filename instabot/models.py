from datetime import datetime

import enum
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Float, ForeignKey

app = Flask(__name__)
DIR = os.path.dirname(os.path.realpath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/test.db'.format(DIR)
db = SQLAlchemy(app)


class InstaAccount(db.Model):
    """
    Instagram User
    """
    id = Column(Integer, primary_key=True)
    username = Column(String(256), unique=True)
    password = Column(String(256))

    created_at = Column(DateTime)

    def __init__(self, username, password, created_at=datetime.utcnow()):
        self.username = username
        self.password = password
        self.created_at = created_at

    def __repr__(self):
        return '<Username %r>' % self.username


class Content(db.Model):
    """
    User content model for storing photos and videos
    """
    id = Column(Integer, primary_key=True)
    insta_account_id = Column(Integer, ForeignKey('insta_account.id'))
    caption = Column(String(1024))
    url = Column(String(512))
    path = Column(String(512))
    verified = Column(Boolean)
    created_at = Column(DateTime)

    def __init__(self, insta_account_id, caption, url, path, verified=False, created_at=datetime.utcnow()):
        self.insta_account_id = insta_account_id
        self.caption = caption
        self.url = url
        self.path = path
        self.verified = verified
        self.created_at = created_at

    def __repr__(self):
        return '<User %r> <URL %r>' % (self.insta_account_id, self.url)


class BotType(enum.Enum):
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    POST = "post"


class Bot(db.Model):
    """
    Bots Model to store active bots
    """
    id = Column(Integer, primary_key=True)
    insta_account_id = Column(Integer, ForeignKey('insta_account.id'))
    bot = Column(Enum(BotType))
    interval = Column(Float)
    action_interval = Column(Float)
    rate = Column(Integer)
    unix_pid = Column(String(16))
    created_at = Column(DateTime)

    def __init__(self, insta_account_id, bot, interval, action_interval, rate, unix_pid=None,
                 created_at=datetime.utcnow()):
        self.insta_account_id = insta_account_id
        self.bot = bot
        self.interval = interval
        self.action_interval = action_interval
        self.rate = rate
        self.unix_pid = unix_pid

        self.created_at = created_at

    def __repr__(self):
        return '<User %r Bot %r>' % (self.insta_user_id, self.bot)


@app.route('/', methods=['GET'])
def home():
    return "Home"


def main():
    db.create_all()

    account = InstaAccount('hwzearth', '1234')
    db.session.add(account)
    db.session.commit()

    hwzearth = InstaAccount.query.filter_by(username='hwzearth').first()
    print hwzearth
    content = Content(hwzearth.id, 'caption', 'url', 'path')
    bot = Bot(hwzearth.id, BotType.FOLLOW, 1.0, 2.0, 3)

    db.session.add(content)
    db.session.add(bot)
    db.session.commit()
    app.run(host="0.0.0.0", port="5000")


if __name__ == '__main__':
    main()
