//#include "skheadC.h"
//#include "skparmC.h"
//#include "geopmtC.h"
//#include "sktqC.h"

#include <iostream>
#include <fstream>
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
using namespace std;

//int read_wcsim_images_sub_e(int argc, char* argv[], bool verbose = true, bool electron = true)

int read_wcsim_images_e(bool verbose = true, bool electron = true)
{
    // Load the library with class dictionary info
    // (create with "gmake shared")
    // Use TTree name tree, not wcsimT
    
    char* wcsimdirenv;
    wcsimdirenv = getenv ("WCSIMDIR");
    
    /*if(wcsimdirenv !=  NULL){
     gSystem->Load("${WCSIMDIR}/libWCSimRoot.so");
     }else{
     gSystem->Load("../libWCSimRoot.so");
     }*/
    
    gSystem->Load("libWCSimRoot.so");
    
    ///////////////////////////////////////////////////
    // MODIFY//
    
    const char* filename = "/home/t/tanaka/qiuemily/WCSim_build/mydir/ROOT_FILES/e-_50_file001.root";
    const char* out_filename = "/scratch/t/tanaka/qiuemily/WCSim_Output/IMAGES/images_e-_50_file001";
    const char* event_filename = "/scratch/t/tanaka/qiuemily/WCSim_Output/EVT_INFO/evt_info_e-_50_file001.txt";
    
    bool save = true;
    
    int particle_out_id = ((electron)? 11 : 13);
    
    ofstream out_file;
    ofstream event_info;
    
    event_info.open(event_filename);
    out_file.open(out_filename);
    
    ///////////////////////////////////////////////////
    
    stringstream ss;
    ss << (electron == true? 1: 0) << ", " << (electron == false? 1: 0);
    // cout << ss.str() << endl;
    
    TFile *file = new TFile(filename,"read");
    
    if (!file->IsOpen()){
        cout << "Error, could not open input file: " << filename << endl;
        return -1;
    }
    
    // Get the pointer to the tree from the file
    
    TTree *tree = (TTree*)file->Get("wcsimT");
    
    // Create a WCSimRootEvent to put stuff from the tree in
    
    WCSimRootEvent* wcsimrootsuperevent = new WCSimRootEvent();
    
    // Set the branch address for reading from the tree
    // tree has branch wcsimrootevent
    
    TBranch *branch = tree->GetBranch("wcsimrootevent");
    branch->SetAddress(&wcsimrootsuperevent);
    
    // Alternatively
    // tree->SetBranchAddress("wcsimrootevent",&wcsimrootevent);
    
    // Force deletion to prevent memory leak
    tree->GetBranch("wcsimrootevent")->SetAutoDelete(kTRUE);
    
    // geotree has 1 entry containing the geometry information for simulated detector
    // wcsimGeoT has branch wcsimrootgeom
    
    TTree *geotree = (TTree*)file->Get("wcsimGeoT");
    WCSimRootGeom *geo = 0;
    
    //WCSimRootGeom *geo = new WCSimRootGeom()
    geotree->SetBranchAddress("wcsimrootgeom", &geo);
    
    if(geotree->GetEntries() == 1) printf("Confirmed... GeoTree has 1 entry. \n \n");
    if (geotree->GetEntries() == 0) exit(9);
    
    geotree->GetEntry(0);
    
    // start with the main "subevent", as it contains most of the info and always exists.
    
    WCSimRootTrigger* wcsimrootevent;
    
    int nevent = tree->GetEntries();
    int parentID_particletype, index, num_neg_triggers, pmt_unfound, total_hits;
    
    if (verbose) printf("Total number of events: %d \n", nevent);
    
    // Info in output images
    // {"true_vertex": [-358.315, 871.359, 1591.82],
    // "true_direction": [0.024953, 0.080551, 0.996438],
    // "vertex": [-376.02, 892.217, 1596.6],
    // "direction": [0.0597496, 0.0283124, 0.997812],
    // "particle_id": 11,
    // "worked_fiTQun": true,
    // "nllcut_fiTQun": 464.777,
    // "nll_e": 5615.52,
    // "energy": 404.834,
    // "data_set": 4,
    // "dist_to_wall": 213.867,
    // "radius": 213.867,
    // "image_width": 1249.73,
    // "phi_vec": [0.428209, -0.90368, 0],
    // "theta_vec": [-0.901702, -0.427272, 0.0661181]}
    
    // Now loop over events
    
    TH2F* image = new TH2F("h", "PMT Display", NUM_PIXELS, -1., 1., NUM_PIXELS, -1., 1.);
    
    TObject *tr;
    WCSimRootTrack *track;
    
    for (int ev=0; ev<nevent; ev++){
        //for (int ev=0; ev<nevent; ev++){
        
        // Read the event from the tree into the WCSimRootEvent instance
        tree->GetEntry(ev);
        
        int number_triggers = wcsimrootsuperevent->GetNumberOfEvents();
        
        index = 0;
        num_neg_triggers = 0;
        parentID_particletype = 0;
        pmt_unfound = 0;
        total_hits = 0;
        
        EventInformation evt_info;
        
        if (verbose){
            printf("Event: %d \n", ev);
            printf("Number of Sub-events (triggers) in current event: %d \n", number_triggers);
        }
        
        if (number_triggers < 1) { num_neg_triggers++; continue;} //Looking only at first trigger if it exists
        
        //Loop over triggers/subevents
        
        //Comment this line and //Loop over triggers at end of loop
        //for (int index = 0 ; index < number_triggers; index++){
        
        wcsimrootevent = wcsimrootsuperevent->GetTrigger(index);
        
        int ncherenkovdigihits = wcsimrootevent->GetNcherenkovdigihits();
        int ncherenkovhits     = wcsimrootevent->GetNcherenkovhits();
        
        // Cherenkov hits associated with current trigger of current event
        if(verbose){
            printf("Sub event number: %d \n", index);
            
            printf("Ncherenkovhits %d \n",     ncherenkovhits);
            printf("Ncherenkovdigihits %d \n", ncherenkovdigihits);
            printf("Number of Tracks: %d \n", wcsimrootevent->GetNtrack());
            
        }
        
        if (ncherenkovhits < 1 || ncherenkovdigihits < 1) continue;
        
        ///////////////////////////////////////////////////////////
        // Getting the vertex
        
        int ntrack = wcsimrootevent->GetNtrack();
        int ipnu, id;
        double track_energy;
        
        //for (int k=0; k==0;k++){
        
        int track_num = 0;
        
        tr = (wcsimrootevent->GetTracks())->At(track_num);
        track = dynamic_cast<WCSimRootTrack*>(tr);
        
        TVector3 particle_vertex(wcsimrootevent->GetVtx(0), wcsimrootevent->GetVtx(1), wcsimrootevent->GetVtx(2));
        TVector3 particle_direction(track->GetDir(0), track->GetDir(1), track->GetDir(2));
        TVector3 particle_momentum(track->GetPdir(0), track->GetPdir(1), track->GetPdir(2));
        
        track_energy = track->GetE();
        ipnu = track->GetIpnu();
        id = track->GetId();
        
        if (verbose){
            printf("Particle Vertex: (%f, %f, %f) \n", particle_vertex(0), particle_vertex(1), particle_vertex(2));
            printf("Particle Direction: (%f, %f, %f) \n", particle_direction(0), particle_direction(1), particle_direction(2));
            
            printf("Energy: %f\n", track_energy);
            printf("Ipnu: %d \n", ipnu);
            printf("ID: %d \n", id);
        }
        
        /////////////////////////////////////////////////////////////
        
        evt_info.true_vertex = particle_vertex;
        evt_info.true_direction = particle_direction;
        
        bool in_cylinder = false;
        
        if (particle_vertex.Z() > (200.0 - CAP_HEIGHT) && particle_vertex.Z() < (CAP_HEIGHT - 200.0)){
            if (sqrt(pow(particle_vertex.X(), 2) + pow(particle_vertex.Y(), 2)) < (CYLINDER_RADIUS - 200.0)){
                in_cylinder = true;
            }
        }
        
        bool passed_cut = (wcsimrootevent->GetNumTubesHit()>160) && in_cylinder;
        
        if (!passed_cut) {
            printf("Failed cut, continue to next event. \n \n");
            continue;
        }
        
        // Distance of vertex to the intercept of particle trajectory with cylinder wall
        double dist_cylinder = (sqrt(pow(particle_direction.X()*particle_vertex.X() + particle_direction.Y()*particle_vertex.Y(), 2) - (pow(particle_direction.X(), 2) + pow(particle_direction.Y(), 2))*(pow(particle_vertex.X(), 2) + pow(particle_vertex.Y(), 2) - pow(CYLINDER_RADIUS, 2))) - (particle_direction.X()*particle_vertex.X() + particle_direction.Y()*particle_vertex.Y()))/(pow(particle_direction.X(), 2) + pow(particle_direction.Y(), 2));
        
        double dist_cap = (particle_direction.Z()/abs(particle_direction.Z())*CAP_HEIGHT-particle_vertex.Z())/particle_direction.Z();
        
        double distance_to_wall = min(dist_cylinder, dist_cap);
        
        // Distance of the vertex to centre of image (always in direction of particle trajectory)
        double radius = min(DEFAULT_RADIUS, distance_to_wall);
        
        // Image width where resolution(PMTs) ~ resolution(image pixels)
        double min_width = PMT_DIAM*NUM_PIXELS;
        
        // Image width, scaled with radius, for data_set 1 and 2
        double scaled_width = 2*CAP_HEIGHT*radius/DEFAULT_RADIUS;
        
        double image_width;
        int set;
        
        // Set number of image
        if (radius > 550.){
            
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
        
        double phi = particle_direction.Phi();
        double theta = particle_direction.Theta();
        double total_curr_charge = 0;
        
        TVector3 phi_vec = TVector3(sin(phi), -cos(phi), 0.);
        TVector3 theta_vec = TVector3(-cos(theta)*cos(phi), -cos(theta)*sin(phi), sin(theta));
        
        //for (i=0;i<(ncherenkovdigihits>4 ? 4 : ncherenkovdigihits);i++){
        for (int i=0;i<ncherenkovdigihits;i++)
        {
            // Loop through elements in the TClonesArray of WCSimRootCherenkovDigHits
            
            TObject *element = (wcsimrootevent->GetCherenkovDigiHits())->At(i);
            TObject *cht, *tr;
            WCSimRootTrack *track;
            
            TVector3 pmt_x(0., 0., 0.);
            TVector3 pmt_y(0., 0., 0.);
            TVector3 pmt_position;
            
            bool flag = 1;
            
            WCSimRootCherenkovDigiHit *wcsimrootcherenkovdigihit = dynamic_cast<WCSimRootCherenkovDigiHit*>(element);
            WCSimRootPMT pmt;
            WCSimRootCherenkovHitTime *cHitTime;
            
            // Input Vector text file:
            double curr_charge, energy;
            int tubeid, t, particle_type, parent_id;
            vector<int> hit_id;
            
            curr_charge = wcsimrootcherenkovdigihit->GetQ();
            t = wcsimrootcherenkovdigihit->GetT();
            tubeid = wcsimrootcherenkovdigihit->GetTubeId();
            
            WCSimRootPMT pmt = geo->GetPMT(tubeid);
            
            hit_id = (wcsimrootcherenkovdigihit->GetPhotonIds());
            
            if (hit_id.size() <= 0){
                printf("Hit ID array size non-positive, continue to next digitized charge: No. %d \n \n", i);
                continue;
            }
            
            if (i==0 && verbose) printf("Number of Hits: %d \n", hit_id.size());
            
            total_hits += hit_id.size();
            
            for (int id=0; id<hit_id.size();id++){
                
                //Within 1 event, have same hit IDs for different digitized hits (i.e. 1 through hit_id.size()
                //id = 0;
                
                cht = (wcsimrootevent->GetCherenkovHitTimes())->At(hit_id[id]);
                cHitTime = dynamic_cast<WCSimRootCherenkovHitTime*>(cht);
                
                parent_id = cHitTime->GetParentID();
                
                if (parent_id != 1){
                    flag = 0;
                    //printf("ParentID/ParticleType are not 1/0. Not adding to image file. \n \n");
                    parentID_particletype++;
                    printf("Parent ID not 1. Raised flag no: %d \n", parentID_particletype+pmt_unfound);
                    break;
                }
                
                tr = (wcsimrootevent->GetTracks())->At(parent_id);
                track = dynamic_cast<WCSimRootTrack*>(tr);
                
                particle_type = track->GetIpnu();
                
                if (particle_type != 0){
                    flag = 0;
                    //printf("ParentID/ParticleType are not 1/0. Not adding to image file. \n \n");
                    parentID_particletype++;
                    printf("Particle Type not 0. Raised flag no: %d \n", parentID_particletype+pmt_unfound);
                    break;
                }
                
                /*if (i==0 && verbose){
                 //printf("x, y, z position: (%d, %d, %d) \n", pos[0], pos[1], pos[2]);
                 //printf("x, y, z direction: (%d, %d, %d) \n", dir[0], dir[1], dir[2]);
                 
                 //printf("Hit ID: %d \n", hit_id[id]);
                 
                 //ID of parent of particle (0 if primary)
                 //These are typically 1... assume 1 if primary
                 
                 //printf("Parent ID: %d \n", parent_id);
                 
                 //Particle Type is 0 if primary
                 //printf("Particle: %d \n", particle_type);
                 }*/
                
            }
            
            pmt_position = TVector3(pmt.GetPosition(0), pmt.GetPosition(1), pmt.GetPosition(2));
            
            // printf("PMT Position: (%f, %f, %f) \n", pmt_position(0), pmt_position(1), pmt_position(2));
            
            if (abs(pmt_position[2]) < 1800){
                pmt_x = TVector3(pmt_position[1], - pmt_position[0], 0.).Unit();
                pmt_y = TVector3(0., 0., 1.);
            }
            
            else if ((int)abs(pmt_position[2]) == 1818){
                pmt_x = TVector3(1., 0., 0.);
                pmt_y = TVector3(0., 1., 0.);
            }
            
            else{
                //cout << "ERROR, PMT NOT FOUND" << endl;
                flag = 0;
                printf("PMT Not found. Position: (%f, %f, %f) \n", pmt.GetPosition(0), pmt.GetPosition(1), pmt.GetPosition(2));
                printf("Raised flag no: %d \n",parentID_particletype+pmt_unfound);
                
                pmt_unfound++;
            }
            
            if (!flag) {continue;}
            
            // Set number of photons to generate, default PHOTONS_PER_PMT but three times as many for sets 3 and 4 to get smoother images.
            bool extra_photons = (set == 3 || set == 4);
            int num_photons = PHOTONS_PER_PMT + (int)extra_photons*2*PHOTONS_PER_PMT;
            
            // Generate photons on surface of the PMT and apply the conical projection to each photon individually.
            for (int photon_num = 0; photon_num < num_photons; ++photon_num){
                
                // Get random position on surface of (approximately flat and circular) PMT.
                double rad = sqrt((double)rand()/RAND_MAX*pow(PMT_DIAM/2, 2));
                double angle = (double)rand()/RAND_MAX*2*PI;
                
                // Coordinates of randomized position in plane that is locally parallel to detector wall
                double x_coord = rad*cos(angle);
                double y_coord = rad*sin(angle);
                
                // Relative vector between the photon intercept with PMT plane and the vertex of the cone
                
                TVector3 rel_vec = x_coord*pmt_x + y_coord*pmt_y + pmt_position - particle_vertex;
                
                double z_rel = rel_vec.Dot(particle_direction.Unit()); // Distance along the axis of the cone of the photon intercept
                
                // Find the radial coordinates of the photon intercept (rel. to cone) and transform to get the image coordinates
                //    1) Scale with radius/z to get the conical projection as opposed to a linear projection
                //    2) Scale with 1/(image_width/2) so that the image coordinate go from -1 to 1
                
                double x_rel = rel_vec.Dot(phi_vec)/(z_rel/radius*image_width/2);   // Image x-position
                double y_rel = rel_vec.Dot(theta_vec)/(z_rel/radius*image_width/2); // Image y-position
                
                // Fill the 2D histogram at the image coordinates specified, with weights that average the PMT charge over each photon that is projected
                
                if (save){
                    image->Fill(x_rel, y_rel, curr_charge/num_photons);
                }
            }
            
            /* if (i == 0 && verbose){
             printf("q, t, tubeid: %f %f %d \n", curr_charge, t, tubeid, pmt_x, pmt_y, pmt_z);
             //printf("Track parent ID: %d\n",track->GetParenttype());
             }*/
            if (i%100 == 0) printf("Cherenkov hit: %d \n", i);
            
        } printf("End loop over digitized hits. \n");// End of loop over Cherenkov digihits
        
        //} printf("\n"); // Loop over triggers
        
        printf("Number of hits with ParentID != 1 or ParticleType != 0: %d \n", parentID_particletype);
        
        printf("Number of hits with PMTs not found: %d \n \n", pmt_unfound);
        
        if (save && (parentID_particletype+pmt_unfound) < 50) {
            evt_info.particle_id = particle_out_id;
            
            evt_info.energy = track_energy;
            evt_info.data_set = set;
            evt_info.dist_to_wall = distance_to_wall;
            evt_info.radius = radius;
            evt_info.image_width = image_width;
            evt_info.phi_vec = phi_vec;
            evt_info.theta_vec = theta_vec;
            
            print_struct(event_info, &evt_info);
            
            for (int x_pixel = 1; x_pixel <= NUM_PIXELS; ++x_pixel){
                for (int y_pixel = 1; y_pixel <= NUM_PIXELS; ++y_pixel){
                    out_file << image->GetBinContent(x_pixel, y_pixel) << ", ";
                }
            }
            image->Reset();
            
            // Append to the line the data_set number as well as the true particle identification (in 1hot form) before endl.
            out_file << set;
            out_file << ", " << ss.str() << endl;
        }
        // Reinitialize super event between loops.
        wcsimrootsuperevent->ReInitialize();
        
    } printf("\n \n"); // End of loop over events
    
    delete image;
    out_file.close();
    event_info.close();
    
    return 0;
}


