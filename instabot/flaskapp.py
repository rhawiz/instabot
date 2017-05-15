import os
import uuid
from random import randint
import time

import datetime
import jinja2
import multiprocessing

import signal

from flask import Flask, request, redirect, url_for, flash
from flask import render_template
from flask import send_file
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from utils import execute_query
from instabot import post_contents, collect_followers

UPLOAD_FOLDER = '../static/content'
UPLOAD_URL = '/content'
STATIC_URL = '/static'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['../templates']),
])
app.jinja_loader = my_loader

DB_PATH = "content.db"
INSERT_CONTENT_QUERY = "INSERT INTO insta_content ('user', 'caption', 'path', 'url')  VALUES ('{user}', '{caption}', '{path}', '{url}');"
RETRIEVE_CONTENT_QUERY = "SELECT rowid, user, caption, url, created_at, verified from insta_content"
DELETE_CONTENT_QUERY = "DELETE from insta_content WHERE ROWID = {id}"
VERIFY_CONTENT_QUERY = "UPDATE insta_content SET verified = 1 WHERE ROWID={id};"
UNVERIFY_CONTENT_QUERY = "UPDATE insta_content SET verified = 0 WHERE ROWID={id};"

LOG_FILE = "instabot.log"

processes = {}


@app.route('{}/<path:filename>'.format(UPLOAD_URL))
def serve_content(filename):
    root_dir = os.path.dirname(os.getcwd())
    return send_from_directory(os.path.join(root_dir, 'static', 'content'), filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/content', methods=['GET'])
def view_contents():
    contents = execute_query(DB_PATH, RETRIEVE_CONTENT_QUERY)
    return render_template('contents.html', content=contents)


@app.route('/logs', methods=['GET'])
def logs():
    if not os.path.isfile("instabot.log"):
        return render_template('log.html', content="")

    with open(LOG_FILE, "rb") as f:
        log = f.read()[-300000:]

    return render_template('log.html', log=log)


@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    open(LOG_FILE, 'w').close()
    return redirect(url_for('logs'))


@app.route('/verify', methods=['POST'])
def verify_photo():
    if request.method == 'POST':
        id = request.form.get('id')
        verified = int(request.form.get('verified'))

        if verified:
            execute_query(DB_PATH, UNVERIFY_CONTENT_QUERY.format(id=id))
        elif not verified:
            execute_query(DB_PATH, VERIFY_CONTENT_QUERY.format(id=id))

    return redirect(url_for('view_contents'))


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
        follow_action_wait = int(request.form.get('faction_wait'))
        unfollow_action_wait = int(request.form.get('uaction_wait'))
        follow_first = request.form.get('follow_first')

        if username and password:

            similar_users = similar_users_unparsed.split(",")
            for idx, user in enumerate(similar_users):
                similar_users[idx] = user.strip()

            p = multiprocessing.Process(target=collect_followers,
                                        args=(
                                            username, password, similar_users, follow_rate, unfollow_rate, wait,
                                            follow_action_wait, unfollow_action_wait))

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
        if username and password:
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
            file_url = "{}/{}".format(UPLOAD_URL, fn)
            file.save(path)

            execute_query(DB_PATH, INSERT_CONTENT_QUERY.format(user=user, caption=caption, path=path, url=file_url))

            # return render_template('contents.html', url=path, user=user, caption=caption)
            return redirect(url_for('view_contents'))


def main():
    app.run(host="0.0.0.0", port="5000")


if __name__ == '__main__':
    main()
