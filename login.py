from flask import Flask, render_template, request, abort, redirect, url_for, flash
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import os
from smtplib import SMTP
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
import datetime, pyotp, base64, time
from thread import *

def check_expiration(code_list):
    while True:
        for pair in list(code_list):
            diff = time.time() - pair[1]
            if diff > 90:
                code_list.remove(pair)

DEBUG = True
SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'mysql://root:shadow@localhost:3306/mfauth'
 
app = Flask(__name__)
app.config.from_object(__name__)
 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'
 
db = SQLAlchemy(app)
user = None
f = open('in','r')
pw = f.readline()
smtp = SMTP()
smtp.set_debuglevel(0)
smtp.connect('smtp.gmail.com', 25)
smtp.ehlo()
smtp.starttls()
smtp.ehlo
smtp.login('ryan.holt36', base64.b64decode(pw))

from_addr = "Ryan Holt <ryan.holt36@gmail.com>"
code_list = []
start_new_thread(check_expiration,(code_list,))


def send_one_time(email):
    totp = pyotp.TOTP(pyotp.random_base32())
    auth_code = totp.now()
    start = time.time()
    code_list.append((auth_code,start))

    body = auth_code
    msg = MIMEMultipart()
    msg['Subject'] = 'Your Verification Code'
    msg['From'] = from_addr
    msg['To'] = email
    msg.attach(MIMEText(body,'plain'))

    smtp.sendmail(from_addr, email, msg.as_string())
 
class User(db.Model, UserMixin):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45))
    password = db.Column(db.String(45))
    email = db.Column(db.String(45))

@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id)
    if user.count() == 1:
        return user.one()
    return None

@app.before_first_request
def init_request():
    db.create_all()

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    global user
    print '<1>'
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form['txtUsername']
        password = request.form['txtPassword']
        user = User.query.filter_by(username=username).filter_by(password=password)
        if user.count() == 1:
            email = user.one().email
            send_one_time(email)
            return redirect(url_for('key'))
        else:
            flash('Invalid login')
            return 'fail';
    else:
        return abort(405)

@app.route('/key', methods=['GET', 'POST'])
def key():
    global user
    if request.method == 'GET':
        return render_template('key.html')
    elif request.method == 'POST':
        key = request.form['txtKey']
        if [pair for pair in code_list if pair[0] == key]:
            login_user(user.one())
            #flash('Welcome back {0}'.format(username))
            return redirect(url_for('index'))
        return 'error'
    else:
        return abort(405)

@app.route('/')
def index():
    return render_template('index.html')

 
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('IP', '127.0.0.1')
    app.run(port=port, host=host)