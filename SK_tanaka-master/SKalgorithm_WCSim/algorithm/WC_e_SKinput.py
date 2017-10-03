import tensorflow as tf
import SKheader as h
import os
import json
from shutil import move
from os import remove

FLAGS = h.FLAGS

class DirectoryEmbedded(object):
    ''' Simple class that facilitates working within a (possibly previously non-existent) directory. '''
    def __init__(self, directory):
        ''' Initialize the object with the desired directory.
        
        :param directory: Directory to work in. If non-existent it will be created.
        '''
        
        self.directory = directory
        self.update()
        
    def is_current(self, directory):
        #Check if the directory is an empty string, meaning you are working in the directory from which python was run.
        return directory == ""
    
    def update(self, directory=None):
        ''' Set a given directory as the one used by class, create it if non-existent. 
        
        :param directory: Directory to initialize, if none is given initialize the directory already in use by class.
        '''
        
        #If no directory is given, use the one already saved in class.
        if directory is None:
            directory = self.directory
        #Check if directory needs to be created
        if not self.is_current(directory) and not os.path.exists(directory):
            #Create directory
            os.makedirs(directory)
            #Check that it was created successfully
            assert os.path.exists(directory), "Failed to create set_directory, " + directory
        #Save the directory name in class attribute "directory"
        self.directory = directory
    
    def file(self, file_name):
        ''' Path generation for files in the initialized directory.
        
        :param file_name: Name of file without path information
        :return: Path of hypothetical file of the name file_name in the directory self.directory
        '''
        
        if self.is_current(self.directory):
            return file_name
        return os.path.join(self.directory, file_name)

class Saver(DirectoryEmbedded):
    ''' Custom class that is responsible for saving and loading network parameters in/from checkpoint files. '''
    
    def __init__(self):
        #Initialize the class in a 'checkpoints' directory within the run_directory set by user
        DirectoryEmbedded.__init__(self, os.path.join(FLAGS.run_directory, 'checkpoints'))
        
        #Tensorflow Moving Averages object that is responcible for keeping track of averages during training
        self.ema = tf.train.ExponentialMovingAverage(decay=FLAGS.average_decay_rate)
        #Tensorflow operation to be called whenever you want the averages to be updated
        self.maintain_averages_op = self.ema.apply(tf.trainable_variables())
        
        #Saver objects of type tf.train.Saver for saving and loading to checkpoint
        self.average_variables = None
        self.graph_variables = None
        #Initialize the saver objects above
        self.set_variables()
    
    def checkpoint_name(self, data_set):
        #Get the name of the checkpoint file for a particular data_set
        assert 1 <= data_set <= FLAGS.num_data_sets, "No network corresponding to data_set = " + str(data_set)
        return os.path.join(self.directory, 'network' + str(data_set))
    
    def set_variables(self):
        #Get the list of pointers to trainable variables in Tensorflow
        variables_to_restore = self.ema.variables_to_restore()
        
        #Save dictionaries between the variable name and the variable pointer (moving averages and regular variables resp.)
        #One dictionary for each set of variables (i.e. one for each data set)
        average_dict = [None]*FLAGS.num_data_sets
        graph_dict = [None]*FLAGS.num_data_sets
        #Initialize
        for index in range(FLAGS.num_data_sets):
            average_dict[index] = dict()
            graph_dict[index] = dict()
        
        #Iterate over the list of trainable variables in tensorfow, and add each to the corresponding dictionaries
        for key in variables_to_restore:
            #Check that the variable belongs to one of the sets and is tracked my moving average
            if key.startswith("set") and self.ema.average(variables_to_restore[key]) is not None:
                #Set number immediately following "set" in the variable name
                set = int(key[3])
                index = set - 1
                #Save the variable name in the average dictionary, corresponding the the appropriate set, with the pointer to the moving average
                average_dict[index][key] = self.ema.average(variables_to_restore[key])
                #Save the variable name in the graph dictionary, corresponding the the appropriate set, with the pointer to the graph variable
                graph_dict[index][key] = variables_to_restore[key]
                
        #Initialize saver objects using each of the dictionaries that will be responsible for saving and loading 
        # Tensorflow objects to/from values of the same name in checkpoint files.
        list1 = [(tf.train.Saver(d) if len(d.keys()) else None) for d in average_dict]
        list2 = [(tf.train.Saver(d) if len(d.keys()) else None) for d in graph_dict]
        self.average_variables = tuple(list1)
        self.graph_variables = tuple(list2)

    def restore(self, session, data_set):
        ''' Restore the network variables of a specific data_set into the current session.
        
        :param session: The current session to initialize the network in.
        :param data_set: The single network that is to be restored (if multiple networks are needed call this for each individually)
        '''
        
        index = data_set - 1
        #Set the moving averages and the graph variables in current session to the values saved in the checkpoint file for the specific data_set
        self.average_variables[index].restore(session, self.checkpoint_name(data_set))
        self.graph_variables[index].restore(session, self.checkpoint_name(data_set))
    
    def restore_all(self, session):
        #Restore all the networks at once
        for data_set in range(1, FLAGS.num_data_sets + 1):
            self.restore(session, data_set)
    
    def save(self, session, data_set):
        #Save the values in the current session moving averages (in a single data set) to the corresponding checkpoint file
        index = data_set - 1
        self.average_variables[index].save(session, self.checkpoint_name(data_set))

