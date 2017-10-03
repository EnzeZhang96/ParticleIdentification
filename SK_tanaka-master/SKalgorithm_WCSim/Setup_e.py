import algorithm.WC_e_SKinput as input
import algorithm.SKheader as h
import sys
import getopt
import os

FLAGS = h.FLAGS

class SetWriter(input.DirectoryEmbedded):
    ''' Writer class that takes care of writing images and info dictionaries for a particular data_set into separate directories. '''
    
    def __init__(self, set_number, set_directory=""):
        ''' Initialize the empty directory for writing images of a particular set.
        
        :param set_number: The number identifying a particular data_set.
        :param set_directory: The directory that will contain the different directories for each data_set.
        '''
        
        # Create the directory where writing will take place, parent class takes care of file paths.
        input.DirectoryEmbedded.__init__(self, os.path.join(set_directory, "set" + str(set_number)))
        self.set_number = set_number # Set this in case it is needed in future
        self.file_num = 0 # The file number of the current line iteration (max 2000 lines per file)
        self.num_entries = 0 # The line number of the current line iteration, within current file
        
        # File objects that are open concurrently 
        self.image_file = None # The currently open file where images are written by line
        self.info_file = None # The currently open file where info directories are written by line
    
    @property
    def image_path(self):
        # Path of current image file
        return self.file("wc_e_images" + str(self.file_num) + ".txt")
    
    @property
    def info_path(self):
        # Path of current info file
        return self.file("wc_e_info" + str(self.file_num) + ".txt")
    
    def close(self):
        # Close both files if they are open (and not None)
        if self.image_file is not None:
            self.image_file.close()
            # Reset unopened status by indicating None
            self.image_file = None
        if self.info_file is not None:
            self.info_file.close()
            # Reset unopened status
            self.info_file = None
    
    def open_next(self):
        # Open a pair of files corresponding to the next file number, close previous files, reset line number
        self.file_num += 1
        self.num_entries = 0
        self.close()
        self.image_file = open(self.image_path, "w")
        self.info_file = open(self.info_path, "w")
    
    def write(self, image, info):
        ''' Writes the image-info pair to their respective files.
        
        :param image: String corresponding to an image (with '\n' character at the end for line return)
        :param info:  String corresponding to an info dictionary (with '\n' character at the end for line return)
        '''
        
        # Open first files if none have yet been opened
        if self.image_file is None or self.info_file is None:
            self.open_next()
        
        # Write lines and iterate line number
        self.image_file.write(image)
        self.info_file.write(info)
        self.num_entries += 1
        
        # When the line number reaches 2000 print status and open the next file pair for further writing
        if not self.num_entries % 2000:
            print "File ", self.set_number, "-", self.file_num, " Complete"
            self.open_next()

class Separate(input.DirectoryEmbedded):
    def __init__(self, image_directory="", set_directory="", test=False, prefix=""):
        ''' Class that filters image and info file pairs in the image_directory into separate folders in set_directory
            corresponding to different data_sets.
        
        :param image_directory: Directory containing images*.txt and info*.txt files outputted by skimzbs
        :param set_directory: Directory where set folders are to be saved
        :param test: If test then files are dumped into $set_directory/set0 folder without data_set separation
        :param prefix: Prefix used by the image files (e.g. "approx_images*.txt")
        '''
        
        # Embed into directory where image and info files are being read
        input.DirectoryEmbedded.__init__(self, image_directory)
        self.set_directory = set_directory
        self.prefix = prefix
        self.test = test
        
        #Initialize writer objects
        self.writers = self.set_writers(set_directory)
    
    def set_writers(self, set_directory):
        # Initialize an instance of SetWriter for each folder that is being written to.
        # If self.test then only dump to $self.set_directory/set0, otherwise initialize one writer for each 
        # data_set for training the networks independently.
        if self.test:
            return SetWriter(0, set_directory)
        writers = [SetWriter(data_set, set_directory) for data_set in range(1, FLAGS.num_data_sets + 1)]
        return tuple(writers)
    
    def get_writer(self, data_set):
        # Get the writer associated with a particular data_set, or the only writer if testing
        if self.test:
            return self.writers
        return self.writers[data_set]
    
    def get_file_list(self):
        # Return the list of file_names in image_directory associated with images and info dictionaries respectively
        
        # The info files index all the files in the directory since the image files should have the same 
        # suffixes (e.g. "approx_images1-3.txt" is associated with "info1-3.txt")
        suffixes = [f[len("wc_e_info"):] for f in os.listdir(self.directory) if f.startswith("wc_e_info")]
        
        # Generate the list of file paths in the image_directory (image files can have prefixes
        image_files = [self.file((self.prefix  + "_" if self.prefix != "" else "") + "wc_e_images" + suffix) for suffix in suffixes]
        info_files = [self.file("wc_e_info" + suffix) for suffix in suffixes]
        
        # Check that all the files that are listed exist
        for image_file, info_file in zip(image_files, info_files):
            assert os.path.exists(image_file), "Failed to find file: " + image_file
            assert os.path.exists(info_file), "Failed to find file: " + info_file
        
        return image_files, info_files

