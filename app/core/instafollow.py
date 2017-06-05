import datetime
import json
import logging
import os
from random import randint, uniform
from time import sleep, time

import click
from requests.exceptions import ChunkedEncodingError

from app.core.utils import csv_to_list, append_to_file, pop_text_file
from instagramapi import InstagramAPI


class InstaFollow:
    def __init__(self, username, password, similar_users, action_interval=8.0, rate=75, interval=5400):
        self.username = username
        self.password = password

        if isinstance(similar_users, (str, unicode)):
            self.similar_users = [x.strip() for x in similar_users.split(",")]
        else:
            self.similar_users = similar_users

        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval

    def _get_user_ids(self, save_to=None):
        logging.info('Collecting users to follow...', extra={'user': self.username})

        # Randomly select root account to search for users
        account = self.similar_users[randint(0, len(self.similar_users) - 1)]
        self.API.search_username(account)

        # Get root account id
        root_account_id = self.API.last_json.get('user').get('pk')

        # Get root account posts
        max_id = ''
        pages = 1
        media_ids = []

        for i in range(0, pages):
            self.API.get_user_feed(root_account_id, max_id=max_id)
            media_items = self.API.last_json.get('items')
            for media in media_items:
                media_ids.append(media.get('id'))
            max_id = self.API.last_json.get('next_max_id')

        user_ids = []

        for media_id in media_ids:
            self.API.get_media_likers(media_id)

            try:
                users = self.API.last_json.get('users')
            except ChunkedEncodingError, e:
                logging.error("Failed to retrieve user list", e, extra={'user': self.username})
                users = []

            for user in users:
                id = user.get('pk')
                user_ids.append(id)

        user_ids = list(set(user_ids))

        logging.info("Found {} new users...".format(len(user_ids)), extra={'user': self.username})

        return user_ids

    def start(self):

        self.API = InstagramAPI(self.username, self.password)
        self.API.login()
        logging.info("Follow bot started...", extra={'user': self.username})

        users = self._get_user_ids()
        progress = 0
        while True:
            progress += 1
            if not self.API.is_logged_in:
                self.API.login()

            followings = len(self.API.get_total_self_followings())

            if followings >= 7000:
                logging.info("{} >= 7000, sleeping for {} mins.".format(len(users), self.interval / 60),
                             extra={'user': self.username})
                sleep(self.interval)
                continue

            if not len(users):
                try:
                    users = self._get_user_ids()
                except Exception, e:
                    logging.error(e.message, e, extra={'user': self.username})
                    continue

            id = users.pop(0)

            self.API.follow(id)

            logging.debug(self.API.last_response.content, extra={'user': self.username})

            if not (progress % self.rate):
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
