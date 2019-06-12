"""
Script to plot Track Simulation of various bias onset times, pre-recorded vehicle trajectories, and yaw-rates biases. 


"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

#http://jonathansoma.com/lede/algorithms-2017/classes/fuzziness-matplotlib/understand-df-plot-in-pandas/

simresults = pd.read_csv('Data//Untouched_Trajectories.csv')

fig, ax = plt.subplots()
simresults.groupby('UID').plot(x='World_x', y='World_z', ax=ax, legend=False)

plt.show()