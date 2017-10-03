#ifndef Header
#define Header 1

#include <iostream>
#include <cstdio>
#include "TMinuit.h"
#include "TFile.h"
#include "TTree.h"
#include "TEfficiency.h"
#include "TH2.h"
#include <cmath>
#include <vector>
#include <utility>

//#define DATA_SIZE 11146
#define NUM_PIXELS 30
#define PHOTONS_PER_PMT 20
#define PMT_DIAM 70.0
#define PI 3.1415926535897932384
#define NUM_TALL 51
#define NUM_AROUND 150
#define CYLINDER_RADIUS 1690.0
#define CAP_HEIGHT 1810.0
#define ATTENUATION_LENGHT = 7496.46
#define DEFAULT_RADIUS 1453.38
#define REQ_ADJACENT 2
#define CERENKOV_ANGLE 0.6981317008
#define PMT_THRESHOLD 0.0001

bool passed_cut(int num_tubes, double *vertex){
    // If at least 2m from wall and over 160 PMTs hit
    if (num_tubes > 160 && in_cylinder(vertex, 200.0)) return true;
    else return false;
}

double dist_to_wall(double *vertex, double *direction){
    // Calculate the distance of the vertex to the cylinder walls, in the 'direction' direction.
    // User should check that the vertex is inside cylinder before calling thos function.
    
    // dist_cylinder = (sqrt(pow(direction.X()*vertex.X() + direction.Y()*vertex.Y(), 2) - (pow(direction.X(), 2) + pow(direction.Y(), 2))*(pow(vertex.X(), 2) + pow(vertex.Y(), 2) - pow(CYLINDER_RADIUS, 2))) - (direction.X()*vertex.X() + direction.Y()*vertex.Y()))/(pow(direction.X(), 2) + pow(direction.Y(), 2));
    // dist_cap = (direction.Z()/abs(direction.Z())*CAP_HEIGHT-vertex.Z())/direction.Z();
    
    double dist_cylinder = (sqrt(pow(direction[0]*vertex[0] + direction[1]*vertex[1], 2) - (pow(direction[0], 2) + pow(direction[1], 2))*(pow(vertex[0], 2) + pow(vertex[1], 2) - pow(CYLINDER_RADIUS, 2))) - (direction[0]*vertex[0] + direction[1]*vertex[1]))/(pow(direction[0], 2) + pow(direction[1], 2));

    double dist_cap = (direction[2]/abs(direction[2])*CAP_HEIGHT-vertex[2])/direction[2];
    
    // Return whichever distance is smaller, since particle is enclosed by both shapes
    return min(dist_cylinder, dist_cap);

}

bool in_cylinder(double *vertex, double dist){
    // Check if the vertex is inside the detector cylinder, with an optional cut length off the sides
    // out_log("Checking if vertex is in cylinder");
    
    /*if (vertex.Z() > cut - CAP_HEIGHT && vertex.Z() < CAP_HEIGHT - cut){
        if (sqrt(pow(vertex.X(), 2) + pow(vertex.Y(), 2)) < CYLINDER_RADIUS - cut){
            return true;
        }
    }*/
    
    if (vertex[2] > (dist - CAP_HEIGHT) && vertex[2] < (CAP_HEIGHT - dist)){
        if (sqrt(pow(vertex[0], 2) + pow(vertex[1], 2)) < CYLINDER_RADIUS - dist){
            return true;
        }
    }
    return false;
}


