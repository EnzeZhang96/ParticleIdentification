#ifndef Header
#define Header 1

#include "skheadC.h"
#include "skparmC.h"
#include "geopmtC.h"
#include "sktqC.h"
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
#include "EventInformation.h"

//External Fortran functions
extern"C" {
  void fortinit_(char*, char*, int, int);
  int fortread_();
  void skclosef_(int*);
}

//Constants
#define DATA_SIZE 11146
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
using namespace std;

// Geometry of cap globals
TVector3 pmt_pos[DATA_SIZE];

// Global variables where PMT hits are saved
vector<pair<float, int> > all_charges;
float total_charge;

// fiTQun variables that are loaded from .root file
Int_t num_clusters;
Int_t num_1rclusters;
// First index in the following arrays is the cluster number which has
// index 0 for the correct event, but there can be up to 2 clusters.
Float_t cluster_time[2]; // Time of the PMT hit cluster
Float_t pos[2][3]; // Prefit vertex from fiTQun using only timing information (for each cluster)
Float_t nll_1r[2][7]; // Negative Log Likelihood of each of the seven fiTQun 1-ring fits (for each cluster)
Float_t fqmsnll; // Negative Log Likelihood of the multi-segmented muon fit
Float_t pos_1r[2][7][3]; // Reconstructed vertex for each 1-ring fit (for each cluster)
Float_t dir_1r[2][7][3]; // Reconstructed direction for each 1-ring fit (for each cluster)

//Forward Function Declaration
Bool_t in_cylinder(TVector3 vertex, Double_t cut);
Bool_t apply_cut(TVector3 fit_vertex, int num_pmts);
Double_t dist_wall(TVector3 vertex, TVector3 direction);
Double_t abs_dist_wall(TVector3 vertex);
vector<int> adjacent_pmts(int icab);
void fill_histogram(TVector3 vertex, TVector3 direction, EventInformation* info, TH2F* h);
void print_image(ofstream &file, TH2F* h, int data_set, string particle_1hot);
string get_1hot(int particle_id);

void fill_histogram(TVector3 vertex, TVector3 direction, EventInformation* info, TH2F* h){
  // Performs the conical projection of the PMT data onto a square image
  // Saves some information to the info structure, and output the image into the "h" 2D histogram
  out_log("Begin Filling Image Histogram");

  //Image Characteristics
  Double_t dist_to_wall = dist_wall(vertex, direction); // Distance of vertex to the intercept of particle trajectory with cylinder wall
  Double_t radius = min(DEFAULT_RADIUS, dist_to_wall); // Distance of the vertex to centre of image (always in direction of particle trajectory)
  Double_t min_width = PMT_DIAM*NUM_PIXELS; // Image width where resolution(PMTs) ~ resolution(image pixels)
  Double_t scaled_width = 2*CAP_HEIGHT*radius/DEFAULT_RADIUS; // Image width, scaled with radius, for data_set 1 and 2
  
  // Calculate the width of the image and the integer 'set' number which indicates data_set
  Double_t image_width;
  Int_t set;
  if (radius > 550.) {
    // Use the same (scaled) image size until radius falls below 550cm
    image_width = scaled_width;
    if (scaled_width > min_width){
      // set 1: If the resolution of the PMTs is better than that of the image
      set = 1;
    }
    else {
      // set 2: If the resolution of the PMTs is worse than that of the image
      set = 2;
    }
  }
  else if (radius > 375.) {
    // set 3: For smaller rings, when PMT resolution is sufficiently low compared to ring-size
    float artificial_scale = 1.25;
    // Set image_width so that the resolution(PMTs) ~ resolution(image pixels) for radii at the centre of the set's range.
    // Scale pixels up by factor of $artificial_scale to wrok better with standard filters
    image_width = (min_width/artificial_scale)*radius/((375.+550.)/2.);
    set = 3;
  }
  else {
    // set 4: For even smaller rings
    float artificial_scale = 1.25;
    // Same logic as set 3, but with a smaller radii range (note that radius < 200cm events are cut in the analysis)
    image_width = (min_width/artificial_scale)*radius/((200.+375.)/2.);
    set = 4;
  }
  
  // Set up orthogonal axes to characterize the image plane
  Double_t phi = direction.Phi();
  Double_t theta = direction.Theta();
  TVector3 phi_vec = TVector3(sin(phi), -cos(phi), 0.);
  TVector3 theta_vec = TVector3(-cos(theta)*cos(phi), -cos(theta)*sin(phi), sin(theta));

  // Iterate over the all_charges global variable with each entry corresponding to a single PMT (pair<pmt_charge, pmt_index>)
  out_log("Iterating over PMTs");
  for (vector<pair<float, int> >::iterator it = all_charges.begin(); it != all_charges.end(); ++it){
    TVector3 this_pos = pmt_pos[it->second]; // Get the 3D position of the pmt

    // Set up orthogonal axes in the plane of the detector wall (used for randomizing photons through each PMT)
    TVector3 pmt_x(0., 0., 0.);
    TVector3 pmt_y(0., 0., 0.);
    if (abs(this_pos[2]) < 1800){
      pmt_x = TVector3(this_pos[1], -this_pos[0], 0.).Unit();
      pmt_y = TVector3(0., 0., 1.);
    }
    else if ((int)abs(this_pos[2]) == 1810){
      pmt_x = TVector3(1., 0., 0.);
      pmt_y = TVector3(0., 1., 0.);
    }
    else cout << "ERROR, PMT NOT FOUND" << endl;

    // Set number of photons to generate, default PHOTONS_PER_PMT but three times as many for sets 3 and 4 to get smoother images.
    bool extra_photons = (set == 3 || set == 4);
    int num_photons = PHOTONS_PER_PMT + (int)extra_photons*2*PHOTONS_PER_PMT;

    // Generate photons on surface of the PMT and apply the conical projection to each photon individually.
    for (Int_t photon_num = 0; photon_num < num_photons; ++photon_num){
      // Get random position on surface of (approximately flat and circular) PMT.
      Double_t rad = sqrt((double)rand()/RAND_MAX*pow(PMT_DIAM/2, 2));
      Double_t angle = (double)rand()/RAND_MAX*2*PI;
      // Coordinates of randomized position in plane that is locally parallel to detector wall
      Double_t x_coord = rad*cos(angle);
      Double_t y_coord = rad*sin(angle);

      // Relative vector between the photon intercept with PMT plane and the vertex of the cone
      TVector3 rel_vec = x_coord*pmt_x + y_coord*pmt_y + this_pos - vertex;
      Double_t z = rel_vec.Dot(direction.Unit()); // Distance along the axis of the cone of the photon intercept
      // Find the radial coordinates of the photon intercept (rel. to cone) and transform to get the image coordinates
      //    1) Scale with radius/z to get the conical projection as opposed to a linear projection
      //    2) Scale with 1/(image_width/2) so that the image coordinate go from -1 to 1
      Double_t x = rel_vec.Dot(phi_vec)/(z/radius*image_width/2);   // Image x-position
      Double_t y = rel_vec.Dot(theta_vec)/(z/radius*image_width/2); // Image y-position
      // Fill the 2D histogram at the image coordinates specified, with weights that average the PMT charge over each photon that is projected
      h->Fill(x, y, it->first/num_photons); 
    }
  }
  
  out_log("Image Histogram Filled");

  // Save details of the image processing to the EventInformation object
  info->dist_to_wall = dist_to_wall;
  info->radius = radius;
  info->image_width = image_width;
  info->phi_vec = phi_vec;
  info->theta_vec = theta_vec;
  info->data_set = set;

  
  out_log("Image Information Saved");
}

