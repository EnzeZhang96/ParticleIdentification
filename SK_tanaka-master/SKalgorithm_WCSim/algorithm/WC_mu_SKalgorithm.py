import tensorflow as tf
import numpy as np
import os
import sys
import getopt
import SKheader as h
import WC_mu_SKinput
import SKgraph
import math
import json

FLAGS = h.FLAGS

help_message = 'SKalgorithm.py -p <parameter_file> -t <training_set/testing> -r <regime_name>' \
               '-i <set_directory> -o <run_directory> -n <num_batches/files/images> -c <num_cores> ' \
               '--continue --tensorboard -e -u --worked -s <tensorboard_set> --custom'

try:
    opts, args = getopt.getopt(sys.argv[1:],"heus:p:t:r:i:o:n:c:",["continue", "tensorboard", "worked", "custom"])
except getopt.GetoptError:
    print help_message
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print help_message
        sys.exit()
    elif opt == "-p":
        #Attempt to read a parameter file, defaults used if not found.
        #Should be file with single-line dictionary string, readable
        #by JSON and with keys associated with FLAG names in h.GlobalFlags
        #object.
        try:
            FLAGS.set_parameters(WC_mu_SKinput.ParameterReadWrite(arg).read())
        except:
            print "Parameter file not found, using defaults for run."
            pass
    elif opt == "-t":
        #Integer describing which network to train, 0 for testing
        assert int(arg) <= FLAGS.num_data_sets
        FLAGS.training = int(arg)
    elif opt == "-i":
        #Input directory that contains set0, set1, set2, etc. image folders
        if not os.path.exists(arg):
            print "Input Directory not found."
            sys.exit()
        else:
            FLAGS.set_directory = arg
    elif opt == "-o":
        #Run directory where network parameters and statistics are saved
        if not os.path.exists(arg):
            print "Output Directory not found."
            sys.exit()
        else:
            FLAGS.run_directory = arg
    elif opt == "-n":
        #Number of batches/files/images are run when training/testing/tensorboard-ing
        FLAGS.set_num_iterations(int(arg))
    elif opt == "-r":
        #Define suffix to be used in the dictionaries that are saved for each event
        FLAGS.regime_name = arg
    elif opt == "-c":
        #Number of cores to use (UNSURE IF THIS ACTUALLY WORKS)
        FLAGS.num_cores = int(arg)
    elif opt == "--continue":
        #Initialize the training session that picks up from most recent save point,
        #or run another testing process without overwriting the last one (must use different regime name)
        FLAGS.continue_session = True
    elif opt == "--tensorboard":
        #Run Network testing with the purpose of getting Tensorboard output (no event information saved)
        FLAGS.training = 0
        FLAGS.print_tensorboard = True
    elif opt == "-e":
        #Allow Tensorboard to show electron rings
        FLAGS.show_electrons = True
    elif opt == "-u":
        #Allow Tensorboard to show muon rings
        FLAGS.show_muons = True
    elif opt == "-s":
        #Restrict Tensorboard output to a specific image set
        FLAGS.tensorboard_set = int(arg)
    elif opt == "--worked":
        #Allow Tensorboard to show rings that were classified properly by CNN
        FLAGS.show_worked = True
    elif opt == "--custom":
        #Filter rings for Tensorboard output using also the custom filter defined in source code below
        FLAGS.custom_cut = True

