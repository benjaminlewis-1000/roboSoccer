import xmlrpclib
import time
import sys


s = xmlrpclib.ServerProxy('http://localhost:8000')

s.drive_forward(2)
