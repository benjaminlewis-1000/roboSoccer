//Initialization file for C++

#ifndef PARAMETERS_H
#define PARAMETERS_H

#include <iostream>
#include "opencv2/core/core.hpp"
#include <queue>
#include <list>
#include <unistd.h> // For usleep control
#include <pthread.h>

#define QUEUE_SLEEP 5 //Number of ms for the serial queue to sleep before it checks if there's more to do.

#include </usr/include/python2.7/Python.h> // python2.7 Needed on minnowboard
//#include </usr/include/python2.7/pythonrun.h>

//Actions in motor_command
#define READ 0
#define DRIVE 1
#define P_CONTROLLER 2
#define P_FINISHED 3

#define ERRORNO -999  //Should be a number that I won't be getting back from my encoders.

//Defs for python files and functions
#define READ_ENC_FILE "read_encoders"
#define MOTOR_FILE "drive_motor"
#define CONTROLLER_FILE "p_control"

#define READ_FUNC "run_enc"
#define MOTOR_FUNC "run_drive"
#define P_CONTROL_FUNC "p_controller"

//Defs for whether the run_queue is running or not
#define STOPPED 0
#define RUNNING 1

#define ADD 0
#define DONT_ADD 1


//To be defined, once I can characterize each motor roughly. 
#define QUADRATIC_1 -117.52
#define LINEAR_1 6489
#define CONSTANT_1 654.28
#define QUADRATIC_2 -117.52
#define LINEAR_2 6489
#define CONSTANT_2 654.28
#define QUADRATIC_3 -117.52
#define LINEAR_3 6489
#define CONSTANT_3 654.28


struct motor_command{
	int action;  //Either READ or DRIVE
	int board_address;
	int motor_num;
	int speed;
	int PID;
	double result;
};

#endif
