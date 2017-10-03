#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <algorithm>
#include "TFile.h"
#include "TTree.h"
#include "TH2.h"
using namespace std;

// to run this program, type:
// root -l
// .L randomize.C
// .x convert(set, start_number, end_number)

int convert(int set, int start_number, int end_number)
{
  // This program selects images of given set and converts them to a text file
  // param: set: set number of which images are selected
  // param: start_number: start number of root image files to be read
  // param: end_number: end number of root image files to be read

  // read root image files, add all events to a chain
  TChain chain("T");
  for (int i=start_number; i<=end_number; i++){
    stringstream ss;
    ss << i;
    TString str = ss.str();
    TString name_e = "/scratch/t/tanaka/ezzhang/WCSim_images/image_e-_200_file_" + str + ".root";
    chain.Add(name_e);
  }
  for (int i=start_number; i<=end_number; i++){
    stringstream ss;
    ss << i;
    TString str = ss.str();
    TString name_mu = "/scratch/t/tanaka/ezzhang/WCSim_images/image_mu+_200_file_" + str + ".root";
    chain.Add(name_mu);
  }

  int nevents = chain.GetEntries();
  cout << "nevents: " << nevents << "\n";

  // create an auxiliary array of integers from 0 to nevent-1, and shuffle them
  // so that we read events in chain randomly
  int *darray = new int[nevents];
  for (int i=0; i<nevents; i++){
    darray[i] = i;
  }
  randomize(darray, nevents); // function randomize defined in randomize.C 
  //random_shuffle(&darray[0], &darray[nevents]);
  
  TH2F *image = new TH2F("h", "PMT Display", 30, -1., 1., 30, -1., 1.);
  Int_t data_set, particle_id;
  T->SetBranchAddress("image",&image);
  T->SetBranchAddress("data_set",&data_set);
  T->SetBranchAddress("particle_id",&particle_id);

  // create output text file
  stringstream ss;
  ss << set;
  TString str = ss.str();
  TString filename = "/scratch/t/tanaka/ezzhang/set_directory/set" + str + "/image1.txt";
  ofstream out_file(filename);
  if (!out_file.is_open()){
    cout << "Unable to open file";
    return -1;
  }

  int nset = 0; // number of events in selected set
  for (int i=0; i<nevents; i++){
    int j = darray[i];
    T->GetEntry(j);
    if (data_set != set){continue;}
    // write down image pixels, seperated by ", " 
    for (int x_pixel=1; x_pixel<=30; x_pixel++){
      for (int y_pixel=1; y_pixel<=30; y_pixel++){
        out_file << image->GetBinContent(x_pixel, y_pixel) << ", ";
      }
    }
    image->Reset();
    // write down date_set
    out_file << data_set << ", ";

    // write down label
    stringstream ss;
    if (particle_id == 11){
      ss << 1 << ", " << 0;   
    }
    else if (particle_id == 13){
      ss << 0 << ", " << 1;
    }
    else {
      cout << "particle not electron or muon";
      return -1;
    }
    out_file << ss.str() << "\n";
    nset = nset + 1;
  }
  out_file.close();
  cout << "nset: " << nset << "\n";

  return 0;
}


