#import serial
#import sys

#board_num = sys.argv[1];
#motor = sys.argv[2];

def run_enc(board_num, motor):
	import serial
	import sys
	import param_vars

	#Returns the speed of motor 0 or 1 on a board addressed 0x80 to 0x87
	motor_min = 0
	motor_max = 1 # These are the two acceptable values for motor enumerated values. 
	e_code = -999 # Error code

	try:
		ser = serial.Serial('/dev/ttyPCH1', 38400)
	except:
		print "The serial port /dev/ttyPCH1 is not available."
		sys.exit(e_code)

	try:
		board_num = int(board_num, 0) 
	except:
		print "Invalid address format: Must be a number"
		sys.exit(e_code) 
		# sys.exit is important to use because it will allow the calling processes to continue, if necessary. 	  Also, it won't kill other python processes running on the interpreter. (Kind of important...)
	try:
		motor = int(motor, 0)
	except:
		print "Motor must be either motor 0 or 1. Or possibly one or two..."
		sys.exit(e_code)


	if ((board_num > 0x87) or (board_num < 0x80)):
		print "Roboclaw board number is out of the scope of possible addresses."
		sys.exit(e_code)
	if ((motor != 0) and (motor != 1)):
		print "Please select motor 0 or 1. Yes, I know the boards say 1 and 2. Yes, I know that doesn't make any sense."
		sys.exit(e_code)

	command = (30 - motor_min + motor)  # In case I decide to go with a 1-2 schema.

	data = [] # Declared before doing the serial just in case it would mess up timing otherwise.

	ser.write(chr(board_num))  # Write a command to read motor speed, 32 bit resolution. 
	ser.write(chr(command))	   # See roboclaw documentation for further detail

	#Since the serial data is kind of touchy, we NEED to implement a mutex flag for accessing the roboclaw: otherwise, our data will get corrupted and we won't be able to command the motors as we need to.

#	ser.write(chr(0x80))
#	ser.write(chr(0x1E))
	for i in range(6):
		data.append(ser.read())

	#for i in range(len(data)):
	#	print ord(data[i])

	speed = (data[0].encode("hex")) + (data[1].encode("hex")) + (data[2].encode("hex")) + (data[3].encode("hex"))
	#print speed ## Hex value
	speed = int(speed, 16)

	if ((ord(data[4]) == 1) and (speed != 0)):
		speed = ~(0xffffffff - speed) + 1
	# print speed #Signed ticks/125th seconde value
	rotations_per_second = float(speed) * 125 / 8192 # *125/8192 --> resolution in 125ths of a second, and then (apparently) 8192 ticks per rotation.
	print '\n' + str(rotations_per_second) 
	return rotations_per_second

#print run_enc(sys.argv[1], sys.argv[2])
