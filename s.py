from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import serial
import param_vars
import sys
from time import sleep
from time import time

ser_x80 = serial.Serial('/dev/ttyPCH1', param_vars.baud_rate)
ser_x81 = serial.Serial('/dev/ttyPCH2', param_vars.baud_rate)

start_const = 25000
k_const = 10000

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
server = SimpleXMLRPCServer(("localhost", 8000),
                            requestHandler=RequestHandler, logRequests = False, 										 allow_none = True)
   # logRequests = False suppresses all output from the server about date and host location.
   
server.register_introspection_functions()
# Functions such as system.listMethods()

def derp():
	sleep(3)

server.register_function(derp)

################
def drive_motor(board_num, motor, speed):

	if (board_num == 0x80):
		ser = ser_x80
	else:
		ser = ser_x81
			
	if ((board_num > 0x87) or (board_num < 0x80)):
		print "Roboclaw board number is out of the scope of possible addresses."
		return param_vars.e_code
	if ((motor != 0) and (motor != 1)):
		print "Please select motor 0 or 1. Yes, I know the boards say 1 and 2. Yes, I know that doesn't make any sense."
		return param_vars.e_code
		
	command = (35 - param_vars.motor_min + motor)  # In case I decide to go with a 1-2 schema.

	speed_byte3 = speed & 0xff  #Least significant bit
	speed = speed >> 8
	speed_byte2 = speed & 0xff
	speed = speed >> 8
	speed_byte1 = speed & 0xff
	speed = speed >> 8
	speed_byte0 = speed & 0xff  # Most significant bit

	checksum = (board_num + command + speed_byte0 + speed_byte1 + speed_byte2 + speed_byte3) & 0x7f

	cmdList = [board_num, command, speed_byte0, speed_byte1, speed_byte2, speed_byte3, checksum]
	# Written MSB to LSB, per the spec sheet. 

	for i in range(len(cmdList)):
		ser.write(chr(cmdList[i]))
		#print cmdList[i]
	return 0;
		
server.register_function(drive_motor, 'drive_motor')
################

def read_encoder(board_num, motor):
	if (board_num == 0x80):
		ser = ser_x80
	else:
		ser = ser_x81
		
	if ((board_num > 0x87) or (board_num < 0x80)):
		print "Roboclaw board number is out of the scope of possible addresses."
		return param_vars.e_code
	if ((motor != 0) and (motor != 1)):
		print "Please select motor 0 or 1. Yes, I know the boards say 1 and 2. Yes, I know that doesn't make any sense."
		return param_vars.e_code

	command = (30 - param_vars.motor_min + motor)  # In case I decide to go with a 1-2 schema.
	
	data = [] # Declared before doing the serial just in case it would mess up timing otherwise.
	ser.write(chr(board_num))  # Write a command to read motor speed, 32 bit resolution. 
	ser.write(chr(command))	   # See roboclaw documentation for further detail

	#Since the serial data is kind of touchy, we NEED to implement a mutex flag for accessing the roboc1law: otherwise, our data will get corrupted and we won't be able to command the motors as we need to.

	for i in range(6):
		data.append(ser.read())


	speed = (data[0].encode("hex")) + (data[1].encode("hex")) + (data[2].encode("hex")) + (data[3].encode("hex"))
	#print speed ## Hex value
	speed = int(speed, 16)

	if ((ord(data[4]) == 1) and (speed != 0)):
		speed = ~(0xffffffff - speed) + 1
	# print speed #Signed ticks/125th seconde value
	rotations_per_second = float(speed) * 125 / 8192 # *125/8192 --> resolution in 125ths of a second, and then (apparently) 8192 ticks per rotation.
	return rotations_per_second
	
server.register_function(read_encoder, 'read_encoder')

#######################

def stop():
	stop_1 = [0x80, 35, 0, 0, 0, 0, 0x23]
	stop_2 = [0x80, 36, 0, 0, 0, 0, 0x24]
	stop_3 = [0x81, 35, 0, 0, 0, 0, 0x24]
	stop_4 = [0x81, 36, 0, 0, 0, 0, 0x25]
	for i in range(len(stop_1)):
		ser_x80.write(chr(stop_1[i]))	
	for i in range(len(stop_2)):
		ser_x80.write(chr(stop_2[i]))	

	#ser_x81.write(chr(stop_3[i]))	
	for i in range(len(stop_4)):
		ser_x81.write(chr(stop_4[i]))	
	return 0
	
