#ifndef SERIAL_CPP
#define SERIAL_CPP

#include "parameters.h"
#include <queue>
#include <list>
#include <pthread.h>

#define NUM_THREADS 4

using namespace std;

queue<motor_command> command_queue;
vector<motor_command> finished_vector;

void *run_queue(void *threadid);

double run_python(motor_command *command);

int add_to_queue(motor_command toAdd);

double check_completion(int PID);

int PID = 1;
int run_flag = STOPPED;

int main(int argc, char** argv){
//Test structure
	motor_command next;
	next.action = DRIVE;
	next.motor_num = 0;
	next.speed = 2000;
	next.board_address = 0x80;
	add_to_queue(next) ;
	add_to_queue(next) ;
	add_to_queue(next) ;
	add_to_queue(next) ;
	sleep(5);
	add_to_queue(next) ;
	add_to_queue(next) ; 
	cout << check_completion(1) << endl;

	sleep(5);


	cout << "Exiting main thread." << endl; //Shouldn't ever get here. 
}

/********************************************/
int add_to_queue(motor_command toAdd){
	toAdd.PID = PID;
	toAdd.result = ERRORNO; //Defaults to the error code for reporting completion purposes. 
	command_queue.push(toAdd);
	if (run_flag == STOPPED){
		run_flag = RUNNING; //Semaphore for the serial controller, should be reset at END of run_queue.
		//Run the run_queue as a separate thread.
		//I did this so that I can add things to the queue and then go on with my life. If I were to call run_queue as a normal function call, I would have to wait for it to complete before calling it again. This lets me not get hung up on calling the function and waiting for the hardware. Now I can add_to_queue, go on, compute the next serial call, add that to the queue, check back in if the first one is completed, and go on my merry way while the run thread does its business. 
		/*******************************/
				pthread_t thread;
				int rc;
				cout << "add_to_queue() : Creating the run_queue thread." << endl;
				rc = pthread_create(&thread, NULL, run_queue, (void *)0);
				if (rc){
					cout << "Error: Unable to create the run_queue thread." << endl;
					exit(-1);
				}
		/****************************************/
	}
	//Then call run_queue? I'll have to make sure it's not already running is the thing. 
	return PID++;
}

/********************************************/

double check_completion(int PID){
	motor_command match;
	match.PID = ERRORNO;
	for (unsigned i = 0; i < finished_vector.size(); i++){
		if (finished_vector.at(i).PID == PID){
			match = finished_vector.at(i); //Get the struct matching the PID
			if (match.result == ERRORNO){
				//printf("The serial command has not completed yet.");
				return ERRORNO; //Don't want to remove it yet. 
			}
			finished_vector.erase(finished_vector.begin() + i); //Don't need to keep old data.
			break;
		}
	}
	if (match.PID == ERRORNO){
		return ERRORNO;
	}else{
		return match.result;
	}
	return ERRORNO;
}

/********************************************/

void *run_queue(void *threadid){ //Threaded run function that allows me to add on other serial commands to the end of the queue and continue with my business. 
	//timespec sleepValue = {0};
	//Py_Initialize();  //Actually, this is taken care of in run_python
	//sleepValue.tv_nsec = QUEUE_SLEEP * 1000000; //Sleep value of QUEUE_SLEEP ms
	double result;
	//while(1){
		while (command_queue.size() != 0){  //CHECK HERE that the queue is getting its size changed dynamically.
			motor_command next = (motor_command) command_queue.front();
			command_queue.pop(); // Since someone thought that front and pop should do two completely separate things in the C++ queue.
			result = run_python(&next);  //Result is also put in next.result field
			finished_vector.push_back(next);  //Add the structure to the finished vector, so that completion can be checked and then the 
																				//structure erased.
		/*	
cout << result << endl;
cout << "Now what?" << endl;*/
		}
//		nanosleep(&sleepValue, NULL);
//		cout << "Exiting" << endl;
		run_flag = STOPPED;  //Tells the program that it's finished its queue.
//	}
//	pthread_exit(NULL); //If not a pthread...
	return NULL;
}

/********************************************/

