import xmlrpclib
import time
import sys

delay = sys.argv[1]
speed = int(sys.argv[2])

s = xmlrpclib.ServerProxy('http://localhost:8000')

s.drive_motor(0x80, 0, int(1 * speed))
s.drive_motor(0x80, 1, int(1 * speed))
s.drive_motor(0x81, 1, int(1 * speed))
print s.read_encoder(0x80, 0)
print s.read_encoder(0x80, 1)
print s.read_encoder(0x81, 0)
time.sleep(float(delay))
s.stop()
