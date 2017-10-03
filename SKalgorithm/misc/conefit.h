#include "getqtinfo.h"
#define NUM_FITS 5

#if VERBOSE
  #define MIGRAD_PRINT 1
#else
  #define MIGRAD_PRINT -1
#endif

float initial_vertex[3];
float initial_phi;
float initial_theta;
vector<int> num_in_row;
vector<pair<float, int> > pmt_charge;

pair<TVector3, TVector3> get_cone_info(Double_t *par);
void initialize_geometry();
Double_t get_chi2(TVector3 vertex, TVector3 direction, Double_t angle, Double_t* max_delta, Double_t* min_z);
void cone_chi2(Int_t &npar, Double_t *gin, Double_t &f, Double_t *par, Int_t iflag);
void cerenkov_chi2(Int_t &npar, Double_t *gin, Double_t &f, Double_t *par, Int_t iflag);
void fit_cone(Double_t* val, Int_t min_type);

void initialize_geometry(){
  int row_size = 1;
  int y_row_rounded;
  for (int icab=0; icab < DATA_SIZE; icab++) {
    pmt_pos[icab] =  TVector3(geopmt_.xyzpm[icab][0], geopmt_.xyzpm[icab][1], geopmt_.xyzpm[icab][2]);
    if (icab == NUM_TALL*NUM_AROUND) y_row_rounded = (int)round(geopmt_.xyzpm[icab][1]);
    if (icab > NUM_TALL*NUM_AROUND && icab <= NUM_TALL*NUM_AROUND + (DATA_SIZE - NUM_TALL*NUM_AROUND)/2){
      if ((int)round(geopmt_.xyzpm[icab][1]) == y_row_rounded){
        ++row_size;
      }
      else{
        num_in_row.push_back(row_size);
        y_row_rounded = (int)round(geopmt_.xyzpm[icab][1]);
        row_size = 1;
      }
    }
  }
}

void set_initial(){
    // Requires fiTQun data loaded from ROOT TTree, PMT charges loaded into all_charges, and PMT charges loaded by fortread
    initial_vertex[0] = pos[0][0];
    initial_vertex[1] = pos[0][1];
    initial_vertex[2] = pos[0][2];

    pmt_charge.clear();
    TVector3 weighted_sum(0., 0., 0.);
    for (vector<pair<float, int> >::iterator pair = all_charges.begin(); pair != all_charges.end(); ++pair){
      float charge = pair.first;
      int index = pair.second;
      if (charge > PMT_THRESHOLD){
        vector<int> adjacent = adjacent_pmts(index);
        int num_adjacent = 0;
        for (vector<int>::iterator it = adjacent.begin(); it != adjacent.end(); ++it){
          if (skq_.qisk[*it] > PMT_THRESHOLD) ++num_adjacent;
        }
        if (num_adjacent >= REQ_ADJACENT){
          pmt_charge.push_back(make_pair(charge, index));
        }
        TVector3 rel_vec = pmt_pos[index] - TVector3(initial_vertex[0], initial_vertex[1], initial_vertex[2]);
        weighted_sum += charge*rel_vec.Unit();
      }
    }
    #if VERBOSE
    cout << "Number of PMTs Considered: " << pmt_charge.size() << " of " << all_charges.size() << endl;
    #endif
    initial_phi = weighted_sum.Phi();
    initial_theta = weighted_sum.Theta();
}

