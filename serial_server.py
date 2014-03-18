from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import serial
import param_vars
import sys

ser_x80 = serial.Serial(param_vars.port_80, param_vars.baud_rate)
ser_x81 = serial.Serial(param_vars.port_81, param_vars.baud_rate)

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
server = SimpleXMLRPCServer(("localhost", 8000),
                            requestHandler=RequestHandler, logRequests = False, 										 allow_none = True)
   # logRequests = False suppresses all output from the server about date and host location.
   
server.register_introspection_functions()
# Functions such as system.listMethods()


################
def drive_motor(board_num, motor, speed):

	if (int(board_num, 0) == 0x80):
		ser = ser_x80
	else:
		ser = ser_x81
		
	try:
		board_num = int(board_num, 0)
	except:
		print "Invalid address format: Must be a number"
		return param_vars.e_code
	try:
		motor = int(motor, 0)
	except:
		print "Motor must be either motor 0 or 1. Or possibly one or two..."
		return param_vars.e_code
	try:
		speed = int(speed, 0)
	except:
		print "Motor speed must be an integer."
		return param_vars.e_code
		
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
	if (int(board_num, 0) == 0x80):
		ser = ser_x80
	else:
		ser = ser_x81
		
	try:
		board_num = int(board_num, 0) 
	except:
		print "Invalid address format: Must be a number"
		return param_vars.e_code
		# sys.exit is important to use because it will allow the calling processes to continue, if necessary. 	  Also, it won't kill other python processes running on the interpreter. (Kind of important...)
	try:
		motor = int(motor, 0)
	except:
		print "Motor must be either motor 0 or 1. Or possibly one or two..."
		return param_vars.e_code

	if ((board_num > 0x87) or (board_num < 0x80)):
		print "Roboclaw board number is out of the scope of possible addresses."
		return param_vars.e_code
	if ((motor != 0) and (motor != 1)):
		print "Please select motor 0 or 1. Yes, I know the boards say 1 and 2. Yes, I know that doesn't make any sense."
		return param_vars.e_code

	command = (30 - motor_min + motor)  # In case I decide to go with a 1-2 schema.
	
	data = [] # Declared before doing the serial just in case it would mess up timing otherwise.
	ser.write(chr(board_num))  # Write a command to read motor speed, 32 bit resolution. 
	ser.write(chr(command))	   # See roboclaw documentation for further detail

	#Since the serial data is kind of touchy, we NEED to implement a mutex flag for accessing the roboclaw: otherwise, our data will get corrupted and we won't be able to command the motors as we need to.

	for i in range(6):
		data.append(ser.read())

	for i in range(len(data)):
		print ord(data[i])

	speed = (data[0].encode("hex")) + (data[1].encode("hex")) + (data[2].encode("hex")) + (data[3].encode("hex"))
	#print speed ## Hex value
	speed = int(speed, 16)

	if ((ord(data[4]) == 1) and (speed != 0)):
		speed = ~(0xffffffff - speed) + 1
	# print speed #Signed ticks/125th seconde value
	rotations_per_second = float(speed) * 125 / 8192 # *125/8192 --> resolution in 125ths of a second, and then (apparently) 8192 ticks per rotation.
	return rotations_per_second
	
server.register_function(read_encoder, 'read_encoder')

# Run the server's main loop
server.serve_forever()
