import logging
from app.core.instaunfollow import InstaUnfollow

from app.core.instafollow import InstaFollow

def collect_followers(follow_bot, unfollow_bot):
    if not isinstance(follow_bot, InstaFollow.__class__) or not isinstance(unfollow_bot, InstaUnfollow.__class__):
        return

    while True:
        try:
            unfollow_bot.start()
        except Exception, e:
            logging.critical(e)
        try:
            follow_bot.start()
        except Exception, e:
            logging.critical(e)

