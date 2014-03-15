//motor_controls.h

//This file is purposely crippled to not be plug-and-play. It requires the file parameters.h, which defines constants, motor_command struct, and includes libraries such as queue, list, opencv, pthread, and iostream. 

//Additionally, two structures are needed for this .h file to work: queue<motor_command*> command_queue and vector<motor_command*> finished_vector. 
//The rationale for not putting these two data structures in is to prevent accidental use of this file more than once in the robot structure. Since this file is used to control UART serial transactions, it is imperative that no more than one serial command is given over the UART at a time. By deliberately making this file unusable by default, I prevent accidental contention for the UART via this file. This is the poor man's (/busy college student's) way of providing a resource lock as it pertains to this file. 

int PID = 1;
int run_flag = STOPPED;
int dont_add = ADD;

void *run_queue(void *threadid);

double run_python(motor_command *command);

int add_to_queue(motor_command* toAdd);

double check_completion(int PID);

int move_xyw(double x_d, double y_d, double theta_d);

int P_loop_command(int roboclaw_command_data1, int roboclaw_command_data2, int roboclaw_command_data3, double rps_d1, double rps_d2, double rps_d3, int k1, int k2, int k3); //k1, k2, and k3 are the proportional gains of the respective motors P controllers.

int read_speed_1();

int read_speed_2();

int read_speed_3();

int read_speed_1(){
	motor_command get_speed;
	get_speed.action = READ;
	get_speed.motor_num = 0;
	get_speed.board_address = 0x80;
	int PID = add_to_queue(&get_speed);
	return PID;
}

int read_speed_2(){
	motor_command get_speed;
	get_speed.action = READ;
	get_speed.motor_num = 1;
	get_speed.board_address = 0x80;
	int PID = add_to_queue(&get_speed);
	return PID;
}

int read_speed_3(){
	motor_command get_speed;
	get_speed.action = READ;
	get_speed.motor_num = 0;
	get_speed.board_address = 0x81;
	int PID = add_to_queue(&get_speed);
	return PID;
}


/*********************************************/

int move_xyw(double x_d, double y_d, double theta_d){
	double M_array[] = {1,2,3,4,5,6,7,8,9};
	if (sizeof(M_array)/sizeof(double) == 9){
		cv::Mat M(3,3,CV_64FC1, &M_array); //This will eventually be hard-coded and initialized once. 
		cv::Mat desired_motion = (cv::Mat_<double>(3,1) << x_d, y_d, theta_d); //Initialization of matrix
		cv::Mat rps_Motors(3,1,CV_64FC1);
		rps_Motors = M * desired_motion;
		double rps_1 = rps_Motors.at<double>(1,1);
		double rps_2 = rps_Motors.at<double>(2,1);
		double rps_3 = rps_Motors.at<double>(3,1);
		int commanded_1 = QUADRATIC_1 * rps_1 * rps_1 + LINEAR_1 * rps_1 + CONSTANT_1;
		int commanded_2 = QUADRATIC_2 * rps_2 * rps_2 + LINEAR_2 * rps_2 + CONSTANT_2;
		int commanded_3 = QUADRATIC_3 * rps_3 * rps_3 + LINEAR_3 * rps_3 + CONSTANT_3;
		
		int k1 = 1;
		int k2 = 1;
		int k3 = 1;
		
	/*	add_to_queue(0x80, 0, commanded_1);
		add_to_queue(0x80, 1, commanded_2);
		add_to_queue(0x81, 0, commanded_3);*/
		int success = P_loop_command(commanded_1, commanded_2, commanded_3, rps_1, rps_2, rps_3, k1, k2, k3);
		return success;
	}
	else{
		cout << "M_array is the wrong size." << endl;
	}
	return 0;
}

/*********************************************/

