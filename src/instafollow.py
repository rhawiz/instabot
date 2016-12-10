# dilman1234

import json
from random import randint, uniform
import datetime

import re
from time import sleep

import click
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ChunkedEncodingError

from configs import accounts
from netutils import generate_request_header

from instagramapi import InstagramAPI
from utils import list_to_csv, csv_to_list, text_to_list, append_to_file, write_to_file, pop_text_file


class InstaFollow:
    def __init__(self, username, password, similar_users):
        self.username = username
        self.password = password
        self.similar_users = similar_users
        self.users_file_path = "../data/{}_users.txt".format(self.username)
        self.log_file = "{}_log.txt".format(self.username)

    def print_and_log(self, text):
        print text
        with open(self.log_file, "ab") as f:
            f.write("{}\n".format(text))

    def _get_user_ids(self, save_to):
        self.print_and_log("Gathering user ids...")

        # Randomly select root account to search for users
        root_acc = self.similar_users[randint(0, len(self.similar_users) - 1)]
        self.API.search_username(root_acc)

        # Get root account id
        root_acc_id = self.API.last_json.get(u"user").get(u"pk")

        # Get root account posts
        maxid = ''
        pages = 1
        media_ids = []
        for i in range(0, pages):
            self.API.get_user_feed(root_acc_id, maxid=maxid)
            media_items = self.API.last_json[u"items"]
            for media in media_items:
                media_ids.append(media[u"id"])
            maxid = self.API.last_json[u"next_max_id"]

        user_accounts = []

        for media_id in media_ids:
            self.API.get_media_likers(media_id)
            try:
                users = self.API.last_json[u"users"]
            except ChunkedEncodingError, e:
                "Failed to retrieve user list"
                users = []

            for user in users:
                id = user[u"pk"]
                username = user[u"username"]
                user_accounts.append((id, username))

        user_accounts = list(set(user_accounts))

        self.print_and_log("\tFound {} new users".format(len(user_accounts)))

        self.print_and_log("\t\tSaving to {}".format(save_to))

        for id, username in user_accounts:
            append_to_file("{},{}\n".format(id, username), save_to)

        return user_accounts

    def _get_followers(self):

        followers_details = self.API.get_total_followings(username_id=self.API.username_id)
        followers = []
        for details in followers_details:
            followers.append((details[u"pk"], details[u"username"]))
        return followers

    def start(self, follows, wait):
        start_time = datetime.datetime.now()
        self.print_and_log("Started at {}".format(start_time.strftime("%Y-%m-%d %H:%M")))

        self.API = InstagramAPI(self.username, self.password)

        attempts = 0
        while attempts <= 5:
            try:
                self.API.login()
                # followers = self._get_followers()
                users = []

                try:
                    users = csv_to_list(self.users_file_path)
                except IOError, e:
                    self.print_and_log("No user list found...")

                if not len(users):
                    users = self._get_user_ids(save_to=self.users_file_path)
                self.print_and_log("Starting...{} new users.".format(len(users)))

                wait_seconds = wait * 60
                self._follow_users(users, follows, wait_seconds)
                break
            except Exception, e:
                self.print_and_log(e)
                attempts += 1
        end_time = datetime.datetime.now()
        self.print_and_log("Ended at {}".format(end_time.strftime("%Y-%m-%d %H:%M")))

    def _follow_users(self, users, follows, wait):
        fail_count = 0
        progress = 0
        while users:
            progress += 1
            id, username = users.pop(0)
            pop_text_file(self.users_file_path)
            self.print_and_log("{} following user {}({})".format(self.username, username, id))
            status = self.API.follow(id)
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
            if not (progress % follows):
                if wait < 1:
                    wait_time = randint(2700, 4500)
                else:
                    wait_time = wait
                self.print_and_log("{} requests sent. Sleeping for {} mins".format(follows, wait_time / 60))
                sleep(wait_time)

            sleep(uniform(1.0, 4.0))  # wait 1-4 secs between requests


@click.command()
@click.option('--username', default='hwzearth', prompt='Username:', help='Instagram account name')
@click.option('--password', default='', prompt='Password:', help='Instagram account name')
@click.option('--follows', default=100, prompt='Follows per cycle:', help='Follow user rate')
@click.option('--wait', default=-1, prompt='Minutes between requests (-1 for random):', help='Follow user rate')
@click.option('--similar_users', default='', prompt='Similar users accounts:', help='Similar user accounts')
def main(username, password, follows, wait, similar_users):
    similar_users = similar_users.split(",")

    bot = InstaFollow(username, password, similar_users)
    bot.start(follows, wait)


if __name__ == "__main__":
    main()
