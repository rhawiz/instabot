import os
import threading
from datetime import datetime
from time import sleep

import enum
import signal

import multiprocessing

import logging
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Float, ForeignKey

from app import app, db, bot_config


class InstaAccount(db.Model):
    """
    Instagram User
    """
    id = Column(Integer, primary_key=True)
    username = Column(String(256), unique=True)
    password = Column(String(256))
    similar_users = Column(String(1024))
    pid = Column(Integer)
    active = Column(Boolean)
    created_at = Column(DateTime)
    __table_args__ = {'extend_existing': True}

    def __init__(self, username, password, similar_users, pid=None, active=False, created_at=datetime.utcnow()):
        self.username = username
        self.password = password
        self.similar_users = similar_users
        self.created_at = created_at
        self.pid = pid
        self.active = active

    def deactivate(self):
        try:
            os.kill(int(self.pid), signal.SIGTERM)
            logging.info("Killing process {}".format(self.pid))
        except Exception as e:
            logging.exception(e)
        finally:
            self.pid = None
            self.active = False

        db.session.commit()

    def activate(self):
        from app.core.instafollow import InstaFollow
        from app.core.instapost import InstaPost
        from app.core.instaunfollow import InstaUnfollow
        from core.instagramapi import InstagramAPI
        API = InstagramAPI(self.username, self.password)
        base_config = {
            'username': self.username,
            'password': self.password,
            'API': API
        }
        follow_config = bot_config.get('follow')
        follow_config.update(base_config)
        follow_config['similar_users'] = self.similar_users

        unfollow_config = bot_config.get('unfollow')
        unfollow_config.update(base_config)

        post_config = bot_config.get('post')
        post_config.update(base_config)

        follow_bot = InstaFollow(**follow_config)
        unfollow_bot = InstaUnfollow(**unfollow_config)
        post_bot = InstaPost(**post_config)

        while API.is_logged_in is not True:
            API.login()
            logging.exception("Failed to log in...retrying in 3 seconds.")
            sleep(3)

        p = multiprocessing.Process(
            target=bot_worker,
            args=(follow_bot, unfollow_bot, post_bot,)
        )

        self.active = True

        p.start()

        self.pid = p.pid
        logging.info("Created process {}".format(p.pid))

        db.session.commit()

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

    def delete_content(self):
        try:
            os.remove(self.path)
        except Exception as e:
            logging.exception(e)

    def __repr__(self):
        return '<User %r> <URL %r>' % (self.insta_account_id, self.url)


def bot_worker(follow, unfollow, post):
    t1 = threading.Thread(target=grow_followers_worker, args=(follow, unfollow,))
    t2 = threading.Thread(target=instapost_worker, args=(post,))
    # print t2, t2.is_alive
    t2.start()
    t1.start()

    logging.info(t1.is_alive)
    logging.info(t2.is_alive)

    t1.join()
    t2.join()


def grow_followers_worker(follow_bot, unfollow_bot):
    try:
        followings = len(unfollow_bot.API.get_total_self_followings())
    except Exception as e:
        followings = 0
    logging.info(followings)
    if followings > 7000:
        bot1 = unfollow_bot
        bot2 = follow_bot
    else:
        bot1 = follow_bot
        bot2 = unfollow_bot

    while True:
        try:
            with app.app_context():
                bot1.start()
        except Exception, e:
            logging.critical("Unfollow failed to start", e)
        try:
            with app.app_context():
                bot2.start()
        except Exception, e:
            logging.critical("Follow failed to start", e)


def instapost_worker(bot):
    while True:
        try:
            with app.app_context():
                bot.start()
        except Exception, e:
            logging.critical(e)


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
        try:
            os.kill(int(self.unix_pid), signal.SIGTERM)
        except OSError as e:
            logging.error("Could not kill process", e)
        finally:
            self.unix_pid = None
            self.active = False

        db.session.commit()

    def activate(self, pid):
        self.unix_pid = pid
        self.active = True
        db.session.commit()

    def create(self):
        from app.core.instafollow import InstaFollow
        from app.core.instapost import InstaPost
        from app.core.instaunfollow import InstaUnfollow

        user = self.get_user()
        if self.bot == BotType.FOLLOW:
            return InstaFollow(
                username=user.username,
                password=user.password,
                action_interval=self.action_interval,
                rate=self.rate,
                interval=self.interval,
                similar_users=user.similar_users
            )
        elif self.bot == BotType.UNFOLLOW:
            return InstaUnfollow(
                username=user.username,
                password=user.password,
                action_interval=self.action_interval,
                rate=self.rate,
                interval=self.interval
            )
        elif self.bot == BotType.POST:
            return InstaPost(
                username=user.username,
                password=user.password,
                action_interval=self.action_interval,
                rate=self.rate,
                interval=self.interval
            )

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
