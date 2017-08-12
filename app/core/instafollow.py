from app import logger
from random import randint, uniform
from time import sleep
from requests.exceptions import ChunkedEncodingError
from instagramapi import InstagramAPI


class InstaFollow:
    def __init__(self, username, password, similar_users, API=None, action_interval=8.0, rate=75, interval=5400):
        self.username = username
        self.password = password

        if isinstance(similar_users, (str, unicode)):
            self.similar_users = [x.strip() for x in similar_users.split(",")]
        else:
            self.similar_users = similar_users

        self.action_interval = action_interval
        self.rate = rate
        self.interval = interval
        self.API = InstagramAPI(self.username, self.password) if API is None else API

    def _get_user_ids(self, save_to=None):

        logger.info('Collecting users to follow...', extra={'user': self.username})

        # Randomly select root account to search for users
        account = self.similar_users[randint(0, len(self.similar_users) - 1)]
        self.API.search_username(account)

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

        user_ids = []

        for media_id in media_ids:
            self.API.get_media_likers(media_id)

            try:
                users = self.API.last_json.get('users')
            except ChunkedEncodingError, e:
                logger.error("Failed to retrieve user list", e, extra={'user': self.username})
                users = []

            for user in users:
                id = user.get('pk')
                user_ids.append(id)

        user_ids = list(set(user_ids))

        logger.info("Found {} new users...".format(len(user_ids)), extra={'user': self.username})

        return user_ids

    def _login(self):
        attempts = 0
        while attempts <= 10:
            try:
                if self.API.login():
                    return True
            except Exception as e:
                logger.error("Failed to login", e)

            sleep(6)
            attempts += 1

        return False

    def start(self):

        if not self.API.is_logged_in:
            if not self._login():
                return False

        logger.info("Follow bot started...", extra={'user': self.username})
        users = []
        while len(users) < 7000:
            users += self._get_user_ids()
        progress = 0
        bad_requests = 0
        while users:
            progress += 1
            if not self.API.is_logged_in:
                self.API.login()

            id = users.pop(0)

            self.API.follow(id)

            if self.API.last_response.status_code in (429, 400):
                users.append(id)
                bad_requests += 1

            if bad_requests == 10:
                sleep(randint(60, 100))
                bad_requests = 0

            logger.debug(self.API.last_response.content)

            if not (progress % self.rate):
                progress = 0
                followings = len(self.API.get_total_self_followings())
                if followings > 7000:
                    break
                sleep(uniform(self.interval * 0.9, self.interval * 1.1))

            # Sleep n seconds +/ 10% to induce randomness between each action
            sleep(uniform(self.action_interval * 0.9, self.action_interval * 1.1))
