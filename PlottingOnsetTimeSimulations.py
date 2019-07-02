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

onset_time = 6 #fixed onset time.
simresults= simresults[simresults[:,2]==onset_time]

yr = -np.rad2deg(8.0 / myrads)
print(yr)
#retrieve ttlc for 3.141. 
yr_mask = simresults[simresults[:,0]<= yr]
ttlc_max = max(yr_mask[:,3])
print(ttlc_max)


plt.figure(2)
plt.plot(simresults[:,0], simresults[:,3], 'k.', markersize=5, alpha = .2)
plt.xlabel("Yaw Rate Offset (deg/s)")
plt.ylabel("Time from Onset to Lane Crossing (s)")
plt.title("Radius: " + str(myrads))
plt.plot(yr, ttlc_max, 'r.', markersize= 10)
plt.savefig(str(myrads) + '_simulated_onsettimes_6s_midline_80_1.png', dpi = 300)
plt.show()
