import xmlrpclib
import time

s = xmlrpclib.ServerProxy('http://localhost:8000')

#s.echo()

# Print list of available methods
print s.system.listMethods()

## Spin
s.drive_motor(128, 0, 35000)
s.drive_motor(0x80, 1, 35000)
s.drive_motor(0x81, 1, 35000)
#s.read_encoder(0x80, 0)

time.sleep(2)

s.drive_motor(0x80, 0, 0)
s.drive_motor(0x80, 1, 0)
s.drive_motor(0x81, 1, 0)

s.p_control(0,0,0,0,0,0,0,0,0)
