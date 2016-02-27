#!/usr/bin/python
from app import db

SQLALCHEMY_DATABASE_URI = 'mysql://root:shadow@localhost:3306/mock'
db.create_all()