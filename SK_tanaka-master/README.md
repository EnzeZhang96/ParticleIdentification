# Particle Identification in Cherenkov Detectors using SKAlgorithm and WCSim

### Author: Theodore Tomalty
#### Email: theo@tomalty.com

### Additional Comments by: Emily Qiu
#### Email: emily.qiu@mail.utoronto.ca

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Folder Permissions

The following list of files must be accessible in order to run the SKdetsim simulation and get the machine-learning friendly images (using Theo's scripts):

For sourcing Geant4/ROOT in the T2K directory:
    - /project/t/tanaka/T2K/HyperK/ROOT/install/root_v5.34.34/bin/thisroot.sh
    - /project/t/tanaka/T2K/HyperK/Geant4/useGeant4.9.6p04.sh

For running SKdetsim (simulation.sh):
    - /scratch/t/tanaka/shimpeit/lib/skanada_head_neut5142/skofl/const/lowe/runsum.dat

For running fiTQun (fiTQun.sh):
    - /scratch/t/tanaka/shimpeit/lib/v4r2
    - /scratch/t/tanaka/shimpeit/lib/skanada_head_neut5142/

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SOME NOTES ON WCSIM

Building WCSim: instructions in the README file in https://github.com/WCSim/WCSim
    - Need to load cmake: 'module load cmake/2.8.12.2'
    - If errors produced during make, delete partially-created files before re-trying

When performing consecutive runs, be sure to change the seed number using the syntax '/WCSim/random/seed seed_number' to ensure that each run will contain different data.

Running WCSim
    - macros contain the parameters for each run, which includes:
        - particle type, energy, vertex, direction of propagation
        - detector configuration
        - distribution of vertices within detector volume
        - seed number for random data generation
    - syntax of the form: './WCSim macro_name.mac'

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SK_tanaka

Contains following:
    - SKalgorithm_WCSim: folder, discussed in further detail below
    - mu_sub.sh and e_sub.sh: files to be submitted as tickets to Scinet to run the WCSim read program (discussed in further detail below). These scripts assume that the relevant WCSim read program code is located in the ${WCSIM_DIR}. Once the user has defined their environment variables (discussed later), run the following commands. Alternatively, the user can modify the lines in these scripts that read 'cd ${WCSIM_DIR}' to the location of the code to the user's preference.

        cd prev_folder/SK_tanaka/SKalgorithm_WCSim/read_wcsim
	mv check_nevent.cc $WCSIM_OUT_DIR
	mv read_only_images.cc $WCSIM_OUT_DIR
        mv * $WCSIM_DIR

    - sk_wcsim.mac: WCSim macro which specifies SuperK detector configuration, cylindrical fiducial volume within 2m of detector walls and top/bottom caps, homogeneous, isotropic vertex distribution (within this volume), energy distribution between 200MeV~1GeV, sets a random seed, etc.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SKalgorithm_WCSim

Sourcing ROOT and Geant4, using setup_trunk.sh (Theo) vs. pre_run.sh

    - setup_trunk.sh sets up the environment variables as necessary for running SKdetsim.
        - Updated in setup_trunk.sh:
        - NEUT_ROOT=/scratch/t/tanaka/T2K/Software/neut_5142_root530
    - pre_run.sh sets up the environment variables (as in setup_trunk.sh), and performs the following:
        - load compatible versions of gcc/cmake required for process.sh
        - source ROOT v5.34.34 (located in /project/t/tanaka/T2K/HyperK/ROOT)
        - setup environment variables for using Geant4.9.6
        - defining extra environment variables for convenience (such as $WCSIM_DIR, $WCSIM_IN_DIR and $WCSIM_OUT_DIR), or adding github key ID's (required at every log-in)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SKalgorithm_WCSim/scripts

Modifications to scripts in SKalgorithm

A few things were modified/updated in Theo's scripts (to include such sourcing discussed previously), which are reflected in all the files in this folder.

Extra environment variables
    - define the following environment variables in pre_run.sh as the user sees fit:
        - ${WCSIM_DIR}: contains the user's WCSIM build, should be the same folder containing WCSim macros.
        - ${WCSIM_IN_DIR}: contains WCSim output ROOT files of the form mu+_500_file_${FILE_NO}.root or e-_500_file_${FILE_NO}.root (must be the same folder as the location of the user's WCSim build, otherwise the user must modify his/her WCSim macro file to specify the location of output root files. Alternatively, move the output root files to this folder following each run.)
        - ${WCSIM_OUT_DIR}: run the code to read the root files and write the machine learning images/info files to this folder.

example:

export WCSIM_DIR=${HOME}/WCSim/my_build/
export WCSIM_IN_DIR=${WCSIM_DIR}
export WCSIM_OUT_DIR=${SCRATCH}/WCSim_Output/

Prior to running the code, ensure that $WCSIM_DIR and $WCSIM_IN_DIR are correct and contain the relevant files, and that $WCSIM_OUT_DIR is an existing folder (the code does not create this folder).

CHANGES TO AUTOMATED SCRIPTS IN SKALGORITHM/SCRIPTS

In each of simulation.sh, fitqun.sh, process.sh, algorithm.sh:
    - Added: #PBS -A sab-064-af
    - source ${HOME}/SKalgorithm/setup_trunk.sh (in simulation.sh, fitqun.sh, and algorithm.sh)
    - source ${HOME}/SKalgorithm/pre_run.sh (rather than setup_trunk.sh in process.sh)

In algorithm.sh:
    - performs CNN training/testing (comment training/testing lines in this file if you'd like to perform one or the other, but not both)
    - requires Tensorflow, which is installed on Scinet on Python 2.7.8, so the following commands were included (modules need to be unloaded in order to load other versions of the same module)

module unload intel/12.1.3
module unload python/2.7.2

module load intel/15.0.6
module load python/2.7.8

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
WCSim Read Program Input/Output File Structure:

This program was created to read the WCSim output ROOT files and write the PMT charge/timing information to 2D machine learning friendly images (as discussed in Theo's report). It looks only at the first trigger for each event, and gets the corresponding parent_id for each PMT CherenkovDigiHit and the particle type corresponding to each track. If these are not 0 and 1 respectively, the PMT charge information is not saved. If the number of these faulty hits exceeds 50, the event is not saved as an image. For WCSim, this code is the equivalent of Theo's process.sh (fiTQun is not performed here).

For 500 WCSim electron/muon events, ROOT files of the form:

    - ${WCSIM_IN_DIR}/e-_500_file_${FILE_NO}.root
    - ${WCSIM_IN_DIR}/mu+_500_file_${FILE_NO}.root

When running read_wcsim_images_mu_sub.cc and read_wcsim_images_e_sub.cc (for reading muon and electron WCSim ROOT files respectively), output image/info files will be written in the following form:

    - images, 1 image per event per line
        - ${WCSIM_OUT_DIR}/images_e-_500_file_${FILE_NO}.txt
        - ${WCSIM_OUT_DIR}/images_mu+_500_file_${FILE_NO}.txt

    - information files, contain json strings (1 string per event per line) of true event information
        - ${WCSIM_OUT_DIR}/info_e-_500_file_${FILE_NO}.txt
        - ${WCSIM_OUT_DIR}/info_e-_500_file_${FILE_NO}.txt

It is important to note that since WCSim simulates one type particle at a time, all of run_directory, set_directory contain separate folders for both particles and separate networks must be trained on each particle type. Next steps include combining all the data (both electrons and muons) to ensure that the architecture functions as expected.

Once the correct environment variables have been defined, the mu_sub.sh and e_sub.sh files run the following commands, which run the code that reads the ROOT files and writes their corresponding images and information files.

To submit a ticket, the syntax is (for electrons and muons, respectively):

        qsub -v "FILE_NO=file_no, START_NO=start_no, END_NO=end_no" e_sub.sh
        qsub -v "FILE_NO=file_no, START_NO=start_no, END_NO=end_no" mu_sub.sh

It is recommended to run the program on 20 events at a time (for electrons) and 40 events at a time (for muons), though the user can attempt to run on more events in 1 submission. For a larger number of events, there is a higher probability for job time-out; when this occurs, perform the following steps:

    - go to end of the corresponding information file (shortcut: capital G). If the last line consists of a non-complete json string (typically something along the lines of '{{' or '{', delete it (shortcut: dd). Save and exit.
    - go to the end of the corresponding image file. If the last line does not give the event number, the previous event was not fully processed. Delete the partially-completed image, save and exit. The (updated) last line of the file should give the number of the latest completed event number.
        - NOTE: not all events are saved as images (total number of images will be less than the number of simulated events).
    - run check_nevent.cc, which ensures that there are the same number of events in the info file as well as the image file. After performing the previous 2 steps, this should output true.

        cd $WCSIM_OUT_DIR
        root
        .x check_nevent('img_filename', 'info_filename')

For the next job submission, change START_NO to the latest completed event number+1, and update END_NO as the user sees fit. No new image and info files will be created, since the existing ones will be updated.

After getting all the images from the ROOT files, the lines containing the event numbers in the image files need to be removed and the files need to be processed for the machine learning step. For this, run read_only_images.cc, using the following commands:

        cd $WCSIM_OUT_DIR
        root
        .x read_only_images('img_filename', 'info_filename', 'output_img_filename', 'output_info_filename' )

For the output file names, use the following structure - this is important for the machine learning step!

        wc_e_images#-#.txt
        wc_mu_images#-#.txt

        wc_e_info#-#.txt
        wc_mu_info#-#.txt

Where the second number in #-#.txt ranges from 1 to 10 (as in Theo's architecture, discussed at the end of this file).

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Machine learning stage using the WCSim architecture:

New code is provided for this stage (their usage is discussed in Theo's section), for electron and muon images respectively.

    - Setup.py 		-> Setup_e.py and Setup_mu.py
    - SKalgorithm.py 	-> WC_e_SKalgorithm.py and WC_mu_SKalgorithm.py
    - SKinput.py	-> WC_e_SKinput.py and WC_mu_SKinput.py

In misc, which includes code for plotting:

    - Plot.py 		-> Plot_WC.py
    - Stats.py 		-> Stats_WC.py

As discussed previously, the next step involves training 4 networks (corresponding to the 4 datasets, discussed in Theo's work) on both electron and muon events. Currently, separate networks were trained on electron events and muon events, and are tested on their classification of electron and muon images respectively. It is worth investigating networks trained on both images, and to see whether the performance improves when testing on both images (as compared to the separate case).

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sample_Data

/ERRORS
    - contains all errors encountered during ticketed job submissions on Scinet (as reference, email Emily for any questions related to these).

/ML_Sample_Outputs
    - contains sample outputs from testing/training of CNN (discussed in SKalgorithm section), for reference.

SK_SKDETSIM: Trained on 160,000 events
    - Training data of the form:
        - Equal number of electrons/muons
        - Vertices at centre of detector
        - Direction along y-axis
        - Momenta of 500 MeV/c
    - file structure (also discussed in SKalgorithm section, discussed below):
        - images_640k_fixed: contains machine-learning-friendly training images
        - run: contains all outputs from each run, numbers 1 through 40
        - run_directory: contains run directory run_1_40, CNN trained on runs 1 through 40 

SK_WCSIM: Trained on 640,000 SKDETSIM events, tested on 10,000 WCSIM events
    - Training data: SKDETSIM, same as discussed above
    - Testing data: WCSIM, details as follows:
        - Equal number of electrons/muons
        - Vertices distributed homogeneously throughout detector, within 2m from walls/top/bottom caps
        - Isotropic
        - Energies varying from 200 MeV/c^2 to 1 GeV/c^2
    - file structure:
        - RUN_DIRECTORY: contains run directories for electron and muon events, simulated using WCSim
        - SET: contains set directories for electron and muon events
        - RUN_DIRECTORY: contains run directories for electron and muon CNN testing (training contains the CNN information produced during training using SKDETSIM data)
        - IMAGES: contains set directories for electron and muon events
            - images_*_500_file_*.txt/info_*_500_file_*.txt: contain the images and true information for 500 simulated events, pre-processing
            - wc_*_images#-#.txt/wc_*_info#-#.txt: contain the images and true information for 500 simulated events, post-processing

/WCSIM_ROOT_FILES
    - contains the macros (sk_e-_500.mac and sk_mu+_500.mac) used to generate 500 events
    - contains output ROOT files from 20 runs of 500 events each of electrons and muons -> 10,000 events

/WCSim_ML_Images
    - contains the images and info files created using the WCSim read code through submitted tickets

/WCSim_ML_Images_Processed
    - contains post-processing of images and info files in /WCSim_ML_Images, in correct formatting for the modified machine learning code (i.e. Setup_e.py, etc.)

/WCSim_ROOT_FILES_OUTPUT
    - contains the corresponding output to the ROOT files in /WCSIM_ROOT_FILES when running WCSim.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SKalgorithm

SKalgorithm implements the machine learning package, Tensorflow, in an attempt to construct an event selection algorithm that performs better than the current standard (fiTQun).

File Structure:
    - setup_trunk.sh: Defines all the necessary variables to run the code on SciNet, and defines the directories
                      that are used in the scripts.
    - scripts/*: These files are scripts that are used to automate each step of the process: "simulation.sh"
                 runs the simulation, "fitqun.sh" processes fiTQun on the simulated events, "process.sh"
                 outputs the network-friendly images using simulation and fiTQun information, and
                 "algorithm.sh" runs a complete training-testing process on the images (see below for details).
    - Setup.py: Used between "process.sh" and "algorithm.sh" to filter images according to data_set
                and set up directories.
    - algorithm/: Python files that contain the complete neural network infrastructure.
        - SKalgorithm.py: Functions for training and testing, call this file to run the network.
        - SKgraph.py: This is where the network graph is defined, i.e. all the neuron connections, 
                      convolutions, and evaluations.
        - SKheader.py: FLAGS instance of GlobalFlags class, that contains the parameters that will
                       be used by every other file in the directory. Also, generation of initial
                       filters.
        - SKinput.py: All input and output of the network. Reading image files, saving learned network
                      variables, etc.
    - skimzbs/: C++ code that processes the data*.zbs -> image*.txt conversion.
        - getqtinfo.cc: Main file where information is read in from files, processed, and written out.
        - getqtinfo.h: Defines all the global variables, parameters, and custom functions used in ".cc".
        - SkimIO.h: Custom class used for opening and closing all the input-output files, as well as some
                    setup for reading in "getqtinfo.cc".
        - EventInformation.h: Custom class for saving all the relevant information in a single event,
                              and streaming that information into a JSON string dictionary that will later
                              be used in the python files.
    - organization/: Two parameter files for the simulation ("input_card.card") and fiTQun 
                     ("fiTQun.parameters.dat") as well as a python file that can be used to generate 
                     initial conditions for simulated events.
    - report/: Contains the report of my project, written in LaTeX.
    - misc/: A few python files that are used to generate, and plot, statistics. Also a skeleton addition to
             skimbs that can be used as a template for implementing custom cone fits to the PMT information


Getting the Images:
    For these steps it is necessary to call "source setup_trunk.sh" after setting SKNET_ROOT
    to the path where you have saved this code (parent directory of this README). That file is
    tuned for implementing the code on scinet, so if you are on a different system it will be
    necessary to change all the non-relative paths that are exported. MAKE SURE TO RUN SCRIPTS
    FROM THE DIRECTORY THAT CONTAINS "setup_trunk.sh" (or set the global path of that file in
    each the scripts you want to use).
    1.  Raw data currently comes from the SKdetsim simulation package that takes input in the 
        form of a vector list, defining vertex position and momentum, and outputs a .zbs file
        with the run information.
            i)   Set SIM_DIR in setup_trunk.sh to the folder where you wish to have your simulation
                 run directories.
            ii)  Run the "qsub -v RUN_NUM=<run_num> scripts/simulation.sh" command to submit a simulation job.
                 This creates the $SIM_DIR/run$RUN_NUM directory and begins filling it with 80 text
                 files each containing simulation directives for 200 randomized events, and then performs 
                 the simulation on each file. Events are randomized in the detector volume and eight
                 simulations are run at a time to make use of all eight scinet cores.
            iii) Some of these runs will not go to completion. For the runs that hit the time cap
                 go to those directories and check the largest NUM value that is reached. Rerun the
                 command but set NUM in simulation.sh to begin at the largest value seen (include
                 the largest number in the list so that it is redone on all the cores). Don't forget to
                 change it back to 1 for future runs!
    2.  Run fiTQun on the .zbs files to get the approximate vertex of the particles as well
        as the fiTQun particle identification (for comparison). 
            i)  For the same $SIM_DIR/run$RUN_NUM directory as above call ten instances of fitqun.sh,
                which runs fiTQun on eight .zbs files and saves the results in .root files.
                > for job_num in {1..10}
                > do
                >     qsub -v "RUN_NUM=<run_num>, NUM=$job_num" scripts/fitqun.sh
                > done
    3.  Process the data from the combined sources of .zbs file, fiTQun .root file, and vector_list of
        true information using skimzbs. Saves machine-learning friendly images in $IMG_DIR along with
        information of the event in JSON dictionaries and .root statistics. The first time using this
        code it is important to cd into skimzbs directory and type "make" to compile the C++.
            i)   Set the IMG_DIR where you want to save the output files. Note that it is useful to have
                 output files in two directories, one for the training set and one for the testing set.
                 Once that is done it is a simple matter of calling "qsub -v RUN_NUM=<run_num> scripts/process.sh"
            ii)  The processing command is "./getqtinfo <zbs_file> <fitqun_file> <vector_file>
                 <output_directory> <prefix> <suffix> <w/a>" where "w" overwrites the output files and "a"
                 appends the output to an already existing file.
            iii) If you want the output files to have prefix, to differentiate between separate runs of
                 the image processing, you can go into process.sh and replace the empty string with
                 the desired prefix (e.g. you can use the prefixes "approx" and "true" to differentiate between
                 images with different cone vertexes).
        - Process takes the vertex from the fiTQun reconstruction and projects all the pmt charges
          (conically with respect to the vertex) onto a 30x30 pixel image of the charge
          distribution (one image, in one line, for each event). "images*.txt"
        - All the information for the event is saved in the info_file in a JSON string format
          (one JSON dictionary per event in a single line). "info*.txt"
        - ROOT histograms for readily-available statistics are saved in the stats_file. "stats*.txt"

Running Tensorflow:
    1a. With the directory containing all the outputs from process.sh, run "python Setup.py
        -i <image_directory> -o <set_directory> -r <prefix> --test" in order to separate 
        all the {$prefix_}image files into $set_directory/set1/, set2/, set3/, set4/ directories corresponding
        to which network will be used on those images. If the "--test" flag is used the images will be 
        grouped in $set_directory/set0/ without separation (do not simply mv these files to set0 if you want
        later steps to work properly).
    1b. Use "python Setup.py --rundirs -p <parameter_file> -d <run_directory> -n <num_standard>" to set
        up directories to run the algorithm. $run_directory$n/ are made where $n is iterating over the number of
        standard parameter runs and the number of parameter combinations listed in the parameter file.
        If no "-p" or "-n" flags are used, only the directory $run_directory/ is created.
           i)    An example of parameter_file could be parameter_list.txt with one plain text line:
                 "{'num_neuron_pairs': [8, 9, 11, 12], 'average_decay_rate': [0.99, 0.999]}". 
                 Note that the keys correspond to GlobalFlags parameters in SKheader.py, and there is a
                 list of parameters to try. In this case, Setup.py will create 6 directories, each with a
                 parameter.txt file containing one of the elements above.
    2.  Now run SKalgorithm.py, see "python SKalgorithm -h" for a full list of parameters. For a complete training
        and testing run using default parameters and options submit "qsub -v RUN_NUM=<run_num> scripts/algorithm.sh"
        where run_num is the directory number of $RUN_DIRECTORY to be used (set the values in the last section of
        setup_trunk.sh to your preference.) If you have only set up one run directory, simply leave run_num blank.
        Note that to use parameters for the run, add the "-p <parameter_file>" option in the scripts/algorithm.sh
        commands.
           i)    General: "python SKalgorithm -p <parameter_file> -i <set_directory> 
                 -o <run_directory>" where parameter_file is the parameter file with
                 run information, set_directory contains the set0-4 subdirectories with images,
                 and run_directory where checkpoints will be saved and algorithm
                 test results will be stored (e.g. parameter_file can contain the line:
                 "{'num_neuron_pairs': 8, 'average_decay_rate': 0.99}" to overwrite those
                 two parameters of the GlobalFlags class in SKheader.h).

           ii)   Training: To train the algorithm use the flag "-t <training_set> -n 
                 <num_batches>" where the training_set is the natural number associated with the
                 desired network to train. This will use only the images in the directory
                 $input_directory/set$training_set/. If the "--continue" flag is used the algorithm
                 will initialize all the network variables to their last saved values in the
                 corresponding $save_directory/checkpoints/ directory.

           iii)  Testing: To test the algorithm use "-t 0 -n <num_files>" to evaluate the
                 performance of the algorithm on $n files in $input_directory/set0/ (2000
                 images per file). Performance is stored as a list of JSON strings in 
                 $run_directory/complete_info.txt.

           iv)   Visualization: Tensorflow has built-in image visualization capabilities in
                 a program called Tensorboard. These images are saved to /tmp/logs when
                 the "--tensorboard" flag is used. Optional arguments "-e -u --worked -s 
                 <tensorboard_set>" define whether to show electron events, muon events, 
                 events that were correctly identified (as opposed to the default of only 
                 showing bad IDs), and which data set to restrict the output to, respectively. 
                 By default 50 images are saved but this can be modified by using the 
                 "-n <num_images>" flag. Run tensorboard by calling "tensorboard --logdir=/tmp/logs"
                 in the command line, and go to the local url indicated in the text output.

Getting Statistics:
    The output of testing the algorithm is the file $run_directory/complete_info.txt, which has in each
    line a JSON stringified dictionary with information for a single event. In order to perform your own
    statistics it is simply a matter of looping over each line in the file, loading the dictionary, and
    adding the desired quantities to whatever you are calculating. Something like the following:
        '''
        import json
        
        with open('complete_info.txt', 'r') as f:
            for line in f:
                # Load JSON dictionary, and make sure to omit the '\n' character at the end of
                # each line or it won't work
                info = json.loads(line[:-1])
                
                # Access information using info[key]
        '''
    Info Keys:
        - vertex: The vertex position reconstructed by fiTQun.
        - direction: The vertex direction reconstructed by fiTQun.
        - true_vertex/direction: True values of these quantities.
        - particle_id: True PID of the single-particle event.
        - worked_fitqun: Did fiTQun identify the particle properly?
        - nllcut_fiTQun: The difference in negative log likelihood between muon and electron rings in fiTQun.
        - nll_e: The absolute negative log likelihood of the electron ring.
        - energy: True initial energy of particle.
        - data_set: The data set that the event was placed in during processing.
        - radius: Distance from the vertex to the centre of image along 'direction'
        - dist_to_wall: Distance from the vertex to the detector wall in the direction of "direction".
        - image_width: Width of 3D embeded image that the ring is projected on.
        - phi_vec/theta_vec: Orthogonal Unit vectors that lie in the plane of the image.
        - worked{_$prefix}: Did the CNN classify the particle properly?
        - algorithm{_$prefix}: The softmax output representing the certainty of the algorithm for an
                               electron classification in the first channel and the certainty of a
                               muon classification in the second channel.

algorithm_SKnetwork
worked_SKnetwork

    1.  Run "python Stats.py -i <complete_info_file> -o <canvas_file>" to process all the
        JSON string entries in $complete_info_file and put the statistics (histograms and
        efficiencies) into Histogram/Efficiency objects defined in Graph.py. These objects are placed 
        in Canvas containers and written to $canvas_file as JSON stringified dictionaries.
    2.  Plot the Canvas objects in $canvas_file by using "python Plot.py -i <canvas_file>", making
        sure that you are not in a virtual environment since matplotlib is not compatible with
        them.