pair<TVector3, TVector3> do_fits(Int_t nevt){
    TH2F* images[NUM_FITS];
    for (Int_t hist_num = 0; hist_num < NUM_FITS; ++hist_num){
      stringstream to_int;
      to_int << "h" << nevt << "-" << hist_num;
      images[hist_num] = new TH2F(to_int.str().c_str(), "PMT Display", NUM_PIXELS, -1., 1., NUM_PIXELS, -1., 1.);
    }
    EventInformation evt_info;
    
    Double_t val[5] = {0., 0., 0., initial_phi, initial_theta};
    pair<TVector3, TVector3> cone_info;

    cone_info = get_cone_info(val);
    fill_histogram(cone_info.first, cone_info.second, &evt_info, images[0]);

    Int_t min_series[4] = {0, 2, 0, 1};
    for (Int_t min_num = 0; min_num < 4; ++min_num){
      fit_cone(val, min_series[min_num]);
      cone_info = get_cone_info(val);
      fill_histogram(cone_info.first, cone_info.second, &evt_info, images[min_num+1]);
    }

    TMinuit *gMinuit = new TMinuit(5);
    gMinuit->SetFCN(cerenkov_chi2);
    gMinuit->SetPrintLevel(MIGRAD_PRINT);

    Int_t ierflg = 0;
    Double_t arglist[10];

    arglist[0] = 1;
    gMinuit->mnexcm("SET ERR", arglist ,1,ierflg);
    gMinuit->mnparm(0, "angle", CERENKOV_ANGLE, 0.01, 0,0,ierflg);

    arglist[0] = 500;
    arglist[1] = 1.;
    gMinuit->mnexcm("MIGRAD", arglist ,2,ierflg);

    TString name;
    Double_t out_angle, err, xlolim, xuplim;
    Int_t iuint;

    gMinuit->mnpout(0, name, out_angle, err, xlolim, xuplim, iuint);
    angle_dist->Fill(out_angle*180./PI);
    
    return cone_info;
}


Double_t get_chi2(TVector3 vertex, TVector3 direction, Double_t angle, Double_t* max_delta, Double_t* min_z){
  Double_t chi2 = 0;
  Double_t delta;
  vector<int> test;

  *max_delta = 0.;
  *min_z = 1600.;
  for (vector<pair<float, int> >::iterator it = pmt_charge.begin(); it != pmt_charge.end(); ++it){
    TVector3 rel_vec = pmt_pos[it->second] - vertex;
    Double_t z = rel_vec.Dot(direction);

    delta = (Norm(rel_vec - z*direction)/(z*tan(angle)) - 1);
    if (delta > *max_delta) *max_delta = delta;
    if (delta > 1.5 || z < 0) delta = 1.5;
    if (z < *min_z) *min_z = z;
    chi2 += it->first*abs(delta)/total_charge;
  }
  return chi2/((double)pmt_charge.size() - 5.0);
}

pair<TVector3, TVector3> get_cone_info(Double_t *par){
  TVector3 fitqun_vertex(initial_vertex[0], initial_vertex[1], initial_vertex[2]);
  Double_t dir_scale = par[0];
  Double_t dir_phi_corr = par[1];
  Double_t dir_theta_corr = par[2];
  TVector3 direction = TVector3(1., 0., 0.);
  direction.SetPhi(par[3]);
  direction.SetTheta(par[4]);
  TVector3 vertex = fitqun_vertex + dir_scale*direction;

  Double_t dist_to_wall = dist_wall(vertex, direction);

  TVector3 wall_intersect = vertex + dist_to_wall*direction;
  TVector3 to_wall = wall_intersect - vertex;
  to_wall.SetPhi(to_wall.Phi() + dir_phi_corr);
  to_wall.SetTheta(to_wall.Theta() + dir_theta_corr);
  vertex = wall_intersect - to_wall;
  direction.SetPhi(to_wall.Phi());
  direction.SetTheta(to_wall.Theta());

  return make_pair(vertex, direction);
}

void cone_chi2(Int_t &npar, Double_t *gin, Double_t &f, Double_t *par, Int_t iflag){
  pair<TVector3, TVector3> cone_info = get_cone_info(par);

  Double_t max_delta;
  Double_t min_z;

  f = get_chi2(cone_info.first, cone_info.second, CERENKOV_ANGLE, &max_delta, &min_z);
  #if VERBOSE
  cout << par[0] << ", " << par[1] << ", " << par[2] << ": " << par[3] << ", " << par[4] << ", Chisq: " << f << ", Max Delta:" << max_delta << ", Min Z: " << min_z << endl;
  #endif
  return;
}

