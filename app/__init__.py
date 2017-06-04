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

from app import views, models
