import logging
import threading
from time import sleep

import click
from app.core.instagramapi import InstagramAPI
from app.core.instaunfollow import InstaUnfollow

from app.core.instafollow import InstaFollow
from app.core.utils import execute_query

DB_PATH = "content.db"
SELECT_SQL = "SELECT caption, path FROM insta_content WHERE user = \"{user}\" AND verified=1 ORDER BY created_at DESC LIMIT 1"
DELETE_SQL = "DELETE FROM insta_content where rowid in (SELECT rowid FROM insta_content WHERE user = \"{user}\" ORDER BY created_at DESC LIMIT 1)"
LOG_FILE = "app.log"


def collect_followers(
        username,
        password,
        similar_users,
        follow_rate=75,
        unfollow_rate=75,
        wait=75,
        follow_action_wait=30,
        unfollow_action_wait=16,
        follow_first=False
):
    logging.basicConfig(
        filename=LOG_FILE,
        format='[%(asctime)s][%(levelname)s][{}] %(message)s'.format(username),
        datefmt='%d-%m-%Y %I:%M:%S %p', level=logging.DEBUG
    )

    wait_min = wait * 0.9
    wait_max = wait * 1.1

    follow_bot = InstaFollow(username, password, similar_users, action_interval=follow_action_wait)
    unfollow_bot = InstaUnfollow(
        username=username,
        password=password,
        action_interval=unfollow_action_wait,
        rate=unfollow_rate,
        wait=(wait_min * 60, wait_max * 60),
        unfollow_all=True
    )

    fail_count = 0

    while True:
        try:
            unfollow_bot.start()
            fail_count = 0
        except Exception, e:
            fail_count += 1
            logging.critical(e)
        try:
            follow_bot.start(rate=follow_rate, wait=(wait_min * 60, wait_max * 60))
            fail_count = 0
        except Exception, e:
            fail_count += 1
            logging.critical(e)

        if fail_count >= 10:
            logging.info("Failed 10 times, sleeping for 10 mins.")
            sleep(2400)
            fail_count = 0


def post_contents(username, password, wait=86400):
    logging.basicConfig(
        filename=LOG_FILE,
        format='[%(asctime)s][%(levelname)s][{}] %(message)s'.format(username),
        datefmt='%d-%m-%Y %I:%M:%S %p', level=logging.DEBUG
    )
    while True:
        content = None
        try:
            content = execute_query(DB_PATH, SELECT_SQL.format(user=username))
        except Exception, e:
            logging.critical(e)
            continue

        if content:
            api = InstagramAPI(username, password)
            api.login()

            caption, path = content[0]
            try:
                api.upload_photo(path, caption)
                logging.info("{} Uploaded {} with caption {}".format(username, path, caption))
                execute_query(DB_PATH, DELETE_SQL.format(user=username))
            except Exception, e:
                logging.critical(e)

        sleep(wait)


@click.command()
@click.option('--username', default='hwzearth', prompt='Username:', help='Instagram username')
@click.option('--password', prompt='Password:', hide_input=True, help='Instagram password')
@click.option('--similar_users', default='', prompt='Similar users accounts:', help='Similar user accounts')
def main(username, password, similar_users):
    similar_users = similar_users.split(",")
    for idx, user in enumerate(similar_users):
        similar_users[idx] = user.strip()

    t1 = threading.Thread(target=post_contents, args=(username, password,))
    t2 = threading.Thread(target=collect_followers, args=(username, password, similar_users,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
