import math
import json

#TODO: Canvas y-limits and option for log

class Graph(object):
    def __init__(self, name='', label='', points=None, errorbars=None):
      self.name = name
      self.label = label
      if points is None:
          points = []
      self.x = [point[0] for point in points]
      self.y = [point[1] for point in points]
      if errorbars is None:
          errorbars = []
      self.err = errorbars

    @property
    def y(self):
        return self.__y
    
    @y.setter
    def y(self, y):
        self.__y = y
    
    @property
    def err(self):
        return self.__err
    
    @err.setter
    def err(self, err):
        self.__err = err
        
    def get_dict(self):
        d = self.__dict__
        new_dict = dict()
        for key in d:
            if isinstance(d[key], Graph):
                new_dict[key] = d[key].get_dict()
            elif key[0] != '_':
                new_dict[key] = d[key]
        new_dict['y'] = self.y
        new_dict['err'] = self.err
        return new_dict
        
    def GetPoints(self):
        return [[x_i, y_i] for x_i, y_i in zip(self.x, self.y)]
    
    def write(self, file, rewrite=False):
        option = 'a' if not rewrite else 'w'
        with open(file, option) as f:
            f.write(json.dumps(self.get_dict()) + '\n')
      
class Histogram(Graph):
    """Simple class for creating a histogram with basic funcitonality."""
    
    def __init__(self, name='', label='', num_bins=1, start=0., end=1., feed_dict=None):
        self.type = "histogram"
        self.num_bins = num_bins
        self.start = start
        self.end = end
        initial_points = [[start + self.bin_width/2 + bin_num*self.bin_width, 0] for bin_num in range(num_bins)]
        Graph.__init__(self, name, label, initial_points)
        self.out_of_range = 0
        if not feed_dict == None and feed_dict['type'] == self.type:
          for key in feed_dict:
            setattr(self, key, feed_dict[key])
    
    @property
    def width(self):
        return self.end - self.start
    
    @property
    def bin_width(self):
        return self.width/self.num_bins
    
    @Graph.err.getter
    def err(self):
        return [math.sqrt(bin) for bin in self.y]
    
    def fill(self, value, inc_end=True):
        if value >= self.start and value <= self.end:
            index = int(math.floor((value - self.start)/self.bin_width))
            if index == self.num_bins and inc_end:
                index = self.num_bins - 1
            self.y[index] += 1
            return
        else:
            self.out_of_range += 1
            return

    
class Efficiency(Graph):
    def __init__(self, name='', label='', num_bins=1, start=0., end=1., feed_dict=None):
        self.type = "efficiency"
        self.hist_worked = Histogram("worked_hist", label + " Worked Histogram", num_bins, start, end)
        self.hist_total = Histogram("total_hist", label + " Total Histogram", num_bins, start, end)
        Graph.__init__(self, name, label, self.hist_total.GetPoints())
        if not feed_dict == None and feed_dict['type'] == self.type:
          for key in feed_dict:
            if isinstance(feed_dict[key], dict) and feed_dict[key]['type'] == "histogram":
                setattr(self, key, Histogram(feed_dict=feed_dict[key]))
            else:
                setattr(self, key, feed_dict[key])
      
    @Graph.y.getter
    def y(self):
        return [float(bin_worked)/float(bin_total) if bin_total else 0 for bin_worked, bin_total in zip(self.hist_worked.y, self.hist_total.y)]
    
    @Graph.err.getter
    def err(self):
        return [math.sqrt(eff*(1.-eff)/bin) if bin else 0 for bin, eff in zip(self.hist_total.y, self.y)]
    
    def fill(self, value, bool):
      if bool:
          self.hist_worked.fill(value)
      self.hist_total.fill(value)


