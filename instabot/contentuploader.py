import hashlib
import os
import uuid

import click
from flask import Flask, request, redirect, url_for, flash
from flask import render_template
from werkzeug.utils import secure_filename

from dbutils import execute_query

UPLOAD_FOLDER = '../data/content'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_PATH = "../data/content.db"
INSERT_QUERY = "INSERT INTO insta_content ('user', 'caption', 'path')  VALUES ('{user}', '{caption}', '{path}');"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

            # return render_template('view_content.html', url=path, user=user, caption=caption)
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
    #main()