def train(data_set):
    ''' Defines the training procedure for the CNN.
    
    :param data_set: Integer indicating which CNN to train, recall there is a separate CNN for each image set
    '''
    
    with tf.Graph().as_default():
        #Initialize global step variable that will be incrimented during training
        global_step = tf.Variable(0, trainable=False)
        
        #Get images and image_labels in random batches of size FLAGS.batch_size
        #These are just Tensor objects for now and will not actually be evaluated until sess.run(...) is called in the loop
        images, labels = WC_mu_SKinput.input(data_set)
        
        #Get output of the CNN with images as input
        logits = SKgraph.inference(images, data_set, FLAGS.dropout_prob)
        
        #Initialize saver object that takes care of reading and writing parameters to checkpoint files
        saver = WC_mu_SKinput.Saver()
        
        #Values and Operations to evaluate in each batch
        cost = SKgraph.cost(logits, labels)
        accuracy = SKgraph.accuracy(logits, labels)
        train_op = SKgraph.train(cost, saver, global_step)
        
        #Initialize all the Tensorflow Variables defined in appropriate networks, as well as the Tensorflow session object
        initialize = tf.initialize_all_variables()
        sess = tf.InteractiveSession(config=tf.ConfigProto(inter_op_parallelism_threads=FLAGS.num_cores, intra_op_parallelism_threads=FLAGS.num_cores))
        sess.run(initialize)
        
        #Actually Begin Processing the Graph
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)
        
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #!!DO NOT CHANGE THE TENSORFLOW GRAPH AFTER CALLING start_queue_runners!!
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        #Initialize Tracker object that prints averages of quantities after every 20 batches
        tracker = SKgraph.Tracker(["Cost", "Accuracy"])
        
        #Load network parameters from the most recent training session if desired
        if FLAGS.continue_session:
            saver.restore(sess, data_set)
        
        #Iterate over the desired number of batches
        for batch_num in range(1, FLAGS.num_iterations + 1):
            #Run the training step once and return real-number values for cost and accuracy
            _, cost_value, acc_value = sess.run([train_op, cost, accuracy])
            
            assert not math.isnan(cost_value), 'Model diverged with cost = NaN'
            tracker.add([cost_value, acc_value])
            
            #Periodically print cost and accuracy values to monitor training process
            if not batch_num % 20:
                tracker.print_average(batch_num)
            
            #Periodically save moving averages to checkpoint files
            if not batch_num % 100 or batch_num == FLAGS.num_iterations:
                saver.save(sess, data_set)
                
        #Wrap up
        coord.request_stop()
        coord.join(threads)

