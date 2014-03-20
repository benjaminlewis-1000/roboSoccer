// robot_drive_test.cpp
#include "parameters.h"

using namespace std;

queue<motor_command*> command_queue;
vector<motor_command*> finished_vector;

#include "motor_controls.h"  //This file will not work without the command_queue and finished_vector. This is by design so that I don't accidentally have two command vectors for the UART.

int main(int argc, char** argv){
	int PID1 = read_speed_1();
	int PID2 = read_speed_2();
	int PID3 = read_speed_3();
	double s1 = check_completion(PID1);
	double s2 = check_completion(PID2);
	double s3 = check_completion(PID3);
	cout << "Speed 1 (0) is " << s1 << " Speed 2 (0) is " << s2 << " Speed 3 (0) is " << s3 << "." << endl;
	cout << "Rotating..." << endl;
	usleep(1000000); //A second
	int success = move_xyw(0, 0, 0.5);
	cout << "Success? (=0) = " << success << endl;
	PID1 = read_speed_1();
	PID2 = read_speed_2();
	PID3 = read_speed_3();
	s1 = check_completion(PID1);
	s2 = check_completion(PID2);
	s3 = check_completion(PID3);
	cout << "Speed 1 (rotate) is " << s1 << " Speed 2 (rotate) is " << s2 << " Speed 3 (rotate) is " << s3 << "." << endl;
	usleep(1000000); //A second
}
