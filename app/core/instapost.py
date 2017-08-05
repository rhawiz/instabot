import logging
from random import uniform
from time import sleep
from app import db
from instagramapi import InstagramAPI


class InstaPost:
    def __init__(self, username, password, action_interval=8.0, rate=75, interval=5400):
        self.username = username
        self.password = password

        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.API = InstagramAPI(self.username, self.password)

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
                logging.error("Failed to login", e)
            sleep(6)
            attempts += 1

        return False

    def start(self):
        logging.info("Post bot started...")

        if not self._login():
            return False

        progress = 0
        while True:
            progress += 1
            if not self.API.is_logged_in:
                self.API.login()

            content = self._get_content()
            if content.type == 'photo':
                self.API.upload_photo(photo=content.path, caption=content.caption)
            elif content.type == 'video':
                self.API.upload_video(video=content.path, thumbnail=content.thumbnail, caption=content.caption)

            if self.API.last_response.status_code == 200:
                logging.info("Successfully posted content {}".format(content.urls))
                try:
                    content.delete()
                    db.session.remove(content)
                except Exception as e:
                    logging.exception(e)

            if not (progress % self.rate):
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
