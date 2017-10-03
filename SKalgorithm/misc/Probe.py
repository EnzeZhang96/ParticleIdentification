import json
import Graph as g
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

num = 0
hist = g.Histogram("test", "Title", 50, -10.0, 10.0)
electrons = g.Histogram("el", "Title", 50, -10.0, 10.0)
subplot_nums = [[241, 242, 243, 244], [245, 246, 247, 248]]
x = [[[], [], [], []], [[], [], [], []]]
y = [[[], [], [], []], [[], [], [], []]]

plt.figure(figsize=(30,10))
with open("complete_info.txt", "r") as f:
    for line in f:
        info = json.loads(line[:-1])
        num += 1
        hist.fill(info["nllcut_fiTQun_ms"])
        if (info["particle_id"] == 11):
            electrons.fill(info["nllcut_fiTQun_ms"])
            
        x[int(info["particle_id"] == 13)][info["data_set"][0]-1].append(info["nllcut_fiTQun_ms"])
        y[int(info["particle_id"] == 13)][info["data_set"][0]-1].append(info["algorithm_approx"][0])
    
    for part in range(2):
        for set in range(4):
            plt.subplot(subplot_nums[part][set])
            plt.axhline(y=0.5)
            plt.axvline(x=0.0)
            plt.hist2d(x[part][set], y[part][set], bins=40, norm=LogNorm())
            plt.axis([-2000, 2000, 0.0, 1.0])
            plt.colorbar()
    plt.show()
    
    
    #plt.bar(hist.x, hist.y, facecolor="blue", width=hist.bin_width)
    #plt.bar(electrons.x, electrons.y, facecolor="red", width=electrons.bin_width)
#
    #plt.yscale('log', nonposy='clip')
    #plt.axis([-2000, 2000, 0.5, 2250])
    #plt.show()
    #for x_0 in hist.x:
    #    integral = 0
    #    width = hist.bin_width
    #    for x, y_tot, y_pass in zip(hist.x, hist.y, electrons.y):
    #        if x < x_0:
    #            integral += y_pass * width
    #        elif x > x_0:
    #            integral += (y_tot - y_pass) * width
    #        elif x == x_0:
    #            integral += (y_tot - y_pass) * width/2 + y_pass * width/2
    #    print "x: " + str(x_0) + ", y: " + str(integral)