def test():
    ''' Testing the CNN algorithm on -n files in set_directory/set0/ and saving results in event dictionaries. '''
    
    with tf.Graph().as_default():
        #Get images, image_set flags, and classification labels from testing event files (non-shuffled batches of 2000)
        images, sets, labels = WC_mu_SKinput.input(0, shuffle=False)
        
        #Compute CNN prediction and comparison to truth 
        logits = SKgraph.inference(images, sets, 1.0)
        correct = SKgraph.correct(logits, labels)
        
        #Compute accuracy
        accuracy = SKgraph.accuracy(logits, labels)
        
        #Get images for Tensorboard output
        summary_images = WC_mu_SKinput.get_summary_filter(sets, labels, correct)
        real_images = None
        
        #Initialize saver object for reading CNN variables from checkpoint files
        saver = WC_mu_SKinput.Saver()
        
        #Initialize Variables and Session
        initialize = tf.initialize_all_variables()
        sess = tf.InteractiveSession(config=tf.ConfigProto(inter_op_parallelism_threads=FLAGS.num_cores, intra_op_parallelism_threads=FLAGS.num_cores))
        sess.run(initialize)
        
        #Actually Begin Processing the Graph
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(coord=coord)
        
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #!!DO NOT CHANGE THE TENSORFLOW GRAPH AFTER CALLING start_queue_runners!!
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        #Track accuracy to monitor network performance on files
        tracker = SKgraph.Tracker(["Accuracy"])
        
        #Load CNN variables from checkpoint files
        saver.restore_all(sess)
        
        #Define the file that will have every event dictionary written to it (temp file in the case of 
        # "FLAGS.continue_session" so that the standard file and temp file can be combined afterwards)
        complete_info_file = os.path.join(FLAGS.run_directory, "complete_info.txt")
        temp_info_file = os.path.join(FLAGS.run_directory, "temp_info.txt")
        active_file = complete_info_file if not FLAGS.continue_session else temp_info_file
        if not FLAGS.continue_session and not FLAGS.print_tensorboard:
            #Will be appending JSON strings, so must overwrite the file here at the beginning of process
            open(active_file, "w").close()

        #Get the paths of all the "info" files containing JSON string dictionaries from the image processing runs
        info_paths = WC_mu_SKinput.get_files(0, "wc_mu_info")
        for info_path in info_paths:
            #Regular Testing
            if not FLAGS.print_tensorboard:
                #Break if file number exceeds user-defined limits
                if info_paths.index(info_path) >= FLAGS.num_iterations:
                    break
                #Open file that saves all event dictionaries with complete information
                with open(active_file, "a") as complete_info:
                    #Evaluate the relevant information for testing (algorithm output, correct classification, and algorithm accuracy)
                    output, worked, acc_value = sess.run([logits, correct, accuracy])
                    #Cumulatively track and print accuracy for monitoring purposes
                    tracker.add([acc_value])
                    tracker.print_average("Testing",reset=False)
                    
                    #Open info file and stream all the dictionaries into the complete_info file with Algorithm performance information added
                    with open(info_path, "r") as info_file:
                        #Iterate through info file and Tensorflow batch concurrenly (MUST be a 1-1 correspondence between these sources)
                        #Correspondence is ensured by:
                        #  1. setting the batch size in this case to the size of the info_files
                        #  2. not shuffling the batches in Tensorflow input
                        #  3. stiching the batches together properly after separating them to implement separate CNNs
                        
                        for prob, line, did_work in zip(output, info_file, worked):
                            #Load dictionary and add algorithm performance information
                            info = json.loads(line[:-1])
                            info["worked" + ("_" + FLAGS.regime_name if FLAGS.regime_name != "" else "")] = bool(did_work)
                            info["algorithm" + ("_" + FLAGS.regime_name if FLAGS.regime_name != "" else "")] = [float(prob[0]), float(prob[1])]
                            
                            #Write dictionary to the complete_info file
                            complete_info.write(json.dumps(info) + "\n")
            
            #Tensorboard output procedure
            else:
                #Evaluate images and Tensorboard filters, as well as CNN output for use in custom filter
                img, mask, output = sess.run([images, summary_images, logits])
                #Extra boolean mask if decide to use custom filter
                extra_mask = []
                if FLAGS.custom_cut:
                    #Implement custom filter by iterating over event information dictionaries and checking if event passes custom cut
                    with open(info_path, "r") as info_file:
                        for line, prob in zip(info_file, output):
                            #Get dictionary
                            info = json.loads(line[:-1])
                            #Append boolean "passed cut" to the extra_mask filter
                            #DEFINE CUSTOM FILTER HERE IF DESIRED
                            extra_mask.append(bool(info["worked_fiTQun_ms"] and prob[0] < 0.5)) # Set content to custom expression (return False for events to be cut)
                else:
                    #Initialize extra_mask so that all events pass the custom cut (equivalent to not having a cut at all)
                    extra_mask = [True]*len(mask)
                #Add False elements to the extra_mask so that it is the same length as mask.
                #This is needed to avoid errors when the batch is larger than the number of lines read (e.g. in last file of an image set).
                extra_mask += [False]*(len(mask) - len(extra_mask))
                
                #Combine masks and apply to the images.
                final_mask = np.logical_and(mask, extra_mask)
                batch = img[final_mask]
                
                #Group the images from different files into real_images object.
                if real_images is not None:
                    real_images = np.concatenate((real_images, batch))
                else:
                    real_images = np.array(batch)
                
                #Evaluate number of images and print
                size = len(real_images)
                print size
                #Break if output image number has been reached or if there are no more files to search
                if size >= FLAGS.num_iterations or info_paths.index(info_path) == len(info_paths) - 1:
                    #Create summary object from images and save the images in Tensorboard format
                    image_summary = WC_mu_SKinput.get_summary(real_images)
                    WC_mu_SKinput.write(sess, image_summary)
                    break
        
        #If doing testing, and --continue is called, combine all the dictionaries in the temporary output file with those in the previous output file 
        if FLAGS.continue_session and not FLAGS.print_tensorboard:
            WC_mu_SKinput.combine_info_files(complete_info_file, temp_info_file)
        
        #Wrap up
        coord.request_stop()
        coord.join(threads)

if __name__ == "__main__":
    if FLAGS.training:
        train(FLAGS.training)
    else:
        test()
