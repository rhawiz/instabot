import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import *
import jinja2

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
app.secret_key = 'test'

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['templates']),
])
app.jinja_loader = my_loader

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
syslog = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(user)s][%(bot)s] %(message)s')
syslog.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
#if not logger.handlers:
logger.addHandler(syslog)

default_config = {
    'follow': {
        'action_interval': 6.0,
        'interval': 3500,
        'rate': 40
    },
    'unfollow': {
        'action_interval': 4.0,
        'interval': 4000,
        'rate': 120
    },
    'post': {
        'action_interval': 1.0,
        'interval': 28800,
        'rate': 1
    }
}

from app import views, models
