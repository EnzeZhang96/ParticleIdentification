import tensorflow as tf
import numpy as np
from ROOT import *
from array import array
import SKheader as h


def get_arrays(tensor, size, n_image, n_filter):
# Get the arrays for creating a 2D graph
# param: tensor: the tensor to plot
# param: size: the size of the tensor
# n_image: the number of image to plot (there are 50 images in the batch)
# n_filter: the number of filter used for convolution 

    xarray=np.zeros(size*size)
    yarray=np.zeros(size*size)
    zarray=np.zeros(size*size)
    for j in range(size):
        for i in range(size):
            index = size*j + i
            xarray[index] = i
            yarray[index] = j
            zarray[index] = tensor[n_image, i, j, n_filter]
    x = array("d",xarray)
    y = array("d",yarray)
    z = array("d",zarray)

    return x, y, z
    
def plot(images, labels, W_conv1, h_conv1, h_pool1):
# Plot the images in different steps of the network
# 4*4 graphs in each canvas
# 1st column filters, 2nd column origial images
# 3rd column covolution results, 4th column pooling results

    images_value = images.eval()
    labels_value = labels.eval()
    W_conv1_value = tf.transpose(W_conv1, [2, 0, 1, 3]).eval()
    h_conv1_value = h_conv1.eval()
    h_pool1_value = h_pool1.eval()

    # initial index
    index_e = -1
    index_mu = -1
    #find a eletron image and an muon image
    for i in range(50):
        if labels_value[i, 0] == 1:
            index_e = i
            break
    if index_e == -1:
        print "electron not found."
    else:
        print "index_e: ", index_e

    for i in range(50):
        if labels_value[i, 0] == 0:
            index_mu = i
            break
    if index_mu == -1:
        print "muon not found."
    else:
        print "index_mu: ", index_mu

    #create a canvas
    c1 = TCanvas("c1","angle filter",800,800)
    c1.Divide(4,4)

    #plot filter1 on 1st pad
    c1.cd(1)
    x, y, z = get_arrays(W_conv1_value, 5, 0, 0)
    w1graph = TGraph2D("w1graph", "w1graph", 25, x, y, z)
    w1graph.Draw("surf1")
    #same filter on 5th pad
    c1.cd(5)
    w1graph.Draw("surf1")

    #plot filter2 on 9th pad
    c1.cd(9)
    x, y, z = get_arrays(W_conv1_value, 5, 0, 1)
    w2graph = TGraph2D("w2graph", "w2graph", 25, x, y, z)
    w2graph.Draw("surf1")
    #same filter on 13th pad
    c1.cd(13)
    w2graph.Draw("surf1")

    #plot electron image on 2nd pad
    c1.cd(2)
    x, y, z = get_arrays(images_value, 30, index_e, 0)
    egraph = TGraph2D("egraph", "egraph", 900, x, y, z)
    egraph.Draw("surf1")
    #same image on 10th pad
    c1.cd(10)
    egraph.Draw("surf1")

    #plot muon image on 6th pad
    c1.cd(6)
    x, y, z = get_arrays(images_value, 30, index_mu, 0)
    mugraph = TGraph2D("mugraph", "mugraph", 900, x, y, z)
    mugraph.Draw("surf1")
    #same image on 14th pad
    c1.cd(14)
    mugraph.Draw("surf1")

    #plot h_conv1
    c1.cd(3)
    x, y, z = get_arrays(h_conv1_value, 30, index_e, 0)
    h_conv1_1e_graph = TGraph2D("h_conv1_1e_graph", "h_conv1_1e_graph", 900, x, y, z)
    h_conv1_1e_graph.Draw("surf1")

    c1.cd(7)
    x, y, z = get_arrays(h_conv1_value, 30, index_mu, 0)
    h_conv1_1mu_graph = TGraph2D("h_conv1_1mu_graph", "h_conv1_1mu_graph", 900, x, y, z)
    h_conv1_1mu_graph.Draw("surf1")

    c1.cd(11)
    x, y, z = get_arrays(h_conv1_value, 30, index_e, 1)
    h_conv1_2e_graph = TGraph2D("h_conv1_2e_graph", "h_conv1_2e_graph", 900, x, y, z)
    h_conv1_2e_graph.Draw("surf1")

    c1.cd(15)
    x, y, z = get_arrays(h_conv1_value, 30, index_mu, 1)
    h_conv1_2mu_graph = TGraph2D("h_conv1_2mu_graph", "h_conv1_2mu_graph", 900, x, y, z)
    h_conv1_2mu_graph.Draw("surf1")

    #plot h_pool1
    c1.cd(4)
    x, y, z = get_arrays(h_pool1_value, 10, index_e, 0)
    h_pool1_1e_graph = TGraph2D("h_pool1_1e_graph", "h_pool1_1e_graph", 100, x, y, z)
    h_pool1_1e_graph.Draw("surf1")

    c1.cd(8)
    x, y, z = get_arrays(h_pool1_value, 10, index_mu, 0)
    h_pool1_1mu_graph = TGraph2D("h_pool1_1mu_graph", "h_pool1_1mu_graph", 100, x, y, z)
    h_pool1_1mu_graph.Draw("surf1")

    c1.cd(12)
    x, y, z = get_arrays(h_pool1_value, 10, index_e, 1)
    h_pool1_2e_graph = TGraph2D("h_pool1_2e_graph", "h_pool1_2e_graph", 100, x, y, z)
    h_pool1_2e_graph.Draw("surf1")

    c1.cd(16)
    x, y, z = get_arrays(h_pool1_value, 10, index_mu, 1)
    h_pool1_2mu_graph = TGraph2D("h_pool1_2mu_graph", "h_pool1_2mu_graph", 100, x, y, z)
    h_pool1_2mu_graph.Draw("surf1")

    #save canvas
    c1.SaveAs("c1.C")


    #2nd canvas
    c2 = TCanvas("c2","angle filter 45 degree rotated",800,800)
    c2.Divide(4,4)

    #plot filter3 on 1st pad
    c2.cd(1)
    x, y, z = get_arrays(W_conv1_value, 5, 0, 2)
    w3graph = TGraph2D("w3graph", "w3graph", 25, x, y, z)
    w3graph.Draw("surf1")
    #same filter on 5th pad
    c2.cd(5)
    w3graph.Draw("surf1")

    #plot filter4 on 9th pad
    c2.cd(9)
    x, y, z = get_arrays(W_conv1_value, 5, 0, 3)
    w4graph = TGraph2D("w4graph", "w4graph", 25, x, y, z)
    w4graph.Draw("surf1")
    #same filter on 13th pad
    c2.cd(13)
    w4graph.Draw("surf1")

    #plot electron image on 2nd pad
    c2.cd(2)
    egraph.Draw("surf1")
    #same image on 10th pad
    c2.cd(10)
    egraph.Draw("surf1")

    #plot muon image on 6th pad
    c2.cd(6)
    mugraph.Draw("surf1")
    #same image on 14th pad
    c2.cd(14)
    mugraph.Draw("surf1")

    #plot h_conv1
    c2.cd(3)
    x, y, z = get_arrays(h_conv1_value, 30, index_e, 2)
    h_conv1_3e_graph = TGraph2D("h_conv1_3e_graph", "h_conv1_3e_graph", 900, x, y, z)
    h_conv1_3e_graph.Draw("surf1")

    c2.cd(7)
    x, y, z = get_arrays(h_conv1_value, 30, index_mu, 2)
    h_conv1_3mu_graph = TGraph2D("h_conv1_3mu_graph", "h_conv1_3mu_graph", 900, x, y, z)
    h_conv1_3mu_graph.Draw("surf1")

    c2.cd(11)
    x, y, z = get_arrays(h_conv1_value, 30, index_e, 3)
    h_conv1_4e_graph = TGraph2D("h_conv1_4e_graph", "h_conv1_4e_graph", 900, x, y, z)
    h_conv1_4e_graph.Draw("surf1")

    c2.cd(15)
    x, y, z = get_arrays(h_conv1_value, 30, index_mu, 3)
    h_conv1_4mu_graph = TGraph2D("h_conv1_4mu_graph", "h_conv1_4mu_graph", 900, x, y, z)
    h_conv1_4mu_graph.Draw("surf1")

    #plot h_pool1
    c2.cd(4)
    x, y, z = get_arrays(h_pool1_value, 10, index_e, 2)
    h_pool1_3e_graph = TGraph2D("h_pool1_3e_graph", "h_pool1_3e_graph", 100, x, y, z)
    h_pool1_3e_graph.Draw("surf1")

    c2.cd(8)
    x, y, z = get_arrays(h_pool1_value, 10, index_mu, 2)
    h_pool1_3mu_graph = TGraph2D("h_pool1_3mu_graph", "h_pool1_3mu_graph", 100, x, y, z)
    h_pool1_3mu_graph.Draw("surf1")

    c2.cd(12)
    x, y, z = get_arrays(h_pool1_value, 10, index_e, 3)
    h_pool1_4e_graph = TGraph2D("h_pool1_4e_graph", "h_pool1_4e_graph", 100, x, y, z)
    h_pool1_4e_graph.Draw("surf1")

    c2.cd(16)
    x, y, z = get_arrays(h_pool1_value, 10, index_mu, 3)
    h_pool1_4mu_graph = TGraph2D("h_pool1_4mu_graph", "h_pool1_4mu_graph", 100, x, y, z)
    h_pool1_4mu_graph.Draw("surf1")

    c2.SaveAs("c2.C")


    #3rd canvas
    c3 = TCanvas("c3","custom filters",800,800)
    c3.Divide(4,4)

    #plot full filter on 1st pad
    c3.cd(1)
    x, y, z = get_arrays(W_conv1_value, 5, 0, 16)
    w17graph = TGraph2D("w17graph", "full filter", 25, x, y, z)
    w17graph.Draw("surf1")
    #same filter on 5th pad
    c3.cd(5)
    w17graph.Draw("surf1")

    #plot medium filter on 9th pad
    c3.cd(9)
    x, y, z = get_arrays(W_conv1_value, 5, 0, 18)
    w19graph = TGraph2D("w19graph", "medium filter", 25, x, y, z)
    w19graph.Draw("surf1")
    #same filter on 13th pad
    c3.cd(13)
    w19graph.Draw("surf1")

    #plot electron image on 2nd pad
    c3.cd(2)
    egraph.Draw("surf1")
    #same image on 10th pad
    c3.cd(10)
    egraph.Draw("surf1")

    #plot muon image on 6th pad
    c3.cd(6)
    mugraph.Draw("surf1")
    #same image on 14th pad
    c3.cd(14)
    mugraph.Draw("surf1")

    #plot h_conv1
    c3.cd(3)
    x, y, z = get_arrays(h_conv1_value, 30, index_e, 16)
    h_conv1_17e_graph = TGraph2D("h_conv1_17e_graph", "h_conv1_17e_graph", 900, x, y, z)
    h_conv1_17e_graph.Draw("surf1")

    c3.cd(7)
    x, y, z = get_arrays(h_conv1_value, 30, index_mu, 16)
    h_conv1_17mu_graph = TGraph2D("h_conv1_17mu_graph", "h_conv1_17mu_graph", 900, x, y, z)
    h_conv1_17mu_graph.Draw("surf1")

    c3.cd(11)
    x, y, z = get_arrays(h_conv1_value, 30, index_e, 18)
    h_conv1_19e_graph = TGraph2D("h_conv1_19e_graph", "h_conv1_19e_graph", 900, x, y, z)
    h_conv1_19e_graph.Draw("surf1")

    c3.cd(15)
    x, y, z = get_arrays(h_conv1_value, 30, index_mu, 18)
    h_conv1_19mu_graph = TGraph2D("h_conv1_19mu_graph", "h_conv1_19mu_graph", 900, x, y, z)
    h_conv1_19mu_graph.Draw("surf1")

    #plot h_pool1
    c3.cd(4)
    x, y, z = get_arrays(h_pool1_value, 10, index_e, 16)
    h_pool1_17e_graph = TGraph2D("h_pool1_17e_graph", "h_pool1_17e_graph", 100, x, y, z)
    h_pool1_17e_graph.Draw("surf1")

    c3.cd(8)
    x, y, z = get_arrays(h_pool1_value, 10, index_mu, 16)
    h_pool1_17mu_graph = TGraph2D("h_pool1_17mu_graph", "h_pool1_17mu_graph", 100, x, y, z)
    h_pool1_17mu_graph.Draw("surf1")

    c3.cd(12)
    x, y, z = get_arrays(h_pool1_value, 10, index_e, 18)
    h_pool1_19e_graph = TGraph2D("h_pool1_19e_graph", "h_pool1_19e_graph", 100, x, y, z)
    h_pool1_19e_graph.Draw("surf1")

    c3.cd(16)
    x, y, z = get_arrays(h_pool1_value, 10, index_mu, 18)
    h_pool1_19mu_graph = TGraph2D("h_pool1_19mu_graph", "h_pool1_19mu_graph", 100, x, y, z)
    h_pool1_19mu_graph.Draw("surf1")

    c3.SaveAs("c3.C")


    #4th canvas
    c4 = TCanvas("c4","custom filters",800,800)
    c4.Divide(4,4)

    #plot cross filter on 1st pad
    c4.cd(1)
    x, y, z = get_arrays(W_conv1_value, 5, 0, 20)
    w21graph = TGraph2D("w21graph", "cross filter", 25, x, y, z)
    w21graph.Draw("surf1")
    #same filter on 5th pad
    c4.cd(5)
    w21graph.Draw("surf1")

    #plot electron image on 2nd pad
    c4.cd(2)
    egraph.Draw("surf1")

    #plot muon image on 6th pad
    c4.cd(6)
    mugraph.Draw("surf1")

    #plot h_conv1
    c4.cd(3)
    x, y, z = get_arrays(h_conv1_value, 30, index_e, 20)
    h_conv1_21e_graph = TGraph2D("h_conv1_21e_graph", "h_conv1_21e_graph", 900, x, y, z)
    h_conv1_21e_graph.Draw("surf1")

    c4.cd(7)
    x, y, z = get_arrays(h_conv1_value, 30, index_mu, 20)
    h_conv1_21mu_graph = TGraph2D("h_conv1_21mu_graph", "h_conv1_21mu_graph", 900, x, y, z)
    h_conv1_21mu_graph.Draw("surf1")

    #plot h_pool1
    c4.cd(4)
    x, y, z = get_arrays(h_pool1_value, 10, index_e, 20)
    h_pool1_21e_graph = TGraph2D("h_pool1_21e_graph", "h_pool1_21e_graph", 100, x, y, z)
    h_pool1_21e_graph.Draw("surf1")

    c4.cd(8)
    x, y, z = get_arrays(h_pool1_value, 10, index_mu, 20)
    h_pool1_21mu_graph = TGraph2D("h_pool1_21mu_graph", "h_pool1_21mu_graph", 100, x, y, z)
    h_pool1_21mu_graph.Draw("surf1")

    c4.SaveAs("c4.C")



