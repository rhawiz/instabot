import os
from datetime import datetime

import enum
import signal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Float, ForeignKey

from app import app, db


class InstaAccount(db.Model):
    """
    Instagram User
    """
    id = Column(Integer, primary_key=True)
    username = Column(String(256), unique=True)
    password = Column(String(256))
    similar_users = Column(String(1024))
    created_at = Column(DateTime)
    __table_args__ = {'extend_existing': True}

    def __init__(self, username, password, similar_users, created_at=datetime.utcnow()):
        self.username = username
        self.password = password
        self.similar_users = similar_users
        self.created_at = created_at

    def create_bots(self):
        db.session.add(Bot(self.id, BotType.FOLLOW, 5400, 8.0, 75))
        db.session.add(Bot(self.id, BotType.UNFOLLOW, 5400, 8.0, 120))
        db.session.add(Bot(self.id, BotType.POST, 86400, 1.0, 1))

    def follow_bot(self):
        return Bot.query.filter_by(insta_account_id=self.id, bot=BotType.FOLLOW).first()

    def unfollow_bot(self):
        return Bot.query.filter_by(insta_account_id=self.id, bot=BotType.UNFOLLOW).first()

    def post_bot(self):
        return Bot.query.filter_by(insta_account_id=self.id, bot=BotType.POST).first()

    def __repr__(self):
        return '<Username %r>' % self.username


class Content(db.Model):
    """
    User content model for storing photos and videos
    """
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    insta_account_id = Column(Integer, ForeignKey('insta_account.id'))
    caption = Column(String(1024))
    url = Column(String(512))
    path = Column(String(512))
    type = Column(String(64))
    thumbnail = Column(String(512))
    verified = Column(Boolean)
    created_at = Column(DateTime)

    def __init__(self, insta_account_id, caption, url, path, type, thumbnail=None, verified=False,
                 created_at=datetime.utcnow()):
        self.insta_account_id = insta_account_id
        self.caption = caption
        self.url = url
        self.path = path
        self.verified = verified
        self.type = type
        self.thumbnail = thumbnail
        self.created_at = created_at

    def get_user(self):
        return InstaAccount.query.filter_by(id=self.insta_account_id).first()

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
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    insta_account_id = Column(Integer, ForeignKey('insta_account.id'))
    bot = Column(Enum(BotType))
    interval = Column(Float)
    action_interval = Column(Float)
    rate = Column(Integer)
    unix_pid = Column(String(16))
    active = Column(Boolean)
    created_at = Column(DateTime)

    def __init__(self, insta_account_id, bot, interval, action_interval, rate, active=False, unix_pid=None,
                 created_at=datetime.utcnow()):
        self.insta_account_id = insta_account_id
        self.bot = bot
        self.interval = interval
        self.action_interval = action_interval
        self.rate = rate
        self.unix_pid = unix_pid
        self.active = active
        self.created_at = created_at

    def deactivate(self):
        self.unix_pid = None
        self.active = False
        os.kill(int(self.unix_pid), signal.SIGTERM)
        db.session.commit()

    def run(self):
        if self.bot == BotType.FOLLOW:
            pass
        elif self.bot == BotType.UNFOLLOW:
            pass
        elif self.bot == BotType.POST:
            pass

    def get_user(self):
        return InstaAccount.query.filter_by(id=self.insta_account_id).first()

    def __repr__(self):
        return '<User %r Bot %r>' % (self.insta_account_id, self.bot)


def main():
    db.create_all()
    db.session.commit()
    # account = InstaAccount('hwzearth', '1234')
    # db.session.add(account)
    # db.session.commit()
    #
    # hwzearth = InstaAccount.query.filter_by(username='hwzearth').first()
    # print hwzearth
    # content = Content(hwzearth.id, 'caption', 'url', 'path')
    # bot = Bot(hwzearth.id, BotType.FOLLOW, 1.0, 2.0, 3)
    #
    # db.session.add(content)
    # db.session.add(bot)
    # db.session.commit()
    # app.run(host="0.0.0.0", port="5000")


if __name__ == '__main__':
    main()
