from app import db
from sqlalchemy.dialects.mysql import TINYINT

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45))
    password = db.Column(db.String(45))
    email = db.Column(db.String(45))
    services = db.relationship('Service', backref='user', lazy='dynamic')

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

    def __repr__(self):
        return '<User %r>' % (self.username)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45))   
    onetimepass = db.Column(TINYINT(1))
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    locations = db.relationship('Location', backref='service', lazy='dynamic')
    times = db.relationship('Time', backref='service', lazy='dynamic')


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    radius = db.Column(db.Float)
    allow = db.Column(db.Integer)
    place = db.Column(db.String(45))
    serviceid = db.Column(db.Integer, db.ForeignKey('service.id'))

class Time(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.String(45))
    end = db.Column(db.String(45))
    allow = db.Column(db.Integer)
    serviceid = db.Column(db.Integer, db.ForeignKey('service.id'))





