import os
import uuid
import threading

import jinja2
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
INSERT_QUERY = "INSERT INTO insta_content ('user', 'caption', 'path')  VALUES ('{user}', '{caption}', '{path}');"
VIEW_QUERY = "SELECT * from insta_content"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    return "Instabot"


@app.route('/view', methods=['GET'])
def view_contents():
    contents = execute_query(DB_PATH, VIEW_QUERY)
    return render_template('view_contents.html', content=contents)


@app.route('/run', methods=['GET', 'POST'])
def run_bot():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        similar_users_unparsed = request.form.get('users')
        rate = int(request.form.get('rate'))
        wait_min = int(request.form.get('tmin'))
        wait_max = int(request.form.get('tmax'))
        post_rate = request.form.get('post_rate')
        post_rate_secs = float(post_rate) * 60.0 * 60.0

        similar_users = similar_users_unparsed.split(",")
        for idx, user in enumerate(similar_users):
            similar_users[idx] = user.strip()

        t1 = threading.Thread(target=post_contents, args=(username, password, post_rate_secs))
        t2 = threading.Thread(target=collect_followers, args=(username, password, similar_users, rate, wait_min, wait_max))

        t1.start()
        t2.start()

        return "Started"

    return render_template('run_bot.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
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

            user = request.form.get('user')
            caption = request.form.get('caption')

            path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], fn))

            file.save(path)

            execute_query(DB_PATH, INSERT_QUERY.format(user=user, caption=caption, path=path))

            # return render_template('view_contents.html', url=path, user=user, caption=caption)
            return redirect(url_for('upload_file', filename=fn))
    return render_template('upload_content.html')


#
# @click.command()
# @click.option('--host', '-h', default='0.0.0.0', prompt='host:', help='Host')
# @click.option('--port','-p', default='5000', prompt='port:', help='Port')
# def main(host, port):
#     app.run(host=host, port=port)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5000")
    # main()
