import threading
from time import sleep

import click

from dbutils import execute_query
from instagramapi import InstagramAPI
from instafollow import InstaFollow

from instaunfollow import InstaUnfollow

DB_PATH = "../data/content.db"
SELECT_SQL = "SELECT caption, path FROM insta_content WHERE user = \"{user}\" ORDER BY date DESC LIMIT 1"
DELETE_SQL = "DELETE FROM insta_content where rowid in (SELECT rowid FROM insta_content WHERE user = \"{user}\" ORDER BY date DESC LIMIT 1)"


def collect_followers(username, password, similar_users):
    follow_bot = InstaFollow(username, password, similar_users)
    unfollow_bot = InstaUnfollow(username, password)

    while True:
        follow_bot.start(75, (75, 150))

        unfollow_bot.start(75, (75, 150), True)


def post_contents(username, password):
    api = InstagramAPI(username, password)
    api.login()

    while True:
        content = execute_query(DB_PATH, SELECT_SQL.format(user=username))
        if not len(content):
            continue

        caption, path = content[0]
        try:
            api.upload_photo(path, caption)
        except Exception, e:
            print e

        execute_query(DB_PATH, DELETE_SQL.format(user=username))

        # Sleep for 24 hours before posting new content
        sleep(86400)


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
