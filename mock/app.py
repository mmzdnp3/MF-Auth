from flask import Flask, g, render_template, request, abort, redirect, url_for, flash, session
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import datetime, pyotp, base64, time, os, socket
import cPickle as pickle
from thread import *

def create_dictionary(username,email,time,lat,lon,auth_code):
    
    data = {'username': username,
            'email': email,
            'time': time,
            'lat': lat,
            'long': lon,
            'auth_code': auth_code}
    return data;


DEBUG = False
SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'mysql://root:shadow@localhost:3306/mock'
 
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'
 
db = SQLAlchemy(app)

try:
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
except socket.error, msg:
    print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
    sys.exit();

host = socket.gethostname() 

try:
    remote_ip = socket.gethostbyname(host)
except socket.gaierror:
    print 'Hostname could not be resolved. Exiting'
    sys.exit()

s.connect((remote_ip, 6321))
print 'Socket connected to ' + host + ' on IP ' + remote_ip
 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45))
    password = db.Column(db.String(45))
    email = db.Column(db.String(45))

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

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
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form['txtUsername']
        password = request.form['txtPassword']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        print latitude
        print longitude
        user = User.query.filter_by(username=username).filter_by(password=password)
        if user.count() == 1:
            user = user.one()
            dictionary = create_dictionary(username,user.email,'fdsfssd',latitude,longitude, None)
            d = pickle.dumps(dictionary)
            s.sendall(d)
            session['uid'] = user.get_id()
            return redirect(url_for('key'))
        else:
            return 'fail';
    else:
        return abort(405)

@app.route('/key', methods=['GET', 'POST'])
def key():
    user = user_loader(session['uid'])
    if request.method == 'GET':
        if request.referrer != request.url_root + 'login':
            return redirect(url_for('login'))
        return render_template('key.html')
    elif request.method == 'POST':
        key = request.form['txtKey']
        dictionary = create_dictionary(None,None,None,None,None,key)
        d = pickle.dumps(dictionary)
        s.sendall(d)
        authenticated = s.recv(4096)
        if authenticated == 'Yes':
            login_user(user)
        else:
            return 'fail'
        return redirect(url_for('index'))
    else:
        return abort(405)

@app.route('/')
def index():
    return render_template('index.html')

 
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('IP', '127.0.0.1')
    app.run(port=port, host=host)