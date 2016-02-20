from flask.ext.mail import Message
from app import app, mail, code_list
import datetime, pyotp, time
from .decorators import async
from config import ADMINS

@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    send_async_email(app, msg)

def send_one_time(recipients):
    totp = pyotp.TOTP(pyotp.random_base32())
    auth_code = totp.now()
    start = time.time()
    code_list.append((auth_code,start))
    send_email('Your Authentication Code', ADMINS[0], recipients, auth_code)

