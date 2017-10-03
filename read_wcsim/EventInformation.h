#ifndef Event_Information
#define Event_Information 1

#include <string>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include "TVector3.h"

// Set this to 1 if you want the functions to log their progress (to figure out where an error is occurring)
#define VERBOSE 0
using namespace std;

void out_log(string message){
  // Simple function to output a message to cout if VERBOSE is set to 1 in EventInformation.h
  #if VERBOSE
  cout << message << endl;
  #endif
}

//Data structure for event
struct EventInformation {
  // Vertex information
  TVector3 true_vertex;
  TVector3 true_direction;
  TVector3 vertex;
  TVector3 direction;
  
  int particle_id; // True PID
  float energy; // True initial energy
  
  // fiTQun information
  //bool worked_fiTQun; // fiTQun predicted the correct PID
  //float nllcut_fiTQun; // Relative negative log likelihood of muon to electron
  //float nll_e; // Electron negative log likelihood

  // Values resulting from image processing 
  int data_set; // Data_set number for this event
  float dist_to_wall; // Distance from 'vertex' to detector wall along 'direction'
  float radius; // Distance from 'vertex' to image centre along 'direction'
  float image_width; // Width of the image in 3D space (cm)
  // Orthogonal axes of the image plane
  TVector3 phi_vec;
  TVector3 theta_vec;
};

string json_bool(string name, bool val);
string json_string(string name, int num);
string json_string(string name, float num);
string json_string(string name, TVector3 vec);
void print_struct(ofstream &file, EventInformation* evt_info);


void print_struct(ofstream &file, EventInformation* evt_info){
  // Print all the variables saved in evt_info to a .txt output file in JSON string format
  out_log("Printing Information to File");

  file << "{"; // Opening brace
  // Print each entry with a ", " separator
  file << json_string("true_vertex", evt_info->true_vertex) << ", ";
  file << json_string("true_direction", evt_info->true_direction) << ", ";
  //file << json_string("vertex", evt_info->vertex) << ", ";
  //file << json_string("direction", evt_info->direction) << ", ";
  file << json_string("particle_id", evt_info->particle_id) << ", ";
  //file << json_bool("worked_fiTQun", evt_info->worked_fiTQun) << ", ";
  //file << json_string("nllcut_fiTQun", evt_info->nllcut_fiTQun) << ", ";
  //file << json_string("nll_e", evt_info->nll_e) << ", ";
  file << json_string("energy", evt_info->energy) << ", ";
  file << json_string("data_set", evt_info->data_set) << ", ";
  file << json_string("dist_to_wall", evt_info->dist_to_wall) << ", ";
  file << json_string("radius", evt_info->radius) << ", ";
  file << json_string("image_width", evt_info->image_width) << ", ";
  file << json_string("phi_vec", evt_info->phi_vec) << ", ";
  file << json_string("theta_vec", evt_info->theta_vec) << "}" << endl;
  // Closing brace before endl

  out_log("Information Printed");
}

string json_bool(string name, bool val){
  // JSON entry for a boolean value
  out_log(string("Printing: ") + name);
  
  stringstream ss;
  ss << "\"" << name << "\": " << ((val)? "true": "false");
  return ss.str();
}

string json_string(string name, int num){
  // JSON entry for an integer value
  out_log(string("Printing: ") + name);
  
  stringstream ss;
  ss << "\"" << name << "\": " << num;
  return ss.str();
}

string json_string(string name, float num){
  // JSON entry for a floating-point value
  out_log(string("Printing: ") + name);
  
  stringstream ss;
  ss << "\"" << name << "\": " << num;
  return ss.str();
}

string json_string(string name, TVector3 vec){
  // JSON entry for a TVector3 value
  out_log(string("Printing: ") + name);
  
  stringstream ss;
  ss << "\"" << name << "\": [" << vec.X() << ", " << vec.Y() << ", " << vec.Z() << "]";
  return ss.str();
}

#endif
