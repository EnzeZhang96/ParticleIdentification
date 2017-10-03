import Graph as g
import sys
import getopt
import json
import os

complete_info_file = "complete_info.txt"
canvas_file = "canvases.txt"
colours = ["blue", "green", "red", "purple", "yellow"] + ["black"]*20

try:
    opts, args = getopt.getopt(sys.argv[1:],"hi:o:",[])
except getopt.GetoptError:
    print 'Stats.py -h -i <complete_info_file> -o <canvas_file>'
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print 'Stats.py -h -i <complete_info_file> -o <canvas_file>'
        sys.exit()
    elif opt == "-i":
        assert os.path.exists(arg)
        complete_info_file = arg
    elif opt == "-o":
        canvas_file = arg

#Touch canvas file
with open(canvas_file, 'a'):
        os.utime(canvas_file, None)

with open(complete_info_file, "r") as complete_info:
    num_images = {}
    num_wrong = {}
    out_images = []
    ScaleEeff = g.Canvas("scale_error_eff", "Algorithm Performancy vs. Error in Scale", "Scale Error", "Accuracy of Algorithm")
    Check = g.Canvas("check", "Title", "Distance (cm)", "count")
    Hist = g.Canvas("hist", "Softmax Distribution", "Probability of Being a Muon", "count")
    canvas_id = ["Electron", "Muon"]
    Ecan = []
    Scan = []
    Dcan = []
    ScaleCan = []
    Eeff = [{}, {}]
    Seff = [{}, {}]
    Deff = [{}, {}]
    ScaleEff = [{}, {}]
    check_hist = g.Histogram("check_hist", "Dist of True", 30, 0., 300.)
    hist_el = g.Histogram("hist_el", "Electron Events", 200, 0., 1.)
    hist_mu = g.Histogram("hist_mu", "Muon Events", 200, 0., 1.)
    for id, index in zip(canvas_id, range(10)):
        Ecan.append(g.Canvas("Eeff_" + id, "Algorithm Performance on " + id + "s", "Energy (MeV)", "Accuracy of Algorithm"))
        Scan.append(g.Canvas("Seff_" + id, "Algorithm Performance on " + id + "s", "Data Set Number", "Accuracy of Algorithm"))
        Dcan.append(g.Canvas("Deff_" + id, "Algorithm Performance on " + id + "s", "Distance to Wall (cm)", "Accuracy of Algorithm"))
        ScaleCan.append(g.Canvas("ScaleEff_" + id,  "Algorithm Performancy on " + id + "s", "Scale Error", "Accuracy of Algorithm"))

    for line in complete_info:
        info = json.loads(line[:-1])

        prob_of_muon = info["algorithm_SKnetwork_WCSim"]
        check_hist.fill(info['dist_to_wall'])
        worked = [info[key] for key in info if key.startswith("worked")]
        identifiers = [key[7:] for key in info if key.startswith("worked")]
        for index in range(len(identifiers)):
            if identifiers[index] == "":
                identifiers[index] = "WCSim"
                
        for identifier in identifiers:
            if identifier not in Eeff[0]:
                for id, index in zip(canvas_id, range(10)):
                    Eeff[index][identifier] = g.Efficiency(identifier + "_energy_efficiency_" + id, id + " Events (" + identifier + ")", 20, 300., 1000.)
                    Seff[index][identifier] = g.Efficiency(identifier + "_set_efficiency_" + id, id + " Events (" + identifier + ")", 4, 0.5, 4.5)
                    Deff[index][identifier] = g.Efficiency(identifier + "_distance_efficiency_" + id, id + " Events (" + identifier + ")", 20, 200., 3000.)
                    ScaleEff[index][identifier] = g.Efficiency(identifier + "_scale_efficiency_" + id, id + " Events (" + identifier + ")", 10, 0.7, 1.5)

        #raidial_error = v.project(v.sub(info['vertex'][1], info['vertex'][0]), info['direction'][1])
        scale_error = info['image_width']

        index = 0 if info['particle_id'] == 11 else 1
        if index:
            hist_mu.fill(prob_of_muon)
        else:
            hist_el.fill(prob_of_muon)
        for identifier, did_work in zip(identifiers, worked):
            if info['data_set'] == 3 or info['data_set'] == 4:
                ScaleEff[index][identifier].fill(scale_error, did_work)
            Eeff[index][identifier].fill(info['energy'], did_work)
            Seff[index][identifier].fill(info['data_set'], did_work)
            Deff[index][identifier].fill(info['dist_to_wall'], did_work)
            if identifier not in num_images:
                num_images[identifier] = 1.0
            else:
                num_images[identifier] += 1.0
            if not did_work:
                if identifier not in num_wrong:
                    num_wrong[identifier] = 1.0
                else:
                    num_wrong[identifier] += 1.0
    print num_images

    #Writing Out
    Check.add(check_hist, colour="red")
    Hist.add(hist_el, colour="red")
    Hist.add(hist_mu, colour="blue")
    Hist.write(canvas_file, rewrite=True)
    canvases = Ecan + Scan + Dcan + ScaleCan
    efficiency_lists = Eeff + Seff + Deff + ScaleEff
    for canvas, efficiency_list in zip(canvases, efficiency_lists):
        for identifier, colour in zip(efficiency_list, colours):
            canvas.add(efficiency_list[identifier], colour=colour)
        canvas.write(canvas_file)
    Check.write(canvas_file)

    naming = [key for key in Eeff[0]]
    for name in num_wrong:
        print name + ": \t %.3f +- %0.3f" % ((1-num_wrong[name]/num_images[name])*100., num_wrong[name]**(0.5)/num_images[name]*100.)