class ParameterReadWrite(object):
    def __init__(self, parameter_file=""):
        ''' Simple class to read single-line dictionaries from a file, typically for parameter loading.
        
        :param parameter_file: The name of the file to read.
        '''
        
        self.parameter_file = parameter_file
    
    def read(self):
        # Parse the first line of the given file with JSON and return the python dictionary output
        # Return empty dict if no file is given
        if self.parameter_file == "":
            return {}
        assert os.path.exists(self.parameter_file), "Parameter file given does not exist:" + self.parameter_file
        with open(self.parameter_file, "r") as f:
            for line in f:
                # Return the JSON-parsed line (removing the newline character if necessary)
                if line[-1] == "\n":
                    print "Warning: may be multiple dictionaries in \"" + self.parameter_file + "\", whereas only the first is loaded."
                    return json.loads(line[:-1])
                return json.loads(line)
    
    def write(self, dictionary):
        # Write a dictionary to the parameter_file
        with open(self.parameter_file, "w") as f:
            f.write(json.dumps(dictionary))

# Reading file from queue
def read_file(filename_queue):
    '''
    Inform Tensorflow of files to be read. Pack the data in rows into appropriate tensors
    
    :param filename_queue: tf.train.string_input_producer object with files that will be read
    :return: Tensors of the relevant information for running the network (files won't be read until runtime)
    '''
    
    #Initialize the reader object and read a single line from the queue
    reader = tf.TextLineReader()
    _, line = reader.read(filename_queue)
    #Each time the line is evaluated in a session at runtime, the reader progresses to the next line.
    
    # Default values, in case of empty columns. Also specifies the type of the decoded result.
    data_defaults = []
    # Each line should have one input from each pixel in the 30x30 image as well as one number describing the data set
    #  of the image and two numbers, [1, 0] or [0, 1], describing the true particle type
    for i in range(FLAGS.data_size + 3):
      data_defaults.append([0.0])
    
    # Convert a single line, in cvs format, to a list of tf.float tensors with the same size as data_defaults
    data_row = tf.decode_csv(line, record_defaults=data_defaults)
    # Pack pixels tensors together as a single image (and normalize the values)
    datum = tf.pack(data_row[:FLAGS.data_size])
    normalization = tf.reduce_mean(datum, reduction_indices=[0], keep_dims=True)
    datum = tf.div(datum, normalization)
    
    # Next tensor is the data_set number
    data_set = data_row[FLAGS.data_size]
    # Pack last two tensors into particle identification (1hot)
    label = tf.pack(data_row[FLAGS.data_size+1:FLAGS.data_size+3])
    
    #Return the distinct tensors associated with a single-line read of a file
    return datum, data_set, label

