from flask import Flask, render_template, request, abort, redirect, url_for, flash
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from smtplib import SMTP
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
import datetime, pyotp, base64, time, sys, os, socket
from threading import *

def check_code_list(code_list):
    while True:
        for pair in list(code_list):
            diff = time.time() - pair[1]
            if diff > 90:
                code_list.remove(pair)

def read_client(conn):
    data = conn.recv(BUFSIZ)
    print data

def init_socket():
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    try:
        s.bind((HOST,PORT))
    except socket.error , msg:
        print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]
        sys.exit()
    s.listen(10)
    while 1:
        conn, addr = s.accept()
        print 'Connected with ' + addr[0] + ':' + str(addr[1])

        t3 = Thread(target=read_client, args=(conn,))
        t3.setDaemon(True)
        t3.start()
        
    s.close()

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

#Globals
BUFSIZ = 4096
HOST = ''
PORT = 2327
DEBUG = False
SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'mysql://root:shadow@localhost:3306/mfauth'
from_addr = "Ryan Holt <ryan.holt36@gmail.com>"
code_list = []

 #Init flask app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
#Init flask login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'
 
#Init db
db = SQLAlchemy(app)
user = None

#Init smtp
# f = open('in','r')
# pw = f.readline()
# smtp = SMTP()
# smtp.set_debuglevel(0)
# smtp.connect('smtp.gmail.com', 587)
# smtp.ehlo()
# smtp.starttls()
# smtp.ehlo
# smtp.login('ryan.holt36', base64.b64decode(pw))

#Check for one-time password expiration
t1 = Thread(target=check_code_list, args=(code_list,))
t1.setDaemon(True)
t1.start()

#Open socket to mock website
t2 = Thread(target=init_socket)
t2.setDaemon(True)
t2.start()
 
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

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    global user
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form['txtUsername']
        password = request.form['txtPassword']
        user = User.query.filter_by(username=username).filter_by(password=password)
        if user.count() == 1:
            login_user(user.one())
            return redirect(url_for('settings'))
        else:
            flash('Invalid login')
            return 'fail';
    else:
        return abort(405)

@app.route('/')
def index():
    return render_template('index.html')
 
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('IP', '127.0.0.1')
    app.run(port=port, host=host)
