"""
Script to plot Track Simulation of various bias onset times, pre-recorded vehicle trajectories, and yaw-rates biases. 
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


myrads = 40

#filename = "SimResults_OnsetTimes_"+str(myrads)+".csv"
filename = "SimResults_onset_6_traj_40_0.csv"

#columns are: yr_offset, file_i, onsettime, time_til_crossing
simresults = np.genfromtxt(filename, delimiter=',')

#what to plot?
#filemask = simresults[:,1] == 0 #first file mask

#simresults_file = simresults[filemask]
        
#plot yr and time til crossing functions.

onset_time = 6 #fixed onset time.
simresults= simresults[simresults[:,2]==onset_time]

yr = 3.141
#retrieve ttlc for 3.141. 
yr_mask = simresults[simresults[:,3]<= yr]
yr_mask = yr_mask[yr_mask[:,0]< 0]
ttlc_max = max(yr_mask[:,0])
print(ttlc_max)


plt.figure(2)
plt.plot(simresults[:,0], simresults[:,3], 'k.', markersize=5, alpha = .2)
plt.ylabel("Yaw Rate Offset (deg/s)")
plt.xlabel("Time from Onset to Lane Crossing (s)")
plt.title("Radius: " + str(myrads))
plt.hlines(y = yr, xmin = -4, xmax = ttlc_max, color ='r')
plt.vlines(x = ttlc_max, ymin = 2, ymax = yr, color ='r')
plt.savefig(str(myrads) + '_simulated_onsettimes_6s_midline_40_0.png', dpi = 300)
plt.show()
