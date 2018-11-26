import sys 
import time

##add path so do not need to replicate sound files
rootpath = 'C:\VENLAB data\shared_modules'
sys.path.append(rootpath)

#Purpose of File is to pilot cognitive load task. 
#File interfaces with module 'Count_Adjustable'
#Experiment name: Orca18

import viz # vizard library
import numpy as np # numpy library - such as matrix calculation
import random # python library
import vizdriver_Distractor_director as vizdriver_Distractor # vizard library
import viztask # vizard library
import math as mt # python library
import AudioDistractor_Sparrow as AudioDistractor #distractor task

viz.go()

# Prompt for filename
ExpID = "Orca18_Pilot"
DEG_SYM = unichr(176).encode("latin-1")
pname = viz.input('Participant code: ')
file_prefix = str(ExpID) + "_" + str(pname)

####SETUP DRIVER ######

driver = vizdriver_Distractor.Driver(distractor) #initialise driver

global waitButton1, waitButton2
#wait for a gear pad press.
driverjoy = driver.getJoy()		#Set joystick gear pad callbacks
waitButton1 = vizdriver_Distractor.waitJoyButtonDown(5,driverjoy)
waitButton2 = vizdriver_Distractor.waitJoyButtonDown(6,driverjoy)

#### ORDER TRIALS #####

##Create array of trials.
TrialsPerCondition = 3 #how many trials do we want with this? 
FACTOR_targetoccurence = [.2, .4, .6] #probability of response frequency
FACTOR_targetnumber = [1, 2, 3] #number of targets to keep count of.

NCndts = len(FACTOR_targetoccurence) * len(FACTOR_targetnumber)	
ConditionList = range(NCndts) 

#automatically generate factor lists so you can adjust levels using the FACTOR variables
ConditionList_targetoccurence = np.repeat(FACTOR_targetoccurence, len(FACTOR_targetnumber)	)
ConditionList_targetnumber = np.tile(FACTOR_targetnumber, len(FACTOR_targetoccurence)	)

print (ConditionList_targetoccurence)
print (ConditionList_targetnumber)

TotalN = NCndts * TrialsPerCondition

TRIALSEQ = range(0,NCndts)*TrialsPerCondition
np.random.shuffle(TRIALSEQ)

TotalDrivingTime = 20 #including delay (3sec) for initializing steer

def runtrials():	

	for i in TRIALSEQ:	
		
		trial_targetoccurence = ConditionList_targetoccurence[TRIALSEQ[i]] #set occurence parameter for the trial.
		trial_targetnumber = ConditionList_targetnumber[TRIALSEQ[i]] #set target number for the trial.
		

		#### at here! Need to recode the distraction module so that each trial is a class.		

		viz.pause()
		
		d = viz.Data
		yield viztask.waitAny([waitButton2],d)#,waitButton2],d) #need to do this twice
		print 'pressed once'
		
		e = viz.Data
		yield viztask.waitAny([waitButton1],e)#,waitButton2],e) #need to do this twice
		print 'pressed twice'
		
		distractor.Question.message('\n \n \n \n \n \n \n \n Let Go!')
		distractor.lblscore.message('')
		
		yield viztask.waitTime(.5)
		distractor.EoTScreen.visible(viz.OFF)
		distractor.Question.visible(viz.OFF)
		distractor.lblscore.visible(viz.OFF)
		
		viz.play()
				
		
		if edge == 1:
			inside_edge.remove()
			outside_edge.remove()
		
		fixation_change_flag = 0 # initialization of fixation cross flag for near-far condition
		
		groundplane.endAction() # end spinaction.
		yield driver.function_initialize_steering()

		
		#addfix()   # fixation setting
		driver.reset() #reset pause counter
		
	else:	
		
		viz.quit() ##otherwise keeps writting data onto last file untill ESC

viztask.schedule(runtrials())
