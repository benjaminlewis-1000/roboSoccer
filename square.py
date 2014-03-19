import xmlrpclib
import time
import sys

delay = float(sys.argv[1])
mult = float(sys.argv[2])

s = xmlrpclib.ServerProxy('http://localhost:8000')

k = 50000

s.drive_motor(0x80, 0, int(mult * k * 1.1423))
s.drive_motor(0x80, 1, int(mult * k * -0.57))
s.drive_motor(0x81, 1, int(mult * k * -0.57))
time.sleep(delay)
s.drive_motor(0x80, 0, 0)
s.drive_motor(0x80, 1, int(0.98 * k))
s.drive_motor(0x81, 1, int(-0.98 * k))
time.sleep(delay)
s.drive_motor(0x80, 0, int(mult * -1.1423 * k))
s.drive_motor(0x80, 1, int(mult * 0.57 * k))
s.drive_motor(0x81, 1, int(mult * 0.57 * k))
time.sleep(delay)
s.drive_motor(0x80, 0, 0)
s.drive_motor(0x80, 1, int(mult * -0.98 * k))
s.drive_motor(0x81, 1, int(mult * 0.98 * k))
time.sleep(delay)
s.stop()

