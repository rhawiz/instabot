import json
from random import randint, uniform
from time import sleep, time

import click
import logging

from instagramapi import InstagramAPI


class InstaUnfollow:
    def __init__(self, username, password, action_interval=8.0, rate=120, interval=5400, unfollow_all=True):
        self.username = username
        self.password = password
        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.unfollow_all = unfollow_all
        self.API = InstagramAPI(self.username, self.password)
        logging.basicConfig(
            filename="app.log",
            format='[%(asctime)s][%(levelname)s][{}] %(message)s'.format(username),
            datefmt='%d-%m-%Y %I:%M:%S %p', level=logging.DEBUG
        )

    def _get_user_ids(self):
        logging.info('Collecting users to unfollow...')

        # Get people followings
        following_details = self.API.get_total_self_followings()

        followings = []
        for details in following_details:
            pk = details.get('pk', None)
            username = details.get('username', None)
            if pk:
                followings.append((pk, username))

        if self.unfollow_all:
            return followings

        followings = set(followings)

        # Get all followers
        followers_details = self.API.get_total_followers(username_id=self.API.username_id)

        followers = []
        for details in followers_details:
            pk = details.get("pk", None)
            username = details.get("username", None)
            if pk:
                followers.append((pk, username))

        followers = set(followers)

        # Find difference to get a list of people who are not following back
        unfollow_list = list(followings - followers)

        return unfollow_list

    def start(self):
        self.API = InstagramAPI(self.username, self.password)
        self.API.login()

        logging.info("Unfollow bot started...")

        users = self._get_user_ids()

        progress = 0

        while True:
            progress += 1
            if not self.API.is_logged_in:
                self.API.login()

            if len(users) < 7000:
                logging.info("{} < 7000, sleeping for {} mins.".format(len(users), self.interval/60))
                sleep(self.interval)
                continue

            if not len(users):
                try:
                    users = self._get_user_ids()
                except Exception, e:
                    logging.error(e.message, e)
                    continue

            id = users.pop(0)

            self.API.unfollow(id)

            logging.debug(self.API.last_response.content)

            if not (progress % self.rate):
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