server.register_function(stop, 'stop')

#######################

def p_control(s_command1, s_command2, s_command3, rps_d1, rps_d2, rps_d3, k1, k2, k3):
	start_time = time()
	rotations_per_second1 = read_speed(1) 	
	rotations_per_second2 = read_speed(2)
	rotations_per_second3 = read_speed(3)
	
	diff1 = abs(rps_d1 - rotations_per_second1)
	diff2 = abs(rps_d2 - rotations_per_second2)
	diff3 = abs(rps_d3 - rotations_per_second3)
	
	if (diff1 > diff2 and diff1 > diff3):
		# Change speed 1
		change_speed(1, s_command1)
		if (diff2 > diff3):
			# Change speed 2
			# Change speed 3
			change_speed(2, s_command2)
			change_speed(3, s_command3)
		else:
			#Change speed 3
			#Change speed 2
			change_speed(3, s_command3)
			change_speed(2, s_command2)
	elif (diff2 > diff3 and diff2 > diff1):
		#Change speed 2
		change_speed(2, s_command2)
		if (diff1 > diff3):
			#change speed 1
			#change speed 3
			change_speed(1, s_command1)
			change_speed(3, s_command3)
		else:
			#change speed 3
			#change speed 1
			change_speed(3, s_command3)
			change_speed(1, s_command1)
	elif (diff3 > diff1 and diff3 > diff2):
		#Change speed 3
		change_speed(3, s_command3)
		if (diff1 > diff2):
			#Change speed 1
			#Change speed 2
			change_speed(1, s_command1)
			change_speed(2, s_command2)
		else:
			#Change speed 2
			#Change speed 1
			change_speed(2, s_command2)
			change_speed(1, s_command1)
	
	count = 0
	mdiff_1 = abs(float(int(rps_d1)) * 125/8192)
	mdiff_2 = abs(float(int(rps_d2)) * 125/8192)
	mdiff_3 = abs(float(int(rps_d3)) * 125/8192)  #Maximum differences between speed desired and actual speed
	print mdiff_1
	print mdiff_2
	print mdiff_3
	while((count < 10) and ((abs(diff1) > mdiff_1) or (abs(diff2) > mdiff_2) or (abs(diff3) > mdiff_3))):
		count = count + 1
		sleep(0.15)  #Kind of arbitrary
		rotations_per_second1 = read_speed(1) 	
		rotations_per_second2 = read_speed(2)
		rotations_per_second3 = read_speed(3)
	
		diff1 = rps_d1 - rotations_per_second1
		diff2 = rps_d2 - rotations_per_second2
		diff3 = rps_d3 - rotations_per_second3  # Differences for the proportional loop
#		print diff1
#		print diff2
#		print diff3
#		print "****************"
		
		s_command1 = s_command1 + k1 * diff1
		s_command2 = s_command2 + k2 * diff2
		s_command3 = s_command3 + k3 * diff3
		
		change_speed(1, s_command1)
		change_speed(2, s_command2)
		change_speed(3, s_command3)
	stop_time = time()
	time_elapsed = stop_time - start_time
	return time_elapsed
		
			
def change_speed(motor_num, speed):
	speed = int(speed)
	if (motor_num == 1):
		board_num = 0x80
		command = 35
		serial = ser_x80
	elif (motor_num == 2):
		board_num = 0x81
		command = 36
		serial = ser_x81
	elif (motor_num == 3):
		board_num = 0x80
		command = 36
		serial = ser_x80
	else:
		print "Not a possibility."
		
	speed_byte3 = speed & 0xff  #Least significant bit
	speed = speed >> 8
	speed_byte2 = speed & 0xff
	speed = speed >> 8
	speed_byte1 = speed & 0xff
	speed = speed >> 8
	speed_byte0 = speed & 0xff  # Most significant bit

	checksum = (board_num + command + speed_byte0 + speed_byte1 + speed_byte2 + speed_byte3) & 0x7f
	cmdList = [board_num, command, speed_byte0, speed_byte1, speed_byte2, speed_byte3, checksum]
	for i in range(len(cmdList)):
		serial.write(chr(cmdList[i]))
#		print cmdList[i]
	return 0;


