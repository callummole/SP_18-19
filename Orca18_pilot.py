import sys 
import time

##add path so do not need to replicate sound files
rootpath = 'C:\VENLAB data\shared_modules'
sys.path.append(rootpath)

#Purpose of File is to pilot cognitive load task. 
#File interfaces with module 'Count_Adjustable', which serves to load a trial at a time. 
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

driver = vizdriver_Distractor.Driver() #initialise driver

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

TrialTime = 20 #including delay (3sec) for initializing steer

def runtrials():	

	for i in TRIALSEQ:	
		
		trial_targetoccurence = ConditionList_targetoccurence[TRIALSEQ[i]] #set occurence parameter for the trial.
		trial_targetnumber = ConditionList_targetnumber[TRIALSEQ[i]] #set target number for the trial.
		

		Distractor.StartTrial(trial_targetoccurence, trial_targetnumber, fname = file_prefix + "_" + i, TrialTime = TrialTime)		

		def EndTrial():
			"""checks whether distraction task is finished, then waits for input"""
			END = Distractor.GetState()			
			if END:						

				# the following code should be flexible, depending on the amount of targets. 
				d = viz.Data
				yield viztask.waitAny([waitButton2],d)#,waitButton2],d) #need to do this twice
				print 'pressed once'		

				e = viz.Data
				yield viztask.waitAny([waitButton1],e)#,waitButton2],e) #need to do this twice
				print 'pressed twice'

		vizact.ontimer((1.0/30.0),QuitViz)
		
		# distractor.Question.message('\n \n \n \n \n \n \n \n Let Go!')
		# distractor.lblscore.message('')
		
		# yield viztask.waitTime(.5)
		# distractor.EoTScreen.visible(viz.OFF)
		# distractor.Question.visible(viz.OFF)
		# distractor.lblscore.visible(viz.OFF)
		
		#viz.play()		
	else:	
		
		viz.quit() ##otherwise keeps writting data onto last file untill ESC

viztask.schedule(runtrials())
