import os
import uuid
from random import randint
import time

import datetime
import jinja2
import multiprocessing

import signal

import re
from flask import Flask, request, redirect, url_for, flash
from flask import render_template
from werkzeug.utils import secure_filename

from dbutils import execute_query
from instabot import post_contents, collect_followers

UPLOAD_FOLDER = 'content'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['../templates']),
])
app.jinja_loader = my_loader

DB_PATH = "content.db"
INSERT_CONTENT_QUERY = "INSERT INTO insta_content ('user', 'caption', 'path')  VALUES ('{user}', '{caption}', '{path}');"
RETRIEVE_CONTENT_QUERY = "SELECT rowid, user, caption, path, created_at from insta_content"
DELETE_CONTENT_QUERY = "DELETE from insta_content WHERE ROWID = {id}"

INSERT_BOT_QUERY = "INSERT INTO bots ('pid', 'user', 'bot')  VALUES ('{pid}', '{user}', '{bot}');"
RETRIEVE_ALL_BOTS_QUERY = "SELECT pid, user, bot, active, created_at from bots"
RETRIEVE_ACTIVE_BOTS_QUERY = "SELECT pid, user, bot, created_at from bots WHERE active = 1"
DEACTIVATE_BOT_QUERY = "DELETE from bots WHERE pid = {pid}"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


processes = {}


@app.route('/content', methods=['GET'])
def view_contents():
    contents = execute_query(DB_PATH, RETRIEVE_CONTENT_QUERY)
    return render_template('contents.html', content=contents)


@app.route('/log', methods=['GET'])
def log():
    return "Log"


@app.route('/bots', methods=['GET'])
def active_bots():
    content = [
        (
            str(p.get("process").pid),
            p.get('bot'),
            p.get('username'),
            p.get('rate'),
            p.get('wait'),
            p.get('created_at'),
        ) for p in processes.itervalues()
        ]
    return render_template('bots.html', content=content)


@app.route('/stop', methods=['POST'])
def stop_bot():
    if request.method == 'POST':
        pid = request.form.get('pid')
        p = processes.get(pid)
        print pid, p

        if p:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError, e:
                print e
            finally:
                processes.pop(pid)
    return redirect(url_for('active_bots'))


@app.route('/follow_bot', methods=['POST'])
def follow_bot():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        similar_users_unparsed = request.form.get('users')
        follow_rate = int(request.form.get('frate'))
        unfollow_rate = int(request.form.get('urate'))
        wait = int(request.form.get('wait'))

        similar_users = similar_users_unparsed.split(",")
        for idx, user in enumerate(similar_users):
            similar_users[idx] = user.strip()

        p = multiprocessing.Process(target=collect_followers,
                                    args=(
                                        username, password, similar_users, follow_rate, unfollow_rate, wait))

        p.start()
        if p.is_alive():
            data = {
                'process': p,
                'bot': 'follow',
                'username': username,
                'rate': "{}/{}".format(follow_rate, unfollow_rate),
                'wait': str(wait),
                'created_at': time.strftime("%Y-%m-%d at %H:%M"),
            }

            processes[str(p.pid)] = data
        return redirect(url_for('active_bots'))


@app.route('/post_bot', methods=['POST'])
def post_bot():
    if request.method == 'POST':
        post_rate = request.form.get('post_rate')
        username = request.form.get('username')
        password = request.form.get('password')
        post_rate_secs = float(post_rate) * 60.0
        print post_rate_secs
        p = multiprocessing.Process(target=post_contents, args=(username, password, post_rate_secs))
        p.start()

        if p.is_alive():
            data = {
                'process': p,
                'bot': 'post',
                'username': username,
                'rate': "1",
                'wait': post_rate,
                'created_at': time.strftime("%Y-%m-%d at %H:%M"),

            }

            processes[str(p.pid)] = data
        return redirect(url_for('active_bots'))


@app.route('/delete', methods=['POST'])
def delete_content():
    if request.method == 'POST':
        id = request.form.get("id")

        query = DELETE_CONTENT_QUERY.format(id=id)
        execute_query(DB_PATH, query)
        return redirect(url_for('view_contents'))


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        url = request.form.get('url')
        user = request.form.get('user')
        caption = request.form.get('caption')

        # check if the post request has the file part
        if 'file' not in request.files and url == '':
            # flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            fs = secure_filename(file.filename)
            ext = fs.split(".")[-1]
            fn = "{}.{}".format(str(uuid.uuid4()), ext)

            path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], fn))

            file.save(path)

            execute_query(DB_PATH, INSERT_CONTENT_QUERY.format(user=user, caption=caption, path=path))

            # return render_template('contents.html', url=path, user=user, caption=caption)
            return redirect(url_for('view_contents'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5000")