def read_speed(motor_num):
	if (motor_num == 1):
		board_num = 0x80
		command = 30
		serial = ser_x80
	elif (motor_num == 2):
		board_num = 0x81
		command = 30
		serial = ser_x81
	elif (motor_num == 3):
		board_num = 0x80
		command = 31  ## OK, this is seriously a major WTF here. I need to see if the board is wired wrong or something.
		serial = ser_x80
	data = []
	serial.write(chr(board_num))
	serial.write(chr(command)) 
	for i in range(6):
		data.append(serial.read())


	speed = (data[0].encode("hex")) + (data[1].encode("hex")) + (data[2].encode("hex")) + (data[3].encode("hex"))
	speed = int(speed, 16)
	if ((ord(data[4]) == 1) and (speed != 0)):
		speed = ~(0xffffffff - speed) + 1
	rotations_per_second = float(speed) * 125 / 8192 	
	return rotations_per_second
	
server.register_function(p_control)

###################################

def spin(time, bogo):
	time_passed = p_control(start_const, start_const, start_const, 3, 3, 3, k_const, k_const, k_const)
	sleep(time - time_passed)
	print read_speed(1)
	print read_speed(2)
	print read_speed(3)
	stop()
	return 0
	
server.register_function(spin)

###################################

def square(side_length):  # In feet
	sleep_time = (side_length * 0.3048) / 0.15 ## Assuming driving 0.15 m/s
	time_passed = p_control(start_const * 2, -1*start_const, -1*start_const, 1.1423, -0.57, -0.57, k_const, k_const, k_const)  # 0.15 m/s in X
	sleep(sleep_time - time_passed)
	time_passed = p_control(0, start_const*1.5, start_const*-1.5, 0, 0.98, -0.98, k_const, k_const, k_const)  # 0.15 m/s in X
	sleep(sleep_time - time_passed)
	time_passed = p_control(start_const * -2, start_const, start_const, -1.1423, 0.57, 0.57, k_const, k_const, k_const)  # 0.15 m/s in X
	sleep(sleep_time - time_passed)
	time_passed = p_control(0, start_const*-1.5, start_const*1.5, 0, -0.98, 0.98, k_const, k_const, k_const)  # 0.15 m/s in X
	sleep(sleep_time - time_passed)
	stop()
	return 0

server.register_function(square)

###################################

def drive_forward(distance):  ## at 15 cm/sec
	time = float(distance) * 0.3048 / 0.19 * 0.75
	#time_passed = p_control(2*start_const, -1 * start_const, -1 *start_const, 1.14, -0.57, -0.57, k_const, k_const, k_const)
	change_speed(1, -80000)
	change_speed(2, 68000)
	sleep(time)
	stop()

server.register_function(drive_forward)

##################################

def rotate_one_sixth(): ## Left

	time_final = 1 # Designed for a rotation of 1/6th circle/sec
	mult = 0.5
	time_p = p_control(start_const * mult, start_const * mult, start_const * mult, 0.2941, 0.2941, 0.2941, k_const, k_const, k_const)  ## Primed for 20 degrees/sec rotation
	stop()
	return 0

server.register_function(rotate_one_sixth)

##################################

def rotate_one_sixth_dir(direction):
#Left = 0, right = 1
#Right is positive
	time_final = 1
	mult = 0.5
	if (direction == 0):
		time_p = p_control(start_const * mult * -1,  start_const * mult * -1, start_const * mult * -1, -0.2941, -0.2941, -0.2941, k_const, k_const, k_const)
		stop()
		return 0
	else:
		time_p = p_control(start_const * mult,  start_const * mult, start_const * mult, 0.2941, 0.2941, 0.2941, k_const, k_const, k_const)
		stop()
		return 0

server.register_function(rotate_one_sixth_dir)
	
##################################

def rotate_degrees(degrees):
	if (degrees > 0):
		time_final = degrees/20
		time_p = p_control(start_const / 2, start_const /2, start_const / 2, 0.1485, 0.1485, 0.1485, k_const, k_const, k_const)  ## Primed for 20 degrees/sec rotation
		sleep (time_final - time_p)
		stop()
	else:
		time_final = degrees / -20
		time_p = p_control(start_const / -2, start_const /-2, start_const / -2, -0.1485, -0.1485, -0.1485, k_const, k_const, k_const)
		sleep (time_final - time_p)
		stop()

server.register_function(rotate_degrees)

###################################

# Run the server's main loop
server.serve_forever()
