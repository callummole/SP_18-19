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
import vizdriver_Orca18_pilotnosteering as vizdriver # vizard library
import viztask # vizard library
import math as mt # python library
import Count_Adjustable #distractor task

viz.go()
viz.window.setFullscreenMonitor(2)		
viz.window.setFullscreen(viz.ON)

# Prompt for filename
ExpID = "Orca18_Distractor"
DEG_SYM = unichr(176).encode("latin-1")
pname = viz.input('Participant code: ')


########### CHANGE HERE TO TOGGLE PRACTICE ANDS BLOCK #############

#SP CHANGE HERE

PRACTICE = False #if practice, they only do one of each.
BLOCK = 2 #1 or 2. #switch to not save over previous file.
DISTRACTOR_TYPE = "Hard" #"Easy" (1 target) or "Hard" (3 targets). 

#### ORDER TRIALS #####


#previous data was 40%, 2 targets

#A short pilot experiment suggested that target number, not target occurence, should be manipulated.

##Create array of trials.
if PRACTICE:
	TrialsPerCondition = 1 #for practice, do one trial each
	ExpID = ExpID + '_' + 'PRAC' #file name	
	if DISTRACTOR_TYPE == "Easy":
		FACTOR_targetnumber = [1] #number of targets to keep count of.
	elif DISTRACTOR_TYPE == "Hard":
		FACTOR_targetnumber = [3] #number of targets to keep count of.
	else:
		raise Exception("Distractor Type must be Easy or Hard. Case sensitive")
else:
	TrialsPerCondition = 3 #for the isolated task, do three trials each. 
	ExpID = ExpID + '_' + str(BLOCK)
	FACTOR_targetnumber = [1, 3] #number of targets to keep count of.

FACTOR_targetoccurence_prob = [.4] #probability of response frequency

##################

file_prefix = str(ExpID) + "_" + str(pname)


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

TrialTime = 15 
StartScreenTime = 2
TotalTrialTime = TrialTime+StartScreenTime

Distractor = Count_Adjustable.Distractor(file_prefix, max(FACTOR_targetnumber), pname, triallength= TrialTime, ntrials = TrialsPerCondition, startscreentime = StartScreenTime)

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
		

		Distractor.StartTrial(trial_targetoccurence_prob, trial_targetnumber, trialn = i)	#starts trial

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
