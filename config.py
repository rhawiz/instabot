import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    if os.environ.get('DATABASE_URL') is None:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instabot.db')
    else:
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    SQLALCHEMY_RECORD_QUERIES = True
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/content')
    UPLOAD_URL = '/content'
    STATIC_URL = '/static'

print('sqlite:///' + os.path.join(basedir, 'instabot.db'))