import xmlrpclib
import time
import sys


s = xmlrpclib.ServerProxy('http://localhost:8000')

s.rotate_one_sixth_dir(0)
time.sleep(1)
s.rotate_one_sixth_dir(1)

