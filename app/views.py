import multiprocessing
import os
import signal
import time
import uuid

import logging
from flask import request, redirect, url_for, flash, render_template, send_from_directory
from werkzeug.utils import secure_filename
from app.core.instagramapi import InstagramAPI as API
from app.core.utils import execute_query
from core.instabot import post_contents, collect_followers
from app import app, db
from models import Content, InstaAccount, Bot
from config import Config as cfg
from config import basedir

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'mp4'])

DB_PATH = "content.db"
INSERT_CONTENT_QUERY = "INSERT INTO insta_content ('user', 'caption', 'path', 'url')  VALUES ('{user}', '{caption}', '{path}', '{url}');"
RETRIEVE_CONTENT_QUERY = "SELECT rowid, user, caption, url, created_at, verified from insta_content"
DELETE_CONTENT_QUERY = "DELETE from insta_content WHERE ROWID = {id}"
VERIFY_CONTENT_QUERY = "UPDATE insta_content SET verified = 1 WHERE ROWID={id};"
UNVERIFY_CONTENT_QUERY = "UPDATE insta_content SET verified = 0 WHERE ROWID={id};"

LOG_FILE = "app.log"

processes = {}


@app.route('{}/<path:filename>'.format(cfg.UPLOAD_URL))
def serve_content(filename):
    return send_from_directory(os.path.join(basedir, 'app', 'static', 'content'), filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/content', methods=['GET'])
def view_contents():
    # contents = execute_query(DB_PATH, RETRIEVE_CONTENT_QUERY)
    contents = Content.query.all()
    data = [(c.id, c.get_user(), c.caption, c.url, c.created_at, c.verified) for c in contents]
    accounts = InstaAccount.query.all()

    return render_template('contents.html', content=data, accounts=accounts)


@app.route('/logs', methods=['GET'])
def logs():
    if not os.path.isfile("app.log"):
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
        # verified = request.form.get('verified')
        content = Content.query.filter_by(id=id).first()

        content.verified = not content.verified

        db.session.commit()

    return redirect(url_for('view_contents'))


@app.route('/bots', methods=['GET'])
def active_bots():
    bots = Bot.query.all()
    data = [(b.unix_pid, b.bot, b.get_user().username, b.rate, b.interval, b.created_at) for b in bots]
    return render_template('bots.html', content=data)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    accounts = [(a, a.follow_bot(), a.unfollow_bot(), a.post_bot()) for a in InstaAccount.query.all()]
    # data = [(b.unix_pid, b.bot, b.get_user().username, b.rate, b.interval, b.created_at) for b in bots]
    print accounts
    return render_template('dashboard.html', content=accounts)


def verify_account(username, password):
    api = API(username=username, password=password)
    api.login()

    return True if api.last_response.status_code == 200 else False


@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        similar_users = request.form.get('similar_users')

        if username == '' or password == '' or similar_users == '':
            flash("Ensure all fields have been filled in.".format(username), "error")
        elif InstaAccount.query.filter_by(username=username).first():
            flash("User '{}' has already been added.".format(username), "error")
        elif verify_account(username, password):
            account = InstaAccount(username, password, similar_users)
            try:
                db.session.add(account)
                db.session.commit()
                account.create_bots()
                db.session.commit()
            except Exception, e:
                logging.error(e)
            flash("User '{}' succesfully added.".format(username), "success")

        else:
            flash("Invalid credentials for user '{}'".format(username), "error")

    elif request.method == 'GET':
        pass
    # data = [(b.unix_pid, b.bot, b.get_user().username, b.rate, b.interval, b.created_at) for b in bots]
    return redirect(url_for('dashboard'))


@app.route('/stop', methods=['POST'])
def stop_bot():
    if request.method == 'POST':
        pid = request.form.get('pid')

        bot = Bot.query.filter_by(unix_pid=pid).first()

        try:
            bot.deactivate()

        except OSError, e:
            logging.error(e)

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
        account_id = request.form.get('account')
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
            file_url = "{}/{}".format(cfg.UPLOAD_URL, fn)
            file.save(path)

            type = "photo"
            thumbnail = None
            if ext == 'mp4':
                type = "video"
                thumbnail = None

            content = Content(insta_account_id=account_id, caption=caption, url=file_url, path=path, type=type,
                              thumbnail=thumbnail)
            db.session.add(content)
            db.session.commit()
            # execute_query(DB_PATH,
            #               INSERT_CONTENT_QUERY.format(user=account_id, caption=caption, path=path, url=file_url))

            # return render_template('contents.html', url=path, user=user, caption=caption)
            return redirect(url_for('view_contents'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5000")
