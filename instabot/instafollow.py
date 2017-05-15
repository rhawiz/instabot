import json
import os
from random import randint, uniform
import datetime

from time import sleep, time, strftime

import click

from requests.exceptions import ChunkedEncodingError

from instagramapi import InstagramAPI
from utils import csv_to_list, append_to_file, pop_text_file
import logging


class InstaFollow:
    def __init__(self, username, password, similar_users, action_interval=30.0, log_file=None):
        self.username = username
        self.password = password
        self.similar_users = similar_users
        self.action_interval = action_interval
        self.users_file_path = "{}_users.txt".format(self.username)
        self.log_file = "{}.log".format(self.username) if not log_file else log_file

    def _get_user_ids(self, save_to):
        logging.info('Collecting users to follow...')

        # Randomly select root account to search for users
        root_account = self.similar_users[randint(0, len(self.similar_users) - 1)]
        self.API.search_username(root_account)

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

        user_accounts = []

        for media_id in media_ids:
            self.API.get_media_likers(media_id)

            try:
                users = self.API.last_json.get('users')
            except ChunkedEncodingError, e:
                logging.info("Failed to retrieve user list")
                logging.error(e)
                users = []

            for user in users:
                id = user.get('pk')
                username = user.get('username')
                user_accounts.append((id, username))

        user_accounts = list(set(user_accounts))

        logging.info("Found {} new users...Saving to {}...".format(len(user_accounts), save_to))

        [append_to_file("{},{}\n".format(user_id, username), save_to) for user_id, username in user_accounts]

        return user_accounts

    def start(self, rate, wait):
        start_time = datetime.datetime.now()
        logging.info(
            "Instafollow for user {} started on {}".format(self.username, start_time.strftime("%d-%m-%Y %H:%M:%S")))

        self.API = InstagramAPI(self.username, self.password)

        attempts = 0

        while attempts <= 10:

            self.API.login()
            # followers = self._get_followers()
            users = []

            if os.path.isfile(self.users_file_path):
                users = csv_to_list(self.users_file_path)

            if not len(users):
                users = self._get_user_ids(save_to=self.users_file_path)

            logging.info(
                "Instafollow starting on account {}...Following {} users...".format(self.username, len(users)))

            try:
                self._follow_users(users, rate, wait)
                break
            except Exception, e:
                attempts += 1
                logging.debug("Instafollow failed to follow users on attempt {}".format(e))
                logging.debug(e)

        end_time = datetime.datetime.now()
        logging.info(
            "Instafollow ended on account {} at {}".format(self.username, end_time.strftime("%d-%m-%Y %H:%M:%S")))

    def _follow_users(self, users, rate, wait):
        fail_count = 0
        progress = 0
        t0 = time()
        while users:
            progress += 1
            id, username = users.pop(0)
            pop_text_file(self.users_file_path)
            # logging.debug("{} following user {} ({})".format(self.username, username, id))

            status = self.API.follow(id)

            if status:
                fail_count = 0
            elif not status:
                fail_count += 1

            logging.debug(json.dumps(self.API.last_response.content))
            if fail_count == 3:
                logging.info("3 Failed requests in a row...Sleeping for 5 mins.")
                sleep(600)
            elif fail_count > 10:
                logging.info("10 failed follow requests in a row. Ending...")
                break

            if not (progress % rate):
                wait_time = randint(wait[0], wait[1])
                elapsed = time() - t0


                #wait_time = wait_time - elapsed if wait_time > elapsed else 1.0

                logging.info("{} sent {} requests. Sleeping for {} mins".format(self.username, rate, wait_time / 60))
                sleep(wait_time)
                t0 = time()

            # wait between action interval +- 10%
            min_wait = self.action_interval * 0.9
            max_wait = self.action_interval * 1.1
            sleep(uniform(min_wait, max_wait))


@click.command()
@click.option('--username', default='hwzearth', prompt='Username:', help='Instagram account name')
@click.option('--password', default='', prompt='Password:', help='Instagram account name')
@click.option('--rate', default=100, prompt='# Follows per cycle:', help='Follow user rate')
@click.option('--wait', default="60,90", prompt='Minutes between requests (min,max):', help='Follow user rate')
@click.option('--similar_users', default='', prompt='Similar users accounts:', help='Similar user accounts')
def main(username, password, rate, wait, similar_users):
    similar_users = similar_users.split(",")
    for idx, user in enumerate(similar_users):
        similar_users[idx] = user.strip()

    bot = InstaFollow(username, password, similar_users)

    wait_parts = wait.split(",")

    min = 60
    max = 90
    if len(wait_parts) == 1:
        min = int(wait_parts[0].strip())
        max = min
    elif len(wait_parts) > 2:
        min = int(wait_parts[0].strip())
        max = int(wait_parts[-1].strip())

    wait_sec = (min * 60, max * 60)
    bot.start(rate, wait_sec)


if __name__ == "__main__":
    main()
