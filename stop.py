import xmlrpclib
import time

s = xmlrpclib.ServerProxy('http://localhost:8000')

#s.echo()

# Print list of available methods

## Spin
#s.p_control(30000, 30000, 30000, 1, 1, 1, 300000, 30000, 30000)
s.stop()
