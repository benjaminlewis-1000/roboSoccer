
def p_controller(s_command1, s_command2, s_command3, rps_d1, rps_d2, rps_d3, k1, k2, k3):
	#s_commands are 32 bit 2's complement speeds, rps_d1 is the speeds used to calculate these commands, k's are the k values for the proportional controller.
	import sys
	import serial
	import param_vars
	from time import sleep
	
	try:
		ser = serial.Serial(param_vars.port, param_vars.baud_rate)
	except:
		print "The serial port " + param_vars.port + " is not available."
		sys.exit(param_vars.e_code)
		
# Read each motor
	rotations_per_second1 = read_speed(ser, 1) 	
	rotations_per_second2 = read_speed(ser, 2)
	rotations_per_second3 = read_speed(ser, 3)
	
	diff1 = abs(rps_d1 - rotations_per_second1)
	diff2 = abs(rps_d2 - rotations_per_second2)
	diff3 = abs(rps_d3 - rotations_per_second3)
	
	if (diff1 > diff2 and diff1 > diff3):
		# Change speed 1
		change_speed(ser, 1, s_command1)
		if (diff2 > diff3):
			# Change speed 2
			# Change speed 3
			change_speed(ser, 2, s_command2)
			change_speed(ser, 3, s_command3)
		else:
			#Change speed 3
			#Change speed 2
			change_speed(ser, 3, s_command3)
			change_speed(ser, 2, s_command2)
	elif (diff2 > diff3 and diff2 > diff1):
		#Change speed 2
		change_speed(ser, 2, s_command2)
		if (diff1 > diff3):
			#change speed 1
			#change speed 3
			change_speed(ser, 1, s_command1)
			change_speed(ser, 3, s_command3)
		else:
			#change speed 3
			#change speed 1
			change_speed(ser, 3, s_command3)
			change_speed(ser, 1, s_command1)
	elif (diff3 > diff1 and diff3 > diff2):
		#Change speed 3
		change_speed(ser, 3, s_command3)
		if (diff1 > diff2):
			#Change speed 1
			#Change speed 2
			change_speed(ser, 1, s_command1)
			change_speed(ser, 2, s_command2)
		else:
			#Change speed 2
			#Change speed 1
			change_speed(ser, 2, s_command2)
			change_speed(ser, 1, s_command1)
	
	count = 0
	mdiff_1 = abs(float(int(rps_d1)) * 125/8192)
	mdiff_2 = abs(float(int(rps_d2)) * 125/8192)
	mdiff_3 = abs(float(int(rps_d3)) * 125/8192)  #Maximum differences between speed desired and actual speed
	while((count < 3) and (abs(diff1) > mdiff_1) and (abs(diff2) > mdiff_2) and (abs(diff3) > mdiff3)):
		count = count + 1
		sleep(0.03)  #Kind of arbitrary
		rotations_per_second1 = read_speed(ser, 1) 	
		rotations_per_second2 = read_speed(ser, 2)
		rotations_per_second3 = read_speed(ser, 3)
	
		diff1 = rps_d1 - rotations_per_second1
		diff2 = rps_d2 - rotations_per_second2
		diff3 = rps_d3 - rotations_per_second3  # Differences for the proportional loop
		
		s_command1 = s_command1 + k1 * diff1
		s_command2 = s_command2 + k2 * diff2
		s_command3 = s_command3 + k3 * diff3
		
		change_speed(ser, 1, s_command1)
		change_speed(ser, 2, s_command2)
		change_speed(ser, 3, s_command3)
		
			
def change_speed(serial, motor_num, speed):
	if (motor_num == 1):
		board_num = 0x80
		command = 35
	elif (motor_num == 2):
		board_num = 0x80
		command = 36
	elif (motor_num == 3):
		board_num = 0x81
		command = 35
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


def read_speed(serial, motor_num):
	if (motor_num == 1):
		board_num = 0x80
		command = 30
	elif (motor_num == 2):
		board_num = 0x80
		command = 31
	elif (motor_num == 3):
		board_num = 0x81
		command = 30
	data = []
	serial.write(chr(motor))
	serial.write(chr(command)) # Read motor 1 on board 0x80
	for i in range(6):
		data.append(serial.read())
		
	speed = (data[0].encode("hex")) + (data[1].encode("hex")) + (data[2].encode("hex")) + (data[3].encode("hex"))
	speed = int(speed, 16)
	if ((ord(data[4]) == 1) and (speed != 0)):
		speed = ~(0xffffffff - speed) + 1
	rotations_per_second = float(speed) * 125 / 8192 	
	return rotations_per_second
	
p_controller(1, 1, 2, 2, 3, 3, 4, 5, 5)
			
