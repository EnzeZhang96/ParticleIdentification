import tensorflow as tf
import SKheader as h

FLAGS = h.FLAGS

class Tracker(object):
    ''' Simple class to keep track of value averages during training.
        Use tracker.add() to input values in each batch and print_average
        to return the average values, after some number of steps, and
        reset the variables.
    
        >>> tracker = Tracker(["test1", "test2"])
        >>> tracker.add([1.3, 2.4])
        >>> tracker.add([0.7, 0.6])
        >>> tracker.print_average(0)
        0: test1 1.0, test2 1.5
        
        >>> tracker.add([2.0, 3.0])
        >>> tracker.print_average(1)
        1: test1 2.0, test2 3.0
    '''
 
    def __init__(self, var_names):
        ''' Initialize tracker
        
        :param var_names: list of variable names to print with averages
        '''
        
        self.var_names = var_names
        self.num_var = len(var_names)
        self.numerator = [0.]*len(var_names)
        self.denominator = 0
    
    def reset(self):
        self.numerator = [0.]*self.num_var
        self.denominator = 0
    
    def print_average(self, step, reset=True):
        ''' Prints the averages of the variables being tracked.
        
        :param step: Step number in the process to be printed with averages
        :param reset: By default clears numerator and denominator values, set to False to keep values
        '''
        
        assert self.denominator, "Can not divide by zero"
        
        string = str(step) + ": "
        for name, num in zip(self.var_names, self.numerator):
            string += name + " " + str(num/float(self.denominator)) + (", " if name != self.var_names[-1] else "")
        
        if reset:
            self.reset()
        print string
    
    def add(self, vars):
        ''' Append values to the moving average
        
        :param vars: List of values corresponding to each variable name in self.var_names
        '''
        
        for var, index in zip(vars, range(100)):
            self.numerator[index] += float(var)
        self.denominator += 1

def _inf_mask(images, set, keep_set, keep_prob):
    ''' Inference Mask that contains the bulk of the CNN network definitions.
        
        Converts images and associated information into the 2-channel classification
        prediction for a particular network.
        
    :param images: Tensor containing FLAGS.get_batch_size() images of size FLAGS.num_pixels**2
    :param set: Tensor of the same size as images containing the data set number of each image
    :param keep_set: Integer in the range of possible data sets indicating which network to use
    :param keep_prob: Probability of dropout for the neurons
    :return: (Softmax output of only the keep_set images, stitching tensor for later recombination)
    '''
    
    with tf.variable_scope('set' + str(keep_set)):
        #Initialize all the Variables in this network
        
        #Initial filters include straight/smooth edges of different angles and a few arbitrary shapes
        initial_filters, num_filters = h.get_initial_filters(FLAGS.num_angles, FLAGS.num_zero_filters)
        
        #First and only convolution Layer
        W_conv1 = tf.Variable(tf.transpose(tf.reshape(tf.constant(initial_filters), [num_filters, FLAGS.filter_size, FLAGS.filter_size, 1]), [1, 2, 3, 0]))
        b_conv1 = tf.Variable(tf.zeros([num_filters]))
        
        #Fully connected layer takes input from 10x10 pixel feature maps (after pooling)
        layer_shape = [10*10*(num_filters), 2*FLAGS.num_neuron_pairs]
        bias_shape = [2*FLAGS.num_neuron_pairs]
        W_fc1 = tf.Variable(tf.zeros(layer_shape))
        b_fc1 = tf.Variable(tf.zeros(bias_shape))
        
        #Second fully connected layer initialized to 1-1 mapping from first layer.
        W_fc2_initial = [[(0. if not neur2 == neur1 else (1.)) for neur2 in range(2*FLAGS.num_neuron_pairs)] for neur1 in range(2*FLAGS.num_neuron_pairs)]
        W_fc2 = tf.Variable(W_fc2_initial)
        b_fc2 = tf.Variable(tf.zeros(bias_shape))
        
        #Output layer initialized so that alternating neurons map to electron output and muon output.
        neurons = []
        for pair in range(FLAGS.num_neuron_pairs):
          neurons += [[1., 0.], [0., 1.]]
        W_fc3 = tf.Variable(neurons)

    #Convolution, Pooling, and flattening feature maps into 1D input list for each image
    h_conv1 = tf.nn.relu(h.conv2d(images, W_conv1) + b_conv1)
    h_pool1 = tf.nn.max_pool(h_conv1, ksize=[1, 3, 3, 1], strides=[1, 3, 3, 1], padding='VALID')
    h_pool_flat = tf.reshape(h_pool1, [-1, 10*10*(num_filters)])
    #h_pool_flat = tf.reduce_max(h_conv1, reduction_indices=[1, 2])
    
    #First Connected Layer with possible dropout if keep_prob < 1.0
    h_fc1 = tf.matmul(h_pool_flat, W_fc1) + b_fc1
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)
    
    
    #Second Connected Layer with possible dropout if keep_prob < 1.0
    h_fc2 = tf.matmul(h_fc1_drop, W_fc2) + b_fc2
    h_fc2_drop = tf.nn.dropout(h_fc2, keep_prob)
    
    #Boolean mask that keeps only events in the proper image set
    mask =  tf.equal(set, tf.constant(keep_set, shape=[FLAGS.get_batch_size()], dtype=tf.float32))
    
    #Softmax transormation of semi-linear 2-channel output
    output = tf.boolean_mask(tf.nn.softmax(tf.matmul(h_fc2_drop, W_fc3)), mask)
    #Saves the index of each entry in the boolean_mask for later recombination
    stitch = tf.boolean_mask(tf.constant(range(FLAGS.get_batch_size()), dtype=tf.int32), mask)
    
    return output, stitch

