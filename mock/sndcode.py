from smtplib import SMTP
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
import datetime, pyotp, base64, time
from thread import *

def check_expiration(code_list):
    while True:
        for pair in list(code_list):
            diff = time.time() - pair[1]
            if diff > 90:
                code_list.remove(pair)

debuglevel = 0

f = open('in','r')
pw = f.readline()

em = raw_input('What is your email? ')

smtp = SMTP()
smtp.set_debuglevel(debuglevel)
smtp.connect('smtp.gmail.com', 25)
smtp.ehlo()
smtp.starttls()
smtp.ehlo
smtp.login('ryan.holt36', base64.b64decode(pw))

from_addr = "Ryan Holt <ryan.holt36@gmail.com>"
to_addr = em


code_list = []
start_new_thread(check_expiration,(code_list,))
#for i in range(1,20):

totp = pyotp.TOTP(pyotp.random_base32())
auth_code = totp.now()
start = time.time()
code_list.append((auth_code,start))




body = auth_code
msg = MIMEMultipart()
msg['Subject'] = 'Your Verification Code'
msg['From'] = from_addr
msg['To'] = to_addr
msg.attach(MIMEText(body,'plain'))

smtp.sendmail(from_addr, to_addr, msg.as_string())


code = raw_input('What is the verification code: ')

if [pair for pair in code_list if pair[0] == code]:
    print 'Authenticated'
else:
    print 'Failed to authenticate'

smtp.quit()