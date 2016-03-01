from flask import Flask, render_template, request, abort, redirect, url_for, flash, session
from flask.ext.login import LoginManager, login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from time import strftime
import os, json, urllib2

SECRET_KEY = 'yekterces'
SQLALCHEMY_DATABASE_URI = 'mysql://root:shadow@localhost:3306/mock'
SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config.from_object(__name__)
 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

db = SQLAlchemy(app)

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
        return unicode(self.id)

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
        user = User.query.filter_by(username=username).filter_by(password=password)
        if user.count() == 1:  
            user = user.one()
            session['uid'] = user.get_id()

            time = strftime("%H%M")
            d = json.dumps({'username' : username, 'service' : 'mock', 'latitude' : latitude, \
                            'longitude' : longitude, 'time' : time})

            url = 'http://localhost:5000/api/verify_login'
            req = urllib2.Request(url, d, {'Content-Type' : 'application/json', 'Content-Length' : len(d)})
            response = urllib2.urlopen(req)
            data = json.loads(response.read())
            if data['success'] != 1:
                flash('Access Denied')
                return redirect(url_for('login'))    

            response = urllib2.urlopen('http://localhost:5000/api/get_otp_en/mock/' + username)
            data = json.loads(response.read())
            if data['otp_en'] == 1:
                response = urllib2.urlopen('http://localhost:5000/api/send_otp/' + username)
                return redirect(url_for('key'))
            login_user(user)
            return redirect(url_for('index'))        
        else:
            flash('Invalid Credentials')
            return redirect(url_for('login'))    
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
        d = json.dumps({'otp' : key})
        url = 'http://localhost:5000/api/verify_otp'
        req = urllib2.Request(url, d, {'Content-Type' : 'application/json', 'Content-Length' : len(d)})
        response = urllib2.urlopen(req)
        data = json.loads(response.read())
        if data['success'] == 1:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid Key')
            return redirect(url_for('login'))          
        
    else:
        return abort(405)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('IP', '127.0.0.1')
    app.run(port=port, host=host, debug=True)


