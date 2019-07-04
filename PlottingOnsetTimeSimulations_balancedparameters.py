"""
Script to plot Track Simulation of various bias onset times, pre-recorded vehicle trajectories, and yaw-rates biases. 
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


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

bend_yr = -np.rad2deg(8.0 / myrads)
print("limit yr", bend_yr)
#retrieve ttlc for 3.141. 
bend_yr_mask = simresults[simresults[:,0]<= bend_yr]
ttlc_limit = max(bend_yr_mask[:,3])
print("limit ttlc", ttlc_limit)

#noyr = simresults[abs(simresults[:,0]) < .2]
#print("noyr", noyr[:,3])

print("max ttlc", max(simresults[:,3]))
#simresults columns: [yr, file_i, onset, t]       

"""
For the balanced experiment we want five levels for SAB (yr offset).
To stay on the road the TTLC needs to be > 9 s.

So, let's take the limit case of 2.23 s, and conservative estimate of 10 s, then three spaces in between.

"""

ttlc_stay = 12
ttlc_balanced = np.linspace(ttlc_limit, ttlc_stay, 5)
print("ttlc_balanced", ttlc_balanced)

#find closest points.
sab_balanced = np.ones(5)
sab_balanced_diffs = np.ones(5)
ttlc_balanced_predicted = np.ones(5)
simresults_notnan = simresults[~np.isnan(simresults[:,3])]
simresults_notnan = simresults_notnan[simresults_notnan[:,0]< 0]
for i, ttlc in enumerate(ttlc_balanced):
    print(ttlc)
    diffs = simresults_notnan[:,3] - ttlc
    idx = np.argmin(abs(diffs)) 
    print(idx)
    sab = simresults_notnan[idx, 0] #closest sab
    print("sab", sab)
    sab_balanced[i] = sab
    sab_balanced_diffs[i] = min(abs(diffs))
    ttlc_balanced_predicted[i] = simresults_notnan[idx, 3] #closest sab


print("sab_balanced", sab_balanced)
print("sab_balanced_diffs", sab_balanced_diffs)
print("ttlc_balanced_predicted", ttlc_balanced_predicted)

plt.figure(2)
plt.plot(simresults[:,0], simresults[:,3], 'k.', markersize=5, alpha = .2)
plt.xlabel("Steering Angle Biases (deg/s)")
plt.ylabel("Time from Onset to Lane Crossing (s)")
plt.title("Balanced, Radius: " + str(myrads))
plt.plot(sab_balanced, ttlc_balanced_predicted, 'r.', markersize= 10)
plt.savefig(str(myrads) + '_simulated_onsettimes_6s_midline_80_1_chosenparams.png', dpi = 300)
plt.show()
