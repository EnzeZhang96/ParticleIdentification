import json
import Graph as g
import getopt
import sys
import os
import matplotlib.pyplot as plt

plot_hist = False
plot_eff = True
work_on_next = False

if plot_hist:
    start_line = 0
    subplot_nums = [111]
    end_line = 1
elif plot_eff:
    start_line = 3
    subplot_nums = [121, 122]
    end_line = 5
else:
    start_line = 9
    subplot_nums = [111]
    end_line = 10

file = "canvases.txt"

try:
    opts, args = getopt.getopt(sys.argv[1:],"hi:",[])
except getopt.GetoptError:
    print 'Stats.py -h -i <canvas_file>'
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print 'Stats.py -h -i <canvas_file>'
        sys.exit()
    elif opt == "-i":
        file = arg
        
assert os.path.exists(file), "File does not exist: " + file

plots = []
canvases = []
plt.figure(figsize=(15,5))
with open(file, 'r') as f:
    plot_num = 0
    for line, index in zip(f, range(10)):
        if start_line <= index < end_line:
	    #print line
            c = g.Canvas()
            c.load_from_dict(json.loads(line[:-1]))
            canvases.append(c)

            #colours = ["blue", "red", "green", "purple", "black"]
            
	    #show = [False, True, False, True, False, False]
            show = [True, True, True, True, True, True]
	    print c.names
	    for name, colour, do_show in zip(c.names, c.colours, show):
                if do_show:
                    graph = c.get_graph(name)
                    a = graph.x
                    if work_on_next:
                        b_total = graph.hist_total.y
                        b_worked = graph.hist_worked.y
                        b = [0.0]*len(a)
                        for index in range(len(b)):
                            b[index] = b_total[index]-b_worked[index]
                    else:
                        b = graph.y
			print graph.y
                    err = graph.err
                    label = graph.label
	
                    plt.subplot(subplot_nums[plot_num])
                    if graph.type == 'efficiency':
                        plots.append(plt.errorbar(a,b, yerr=err, label=label, color=colour, linestyle="None", marker="^"))
                    elif graph.type == 'histogram':
                        plots.append(plt.bar(a, b, label=label, facecolor=colour, width=graph.bin_width))

            first_legend = plt.legend(loc=0)

            plt.xlabel(c.x_axis)
            plt.ylabel(c.y_axis)
            plt.title(c.title)
	    #plt.grid()

            if index == 0:
                plt.yscale('log', nonposy='clip')
                plt.axis([c.x_low, c.x_high, 0, 1])
            elif not work_on_next and 1 <= index < 9:
                if index == 1 or index == 2:
                    plt.axis([c.x_low, c.x_high, 0.75, 1.])
                elif index == 3 or index == 4:
                    plt.axis([c.x_low, c.x_high, 0.75, 1.])
                elif index == 5 or index == 6:
                    plt.axis([c.x_low, c.x_high, 0.75, 1.])
                elif index == 7 or index == 8:
                    plt.axis([c.x_low, c.x_high, 0.75, 1.])
            elif index == 9:
                plt.yscale('log', nonposy='clip')
                plt.axis([c.x_low, c.x_high, 0.5, 500.])
            plot_num += 1

plt.grid()
plt.savefig("muon.png")
plt.show()
