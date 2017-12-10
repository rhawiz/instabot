import json
import os
import random
import uuid

import logging

import requests
from flask import request, redirect, url_for, flash, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Content, InstaAccount
from config import Config as cfg
from config import basedir
from instagram_web_api import Client

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'mp4'])

DB_PATH = "content.db"
DELETE_CONTENT_QUERY = "DELETE from insta_content WHERE ROWID = {id}"
VERIFY_CONTENT_QUERY = "UPDATE insta_content SET verified = 1 WHERE ROWID={id};"
UNVERIFY_CONTENT_QUERY = "UPDATE insta_content SET verified = 0 WHERE ROWID={id};"

LOG_FILE = "/var/log/apache2/error.log"

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
    tab = request.args.get('tab', 0)
    print(tab)
    contents = Content.query.all()
    data = [(c.id, c.get_user(), c.caption, c.url, c.created_at, c.verified, c.type) for c in contents]
    accounts = InstaAccount.query.all()

    return render_template('contents.html', content=data, accounts=accounts, tab=tab)


@app.route('/logs', methods=['GET'])
def logs():
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


@app.route('/dashboard', methods=['GET'])
def dashboard():
    accounts = [a for a in InstaAccount.query.all()]
    # data = [(b.unix_pid, b.bot, b.get_user().username, b.rate, b.interval, b.created_at) for b in bots]
    return render_template('dashboard.html', accounts=accounts)


@app.route('/find_contents', methods=['POST'])
def find_contents():
    return redirect(url_for('view_contents', tab=1))


@app.route('/toggle_follow', methods=['POST'])
def toggle_follow_bot():
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        account = InstaAccount.query.filter_by(id=account_id).first()
        if account.active:
            account.deactivate()
        else:
            follow_rate = int(request.form.get('{}followRate'.format(account.username)))
            follow_interval = int(request.form.get('{}followInterval'.format(account.username)))
            follow_action_interval = int(request.form.get('{}followActionInterval'.format(account.username)))
            unfollow_rate = int(request.form.get('{}unfollowRate'.format(account.username)))
            unfollow_interval = int(request.form.get('{}unfollowInterval'.format(account.username)))
            unfollow_action_interval = int(request.form.get('{}unfollowActionInterval'.format(account.username)))
            post_rate = int(request.form.get('{}postRate'.format(account.username)))
            post_interval = int(request.form.get('{}postInterval'.format(account.username)))
            post_action_interval = int(request.form.get('{}postActionInterval'.format(account.username)))

            config = {
                'follow': {
                    'action_interval': follow_action_interval,
                    'interval': follow_interval,
                    'rate': follow_rate
                },
                'unfollow': {
                    'action_interval': unfollow_action_interval,
                    'interval': unfollow_interval,
                    'rate': unfollow_rate
                },
                'post': {
                    'action_interval': post_action_interval,
                    'interval': post_interval,
                    'rate': post_rate
                }
            }
            print(config)
            account.activate(config)

        return redirect(url_for('dashboard'))


@app.route('/public_info/<username>', methods=['GET'])
def public_info(username):
    api = Client()
    return json.dumps(api.user_info2(username), indent=4)


def verify_account(username, password):
    return True
    api = API(username=username, password=password)
    api.login()
    return True if api.last_response.status_code == 200 else False


@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        similar_users = request.form.get('users')

        if username == '' or password == '' or similar_users == '':
            flash("Ensure all fields have been filled in.".format(username), "error")
        elif InstaAccount.query.filter_by(username=username).first():
            flash("User '{}' has already been added.".format(username), "error")
        elif verify_account(username, password):
            account = InstaAccount(username, password, similar_users)
            try:
                db.session.add(account)
                db.session.commit()
            except Exception as e:
                logging.error(e)
            flash("User '{}' succesfully added.".format(username), "success")

        else:
            flash("Invalid credentials for user '{}'".format(username), "error")

    elif request.method == 'GET':
        pass

    # data = [(b.unix_pid, b.bot, b.get_user().username, b.rate, b.interval, b.created_at) for b in bots]
    return redirect(url_for('dashboard'))


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        account = InstaAccount.query.filter_by(id=user_id).first()
        if account:
            db.session.delete(account)
            db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/delete_content', methods=['POST'])
def delete_content():
    if request.method == 'POST':
        id = request.form.get("content_id")
        content = Content.query.filter_by(id=id).first()
        if content:
            db.session.delete(content)
            db.session.commit()

        return redirect(url_for('view_contents'))


@app.route('/generate_tags/<categories>', methods=['GET'])
def generate_tag(categories):
    print(categories)
    if request.method == 'GET':
        print(categories)
        category_list = categories.split(" ")
        tags = []
        for category in category_list:

            try:
                resp = requests.get("https://d212rkvo8t62el.cloudfront.net/tag/{}".format(category.strip()))
                _dict = resp.json()
                if not _dict:
                    continue
                results = _dict.get("results")
                for res in results:
                    try:
                        tags.append("#{}".format(res.get("tag")))
                    except UnicodeEncodeError as e:
                        logging.error(e)
            except Exception as e:
                logging.error(e)
        tags = tags[:30]
        random.shuffle(tags)
        return " ".join(tags)


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

            return redirect(url_for('view_contents'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5000")