def input_pipeline(files, size, num_epochs=None, shuffle=True):
    ''' 
    Handles the reading of lines in text files into appropriate *batch* tensors.
    
    :param files: Python list of file names to be read.
    :param size: The size of the batch produced
    :param num_epochs: --
    :param shuffle: Whether or not to randomize the lines and files read. Otherwise reads in order of File > Line
    :return: Input information (Pixels, data set, labels resp.) organized in batches of size $size.
    '''
    
    #Create the queue for the files for proper handling by Tensorflow
    filename_queue = tf.train.string_input_producer(
          files, num_epochs=num_epochs, shuffle=shuffle)
    #Initialize tensors associated with a single line-read of the file queue
    datum, data_set, label = read_file(filename_queue)
    #Large capacity for better shuffling
    capacity = FLAGS.min_after_dequeue + 3 * size
    #Send the single-line read operation into a Tensorflow batch object that calls it $size times in succession (with possible shuffing)
    if shuffle:
        #Generate a batch with randomized line and file numbers for each entry
        pixel_batch, set_batch, label_batch = tf.train.shuffle_batch(
            [datum, data_set, label], batch_size=size, capacity=capacity,
            min_after_dequeue=FLAGS.min_after_dequeue)
    else:
        #Generate a batch with lines and files read in order (File > Line).
        pixel_batch, set_batch, label_batch = tf.train.batch(
            [datum, data_set, label], batch_size=size)
    #Each batch object is a tensor of shape [$size, ...] where ... represents the shape of the objects it contains (ex. [$size, 2] for labels)
    return pixel_batch, set_batch, label_batch

def get_files(data_set, name):
    '''
    Easy Generation of the list of files to use in the algorithm.
    Assumes Setup.py format with a FLAGS.set_directory containing 
    set0 for the testing set, and set1, set2, set3, set4 directories
    for the training sets (one for each network).
    
    :param data_set: The data_set number of the events to use, zero for testing 
    :param name: A string representing the prefix of the files in a given directory (ex. 'info' for info1.txt, info2.txt, etc.)
    :return: The list of files with that prefix in that set{$data_set} directory
    '''
    
    filenames = []
    #The path of the desired data_set directory (0 for testing files)
    set_dir = os.path.join(FLAGS.set_directory, 'set' + str(data_set) + '/')
    for file_num in range(1, 1000):
        #The path of the $name$file_num.txt file in the $set_dir directory
        file_name = os.path.join(set_dir, name + str(file_num) + '.txt')
        #Add the file to filenames if it exists, break the loop if not since there will be no more files of this type
        if os.path.isfile(file_name):
            filenames.append(file_name)
        else:
            break
            
    return filenames

def input(data_set, shuffle=True):
    # Handles all the input necessary for a particular data_set
    filenames = get_files(data_set, 'wc_e_images')
    assert len(filenames), "Error: No files listed in your queue"
    
    # Get the input batches
    pipeline =  input_pipeline(filenames, FLAGS.get_batch_size(), shuffle=shuffle)
    
    # Reshape the pixels tensor into a square image, '-1 ' indicates that this dimension can be any size (to match the size of the batch)
    # while there is a fourth dimension with a length of '1' to indicate that we are dealing with a black-and-white image rather than a
    # 3-channel colour image.
    images = tf.reshape(pipeline[0], [-1, FLAGS.num_pixels, FLAGS.num_pixels, 1])
    sets = pipeline[1]
    labels = pipeline[2]
    
    if data_set:
        #If data_set is specified it is guaranteed that all images are of this set (so the sets tensor is redundant)
        return images, labels
    return images, sets, labels

