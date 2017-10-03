#ifndef Skim_IO
#define Skim_IO 1

#include "getqtinfo.h"
#include "EventInformation.h"

class SkimIO {
    // File names
    string inFileName;
    string outZBSFileName;
    string fitqun_file;
    string vector_file;
    string image_file;
    string info_file;
    string stat_file;

    // Input files
    TFile *f;
    ifstream vect;
    
    // Ouput files
    ofstream images;
    ofstream info;
    TFile *stats;
    
    // Setup
    TTree *t1;
    Int_t nentries;
    string append;
    int inFileLength;
    int outZBSFileLength;
    
    // ROOT statistics objects that will be saved to stats
    TH2F* cut_space;
    TEfficiency* msnll_eff;
    TEfficiency* radsq_eff;
    TEfficiency* z_eff;
    TEfficiency* theta_eff;
    
    
  public:
    // Constructor
    SkimIO(char* argv[]);
    
    // Function Declarations
    void open_files();
    void close_files();
    void setup();
    Int_t set_branches(TTree *t1);
    pair<TVector3, TVector3> get_entry(EventInformation* evt_info, Int_t nevt);
    void print_output(EventInformation* evt_info, TH2F* image);
    void initialize_geometry();
    void create_stats(string file_name);
    void load_stats(string file_name);
    void fill_stats(EventInformation* evt_info, bool passed_fitqun, bool passed_cut);
    string path_join(string directory, string file_name);
};

SkimIO::SkimIO(char* argv[]){
    out_log("Constructing SkimIO object");
    
    // Function Arguments for input-output
    inFileName = argv[1]; // Input .zbs file from SKdetsim simulation
    fitqun_file = argv[2]; // fiTQun .root file from standard analyis
    vector_file = argv[3]; // File defined by generate_vector.py with true information (statistics purposes)
    string image_dir = argv[4]; // Directory where output files will be saved 
    string image_prefix = argv[5]; // Prefix to give output files, used to differentiate between different implementations of the image processing
    string image_suffix = argv[6]; // Suffix to append to each output file before extension
    append = argv[7]; // Option, "a" or "w" indicating whether to append or write to output files
    
    // Output file names
    string prefix = (image_prefix == "")? "": image_prefix + "_";
    image_file = path_join(image_dir, prefix + "images" + image_suffix + ".txt");
    info_file = path_join(image_dir, prefix + "info" + image_suffix + ".txt");
    stat_file = path_join(image_dir, prefix + "stats" + image_suffix + ".root");
    outZBSFileName = path_join(image_dir, "test.zbs"); // Dummy file produced by fortinit_
    
    // Get file name lengths for input and output for fortinit_
    char* cinFileName = (char*)inFileName.c_str();
    for (int char_it=0; char_it<256; char_it++) {
      if (cinFileName[char_it]=='\0') {
        inFileLength=char_it;
        break;
      }
    }
    
    char* coutZBSFileName = (char*)outZBSFileName.c_str();
    for (int char_it=0; char_it<256; char_it++) {
      if (coutZBSFileName[char_it]=='\0') {
        outZBSFileLength=char_it;
        break;
      }
    }
}

void SkimIO::open_files(){
    out_log("Opening files for input and output");
    
    // Initialize input files
    f = new TFile(fitqun_file.c_str());
    vect.open(vector_file.c_str());
    fortinit_((char*)inFileName.c_str(),(char*)outZBSFileName.c_str(),inFileLength,outZBSFileLength); // This automatically reads an event from the .zbs file
    
    // Initialize output files
    if (append == "w"){
      // Overwrite file or create new file if none exists
      create_stats(stat_file);
      images.open(image_file.c_str());
      info.open(info_file.c_str());
    }
    else if (append == "a"){
      // Append to already-existing files
      load_stats(stat_file);
      images.open(image_file.c_str(), fstream::app|fstream::out);
      info.open(info_file.c_str(), fstream::app|fstream::out);
    }
}

void SkimIO::setup(){
    out_log("Setting up fiTQun TTree and PMT positions");
    
    // Load the tree from the fiTQun .root file, and set the TTree branches to variable addresses in header
    ///////////////////////////////////
    t1 = (TTree*)f->Get("fiTQun"); ////
    nentries = set_branches(t1);   ////
    ///////////////////////////////////
    
    //Initialize detector geometry into pmt_pos[DATA_SIZE] global variable defined in getqtinfo.h
    initialize_geometry();
}

