import json
import logging

import requests

from app import logger
from random import randint, uniform
from time import sleep
from requests.exceptions import ChunkedEncodingError
from instagram_private_api import Client
from instagram_web_api import Client as WebClient


class InstaFollow:
    def __init__(self, username, password, similar_users, API=None, action_interval=8.0, rate=75, interval=5400):
        self.username = username
        self.password = password

        if isinstance(similar_users, str):
            self.similar_users = [x.strip() for x in similar_users.split(",")]
        else:
            self.similar_users = similar_users

        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.logger = logging.LoggerAdapter(logger, {'user': self.username, 'bot': 'instafollow'})

        self.API = Client(self.username, self.password) if API is None else API
        self.webAPI = WebClient()

    def _get_user_ids(self, save_to=None):

        self.logger.info('Collecting users to follow...')

        # Randomly select root account to search for users
        account = self.similar_users[randint(0, len(self.similar_users) - 1)]
        username_info = self.API.username_info(account)

        # Get root account id
        root_account_id = username_info.get('user').get('pk')

        # Get root account posts
        max_id = ''
        pages = 1
        media_ids = []

        for i in range(0, pages):
            user_feed = self.API.user_feed(root_account_id, max_id=max_id)
            media_items = user_feed.get('items')
            for media in media_items:
                media_ids.append(media.get('id'))
            max_id = user_feed.get('next_max_id')

        user_ids = []

        for media_id in media_ids:
            media_likers = self.API.media_likers(media_id)

            try:
                users = media_likers.get('users')
            except ChunkedEncodingError as e:
                self.logger.error("Failed to retrieve user list", e)
                users = []

            for user in users:
                id = user.get('pk')
                user_ids.append(id)

        user_ids = list(set(user_ids))

        self.logger.info("Found {} new users...".format(len(user_ids)))

        return user_ids

    def _login(self):
        attempts = 0
        while attempts <= 10:
            try:
                if self.API.login():
                    return True
            except Exception as e:
                self.logger.exception("Failed to login...")

            sleep(6)
            attempts += 1

        return False

    def start(self):

        self.logger.info("Follow bot started...")
        users = []
        while len(users) < 7000:
            users += self._get_user_ids()
        progress = 0
        bad_requests = 0
        successful_requests = 0
        while users:
            progress += 1
            # if not self.API.is_logged_in:
            #     self.API.login()

            id = users.pop(0)

            res = self.API.friendships_create(id)

            if res.get("status", False) != "ok":
                users.append(id)
                bad_requests += 1
            elif res.get("status", False) == "ok":
                successful_requests += 1

            if bad_requests == 10:
                self.logger.info("10 bad requests...sleeping for 3 mins 20 secs.")
                sleep(200)
                bad_requests = 0

            if not (progress % self.rate):
                progress = 0
                followings = self.webAPI.user_info2(self.username).get("follows", {}).get("count", 0)
                if followings > 7000:
                    break

                wait = uniform(self.interval * 0.9, self.interval * 1.1)
                self.logger.info(
                    "Cycle ended for user {} with {} successful requests and {} followers...sleeping for {}mins".format(
                        self.username, successful_requests, followings,
                        wait / 60))
                successful_requests = 0
                sleep(wait)

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
