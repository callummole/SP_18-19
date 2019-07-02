"""
Script to plot Track Simulation of various bias onset times, pre-recorded vehicle trajectories, and yaw-rates biases. 


"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


myrads = 40

filename = "SimResults_OnsetTimes_"+str(myrads)+".csv"

#columns are: yr_offset, file_i, onsettime, time_til_crossing
simresults = np.genfromtxt(filename, delimiter=',')

#what to plot?
#filemask = simresults[:,1] == 0 #first file mask

#simresults_file = simresults[filemask]
        
#plot yr and time til crossing functions.
plt.figure(2)
plt.plot(simresults[:,3], simresults[:,0], 'k.', markersize=5, alpha = .2)
plt.ylabel("Yaw Rate Offset (deg/s)")
plt.xlabel("Time from Onset to Lane Crossing (s)")
plt.title("Radius: " + str(myrads))
plt.savefig(str(myrads) + '_Sims_OnsetTimes.png', dpi = 300)
plt.show()