Int_t SkimIO::set_branches(TTree *t1){
  out_log("Calculating minimal distance to the detector wall");
    
  // Connects the appropriate branches of the fiTQun .root file to the addresses of global variables in getqtinfo.h
  // Information can then be loaded into the globals by calling t1->GetEntry(entry_number)
  t1->SetBranchAddress("fqntwnd",&num_clusters);
  t1->SetBranchAddress("fqtwnd_prftt0",&cluster_time);
  t1->SetBranchAddress("fqtwnd_prftpos",&pos);
  t1->SetBranchAddress("fqnse",&num_1rclusters);
  t1->SetBranchAddress("fq1rnll",&nll_1r);
  t1->SetBranchAddress("fq1rpos",&pos_1r);
  t1->SetBranchAddress("fq1rdir",&dir_1r);
  t1->SetBranchAddress("fqmsnll", &fqmsnll);
  
  // Returns the number of entries in the fiTQun file
  return (Int_t)t1->GetEntries();
}

pair<TVector3, TVector3> SkimIO::get_entry(EventInformation* evt_info, Int_t nevt){
  out_log("Reading single entry from input files");
  
  // Load fiTQun variables from the fiTQun TTree
  t1->GetEntry(nevt);
  
  // Load PMT charges into all_charges vector from the skq_ Fortran list
  all_charges.clear();
  total_charge = 0;
  for (int index = 0; index < DATA_SIZE; ++index){
    float charge = skq_.qisk[index];
    if (charge > PMT_THRESHOLD){ // Consider only charges greater than a certain, low, threshold
      all_charges.push_back(make_pair(charge, index)); // The index can later be used to find the PMT position from pmt_pos[index]
      total_charge += charge;
    }
  }
  
  // Read the next four lines of the input_vector file, defining the true input parameters to the particle simulation
  int vector_lines = 0;
  float dir_array[3];
  float pos_array[3];
  for(string line; vector_lines < 4; ++vector_lines){
    // Read four lines
    getline(vect, line);
    if (line.substr(0,8) == "$ vertex"){
      // This line contains vertex information
      
      // Read numerical values in the next part of this line
      string nums = line.substr(9);
      istringstream qq(nums);
      int value_num = 0; // Value iterator
      while (qq){
        // Placeholders
        float value;
        string element;
        
        // Read the next value in the line, separated by " " character, into element variable
        if (!getline(qq, element, ' ' )) break;
        // Convert element string to value float
        istringstream to_float(element);
        to_float >> value;
        
        // Add the values to the true position array
        if (value_num >= 0 && value_num < 3) pos_array[value_num] = value;
        ++value_num;
      }
    }
    else if (line.substr(0,7) == "$ track"){
      // This line contains particle information
      
      // Read numerical values in the next part of this line
      string nums = line.substr(8);
      istringstream qq(nums);
      int value_num = 0; // Value iterator
      while (qq){
        // Placeholders
        float value;
        string element;
        
        // Read the next value in the line, separated by " " character, into element variable
        if (!getline(qq, element, ' ' )) break;
        // Convert element string to value float
        istringstream to_float(element);
        to_float >> value;
        
        // Add the values in succession to their appropriate locations
        if (value_num == 0) evt_info->particle_id = (int)value; // PID of simulated particle (save to EventInformation structure)
        if (value_num == 1) evt_info->energy = value; // Initial energy of the simulated particle (save also to the information structure)
        if (value_num >= 2 && value_num < 5) dir_array[value_num - 2] = value; // Initial direction of the simulated particle
        ++value_num;
      }
    }
  }
  
  // Convert 3D vectors in arrays to TVector3 object before returning the true information pair
  TVector3 true_dir = TVector3(dir_array[0], dir_array[1], dir_array[2]).Unit();
  TVector3 true_pos = TVector3(pos_array[0], pos_array[1], pos_array[2]);
  return make_pair(true_pos, true_dir);
}

void SkimIO::print_output(EventInformation* evt_info, TH2F* image){
  // Print a line of text output to each output .txt file (one image line, and one EventInformation JSON-style dictionary string)
  print_image(images, image, evt_info->data_set, get_1hot(evt_info->particle_id));
  print_struct(info, evt_info);
}

