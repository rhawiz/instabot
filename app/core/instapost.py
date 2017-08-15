from random import uniform
from time import sleep

import logging

from app import db, logger
from instagramapi import InstagramAPI


class InstaPost:
    def __init__(self, username, password, API=None, action_interval=8.0, rate=1, interval=86400):
        self.username = username
        self.password = password

        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.logger = logging.LoggerAdapter(logger, {'user': self.username, 'bot': 'instapost'})

        self.API = InstagramAPI(self.username, self.password) if API is None else API

    def _get_content(self):
        from app.models import Content, InstaAccount

        insta_account = InstaAccount.query.filter_by(username=self.username).first()
        return Content.query.filter_by(insta_account_id=insta_account.id, verified=True).first()

    def _login(self):
        attempts = 0
        while attempts <= 10:
            try:
                if self.API.login():
                    return True
            except Exception as e:
                pass
            sleep(6)
            attempts += 1

        return False

    def start(self):
        self.logger.info("Post bot started for user {}...".format(self.username))

        if not self.API.is_logged_in:
            if not self._login():
                return False

        progress = 0
        while True:
            progress += 1
            if not self.API.is_logged_in:
                self.API.login()

            content = self._get_content()

            if content is not None:
                try:
                    if content.type == 'photo':
                        self.API.upload_photo(photo=content.path, caption=content.caption)
                    elif content.type == 'video':
                        self.API.upload_video(video=content.path, thumbnail=content.thumbnail, caption=content.caption)
                except (IOError, Exception) as e:
                    self.logger.exception(e)

                try:
                    content.delete_content()
                except Exception as e:
                    self.logger.exception(e)
                finally:
                    db.session.delete(content)
                    db.session.commit()

            if not (progress % self.rate):
                progress = 0
                self.logger.info("Instapost for user {} sleeping for {}mins".format(self.username, self.interval / 60))
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
