from flask import Flask, render_template, request, abort, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from app import app, db,login_manager
from .email import send_one_time
from .models import User, Service, Location, Time

@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id)
    if user.count() == 1:
        return user.one()
    return None

@app.before_first_request
def init_request():
    db.create_all()

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        user = User.query.filter_by(username=current_user.username).first()
        locations = user.services.filter_by(name='Mock').first().locations.all()
        for l in locations:
            print '(' + str(l.latitude) + ', ' + str(l.longitude) + ') Allow: ' + str(l.allow)
        return render_template('settings.html')
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data['addremove'] == "add":
			print "ADD NEW SERVICE" + data['servicename']
			newserv = Service(
        return redirect(url_for('settings'))

@app.route('/settings/<service>', methods=['GET', 'POST'])
@login_required
def subsettings(service=None):
	if request.method == 'GET':
		return render_template('subsettings.html', service=service)
	if request.method == 'POST':
		user = User.query.filter_by(username=current_user.username).first()
		if request.form.get('onetime', None):
			user.onetimepass = 1;
		else:
			user.onetimepass = 0;
		db.session.commit()
	return render_template('subsettings.html', service=service)	
			

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