string get_1hot(int particle_id){
  // Convert the PID to a string, "1, 0" for electron and "0, 1" for muon
  stringstream ss;
  ss << (particle_id == 11? 1: 0) << ", "<< (particle_id == 13? 1: 0);
  return ss.str();
}

Bool_t in_cylinder(TVector3 vertex, Double_t cut){
  // Check if the vertex is inside the detector cylinder, with an optional cut length off the sides
  out_log("Checking if vertex is in cylinder");
  
  if (vertex.Z() > cut - CAP_HEIGHT && vertex.Z() < CAP_HEIGHT - cut){
    if (sqrt(pow(vertex.X(), 2) + pow(vertex.Y(), 2)) < CYLINDER_RADIUS - cut){
      return true;
    }
  }
  return false;
}

Bool_t apply_cut(TVector3 fit_vertex, int num_pmts){
  // The cut used for the analysis. Standard 200cm fiTQun cut with additional cut on num_pmts to remove very near events that slipped passed.
  out_log("Applying the event cut");
  
  if (in_cylinder(fit_vertex, 200.0) && num_pmts > 160){
    return true;
  }
  return false;
}

Double_t dist_wall(TVector3 vertex, TVector3 direction){
  // Calculate the distance of the vertex to the cylinder walls, in the 'direction' direction. 
  // User should check that the vertex is inside cylinder before calling thos function.
  out_log("Calculating distance to the detector wall along trajectory");
  
  
  // Distance to the cylinder extended to \pm infinity
  Double_t dist_cylinder = (sqrt(pow(direction.X()*vertex.X() + direction.Y()*vertex.Y(), 2) - (pow(direction.X(), 2) + pow(direction.Y(), 2))*(pow(vertex.X(), 2) + pow(vertex.Y(), 2) - pow(CYLINDER_RADIUS, 2))) - (direction.X()*vertex.X() + direction.Y()*vertex.Y()))/(pow(direction.X(), 2) + pow(direction.Y(), 2));
  // Distance to caps, planes extended infinitely
  Double_t dist_cap = (direction.Z()/abs(direction.Z())*CAP_HEIGHT-vertex.Z())/direction.Z();
  
  // Return whichever distance is smaller, since particle is enclosed by both shapes
  return min(dist_cylinder, dist_cap);
}

Double_t abs_dist_wall(TVector3 vertex){
  // Calculates the shortest (absolute) distance of the vertex to the cylinder walls
  out_log("Calculating minimal distance to the detector wall");
  
  double dist_cylinder = abs(CYLINDER_RADIUS - sqrt(pow(vertex.X(), 2) + pow(vertex.Y(), 2)));
  double dist_top_cap = abs(CAP_HEIGHT - vertex.Z());
  double dist_bot_cap = abs(-CAP_HEIGHT - vertex.Z());
  return min(min(dist_cylinder, dist_top_cap), dist_bot_cap);
}

void print_image(ofstream &file, TH2F* h, int data_set, string particle_1hot){
  // Prints the image, and extra information used by the CNN, to a line in the desired output file.
  out_log("Printing image histogram to output file");

  // Iterate over each 2D histogram pixel and prints the contents with ", " separations
  for (Int_t x = 1; x <= NUM_PIXELS; ++x){
    for (Int_t y = 1; y <= NUM_PIXELS; ++y){
      file << h->GetBinContent(x, y) << ", ";
    }
  }
  // Append to the line the data_set number as well as the true particle identification (in 1hot form) before endl.
  file << data_set << ", " << particle_1hot << endl;

  
  out_log("Image histogram printed");
}

#endif
