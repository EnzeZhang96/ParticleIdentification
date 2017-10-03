#!/usr/bin/python
# python generate_vector.py <vector_file> <num_events>
# 
# Generates a text file, of name $vector_file, that contains a list of initial kinematics for $num_events events.
# Format of file is specified by SKdetsim. Called to read by "read VECTOR from text file" option in input_card.card
# which is used as the run specifications for skdetsim_high.
#
#######################################################################################################################

import sys
import random
import math

# Detector dimensions
cylinder_radius = 1690.
cap_height = 1810.

# Arguments
vector_file = sys.argv[1]
num_events = int(sys.argv[2])
assert num_events <= 2000, "To write more than 2000 events in a single file make sure to raise the limit set by VECT-NEVT in input_card.card"

# Open vector_file and begin writing initial kinematics information
with open(vector_file, 'w') as f:
    for event_num in range(num_events):
        # Get random position in cylinder
        psi = random.random()*math.pi*2
        rad = math.sqrt(random.random())*cylinder_radius
        z_pos = (random.random()*2. - 1.)*(cap_height)
        x_pos = rad*math.cos(psi)
        y_pos = rad*math.sin(psi)
        
        # Get random direction in cylinder
        phi = random.random()*math.pi*2
        theta = random.random()*math.pi
        x_dir = math.sin(theta)*math.cos(phi)
        y_dir = math.sin(theta)*math.sin(phi)
        z_dir = math.cos(theta)
        
        # Get random particle, between electron and muon, and random energy 
        if random.randrange(0, 2):
            particle_id = 11 # Electron id
            energy = random.random()*(1000. - 300.) + 300.
        else:
            particle_id = 13 # Muon id
            energy = random.random()*(1000. - 300.) + 300.

        #Write randomized information in the appropriate format
        f.write('$ begin\n$ vertex %f %f %f 0\n$ track %d %f %f %f %f 0\n$ end\n' % (x_pos, y_pos, z_pos, particle_id, energy, x_dir, y_dir, z_dir))
            
