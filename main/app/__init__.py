import os, sys, socket
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from .decorators import async
import cPickle as pickle

@async
def read_client(conn):
    from .email import send_one_time
    while True:
        data = pickle.loads(conn.recv(4096))
        code = data['auth_code']
        if data['time'] is None:
            print 'checking code..'
            if [pair for pair in code_list if pair[0] == code]:
                conn.sendall('Yes')
            else:
                conn.sendall('No')
        else:
            print 'sending email..'
            username = data['username']
            email = data['email']
            send_one_time([email])

@async
def init_socket():
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    try:
        s.bind(('',6321))
    except socket.error , msg:
        print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]
        sys.exit()

    s.listen(10)
    while 1:
        conn, addr = s.accept()
        print 'Connected with ' + addr[0] + ':' + str(addr[1])

        read_client(conn)
        
    s.close()
 
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)
init_socket()

code_list = []

from app import views, models