int P_loop_command(int roboclaw_command_data1, int roboclaw_command_data2, int roboclaw_command_data3, double rps_d1, double rps_d2, double rps_d3, int k1, int k2, int k3){

//Need to have a lock on the motor_command queue. 
//This command is used exclusively to drive all three motors. It should change the speed on the one with the highest speed differential first, then move on to the others. 

	dont_add = DONT_ADD;
	
	motor_command toAdd;
	toAdd.action = P_CONTROLLER; //Lets everything that was on the queue before this be completed.
	add_to_queue(&toAdd); // This has a special flag. Once the queue comes to the P_controller struct, then it will break and let this run.
	
	while (run_flag == RUNNING){ //I can't run yet because it will cause contention on the serial bus.
					//However, dont_add will prevent any new commands from restarting the queue once it stops.
		usleep(500); //Sleep for (n) microseconds. One command is about 150usec in serial time. 
	}
	//Then start the p_control.py script.
	
	/*************************************/
	
	Py_Initialize();  //Initialize the python interpreter
	
			/***Vars set up*****/
	PyObject *pName, *pModule, *pDict, *pFunc;

	string pyName, pyFunc; //Declaration of the string and int
	
	pyName = CONTROLLER_FILE;
	pyFunc = P_CONTROL_FUNC;
	
	PyRun_SimpleString("import sys");  //Set the path for the python libraries
	PyRun_SimpleString("sys.path.append(\".\")");
	
			/***Set path and import module and function*****/
	pName = PyString_FromString(pyName.c_str()); 
	pModule = PyImport_Import(pName); // Import the file into the interpreter
	Py_INCREF(pModule); //Save on python stack
	
	if (pModule == NULL){ //Error checking
		printf("pModule is Null\n");
		//return ERRORNO;
	}

	pDict = PyModule_GetDict(pModule); //Get list of functions
	Py_INCREF(pDict); //Save on python stack
	
	if (pDict == NULL){
		printf("pDict is Null\n");
		//return ERRORNO;
	}
	pFunc = PyDict_GetItemString(pDict, pyFunc.c_str());  // Load the function from the file
	if (pFunc == NULL){
		printf("pFunc is Null\n");
		return ERRORNO;
	}
	Py_INCREF(pFunc); //Save on python stack

	PyObject* args;
			/***Create the arg string*****/
	args = PyTuple_Pack(9, PyInt_FromLong(roboclaw_command_data1),
			PyInt_FromLong(roboclaw_command_data2),
			PyInt_FromLong(roboclaw_command_data3),
			PyFloat_FromDouble(rps_d1),
			PyFloat_FromDouble(rps_d2),
			PyFloat_FromDouble(rps_d3),
			PyInt_FromLong(k1),
			PyInt_FromLong(k2),
			PyInt_FromLong(k3));				
		//	def p_controller(s_command1, s_command2, s_command3, rps_d1, rps_d2, rps_d3, k1, k2, k3):

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
	//double result = ERRORNO;
	if (myResult != NULL){
	//	result = PyFloat_AsDouble(myResult);  //If no error, get value from the encoders. 
		Py_DECREF(myResult);
		//command->result = result;
	}

			/***Dereference python vars*****/
	Py_DECREF(pModule); //Dereference all python variables.
	Py_DECREF(pDict);
	Py_DECREF(pFunc);
	Py_DECREF(args);
	
	Py_Finalize();
	
	toAdd.action = P_FINISHED; //Lets everything that was on the queue before this be completed.
	add_to_queue(&toAdd); // This has a special flag. Once the queue comes to the P_controller struct, then it will break and let this run.
	
	/************************************/

	//Go back and start the thread to run any commands that I've built up on the queue while doing the P controller for the motors. 
	//dont_add = ADD;
	//pthread_t thread;
	//int rc;
	//cout << "P_loop_speed() : Creating the run_queue thread." << endl;
	//rc = pthread_create(&thread, NULL, run_queue, (void *)0);
/*	if (rc){
		cout << "Error: Unable to create the run_queue thread." << endl;
		exit(-1);
	}*/
	
	return 0;
}

start(){
//Starts the pthread, which I want to continue running. Must be run at beginning.
	if(run_flag == STOPPED){  //Don't start it twice.
		run_flag = RUNNING;
		pthread_t thread;
		int rc;
		cout << "add_to_queue() : Creating the run_queue thread." << endl;
		rc = pthread_create(&thread, NULL, run_queue, (void *)0);
		if (rc){
			cout << "Error: Unable to create the run_queue thread." << endl;
			exit(-1);
		}
	}
}

/********************************************/
int add_to_queue(motor_command* toAdd){
	if (run_flag == STOPPED){
		start();
	}
	toAdd->PID = PID;
	toAdd->result = ERRORNO; //Defaults to the error code for reporting completion purposes. 
	command_queue.push(toAdd);
	return PID++;
//	if (run_flag == STOPPED && dont_add == ADD){ // The thread only starts running if I don't have the higher priority
																// P_loop_speed running.
	//	run_flag = RUNNING; //Semaphore for the serial controller, should be reset at END of run_queue.
		//Run the run_queue as a separate thread.
		//I did this so that I can add things to the queue and then go on with my life. If I were to call run_queue as a normal function call, I would have to wait for it to complete before calling it again. This lets me not get hung up on calling the function and waiting for the hardware. Now I can add_to_queue, go on, compute the next serial call, add that to the queue, check back in if the first one is completed, and go on my merry way while the run thread does its business. 
		/*******************************/
		/*		pthread_t thread;
				int rc;
				cout << "add_to_queue() : Creating the run_queue thread." << endl;
				rc = pthread_create(&thread, NULL, run_queue, (void *)0);
				if (rc){
					cout << "Error: Unable to create the run_queue thread." << endl;
					exit(-1);
				}*/
		/*****************************************/
	//}
	//Then call run_queue? I'll have to make sure it's not already running is the thing. 
}

/********************************************/

void *run_queue(void *threadid){ //Threaded run function that allows me to add on other serial commands to the end of the queue and continue with my business. 

	double result;
	while(1){
		while (command_queue.size() != 0){  //CHECK HERE that the queue is getting its size changed dynamically.
			motor_command* next = (motor_command*) command_queue.front();
			command_queue.pop(); // Since someone thought that front and pop should do two completely separate things in the C++ queue.
			if (next->action == P_CONTROLLER){
				//break; // I don't need to add this to the finished vector. It is here to stop the queue, it doesn't need to be remembered.
				run_flag = STOPPED; // Let the P_controller know that it's its turn now.
				while( (motor_command*) command_queue.front()->action != P_FINISHED){
					usleep(2000);
				}
				command_queue.pop(); //Take the finished command off the queue to resume normal execution.
				continue;
			}
			result = run_python(next);  //Result is also put in next.result field
			finished_vector.push_back(next);  //Add the structure to the finished vector, so that completion can be checked and then the structure erased.
		}
		usleep(10000); //Sleep 10ms, waiting for new commands.
	}
		//run_flag = STOPPED;  //Tells the program that it's finished its queue.
	return NULL;
}


/********************************************/

double check_completion(int PID){
	motor_command* match;
	match->PID = ERRORNO;
	for (unsigned i = 0; i < finished_vector.size(); i++){
		if (finished_vector.at(i)->PID == PID){
			match = finished_vector.at(i); //Get the struct matching the PID
			if (match->result == ERRORNO){
				//printf("The serial command has not completed yet.");
				return ERRORNO; //Don't want to remove it yet. 
			}
			finished_vector.erase(finished_vector.begin() + i); //Don't need to keep old data.
			break;
		}
	}
	if (match->PID == ERRORNO){
		return ERRORNO;
	}else{
		return match->result;
	}
	return ERRORNO;
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


