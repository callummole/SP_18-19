"""
Script to plot Track Simulation of various bias onset times, pre-recorded vehicle trajectories, and yaw-rates biases. 


"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


myrads = 40

filename = "SimResults_OnsetTimes_"+str(myrads)+".csv"

#columns are: yr_offset, file_i, onsettime, time_til_crossing
simresults = genfromtxt(filename, delimiter=',')

#what to plot?