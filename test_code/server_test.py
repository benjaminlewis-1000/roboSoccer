import xmlrpclib
import time

s = xmlrpclib.ServerProxy('http://localhost:8000')

#s.echo()

# Print list of available methods
print s.system.listMethods()

## Spin

s.square(2)