void cerenkov_chi2(Int_t &npar, Double_t *gin, Double_t &f, Double_t *par, Int_t iflag){
  Double_t angle = par[0];
  Double_t max_delta;
  Double_t min_z;

  f = get_chi2(true_pos, true_dir, angle, &max_delta, &min_z);
  return;
}

void fit_cone(Double_t* val, Int_t min_type){
  bool fit_scale = false;
  bool fit_elong = false;
  bool fit_dir = false;
  switch(min_type) {
  case 0: fit_scale = true; break;
  case 1: fit_elong = true; break;
  case 2: fit_dir = true; break;
  }

  TMinuit *gMinuit = new TMinuit(5);
  gMinuit->SetFCN(cone_chi2);
  gMinuit->SetPrintLevel(MIGRAD_PRINT);

  Int_t ierflg = 0;
  Double_t arglist[10];

  arglist[0] = 1;
  gMinuit->mnexcm("SET ERR", arglist ,1,ierflg);

  gMinuit->mnparm(0, "scale", val[0], fit_scale? 1.: 0., 0,0,ierflg);
  gMinuit->mnparm(1, "vert_phi_corr", val[1], fit_elong? 0.005: 0., 0,0,ierflg);
  gMinuit->mnparm(2, "vert_theta_corr", val[2], fit_elong? 0.005: 0., 0,0,ierflg);
  gMinuit->mnparm(3, "phi", val[3], fit_dir? 0.01: 0., 0,0,ierflg);
  gMinuit->mnparm(4, "theta", val[4], fit_dir? 0.01: 0., 0,0,ierflg);

  arglist[0] = 500;
  arglist[1] = 1.;
  gMinuit->mnexcm("MIGRAD", arglist ,2,ierflg);

  TString name;
  Double_t err, xlolim, xuplim;
  Int_t iuint;
  for (int var_num = 0; var_num < 5; ++var_num){
    gMinuit->mnpout(var_num, name, val[var_num], err, xlolim, xuplim, iuint);
  }

  return;
}


vector<int> adjacent_pmts(int icab){
  vector<int> pmts;
  if (icab < NUM_TALL*NUM_AROUND){
    //PMT is on the wall
    int rel_index[8] = {1, -1, NUM_TALL, NUM_TALL + 1, NUM_TALL - 1, -NUM_TALL, -NUM_TALL + 1, -NUM_TALL - 1};
    for (int i = 0; i < 8; ++i){
      pmts.push_back((icab + rel_index[i]) %  (NUM_TALL*NUM_AROUND));
    }
  }
  else {
    //PMT on cap
    int cap_index = (icab - NUM_TALL*NUM_AROUND) % ((DATA_SIZE - NUM_TALL*NUM_AROUND)/2);
    int row_index = cap_index;
    int row = 0;
    while (row_index >= num_in_row.at(row)){
      row_index -= num_in_row.at(row);
      ++row;
    }
    int row_size = num_in_row.at(row);
    int prev_row_size = 0;
    if (row) prev_row_size = num_in_row.at(row - 1);
    int next_row_size = 0;
    if (row < (int)num_in_row.size() - 1) next_row_size = num_in_row.at(row + 1);
    //Should be an integer + 0.5
    float from_centre = row_index - row_size/2 + 0.5;

    if (row_index) pmts.push_back(-1);
    if (row_index < row_size - 1) pmts.push_back(1);
    for (int prev_index = -1; prev_index <= 1; ++prev_index){
      if (abs(from_centre + prev_index) < prev_row_size/2){
	int prev_row_index = (int)round(from_centre + prev_index + prev_row_size/2 - 0.5);
	pmts.push_back(prev_row_index - row_index - prev_row_size);
      }
    }
    for(int next_index = -1; next_index <= 1; ++next_index){
      if (abs(from_centre + next_index) < next_row_size/2){
	int next_row_index = (int)round(from_centre + next_index + prev_row_size/2 - 0.5);
	pmts.push_back(next_row_index + row_size - row_index);
      }
    }

    for (vector<int>::iterator it = pmts.begin(); it != pmts.end(); ++it){
      *it = *it + icab;
    }
  }
  return pmts;
}