# Action to perform if Setup.py is run from bash
if __name__ == "__main__":
    # Parse arguments
    separate = True # Perform image-info separation into folders based on data_set
    test = False # Put all image-info instances into set0 folder without separation
    image_directory = "" # Directory where image and info files are saved after skimzbs
    set_directory = "" # Directory where set folders will be saved
    prefix = "" # Prefix used by desired image files (exluding the necessary "_" if a prefix exists)
    
    rundirs = False # Setup algorithm run directories
    parameter_file = "" # Optional parameter file, single-line JSON dictionary string with entries in a list. 
                        # A run directory will be created for each list element in each dictionary key with
                        # a parameter file associated with that key and value (for single deviation from default 
                        # algorithm parameters)
    run_directory = "" # Run directory stub (DO NOT END WITH "/") that will be given iterative integer suffix for 
                       # each standard run and then each run with different parameters.
    num_standard = 0 # The number of directories that will be created for separate algorithm runs with standard parameters

    help_message = 'Setup.py -h -i <image_directory> -o <set_directory> -r <image_prefix> --test' \
                   '--rundirs -p <parameter_file> -d <run_directory> -n <num_standard>'
    nset = [0,0,0,0]

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:o:r:p:d:n:",["test", "rundirs"])
    except getopt.GetoptError:
        print help_message
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print help_message
            sys.exit()
        elif opt == "-i":
            assert os.path.exists(arg), "Image directory, '" + arg + "', does not exist."
            image_directory = arg
        elif opt == "-o":
            set_directory = arg
        elif opt == "-r":
            if arg != "":
                prefix = arg
        elif opt == "--test":
            test = True
        elif opt == "--rundirs":
            separate = False
            rundirs = True
        elif opt == "-p":
            parameter_file = arg
        elif opt == "-d":
            run_directory = arg
            if run_directory[-1] == "/":
                run_directory = run_directory[:-1]
        elif opt == "-n":
            num_standard = int(arg)
    
    if separate:
        # Initialize class instance and get file_names in image_directory
        separator = Separate(image_directory, set_directory, test, prefix)
        image_files, info_files = separator.get_file_list()
        
        # For each pair of files open them and filter contents into folders for given set
        for image_path, info_path in zip(image_files, info_files):
            image_file = open(image_path, "r")
            info_file = open(info_path, "r")
            
            for image, info in zip(image_file, info_file):
                # For each line pair, get the data_set from the data_set from the image line and give the pair to the appropriate writer
                data_set = int(image[-8])
		nset[data_set-1] += 1
                separator.get_writer(data_set - 1).write(image, info)

	print nset

    elif rundirs:
        # Read parameter dictionary from parameter_file and setup list of algorithm run directories
        parameters = input.ParameterReadWrite(parameter_file).read()
        dirs = [input.DirectoryEmbedded(run_directory + str(run)) for run in range(1, num_standard + 1)]
        
        num = len(dirs)
        # Initialize a run directory for each value in the list associated with each key in the parameter_file dictionary
        for key in parameters:
            for value in parameters[key]:
                num += 1
                dir = input.DirectoryEmbedded(run_directory + str(num))
                # Save a parameter file in that directory with the key:value pair that will be used in that run of the algorithm
                input.ParameterReadWrite(dir.file("parameters.txt")).write({key:value})
        
        # If no standard directories are made, and no parameter directories are desired then a single directory is made without an integer suffix
        if not num:
            input.DirectoryEmbedded(run_directory)
