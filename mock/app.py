from flask import Flask, render_template, request, abort, redirect, url_for, flash
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import datetime, pyotp, base64, time, os, socket
from thread import *

def create_header(username,email,ip,time):
    s = '#####\n' + \
        username + '\n' + \
        email + '\n' + \
        time + '\n' + \
        ip + '\n' + \
        'Mock\n' + \
        '$$$$$'
    return s


DEBUG = False
SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'mysql://root:shadow@localhost:3306/mfauth'
 
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

 
db = SQLAlchemy(app)
user = None

try:
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
except socket.error, msg:
    print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
    sys.exit();

host = socket.gethostname() 
port = 2327

try:
    remote_ip = socket.gethostbyname(host)
except socket.gaierror:
    print 'Hostname could not be resolved. Exiting'
    sys.exit()

s.connect((remote_ip,port))
print 'Socket connected to ' + host + ' on IP ' + remote_ip
 
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
            header = create_header(username,email,'fdsfssd','fdsfs')
            s.sendall(header)
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