double run_python(motor_command *command){
//A routine that will run a python function that is in the same directory, with arguments. This routine is specialized to the files 
// drive_motor.py with a function run_drive(board_num, motor, speed) and read_encoders.py with a function run_enc(board_num, motor).
	
	Py_Initialize();  //Initialize the python interpreter
	
			/***Vars set up*****/
	PyObject *pName, *pModule, *pDict, *pFunc;

	string pyName, pyFunc; //Declaration of the string and int
	int speed;

	if (command->action == READ){  //READ or DRIVE
		pyName = READ_ENC_FILE; //Determining which python module to call
		pyFunc = READ_FUNC;  //These strings all defined in parameters.h
	}else{
		pyName = MOTOR_FILE;
		pyFunc = MOTOR_FUNC;
		speed = command->speed;  //Additionally gets the speed. 
	}
	
	int board_address = command->board_address;
	int motor = command->motor_num;
	
	
			/***Set path and import module and function*****/
	PyRun_SimpleString("import sys");  //Set the path for the python libraries
	PyRun_SimpleString("sys.path.append(\".\")");
	
	pName = PyString_FromString(pyName.c_str()); //Convert to python object string (name of file)
	pModule = PyImport_Import(pName); // Import the file into the interpreter
	Py_INCREF(pModule); //Save on python stack
	
	if (pModule == NULL){ //Error checking
		printf("pModule is Null\n");
		return ERRORNO;
	}

	pDict = PyModule_GetDict(pModule); //Get list of functions
	Py_INCREF(pDict); //Save on python stack
	
	if (pDict == NULL){
		printf("pDict is Null\n");
		return ERRORNO;
	}
	pFunc = PyDict_GetItemString(pDict, pyFunc.c_str());  // Load the function from the file
	if (pFunc == NULL){
		printf("pFunc is Null\n");
		return ERRORNO;
	}
	Py_INCREF(pFunc); //Save on python stack

	PyObject* args;
	
			/***Create the arg string*****/

	if(command->action == READ){
		args = PyTuple_Pack(2,PyInt_FromLong(board_address),PyInt_FromLong(motor)); //Appropriate args for the read_encoders
	}else{ //Action is DRIVE
		args = PyTuple_Pack(3,PyInt_FromLong(board_address),PyInt_FromLong(motor), PyInt_FromLong(speed)); //Appropriate args for the drive_motor
	} 

	if (args == NULL){
		printf("Problem with args.\n");
		return ERRORNO;
	}
	Py_INCREF(args); //Save on python stack
	PyObject* myResult;

			/***Call function and get result*****/
	if (PyCallable_Check(pFunc)){
		myResult = PyObject_CallObject(pFunc, args);  //Call function
		if (myResult != NULL){  //If no error, then save myResult on stack
			Py_INCREF(myResult);
		}
	}else{
		PyErr_Print();
	}

			/***Report the result*****/
	double result = ERRORNO;
	if (myResult != NULL){
		result = PyFloat_AsDouble(myResult);  //If no error, get value from the encoders. 
		Py_DECREF(myResult);
		command->result = result;
	}

			/***Dereference python vars*****/
	Py_DECREF(pModule); //Dereference all python variables.
	Py_DECREF(pDict);
	Py_DECREF(pFunc);
	Py_DECREF(args);
	
	Py_Finalize(); //Close python interpreter -- this could be a very bad idea (Actually, it seems to work.
	return result;
}

/********************************************/










#endif





//Junk that didn't work
//Oops - I mean, deprecated code.


/*Py_Initialize();

	PyObject *sys_path, *path;

	PyRun_SimpleString("import sys");
	PyRun_SimpleString("sys.path.append(\".\")");

	string pyName; //Declaration of the string and int
	int speed;
	if (command.action == READ){
		pyName = "read_encoders"; //Determining which python module to call
	}else{
		pyName = "drive_motor";
		speed = command.speed;  //Additionally gets the speed. 
	}

	cout << "I got here 1" << endl;
	int board_address = command.board_address;
	int motor = command.motor_num;
	cout << "I got here 2" << endl;

	//PyObject* moduleName = PyString_FromString(pyName.c_str()); //converts the pyName to a C++ string, then import that module into the Python interpreter
//	Py_INCREF(myModule);
	cout << "I got here 2.1" << endl;

	cout << "I got here 2.2" << endl;
	//PyObject* myFunction = PyObject_GetAttrString(myModule, "run"); //Both of these python functions have the function 'run'.

	cout << "I got here 3" << endl;
	PyObject* args;
	if(command.action == READ){
		args = PyTuple_Pack(2,PyInt_FromLong(board_address),PyInt_FromLong(motor)); //Appropriate args for the read_encoders
	}else{
		args = PyTuple_Pack(3,PyInt_FromLong(board_address),PyInt_FromLong(motor), PyInt_FromLong(speed)); //Appropriate args for the drive_motor
	}
Py_INCREF(args);
	cout << "I got here" << endl;
	PyObject* myModule = PyImport_Import(PyString_FromString("drive_motor"));//Python interface junk
	cout << "args = " << args << " module = " << myModule << endl;
Py_INCREF(myModule);
	PyObject* myResult = PyObject_CallObject(myModule, args); //Run it and store the result in myResult
Py_INCREF(myResult);*/
/*	Py_DECREF(moduleName);
	Py_DECREF(myModule);
	Py_DECREF(myFunction);
	Py_DECREF(args);
*/
	/*double result = PyFloat_AsDouble(myResult);
	Py_DECREF(myResult);
cout << result << endl;
	return result;*/