def get_summary_filter(sets, labels, correct):
    '''
    Reduce a batch of images to a list of images that will be added to the Tensorboard visual output.
    Filter the images based on data_set, particle type, and whether or not the algorithm worked on it.
    Custom filter also available (using more detailed information) in SKalgorithm.py
    
    :param sets: The tensor describing the data_set of each image in images
    :param labels: The tensor describing the particle type of the image in images
    :param correct: A tensor of type tf.bool that indicates if the algorithm worked on a particular image in images
    :return: The boolean-mask type filter to be used on the corresponding batch of images 
    '''
    
    #Ensure that all the tensor sizes match up
    size = int(correct.get_shape()[0])
    assert int(sets.get_shape()[0]) == size and int(labels.get_shape()[0]) == size
    
    #Construct a boolean mask for the images: either not FLAGS.tensorboard_set (0 by default for no cut here) or the image set matches the FLAGS.tensorboard_set
    restrict_set = tf.constant(FLAGS.tensorboard_set, dtype=tf.int32, shape=[size])
    right_set = tf.logical_or(tf.logical_not(tf.cast(restrict_set, tf.bool)), tf.equal(restrict_set, tf.cast(sets, tf.int32)))
    
    if FLAGS.show_worked:
        #Show images where the algorithm worked *in addition* to the ones that didn't (i.e. do not apply a cut here)
        right_worked = tf.constant(True, dtype=tf.bool, shape=[size])
    else:
        #Contruct a boolean mask that only shows images where the algorithm failed.
        right_worked = tf.logical_not(correct)
    
    #Construct a boolean mask that shows electrons if $FLAGS.show_electrons and shows muons if $FLAGS.show_muons
    show_particle = tf.tile(tf.constant([[FLAGS.show_electrons, FLAGS.show_muons]], dtype=tf.bool), [size, 1])
    good_particle = tf.logical_and(show_particle, tf.cast(labels, tf.bool))
    right_particle = tf.logical_or(tf.reshape(tf.slice(good_particle, [0,0], [size, 1]), [size]), tf.reshape(tf.slice(good_particle, [0,1], [size, 1]), [size]))
    
    #Group the filters together. Final mask only shows images that passed each one.
    show = tf.logical_and(right_set, tf.logical_and(right_worked, right_particle))
    return show

def mask(images, show):
    return tf.boolean_mask(images, show)

def get_summary(images):
    #Construct the summary object that sends the images tensor to Tensorboard for display (displays a maximum of $max_images images)
    return tf.image_summary("data", images, max_images=FLAGS.num_iterations)
    
def write(session, summary):
    # Function to save images in an image summary (from get_summary) to Tensorboard log files
    logdir = '/tmp/logs' # Standard directory to save the display images in Tensorboard format
    
    # Remove all of the tfevent files from previous saves to stop image mixing
    filelist = [f for f in os.listdir(logdir)]
    for f in filelist:
        # Ensure that you are only removing files that are outputted by Tensorflow (in case there are unrelated files in $logdir)
        if f.startswith("events.out.tfevents."):
            remove(os.path.join(logdir, f))
        else:
            print "Unexpected file in logdir: " + f
    # Write summary object
    writer = tf.train.SummaryWriter(logdir, session.graph)
    writer.add_summary(session.run(summary), 0)
    
def combine_info_files(complete_info_file, temp_info_file):
    # Combines the dictionary lists from two separate files, complete_info_file and temp_info_file
    
    # Create new file that will hold the final result
    combine_info_file = os.path.join(FLAGS.run_directory, "combine_info.txt")
    #Open all three files
    with  open(complete_info_file, "r") as complete_info:
        with open(temp_info_file, "r") as temp_info:
            with open(combine_info_file, "w") as combine_info:
                # Loop over the lines of the two files that will be combined 
                # (recall that each line is a single JSON string representing a python dictionary)
                for line1, line2 in zip(complete_info, temp_info):
                    #Load the strings into dictionaries
                    info1 = json.loads(line1[:-1])
                    info2 = json.loads(line2[:-1])
                    #Combine the dictionaries key-by-key
                    for key in info2:
                        #if key in info1:
                        #    assert info1[key] == info2[key], "Error: Shared dictionary elements in " + complete_info_file + " and " + temp_info_file + " do not match."
                        info1[key] = info2[key]
                    #Write the combined dictionary to the output file
                    combine_info.write(json.dumps(info1) + "\n")
    
    #Remove the original file and temp file
    remove(temp_info_file)
    remove(complete_info_file)
    #Set the output file name to that of the original file
    move(combine_info_file, complete_info_file)
