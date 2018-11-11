from random import randint, uniform
from time import sleep

import logging
import click

from instagram_private_api import Client
from instagram_web_api import Client as WebClient

from app.core.utils import get_logger


class InstaUnfollow:
    def __init__(self, username, password, API=None, action_interval=8.0, rate=120, interval=5400, unfollow_all=True):
        self.username = username
        self.password = password
        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.unfollow_all = unfollow_all
        try:
            from app import logger
            logger = get_logger()
        except ImportError:
            pass
        self.logger = logging.LoggerAdapter(logger, {'user': self.username, 'bot': 'instaunfollow'})
        self.API = Client(self.username, self.password) if API is None else API
        self.webAPI = WebClient()

    def _get_user_ids(self):
        self.logger.info('Collecting users to unfollow...')

        # Get people followings
        rank_token = self.API.generate_uuid()

        following = self.API.user_following(self.id, rank_token=rank_token)

        following_users = following.get("users")

        _ids = [user.get("pk", 0) for user in following_users]

        return _ids

    def _login(self):
        attempts = 0
        while attempts <= 10:
            try:
                if self.API.login():
                    return True
            except Exception as e:
                self.logger.error("Failed to login", e)
            sleep(6)
            attempts += 1

        return False

    def start(self):

        # if not self.API.is_logged_in:
        #     if not self._login():
        #         return False

        self.logger.info("Unfollow bot started for user {}...".format(self.API.username))
        self.id = self.webAPI.user_info2(self.username).get("id")
        users = self._get_user_ids()

        progress = 0
        too_many_request_errors = 0
        while users:
            progress += 1
            # if not self.API.is_logged_in:
            #     self.API.login()

            id = users.pop(0)

            res = self.API.friendships_destroy(id)

            if res.get("status", False) != "ok":
                users.append(id)
                too_many_request_errors += 1

            if too_many_request_errors == 10:
                sleep(randint(60, 100))
                too_many_request_errors = 0

            if not (progress % self.rate):
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))


@click.command()
@click.option('--username', default='hwzearth', prompt='Username:', help='Instagram account name')
@click.option('--password', default='', prompt='Password:', help='Instagram account name')
def main(username, password):
    print(username)
    bot = InstaUnfollow(username=username, password=password)
    bot.start()


if __name__ == "__main__":
    main()
