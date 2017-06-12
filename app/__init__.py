import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import *

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
app.secret_key = 'test'

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

import jinja2

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['templates']),
])
app.jinja_loader = my_loader

logger = logging.getLogger(__name__)
syslog = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(user)] %(message)s')
syslog.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(syslog)

bot_config = {
    'follow': {
        'action_interval': 8.0,
        'interval': 5400,
        'rate': 75
    },
    'unfollow': {
        'action_interval': 8.0,
        'interval': 5400,
        'rate': 120
    },
    'post': {
        'action_interval': 8.0,
        'interval': 1.0,
        'rate': 1
    }
}

# logging.basicConfig(
#     filename="app.log",
#     format='[%(asctime)s][%(levelname)s][%(user)] %(message)s',
#     datefmt='%d-%m-%Y %I:%M:%S %p', level=logging.DEBUG
# )

from app import views, models
