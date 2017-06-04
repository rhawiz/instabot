import datetime
import json
import logging
import os
from random import randint, uniform
from time import sleep, time

import click
from requests.exceptions import ChunkedEncodingError

from app.core.utils import csv_to_list, append_to_file, pop_text_file
from app.models import Content, InstaAccount
from instagramapi import InstagramAPI


class InstaPost:
    def __init__(self, username, password, action_interval=8.0, rate=75, interval=5400):
        self.username = username
        self.password = password

        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.interval = interval

        logging.basicConfig(
            filename="app.log",
            format='[%(asctime)s][%(levelname)s][{}] %(message)s'.format(username),
            datefmt='%d-%m-%Y %I:%M:%S %p', level=logging.DEBUG
        )

    def _get_content(self):
        insta_account = InstaAccount.query.filter_by(username=self.username).first()
        return Content.query.filter_by(insta_account_id=insta_account.id).first()

    def start(self):

        self.API = InstagramAPI(self.username, self.password)
        self.API.login()
        logging.info("Post bot started...")

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

            logging.debug(self.API.last_response.content)

            if not (progress % self.rate):
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
