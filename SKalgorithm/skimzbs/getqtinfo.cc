#include "getqtinfo.h"
#include "SkimIO.h"

int main(int argc, char* argv[]){
  // Initialize image histogram (Reset for each event)
  TH2F* image = new TH2F("h", "PMT Display", NUM_PIXELS, -1., 1., NUM_PIXELS, -1., 1.);

  // Initialize input output, send args to use for input and output file names (see constructor for details)
  SkimIO* inout = new SkimIO(argv); 
  inout->open_files(); // Open input and output files
  inout->setup(); // Setup fiTQun branches and .zbs file for reading, load geometry
  
  // Loop until fortread_() returns non-zero (already have loaded one line of zbs in inout->setup())
  int nevt = 0; // Event counter
  while (1) {
    // Initialize histogram that will be store the square output image.
    stringstream to_int;
    to_int << nevt;
    out_log(string("Processing ZBS line # ") + to_int.str());

    // Initialize the structure where event information will be saved
    EventInformation evt_info;
    // Read one set of fiTQun variables as well as the true information coming from the vector_file
    pair<TVector3, TVector3> true_cone = inout->get_entry(&evt_info, nevt); // Note that energy and particle_id are saved to the struct here.
    // Save true vertex information to evt_info
    evt_info.true_vertex = true_cone.first;
    evt_info.true_direction = true_cone.second;

    // Save the fiTQun results to evt_info
    Int_t particle_guess = (nll_1r[0][1] < nll_1r[0][2])? 1: 2; // Index of the 1-ring fit that worked the best
    evt_info.worked_fiTQun = ((fqmsnll - nll_1r[0][1] > 0.0)? 11: 13) == evt_info.particle_id;
    evt_info.nllcut_fiTQun = fqmsnll - nll_1r[0][1];
    evt_info.nll_e = nll_1r[0][1];

    // Load fiTQun vertex information (and save to evt_info)
    TVector3 fq1r_dir = TVector3(dir_1r[0][particle_guess][0], dir_1r[0][particle_guess][1], dir_1r[0][particle_guess][2]);
    TVector3 fq1r_pos = TVector3(pos_1r[0][particle_guess][0], pos_1r[0][particle_guess][1], pos_1r[0][particle_guess][2]);
    evt_info.vertex = fq1r_pos;
    evt_info.direction = fq1r_dir;

    // Apply the custom cut to the data
    bool passed_cut = apply_cut(evt_info.vertex, all_charges.size());
    // Save ROOT statistics to the appropriate files.
    inout->fill_stats(&evt_info, in_cylinder(evt_info.vertex, 200.0), passed_cut);

    // If the event passes the cut, process the pmt data into a square image of the Cherenkov ring and print the results
    if (passed_cut){
      fill_histogram(evt_info.vertex, evt_info.direction, &evt_info, image);
      inout->print_output(&evt_info, image);
    }

    // Reset the histogram for the next event
    out_log("Resetting Image Histogram");
    image->Reset();

    // Iterate the event counter
    nevt++;
    // Load another line of the .zbs file, and break the while loop if there are no others
    int iret = fortread_();
    if (iret>0) break;
  }

  // Close the input and output files before completing the process.
  inout->close_files();
  delete image;

  return 0;
}