void SkimIO::close_files(){
  // Close input and output .txt files
  out_log("Closing Text Files");
  images.close();
  vect.close();
  info.close();
  
  // Save and close stats .root file
  out_log("Writing/Closing Histogram Files");
  stats->Write();
  stats->Close();
  
  // Close fiTQun .root file
  out_log("Closing fiTQun File");
  f->Close();

  // Close .zbs file
  out_log("Closing ZBS Files");
  int flun = 10;
  skclosef_(&flun);
}

void SkimIO::initialize_geometry(){
  // Load the 3D positions of each PMT into the pmt_pos[DATA_SIZE] global variable defined in getqtinfo.h
  out_log("Loading PMT positions from .zbs file");
  for (int icab = 0; icab < DATA_SIZE; icab++) {
    pmt_pos[icab] =  TVector3(geopmt_.xyzpm[icab][0], geopmt_.xyzpm[icab][1], geopmt_.xyzpm[icab][2]);
  }
}

void SkimIO::create_stats(string file_name){
  // Open the stats output file (overwrite any in existence with the same name)
  out_log("Opening statistics file");
  stats = new TFile(file_name.c_str(),"RECREATE");
  
  // Define the ROOT statistics objects (hists and efficiencies) that will be saved to the stats output file
  out_log("Initializing statistics objects");
  cut_space = new TH2F("cut_space", "Number of Hit PMTs vs. True (Minimum) Distance of Vertex to Detector Wall", 100, 0, 300., 100, 0, 1000);
  msnll_eff = new TEfficiency("msnll_eff", "Proportion of Electrons in Bins of fiTQun Relative Negative Log Likelihood", 100, -400., 600.);
  radsq_eff = new TEfficiency("radsq_eff", "Radial^2 Efficiency of Cut", 200, 0, pow(CYLINDER_RADIUS, 2));
  z_eff = new TEfficiency("z_eff", "Height Efficiency of Cut", 100, -CAP_HEIGHT, CAP_HEIGHT);
  theta_eff = new TEfficiency("theta_eff", "Angle Efficiency of Cut", 30, -PI, PI);
}

void SkimIO::load_stats(string file_name){
    // Load the ROOT statistics objects from existing file to begin appending statistics
    out_log("Loading statistics objects from file");
    
    // Open file and load object contents
    stats = new TFile(file_name.c_str(), "UPDATE");
    cut_space = (TH2F*)stats->Get("cut_space");
    msnll_eff = (TEfficiency*)stats->Get("msnll_eff");
    radsq_eff = (TEfficiency*)stats->Get("radsq_eff");
    z_eff = (TEfficiency*)stats->Get("z_eff");
    theta_eff = (TEfficiency*)stats->Get("theta_eff");
    
    // Reattach the TEfficiency objects to the file (so that later "stats->Write()" will save the newest versions)
    stats->Append(msnll_eff);
    stats->Append(radsq_eff);
    stats->Append(z_eff);
    stats->Append(theta_eff);
}

void SkimIO::fill_stats(EventInformation* evt_info, bool passed_fitqun, bool passed_cut){
    // Fill the ROOT statistics objects
    out_log("Filling statistics into ROOT objects");
    
    if (passed_fitqun){
      // 2D Histogram of events that passed the initial 200cm cut, using just the fiTQun approximated vertex.
      cut_space->Fill(abs_dist_wall(evt_info->true_vertex), all_charges.size());
    } 
    if(passed_cut){
      // For events that passed the final cut, show the percentage of electrons vs. fiTQun Relative Negative Log Likelihood
      msnll_eff->Fill((evt_info->particle_id == 11), fqmsnll - nll_1r[0][1]);
    }
    // Proportion of events that pass the cut for different position variables
    radsq_eff->Fill(passed_cut, pow(evt_info->true_vertex.X(), 2) + pow(evt_info->true_vertex.Y(), 2)); // Radius squared of particle in cylinder
    z_eff->Fill(passed_cut, evt_info->true_vertex.Z()); // Height of particle in cylinder
    theta_eff->Fill(passed_cut, evt_info->true_vertex.Phi()); // Angle of particle in cylinder
}

string SkimIO::path_join(string directory, string file_name){
    // Simple function to join directory names with file names to return the full path
    if (directory != ""){
        if (*directory.rbegin() == '/'){
            return directory + file_name;
        }
        return directory + "/" + file_name;
    }
    return file_name;
}

#endif
