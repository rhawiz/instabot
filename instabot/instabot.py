import threading
from time import sleep

import click

from dbutils import execute_query
from instagramapi import InstagramAPI
from instafollow import InstaFollow

from instaunfollow import InstaUnfollow

DB_PATH = "content.db"
SELECT_SQL = "SELECT caption, path FROM insta_content WHERE user = \"{user}\" ORDER BY date DESC LIMIT 1"
DELETE_SQL = "DELETE FROM insta_content where rowid in (SELECT rowid FROM insta_content WHERE user = \"{user}\" ORDER BY date DESC LIMIT 1)"


def collect_followers(username, password, similar_users, rate=75, wait_min=75, wait_max=150):
    follow_bot = InstaFollow(username, password, similar_users)
    unfollow_bot = InstaUnfollow(username, password)

    while True:
        try:
            unfollow_bot.start(rate=rate, wait=(wait_min * 60, wait_max * 60), unfollow_all=True)

        except Exception, e:
            print "instabot.py", e

        try:
            follow_bot.start(rate=rate, wait=(wait_min * 60, wait_max * 60))

        except Exception, e:
            print "instabot.py", e


def post_contents(username, password, wait=86400):
    while True:
        try:
            content = execute_query(DB_PATH, SELECT_SQL.format(user=username))

            if not len(content):
                continue

        except Exception, e:
            print "instabot.py", e
            continue

        api = InstagramAPI(username, password)
        api.login()

        caption, path = content[0]
        try:
            api.upload_photo(path, caption)
            print "Uploaded {} with caption {}".format(path, caption)
            execute_query(DB_PATH, DELETE_SQL.format(user=username))

        except Exception, e:
            print "instabot.py", e

        # Sleep for 24 hours before posting new content
        sleep(wait)


def get_user_content(user):
    content = None
    CSV_PATH = "";
    with open(CSV_PATH, 'rb') as fin:
        data = fin.read().splitlines(True)
        for i, line in enumerate(data):
            u = line.split("   ")[0]
            if u == user:
                content = data.pop(i).split("   ")
                break

    if not content:
        return []

    with open(CSV_PATH, 'wb') as fout:
        fout.writelines(data)

    for i, col in content:
        content[i] = col.strip()

    return content


@click.command()
@click.option('--username', default='hwzearth', prompt='Username:', help='Instagram username')
@click.option('--password', prompt='Password:', hide_input=True, help='Instagram password')
@click.option('--similar_users', default='', prompt='Similar users accounts:', help='Similar user accounts')
def instabot(username, password, similar_users):
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
    instabot()
