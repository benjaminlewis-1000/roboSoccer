import sys

def stop():
	import xmlrpclib
	s = xmlrpclib.ServerProxy('http://localhost:8000')
	s.stop()
	
def spin(time):
	import xmlrpclib
	s = xmlrpclib.ServerProxy('http://localhost:8000')
	s.spin(time)
	
def square(side_length):
	import xmlrpclib
	s = xmlrpclib.ServerProxy('http://localhost:8000')
	s.square(side_length)
	
def drive_forward(distance):
	import xmlrpclib
	s = xmlrpclib.ServerProxy('http://localhost:8000')
	s.drive_forward(distance)
	
def rotate_one_sixth():
	import xmlrpclib
	s = xmlrpclib.ServerProxy('http://localhost:8000')
	s.rotate_one_sixth()
	
def rotate_one_sixth_dir(direction):
	import xmlrpclib
	s = xmlrpclib.ServerProxy('http://localhost:8000')
	s.rotate_one_sixth_dir(direction)
	

def rotate_degrees(degrees):
	import xmlrpclib
	s = xmlrpclib.ServerProxy('http://localhost:8000')
	s.rotate_degrees(degrees)
