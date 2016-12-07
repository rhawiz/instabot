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
from utils import csv_to_list, append_to_file, write_to_file


class Instabot:
    REDDIT_URL = "https://www.reddit.com/r/{}/top/?sort=top&t={}&count={}"

    def __init__(self, username, password, account_list, subreddits):
        self.username = username
        self.password = password
        self.account_list = account_list
        self.subreddit_list = subreddits
        self.users_file_path = "../data/{}_users.txt".format(self.username)

    def _get_account_ids(self, save_to):
        print "Gathering user ids..."
        # Randomly select root account to search for users
        root_acc = self.account_list[randint(0, len(self.subreddit_list) - 1)]
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

        print media_ids
        account_ids = []

        for media_id in media_ids:
            self.API.get_media_likers(media_id)
            try:
                users = self.API.last_json[u"users"]
            except ChunkedEncodingError, e:
                "Failed to retrieve user list"
                users = []
            for user in users:
                append_to_file("{},{}\n".format(user[u"pk"], user[u"username"]), save_to)
                account_ids.append((user[u"pk"], user[u"username"]))

        return account_ids

    def _get_reddit_content(self):
        subreddit = self.subreddit_list[randint(0, len(self.subreddit_list) - 1)]
        random_page = randint(0, 10) * 25
        reddit_url = self.REDDIT_URL.format(subreddit, "day", random_page)

        html = requests.get(reddit_url, headers=generate_request_header()).content

        soup = BeautifulSoup(html, "lxml")

        content = soup.findAll(name="a", attrs={"class": "title may-blank outbound "})

        content = content[randint(0, len(content) - 1)]

        title = re.sub(r"\[.*\]", "", content.text).strip()
        img_url = content["href"]

        print title, img_url

    def get_followers(self):

        followers_details = self.API.get_total_followings(username_id=self.API.username_id)
        followers = []
        for details in followers_details:
            followers.append((details[u"pk"], details[u"username"]))
        return followers

    def follow_unfollow_users(self, users, followers):
        fail_count = 0
        progress = 0
        while users:
            progress += 1
            if progress % 5 > 0 or not len(followers):
                id, username = users.pop(0)
                print "following user {}({})".format(username, id)
                status = self.API.follow(id)
            else:
                id, username = followers.pop()
                print "unfollowing user {}({})".format(username, id)
                status = self.API.unfollow(id)

            print "\tstatus:{}".format(status)
            if status:
                fail_count = 0
            elif not status:
                print self.API.last_response.content
                fail_count += 1

            if fail_count == 3:
                print "3 failed requests in a row. Sleeping for 10 mins"
                sleep(1200)
            elif fail_count > 10:
                print "10 failed requests in a row. Sleeping for 2 hours"
                sleep(randint(7200))
                break

            # Sleep between 3hrs and 5hrs ever 1225 requests
            if not (progress % 1000):
                rnd_wait = randint(10800, 18000)
                print "1000 requests sent. Sleeping for {} mins".format(rnd_wait * 60)
                sleep(rnd_wait)

            sleep(uniform(2.0, 6.0))

        write_to_file("", self.users_file_path)
        for user in users:
            append_to_file("{},{}\n".format(id, username), self.users_file_path)

    def start(self, unfollow):
        start_time = datetime.datetime.now()
        print "Started at {}".format(start_time.strftime("%Y-%m-%d %H:%M"))

        self.API = InstagramAPI(self.username, self.password)

        attempts = 0
        while attempts <= 5:
            try:
                self.API.login()
                followers = []
                if unfollow:
                    followers = self.get_followers()
                users = []

                try:
                    users = csv_to_list(self.users_file_path)
                except IOError, e:
                    print "No user list found..."
                if not len(users):
                    users = self._get_account_ids(save_to=self.users_file_path)
                print "Starting...{} new users and {} followers.".format(len(users), len(followers))
                self.follow_unfollow_users(users, followers)
                break
            except Exception, e:
                print e
                attempts += 1
        end_time = datetime.datetime.now()
        print "Ended at {}".format(end_time.strftime("%Y-%m-%d %H:%M"))


@click.command()
@click.option('--account', default='hwzearth', prompt='Account: ', help='Instagram account name')
@click.option('--unfollow', is_flag=True, prompt='Unfollow: ', help='Unfollow users')
def main(account, unfollow):
    account_list = accounts[account]["similar_ig_users"]
    subreddits = accounts[account]["subreddits"]
    username = accounts[account]["username"]
    password = accounts[account]["password"]

    bot = Instabot(username, password, account_list, subreddits)
    bot.start(unfollow=unfollow)


if __name__ == "__main__":
    main()