class Canvas(object):
    """ Container class for multiple graphs to be plotted on the same canvas in Plot.py
    
    #h = Histogram('h1')
    #eff = Efficiency('eff')
    #h.fill(0.5)
    #h.fill(0.5)
    #h.fill(0.5)
    #h.fill(0.5)
    #h.fill(0.5)
    #eff.fill(0.5, True)
    #eff.fill(0.5, False)
    #eff.fill(1.5, False)
    #
    #c = Canvas('test', 'No Title', 'distance (cm)', 'count')
    #c.add(h)
    #c.add(eff)
    #
    #print c.get_dict()
    #c.write('eff_data.txt', rewrite=True)
    #with open('eff_data.txt', 'r') as f:
    #    for line in f:
    #        d = Canvas(name='test1')
    #        if d.in_file("eff_data.txt", load=True):
    #            print json.dumps(d.get_dict())
    
    """
    
    def __init__(self, name='', title='', x_axis='', y_axis='', graphs=None, feed_dict=None):
        self.name = name
        self.type = "canvas"
        self.title = title
        self.x_axis = x_axis
        self.y_axis = y_axis
        if graphs is None:
          graphs = []
        self.names = [graph.name for graph in graphs]
        self.colours = ['black']*len(graphs)
        for graph in graphs:
            self.add(graph)
        if not feed_dict == None and feed_dict['type'] == self.type:
            self.load_from_dict(feed_dict)

    def load_from_dict(self, feed_dict):
        for key in feed_dict:
            if isinstance(feed_dict[key], dict):
                if feed_dict[key]['type'] == "histogram":
                    self.add(Histogram(feed_dict=feed_dict[key]))
                elif feed_dict[key]['type'] == "efficiency":
                    self.add(Efficiency(feed_dict=feed_dict[key]))
            else:
                setattr(self, key, feed_dict[key])

    def add(self, graph, colour='black', overwrite=True):
        append = True
        for name in self.names:
            if name == graph.name:
                if not overwrite:
                    return
                else:
                    append = False
        if append:
            self.names.append(graph.name)
            self.colours.append(colour)
        setattr(self, graph.name, graph)
        
    def get_graph(self, name):
        return getattr(self, name)
        
    def get_dict(self):
        d = self.__dict__
        new_dict = dict()
        for key in d:
            if isinstance(d[key], Graph):
                new_dict[key] = d[key].get_dict()
            elif key[0] != '_':
                new_dict[key] = d[key]
        return new_dict
    
    def in_file(self, file, load=False):
        with open(file, 'r') as f:
            for line in f:
                if json.loads(line[:-1])['name'] == self.name:
                    if load:
                        self.load_from_dict(json.loads(line[:-1]))
                    return True
            return False
    
    @property
    def x_low(self):
        x_low = None
        for name in self.names:
            c = self.get_graph(name)
            x_test = 0
            if c.type == 'histogram':
                x_test = c.x[0]
            if c.type == 'efficiency':
                x_test = c.x[0] - c.hist_total.bin_width/2
            if x_test < x_low or x_low is None:
                x_low = x_test
            
        return x_low
    
    @property
    def x_high(self):
        x_high = None
        for name in self.names:
            c = self.get_graph(name)
            x_test = 0
            if c.type == 'histogram':
                x_test = c.x[-1] + c.bin_width
            if c.type == 'efficiency':
                x_test = c.x[-1] + c.hist_total.bin_width/2
            if x_test > x_high or x_high is None:
                x_high = x_test
        return x_high
    
    @property
    def y_high(self):
        y_high = None
        for name in self.names:
            c = self.get_graph(name)
            for val, error in zip(c.y, c.err):
                y_test = 0
                if c.type == 'histogram':
                    y_test = val
                if c.type == 'efficiency':
                    y_test = min(val + error, 1.0)
                if y_test > y_high or y_high is None:
                    y_high = y_test
        return y_high
    
    @property
    def y_low(self):
        y_low = None
        for name in self.names:
            c = self.get_graph(name)
            for val, error in zip(c.y, c.err):
                y_test = 0
                if c.type == 'histogram':
                    y_test = val
                if c.type == 'efficiency':
                    y_test = max(val - error, 0.0)
                if y_test < y_low or y_low is None:
                    y_low = y_test
        return y_low
        
    def write(self, file, rewrite=False):
        option = 'a' if not rewrite else 'w'
        with open(file, option) as f:
            f.write(json.dumps(self.get_dict()) + '\n')
