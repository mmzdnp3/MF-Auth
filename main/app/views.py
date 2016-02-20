from flask import Flask, render_template, request, abort, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from app import app, db,login_manager
from .email import send_one_time
from .models import User

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