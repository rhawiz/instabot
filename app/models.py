import os
import threading
from datetime import datetime
from time import sleep

import enum
import signal

import multiprocessing

import logging
import psutil

from app import logger
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey

from app import app, db, bot_config

logger = logging.LoggerAdapter(logger, {'user': "", 'bot': 'instaccount'})

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
            # os.killpg(int(self.pid), signal.SIGTERM)
            logger.info("killing process {}...".format(self.pid))
            parent = psutil.Process(int(self.pid))
            for child in parent.children(recursive=True):  # or parent.children() for recursive=False
                logger.info("\tkilling child process {}...".format(child.pid))
                child.kill()
            parent.kill()
        except Exception as e:
            logger.exception(e)
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

        p = multiprocessing.Process(
            target=bot_worker,
            args=(follow_bot, unfollow_bot, post_bot,)
        )

        self.active = True

        p.start()

        self.pid = p.pid
        logger.info("created process {}".format(p.pid))

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
            logger.exception(e)

    def __repr__(self):
        return '<User %r> <URL %r>' % (self.insta_account_id, self.url)


def bot_worker(follow, unfollow, post):
    while follow.API.is_logged_in is not True:
        follow.API.login()
        logger.info("failed to log in...retrying in 3 seconds.".format(follow.username))
        sleep(3)

    t1 = threading.Thread(target=grow_followers_worker, args=(follow, unfollow,))
    t2 = threading.Thread(target=instapost_worker, args=(post,))
    # print t2, t2.is_alive
    t2.start()
    t1.start()

    t1.join()
    t2.join()


def grow_followers_worker(follow_bot, unfollow_bot):
    try:
        followings = len(unfollow_bot.API.get_total_self_followings())
    except Exception as e:
        followings = 0

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
            logger.critical("Unfollow failed to start", e)
        try:
            with app.app_context():
                bot2.start()
        except Exception, e:
            logger.critical("Follow failed to start", e)


def instapost_worker(bot):
    while True:
        try:
            with app.app_context():
                bot.start()
        except Exception, e:
            logging.critical(e)


