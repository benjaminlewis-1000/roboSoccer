#Makefile
CC=g++
CFLAGS=-c -Wall

serial: serial_controller.cpp parameters.h drive_motor.py read_encoders.py
#These are all the files that must be in the directory in order for the serial_controller to work.
	g++ serial_controller.cpp -o serial -Wall -lpthread -lpython2.7 -lopencv_core
# -lpthread : Included for pthreads to work.
# -lpython2.7 : Included for loading python code in a C++ file. (Honestly, I think that the Angstrom compiler just isn't quite figuring out where to find these libraries.
# -lopencv_core: use OpenCV for matrix math


all:  serial_controller.cpp parameters.h

clean: 
	rm -rf serial
	rm *~
