import json
from random import randint, uniform
from time import sleep, time

import click
import logging

from instagramapi import InstagramAPI
import datetime


class InstaUnfollow:
    def __init__(self, username, password, action_interval=15.0, log_file=None):
        self.username = username
        self.password = password
        self.action_interval = action_interval
        self.log_file = "{}.log".format(self.username) if not log_file else log_file

    def _get_unfollow_list(self, unfollow_all):
        logging.info('Collecting users to unfollow...')

        # Get people followings
        following_details = self.API.get_total_followings(username_id=self.API.username_id)

        followings = []
        for details in following_details:
            pk = details.get('pk', None)
            username = details.get('username', None)
            if pk:
                followings.append((pk, username))

        if unfollow_all:
            return followings

        followings = set(followings)

        # Get all followers
        followers_details = self.API.get_total_followers(username_id=self.API.username_id)

        followers = []
        for details in followers_details:
            pk = details.get(u"pk", None)
            username = details.get(u"username", None)
            if pk:
                followers.append((pk, username))

        followers = set(followers)

        # Find difference to get a list of people who are not following back
        unfollow_list = list(followings - followers)

        return unfollow_list

    def start(self, rate, wait, unfollow_all):
        start_time = datetime.datetime.now()
        logging.info(
            "Instaunfollow for user {} started on {}".format(self.username, start_time.strftime("%d-%m-%Y %H:%M:%S")))

        self.API = InstagramAPI(self.username, self.password)

        attempts = 0
        while attempts <= 10:

            self.API.login()

            users = self._get_unfollow_list(unfollow_all)
            logging.info(
                "Instaunfollow starting on account {}...Unfollowing {} users...".format(self.username, len(users)))

            wait_seconds = wait * 60
            try:
                self._unfollow_users(users, rate, wait_seconds)
                break
            except Exception, e:
                attempts += 1
                logging.error("Instaunfollow failed to unfollow users on attempt {}".format(e))
                logging.debug(e)

        end_time = datetime.datetime.now()
        logging.info(
            "Instaunfollow ended on account {} at {}".format(self.username, end_time.strftime("%d-%m-%Y %H:%M:%S")))

    def _unfollow_users(self, unfollow_list, rate, wait):
        fail_count = 0
        progress = 0
        t0 = time()
        while unfollow_list:
            progress += 1
            id, username = unfollow_list.pop(0)
            # logging.debug("{} unfollowing user {} ({})".format(self.username, username, id))
            status = self.API.unfollow(id)
            if status:
                fail_count = 0
            elif not status:
                fail_count += 1

            logging.debug(json.dumps(self.API.last_response.content, indent=4))
            if fail_count == 3:
                logging.info("3 Failed requests in a row...Sleeping for 5 mins.")
                sleep(600)
            elif fail_count > 10:
                logging.info("10 failed follow requests in a row. Ending...")
                break

            if not (progress % rate):
                wait_time = randint(wait[0], wait[1])
                elapsed = time() - t0
                wait_time = wait_time - elapsed if wait_time > elapsed else 1.0
                logging.info("{} sent {} requests. Sleeping for {} mins".format(self.username, rate, wait_time / 60))
                sleep(wait_time)
                t0 = time()
            # wait between action interval +- 10%
            min_wait = self.action_interval * 0.9
            max_wait = self.action_interval * 1.1
            sleep(uniform(min_wait, max_wait))

@click.command()
@click.option('--username', default='hwzearth', prompt='Username:', help='Instagram username')
@click.option('--password', default='', prompt='Password:', help='Instagram password')
@click.option('--rate', default=50, prompt='Unfollows per cycle:', help='Unfollow user rate')
@click.option('--wait', default="60,90", prompt='Minutes between requests (-1 for random):', help='Follow user rate')
@click.option('--unfollow_all', is_flag=True, default=True,
              help='Include this to unfollow all users, dont include to only unfollow those not following back')
def main(username, password, rate, wait, unfollow_all):
    bot = InstaUnfollow(username, password)

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

    bot.start(rate, wait_sec, unfollow_all)


if __name__ == '__main__':
    main()
