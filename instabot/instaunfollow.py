from random import randint, uniform
from time import sleep, time

import click

from instagramapi import InstagramAPI
import datetime


class InstaUnfollow:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.log_file = "{}_instaunfollow.log".format(self.username)

    def _get_unfollow_list(self, unfollow_all):

        # Get people followings
        following_details = self.API.get_total_followings(username_id=self.API.username_id)

        followings = []
        for details in following_details:
            pk = details.get(u"pk", None)
            username = details.get(u"username", None)
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

    def print_and_log(self, text):
        try:
            print text
            with open(self.log_file, "ab") as f:
                f.write("{}\n".format(text))
        except Exception, e:
            print "instaunfollow:print_and_log ", e

    def start(self, rate, wait, unfollow_all):
        start_time = datetime.datetime.now()
        self.print_and_log("Started at {}".format(start_time.strftime("%Y-%m-%d %H:%M")))

        self.API = InstagramAPI(self.username, self.password)

        attempts = 0
        while attempts <= 5:
            try:
                print attempts
                self.API.login()

                unfollow_list = self._get_unfollow_list(unfollow_all)
                self.print_and_log("Starting...unfollowing {} followers.".format(len(unfollow_list)))

                wait_seconds = wait * 60
                self._unfollow_users(unfollow_list, rate, wait_seconds)
                break
            except Exception, e:
                self.print_and_log(e)
                attempts += 1
        end_time = datetime.datetime.now()
        self.print_and_log("Ended at {}".format(end_time.strftime("%Y-%m-%d %H:%M")))

    def _unfollow_users(self, unfollow_list, unfollows, wait):
        fail_count = 0
        progress = 0
        t0 = time()
        while unfollow_list:
            progress += 1
            id, username = unfollow_list.pop(0)
            self.print_and_log("{} unfollowing user {}({})".format(self.username, username, id))
            status = self.API.unfollow(id)
            if status:
                fail_count = 0
            elif not status:
                self.print_and_log(self.API.last_response.content)
                fail_count += 1

            self.print_and_log("\tresponse: {}".format(self.API.last_response.content))
            if fail_count == 3:
                self.print_and_log("3 failed follow requests in a row. Sleeping for 10 mins")
                sleep(1200)
            elif fail_count > 10:
                wait_time = randint(21600, 28800)
                self.print_and_log("10 failed follow requests in a row. Sleeping for {} mins".format(wait_time / 60))
                sleep(wait_time)
            if not (progress % unfollows):
                wait_time = randint(wait[0], wait[1])
                elapsed = time() - t0
                wait_time = wait_time - elapsed if wait_time > elapsed else 1
                self.print_and_log("{} requests sent. Sleeping for {} mins".format(unfollows, wait_time / 60))
                sleep(wait_time)
                t0 = time()
            sleep(uniform(11.0, 22.0))  # wait 1-4 secs between requests


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