def inference(images, set, keep_prob):
    ''' Input images and return a properly stitched tensor of the CNN output.
    
    :param images: Tensor containing FLAGS.get_batch_size() images of size FLAGS.num_pixels**2
    :param set: Either a Tensor or Integer describing the data set of the images
    :param keep_prob: Probability of dropout for the neurons
    :return: CNN output corresponding to each input image using the appropriate neural network
    '''
    
    if isinstance(set, int):
        #All images should be in the nonzero data set defined by "set" parameter
        assert set
        
        #Use directly the return of _inf_mask since no recombination is required
        set_tensor = tf.constant(set, shape=[FLAGS.get_batch_size()], dtype=tf.float32)
        output, _ = _inf_mask(images, set_tensor, set, keep_prob)
        return output
    else:
        #'set' is a Tensor corresponding to the data set of each image in the input
        outputs = [None]*FLAGS.num_data_sets
        indices = [None]*FLAGS.num_data_sets
        
        #Pass the input images and set Tensor through each neural network
        for keep_set in range(1, FLAGS.num_data_sets + 1):
            outputs[keep_set - 1], indices[keep_set - 1] = _inf_mask(images, set, keep_set, keep_prob)
        
        #Return recombination of the output using the stitching indices returned by each network
        return tf.dynamic_stitch(indices, outputs)


def cost(logits, labels):
    ''' Cost function to be minimized during network training.
    
    :param logits: Softmax output from inference() function.
    :param labels: Tensor containing [1, 0] label for electron and [0, 1] label for muons 
    :return: Simple squared L2 norm of the 2D vector difference between logits and labels
    '''
    
    return tf.reduce_mean(tf.reduce_sum((labels - logits)*(labels - logits), reduction_indices=[1]))

def train(cost, saver, global_step):
    ''' Group elements together into an object that will perform training steps when called with sess.run(...)
    
    :param cost: Network losses that are to be minimized, returned by cost() function above
    :param saver: Tensorflow saver object that keeps track of moving averages
    :param global_step: Untrainable Variable Tensor that will be incrimented in each step
    :return: Operation object that can be called with sess.run(training_op) to process an individual training step
    '''
    
    #Exponentially reduce step size with each step to improve network convergence (automatic incrementation of global_step)
    learning_rate = tf.train.exponential_decay(FLAGS.initial_learning_rate, global_step,
                                               1000, FLAGS.decay_rate_per_thousand)
    
    #Tensorflow operation that will calculate the gradient of the cost function and step network variables appropriately
    train_step = tf.train.AdamOptimizer(learning_rate).minimize(cost, global_step=global_step)
    with tf.control_dependencies([train_step]):
        #Operation that appends network variables to the moving averages
        #The with statement ensures that the train_step is performed first whenever sess.run(training_op) is called
        training_op = tf.group(saver.maintain_averages_op)
    
    return training_op

def correct(logits, labels):
    ''' Checking if the networks have made the correct classifications
    
    :param logits: Tensor of Network predictions from inference(...)
    :param labels: Tensor of True classifications in [1, 0] or [0, 1] format
    :return: Tensor of type tf.bool with True if the correct classification was made and False otherwise
    '''
    
    return tf.equal(tf.argmax(logits,1), tf.argmax(labels,1))

def accuracy(logits, labels):
    ''' Calculate the accuracy of the Network in a sample batch
    
    :param logits: Tensor of Network predictions from inference(...)
    :param labels: Tensor of True classifications in [1, 0] or [0, 1] format
    :return: Tensor value of type tf.float representing (#correct predictions)/(#predictions)
    '''
        
    return tf.reduce_mean(tf.cast(correct(logits, labels), tf.float32))

