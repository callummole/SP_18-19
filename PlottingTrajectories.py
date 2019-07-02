"""
Script to plot Track Simulation of various bias onset times, pre-recorded vehicle trajectories, and yaw-rates biases. 


"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

#http://jonathansoma.com/lede/algorithms-2017/classes/fuzziness-matplotlib/understand-df-plot-in-pandas/

simresults = pd.read_csv('Data//Untouched_Trajectories.csv')

simresults = simresults.loc[simresults['radius']==80]
for g, d in simresults.groupby('AutoFile'):
    d = d.iloc[:180]
    plt.plot(d.YawRate_radspersec.values, label = g)
plt.legend()
plt.show()

#fig, ax = plt.subplots()
#simresults.groupby('AutoFile').plot(x='f', y='YawRate_radspersec', ax=ax, legend=False)

#plt.show()