import logging

import click

from instaunfollow import InstaUnfollow

from instafollow import InstaFollow


def collect_followers(follow_bot, unfollow_bot):
    if not isinstance(follow_bot, InstaFollow) or not isinstance(unfollow_bot, InstaUnfollow):
        return

    while True:
        try:
            unfollow_bot.start()
        except Exception, e:
            logging.exception(e)
        try:
            follow_bot.start()
        except Exception, e:
            logging.exception(e)


@click.command()
@click.option('--username', default='hwzearth', prompt='Username:', help='Instagram account name')
@click.option('--password', default='', prompt='Password:', help='Instagram account name')
@click.option('--similar_users', default='', prompt='Similar users accounts:', help='Similar user accounts')
def main(username, password, similar_users):
    follow_bot = InstaFollow(username=username, password=password, similar_users=similar_users)
    unfollow_bot = InstaUnfollow(username=username, password=password)
    collect_followers(follow_bot=follow_bot, unfollow_bot=unfollow_bot)


if __name__ == '__main__':
    main()
