from flask import Flask, render_template, request, abort, redirect, url_for, flash, jsonify, make_response
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
import math,re
from app import app, db,login_manager, code_list
from .email import send_one_time
from .models import User, Service, Location, Time

def distance_between_coords(lat1, long1, lat2, long2):
    degrees_to_radians = math.pi/180.0
    earth_radius = 6370
         
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
         
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
     
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + \
           math.cos(phi1)*math.cos(phi2))

    arc = math.acos(cos)

    return arc * earth_radius

def convert_time(start, end):
    startTime = re.search("(\d{1,2}):(\d{2})\s+(AM|PM)",start)
    startTimeV = startTime.group(1) + startTime.group(2);
    startTimeV = int(startTimeV)
    if(startTime.group(3) == "PM"):
        if(startTime.group(1)!="12"):  
            startTimeV += 1200
    print startTimeV

    endTime = re.search("(\d{1,2}):(\d{2})\s+(AM|PM)",end)    
    endTimeV = endTime.group(1) + endTime.group(2);
    endTimeV = int(endTimeV)
    if(endTime.group(3) == "PM"):
        if(endTime.group(1)!="12"):  
            endTimeV+=1200
    print endTimeV
    return startTimeV,endTimeV    

@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id)
    if user.count() == 1:
        return user.one()
    return None

@app.before_first_request
def init_request():
    db.create_all()

@app.route('/api/get_otp_en/<service>/<username>', methods=['GET'])
def get_otp_en(service, username):
    user = User.query.filter_by(username=username)
    if user.count() == 1:
        serv = user.first().services.filter_by(name=service)
        if serv.count() == 1:
            otp_en = serv.first().onetimepass
            return jsonify({'otp_en' : otp_en})
    abort(404)

@app.route('/api/send_otp/<username>', methods=['GET'])
def send_otp(username):
    user = User.query.filter_by(username=username)
    if user.count() == 1:
        email = user.first().email
        send_one_time([email])
        return jsonify({'success' : 1})
    abort(404)

@app.route('/api/verify_otp/<username>', methods=['POST'])
def verify_otp(username):
    if not request.json or not 'otp' in request.json:
        abort(400)
    otp = request.json['otp']
    if [pair for pair in code_list if pair[0] == otp]:
        return jsonify({'success' : 1})
    else:
       return jsonify({'success' : 0})

@app.route('/api/verify_login', methods=['POST'])
def verify_login():
    if not 'username' in request.json:
        abort(400)
    if not 'service' in request.json:
        abort(400)
    if not 'latitude' in request.json:
        abort(400)
    if not 'longitude' in request.json:
        abort(400)
    if not 'time' in request.json:
        abort(400) 

    username = request.json['username']
    service = request.json['service']
    try:
        latitude = float(request.json['latitude'])
        longitude = float(request.json['longitude'])
    except ValueError: 
        abort(404)
    time = int(request.json['time'])

    user = User.query.filter_by(username=username)
    if user.count() != 1:
        abort(404)

    serv = user.first().services.filter_by(name=service) 
    if serv.count() != 1:
        abort(404)

    locations_db = serv.first().locations.all()
    times_db = serv.first().times.all()

    verified_loc = True
    for loc in locations_db:
        lat_db = float(loc.latitude)
        long_db = float(loc.longitude)
        radius_db = float(loc.radius)/1000
        allow = int(loc.allow)
        distance = distance_between_coords(latitude, longitude, lat_db, long_db)
        if allow == 0:
            if distance <= radius_db:
                verified_loc = False
    verified_time = True
    for t in times_db:
        timepair = convert_time(t.start, t.end)
        if t.allow == 0:
            if timepair[0] < time and timepair[1] > time:
                verified_time = False

    
    if verified_loc and verified_time:
        return jsonify({'success' : 1})
    else:
       return jsonify({'success' : 0}) 

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        services = current_user.services.all()
        return render_template('settings.html', serviceList=services)
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data['addremove'] == "add":
            serv = data['servicename']
            newserv = Service(name=serv, onetimepass=0);
            current_user.services.append(newserv)
            db.session.commit()
        if data['addremove'] == "remove":
            serv = data['servicename']
            Service.query.filter_by(name=serv,userid=current_user.id).delete()
            db.session.commit()
    return redirect(url_for('settings'))    

@app.route('/settings/<service>', methods=['GET', 'POST'])
@login_required
def subsettings(service=None):
    serv = Service.query.filter_by(name=service,userid=current_user.id).first()
    onetime = serv.onetimepass
    locations = serv.locations.all()
    times = serv.times.all()
    if request.method == 'GET':
        return render_template('subsettings.html', service=service, onetimepass=onetime, locationList=locations, timeList=times)
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data['type'] == "otp":
            if data['enable'] == 1:
                print "Enabled OTP for " + service
                serv.onetimepass = 1;
            elif data['enable'] == 0:
                print "Disabled OTP for " + service
                serv.onetimepass = 0;
        
        elif data['type'] == "time":
            begin = data['begintime']
            end = data['endtime']
            if data['addremove'] == "check":
                time = Time.query.filter_by(start=begin,end=end,serviceid=serv.id).first()
                if data['allow'] == 1:
                    print "Allow login for " + begin + " - " + end + " for " + service
                    time.allow = 1;
                elif data['allow'] == 0:
                    time.allow = 0;
                    print "Disallow login for " + begin + " - " + end + " for " + service
            if data['addremove'] == "add":
                allow = data['allow']
                newtime = Time(start=begin,end=end,allow=allow);
                serv.times.append(newtime);
                print "Added time " + begin + " - " + end + " for " + service
            elif data['addremove'] == "remove":
                Time.query.filter_by(start=begin,end=end,serviceid=serv.id).delete()
                print "Removed time " + begin + " - " + end + " for " + service
        
        elif data['type'] == "loc":
            latitude = data['latitude']
            longitude = data['longitude']
            radius = data['radius']
            if data['addremove'] == "check":
                loc = Location.query.filter_by(latitude=latitude,longitude=longitude,serviceid=serv.id).first()
                if data['allow'] == 1:
                    print "Allow login for "+ str(latitude) + ", " + str(longitude) + " Radius: " + str(radius) + " for " + service
                    loc.allow = 1
                elif data['allow'] == 0:
                    loc.allow = 0
                    print "Disallow login for "+ str(latitude) + ", " + str(longitude) + " Radius: " + str(radius) + " for " + service
            if data['addremove'] == "add":
                allow = data['allow']
                place = data['place']
                newloc = Location(latitude=latitude,longitude=longitude,radius=radius,allow=allow,place=place)
                serv.locations.append(newloc)
                print "Added loc " + str(latitude) + ", " + str(longitude) + " Radius: " + str(radius) + " for " + service
            elif data['addremove'] == "remove":
                Location.query.filter_by(latitude=latitude,longitude=longitude,radius=radius,serviceid=serv.id).delete()
                print "Removed loc " + str(latitude) + ", " + str(longitude) + " Radius: " + str(radius) + " for " + service            
        db.session.commit()
        return render_template('subsettings.html', service=service, onetimepass=onetime, locationList=locations, timeList=times)
            

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
            flash('Invalid credentials')      
    else:
        return abort(405)
    return render_template('login.html') 

@app.route('/')
def index():
    return render_template('index.html')
