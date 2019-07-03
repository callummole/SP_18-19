"""
Script to plot Track Simulation of various bias onset times, pre-recorded vehicle trajectories, and yaw-rates biases. 
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sobol_seq #library to generate sobol sequences


myrads = 80

#filename = "SimResults_OnsetTimes_"+str(myrads)+".csv"
filename = "SimResults_onset_6_traj_80_1.csv"

#columns are: yr_offset, file_i, onsettime, time_til_crossing
simresults = np.genfromtxt(filename, delimiter=',')

#what to plot?
#filemask = simresults[:,1] == 0 #first file mask

#simresults_file = simresults[filemask]
        
#plot yr and time til crossing functions.

#onset_time = 6 #fixed onset time.
#simresults= simresults[simresults[:,2]==onset_time]

"""
For the balanced experiment we want five levels for SAB (yr offset).
To stay on the road the TTLC needs to be > 9 s.

So, let's take the limit case of 2.23 s, and conservative estimate of 10 s, then three spaces in between.

"""
"""
def map_ttlc_to_sab(ttlc):

    speed = 8.0
    dist_to_edge = 1.5
    dist_travelled = speed * ttlc
    sab = np.sin(dist_to_edge / dist_travelled) 

    return np.rad2deg(sab)
"""

trials = 30
sobol = sobol_seq.i4_sobol_generate(2, trials) # 0,1 scale
ttlc_limit = 2.23
ttlc_stay = 11

ttlc_sobol = sobol[:,0] * (ttlc_stay-ttlc_limit) + ttlc_limit
steer_sobol = sobol[:,1]

#find closest points.
sab_balanced = np.ones(trials)
sab_balanced_diffs = np.ones(5)
ttlc_balanced_predicted = np.ones(trials)

simresults_notnan = simresults[~np.isnan(simresults[:,3])]
simresults_understeer = simresults_notnan[simresults_notnan[:,0]<= 0]
simresults_oversteer = simresults_notnan[simresults_notnan[:,0]>= 0]


for i, ttlc in enumerate(ttlc_sobol):
    print(ttlc)
    steer = steer_sobol[i]
    if steer >= .5:
        sim = simresults_oversteer
    else:
        sim = simresults_understeer

    diffs = sim[:,3] - ttlc
    idx = np.argmin(abs(diffs)) 
    print(idx)
    sab = sim[idx, 0] #closest sab
    print("sab", sab)
    sab_balanced[i] = sab
    ttlc_balanced_predicted[i] = sim[idx, 3] #closest sab


print("sab_balanced", sab_balanced)
print("sab_balanced_diffs", sab_balanced_diffs)
print("ttlc_balanced_predicted", ttlc_balanced_predicted)



plt.figure(2)
plt.plot(simresults[:,0], simresults[:,3], 'k.', markersize=5, alpha = .2)
plt.xlabel("Yaw Rate Offset (deg/s)")
plt.ylabel("Time from Onset to Lane Crossing (s)")
plt.title("Balanced, Radius: " + str(myrads))
plt.plot(sab_balanced, ttlc_balanced_predicted, 'r.', markersize= 5)

#plt.plot(mysab, ttlc, 'r.', markersize= 10)
#plt.savefig(str(myrads) + '_simulated_onsettimes_6s_midline_80_1_chosenparams.png', dpi = 300)
plt.show()
