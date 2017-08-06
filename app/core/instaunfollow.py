import json
from random import randint, uniform
from time import sleep, time

import click
import logging

from instagramapi import InstagramAPI


class InstaUnfollow:
    def __init__(self, username, password, API=None, action_interval=8.0, rate=120, interval=5400, unfollow_all=True):
        self.username = username
        self.password = password
        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.unfollow_all = unfollow_all
        self.API = InstagramAPI(self.username, self.password) if API is None else API

    def _get_user_ids(self):
        logging.info('Collecting users to unfollow...', extra={'user': self.username})

        # Get people followings
        following_details = self.API.get_total_self_followings()

        followings = [d.get('pk') for d in following_details]

        if self.unfollow_all:
            return followings

        followings = set(followings)

        # Get all followers
        followers_details = self.API.get_total_followers(username_id=self.API.username_id)

        followers = [d.get('pk') for d in followers_details]

        followers = set(followers)

        # Find difference to get a list of people who are not following back
        unfollow_list = list(followings - followers)

        return unfollow_list

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

        if not self.API.is_logged_in:
            if not self._login():
                return False

        logging.info("Unfollow bot started...", extra={'user': self.username})

        users = self._get_user_ids()

        progress = 0

        while users:
            progress += 1
            if not self.API.is_logged_in:
                self.API.login()

            id = users.pop(0)
            print(id)
            self.API.unfollow(id)

            if self.API.last_response.status_code != 200:
                logging.debug("Failed to unfollow user {} with status code {}".format(
                    id,
                    self.API.last_response.status_code))

            if not (progress % self.rate):
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
