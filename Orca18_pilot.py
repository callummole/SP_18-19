import sys 
import time

##add path so do not need to replicate sound files
rootpath = 'C:\\VENLAB data\\shared_modules'
sys.path.append(rootpath)

#Purpose of File is to pilot cognitive load task. 
#File interfaces with module 'Count_Adjustable', which serves to load a trial at a time. 
#Experiment name: Orca18

import viz # vizard library
import vizact # vizard library for timers
import numpy as np # numpy library - such as matrix calculation
import random # python library
import vizdriver_Orca18 as vizdriver # vizard library
import viztask # vizard library
import math as mt # python library
import Count_Adjustable #distractor task

viz.go()
viz.window.setFullscreenMonitor(2)		
viz.window.setFullscreen(viz.ON)

# Prompt for filename
ExpID = "Orca18_Pilot"
DEG_SYM = unichr(176).encode("latin-1")
pname = viz.input('Participant code: ')
file_prefix = str(ExpID) + "_" + str(pname)

#### ORDER TRIALS #####

##Create array of trials.
TrialsPerCondition = 3 #how many trials do we want with this? 
FACTOR_targetoccurence_prob = [.2, .4, .6] #probability of response frequency
FACTOR_targetnumber = [1, 2, 3] #number of targets to keep count of.

NCndts = len(FACTOR_targetoccurence_prob) * len(FACTOR_targetnumber)	
ConditionList = range(NCndts) 

#automatically generate factor lists so you can adjust levels using the FACTOR variables
ConditionList_targetoccurence_prob = np.repeat(FACTOR_targetoccurence_prob, len(FACTOR_targetnumber)	)
ConditionList_targetnumber = np.tile(FACTOR_targetnumber, len(FACTOR_targetoccurence_prob)	)

print (ConditionList_targetoccurence_prob)
print (ConditionList_targetnumber)

TotalN = NCndts * TrialsPerCondition

TRIALSEQ = range(0,NCndts)*TrialsPerCondition
np.random.shuffle(TRIALSEQ)

#### SETUP DRIVER & DISTRACTOR MODULES ######

TrialTime = 20 #including delay (3sec) for initializing steer
StartScreenTime = 2
TotalTrialTime = TrialTime+StartScreenTime

Distractor = Count_Adjustable.Distractor(file_prefix, max(FACTOR_targetnumber), pname, startscreentime = StartScreenTime)
driver = vizdriver.Driver(Distractor) #initialise driver

global waitButton1, waitButton2
#wait for a gear pad press.
driverjoy = driver.getJoy()		#Set joystick gear pad callbacks
waitButton1 = vizdriver.waitJoyButtonDown(5,driverjoy)
waitButton2 = vizdriver.waitJoyButtonDown(6,driverjoy)

def runtrials():	
	
	for i, trialtype in enumerate(TRIALSEQ):	
		
		print("Trial: ", str(i))
		print("TrialType: ", str(i))

		trial_targetoccurence_prob = ConditionList_targetoccurence_prob[trialtype] #set occurence parameter for the trial.
		trial_targetnumber = ConditionList_targetnumber[trialtype] #set target number for the trial.

		print(str([trial_targetoccurence_prob, trial_targetnumber]))
		

		Distractor.StartTrial(trial_targetoccurence_prob, trial_targetnumber, trialn = i, triallength = TrialTime)	#starts trial

		print ("Called Start Trial, now waiting")
		
		#yield viztask.waitTime(TotalTrialTime+.5) #this should always wait a little longer than the TrialTime, allowing the EndOfTrial function to get called in Count_Adjustable.
		

		def MonitorDistactor():
			"""will return true if it is the end of trial"""
			EoTFlag = Distractor.getFlag() # True if it's the end of the trial
			return (EoTFlag)

		yield viztask.waitTrue(MonitorDistactor)				


		###interface with End of Trial Screen		
		pressed = 0
		while pressed < trial_targetnumber:
			
			#keep looking for gearpad presses until pressed reaches trial_targetnumber
			print ("waiting for gear press")
			d = yield viztask.waitAny([waitButton1, waitButton2])
			pressed += 1
			print('pressed ' + str(pressed))		
			Distractor.gearpaddown(d.condition) #call gearpaddown. 

			yield viztask.waitTime(.5)
			#Distractor.EoTScreen_Visibility(viz.OFF)
		Distractor.RecordCounts()
		#Finished = True				
	else:	
		
		viz.quit() ##otherwise keeps writting data onto last file untill ESC

viztask.schedule(runtrials())
