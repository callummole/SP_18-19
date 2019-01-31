"""
Script to run silent failure paradigm, with cognitive load. Every trial begins with a period of automation. 

The Class myExperiment handles execution of the experiment.

This script relies on the following modules:

For eyetracking - eyetrike_calibration_standard.py; eyetrike_accuracy_standard.py; also the drivinglab_pupil plugin.

For perspective correct rendering - myCave.py

For motion through the virtual world - vizdriver.py

"""
import sys
from timeit import default_timer as timer

rootpath = 'C:\\VENLAB data\\shared_modules\\Logitech_force_feedback'
sys.path.append(rootpath)
rootpath = 'C:\\VENLAB data\\shared_modules'
sys.path.append(rootpath)
rootpath = 'C:\\VENLAB data\\shared_modules\\pupil\\capture_settings\\plugins\\drivinglab_pupil\\'
sys.path.append(rootpath)

import viz # vizard library
import numpy as np # numpy library - such as matrix calculation
import random # python library
import vizdriver_Orca18 as vizdriver # vizard library
import viztask # vizard library
import math as mt # python library
import vizshape
import vizact
import vizmat
import myCave
import pandas as pd
from vizTrackMaker import vizBend as Bend
#import PPinput

def LoadEyetrackingModules():

	"""load eyetracking modules and check connection"""

	from eyetrike_calibration_standard import Markers, run_calibration
	from eyetrike_accuracy_standard import run_accuracy
	from UDP_comms import pupil_comms

	###Connect over network to eyetrike and check the connection
	comms = pupil_comms() #Initiate a communication with eyetrike	
	#Check the connection is live
	connected = comms.check_connection()

	if not connected:
		print("Cannot connect to Eyetrike. Check network")
		raise Exception("Could not connect to Eyetrike")
	else:
		pass	
	#markers = Markers() #this now gets added during run_calibration				
	
def LoadCave():
	"""loads myCave and returns Caveview"""

	#set EH in myCave
	cave = myCave.initCave()
	caveview = cave.getCaveView()
	return (caveview)

def LoadAutomationModules():

	"""Loads automation modules and initialises automation thread"""

	import logitech_wheel_threaded
	
	handle = viz.window.getHandle()
	mywheel = logitech_wheel_threaded.steeringWheelThreaded(handle)	
	mywheel.init() #Initialise the wheel
	mywheel.start() #Start the wheels thread

	#centre the wheel at start of experiment
	mywheel.set_position(0) #Set the pd control target
	mywheel.control_on()

	return(mywheel)

def GenerateConditionLists(FACTOR_radiiPool, FACTOR_YawRate_offsets, TrialsPerCondition):
	"""Based on two factor lists and TrialsPerCondition, create a factorial design and return trialarray and condition lists"""

	NCndts = len(FACTOR_radiiPool) * len(FACTOR_YawRate_offsets)	
	print ("number of conditiosn", NCndts)
#	ConditionList = range(NCndts) 

	#automatically generate factor lists so you can adjust levels using the FACTOR variables
	ConditionList_radii = np.repeat(FACTOR_radiiPool, len(FACTOR_YawRate_offsets)	)
	ConditionList_YawRate_offsets = np.tile(FACTOR_YawRate_offsets, len(FACTOR_radiiPool)	)

	print (ConditionList_radii)
	print (ConditionList_YawRate_offsets)

	TotalN = NCndts * TrialsPerCondition

	TRIALSEQ = range(1,NCndts+1)*TrialsPerCondition
	np.random.shuffle(TRIALSEQ)

	direc = [1,-1]*(TotalN/2) #makes half left and half right.
	np.random.shuffle(direc) 

	TRIALSEQ_signed = np.array(direc)*np.array(TRIALSEQ)
	
	print("TrialSeq_signed", TRIALSEQ_signed)

	return (TRIALSEQ_signed, ConditionList_radii, ConditionList_YawRate_offsets)

# ground texture setting
def setStage():
	
	"""Creates grass textured groundplane"""
	
	###should set this hope so it builds new tiles if you are reaching the boundary.
	fName = 'C:/VENLAB data/shared_modules/textures/strong_edge.bmp'
	
	# add groundplane (wrap mode)
	groundtexture = viz.addTexture(fName)
	groundtexture.wrap(viz.WRAP_T, viz.REPEAT)	
	groundtexture.wrap(viz.WRAP_S, viz.REPEAT)	
	
	groundplane = viz.addTexQuad() ##ground for right bends (tight)
	tilesize = 500
	planesize = tilesize/5
	groundplane.setScale(tilesize, tilesize, tilesize)
	groundplane.setEuler((0, 90, 0),viz.REL_LOCAL)
	#groundplane.setPosition((0,0,1000),viz.REL_LOCAL) #move forward 1km so don't need to render as much.
	matrix = vizmat.Transform()
	matrix.setScale( planesize, planesize, planesize )
	groundplane.texmat( matrix )
	groundplane.texture(groundtexture)
	groundplane.visible(1)	
	
	viz.clearcolor(viz.SKYBLUE)
	
	return groundplane
	
def BendMaker(radlist):
	
	"""makes left and right roads  for for a given radii and return them in a list"""
	
	leftbendlist = []
	rightbendlist = []
	grey = [.8,.8,.8]	

	for r in radlist:
		rightbend = Bend(startpos = [0,0], rads = r, x_dir = 1, colour = grey, road_width=3.0)
			
		rightbendlist.append(rightbend)

		leftbend = Bend(startpos = [0,0], rads = r, x_dir = -1, colour = grey, road_width=3.0)
		
			
		leftbendlist.append(leftbend)
	
	return leftbendlist,rightbendlist 

class myExperiment(viz.EventClass):

	def __init__(self, eyetracking, practice, exp_id, autowheel, debug, ppid = 1):

		viz.EventClass.__init__(self)
	
		self.EYETRACKING = eyetracking
		self.PRACTICE = practice		
		self.EXP_ID = exp_id
		self.AUTOWHEEL = autowheel
		self.DEBUG = debug


		if EYETRACKING == True:	
			LoadEyetrackingModules()

		self.PP_id = ppid
		self.TrialLength = 15 #length of time that road is visible. Constant throughout experiment
	
		#### PERSPECTIVE CORRECT ######
		self.caveview = LoadCave() #this module includes viz.go()

		
		if self.AUTOWHEEL:
			self.Wheel = LoadAutomationModules()
		else:
			self.Wheel = None		

		# #BirdsEye
		# self.caveview.setPosition([0,100,0])
		# self.caveview.setEuler([0,90,0])


		##### SET CONDITION VALUES #####
		self.FACTOR_radiiPool = [40] # A sharp and gradual bend
		self.FACTOR_YawRate_offsets = [0] #6 yawrate offsets, specified in degrees per second.
		self.TrialsPerCondition = 6
		[trialsequence_signed, cl_radii, cl_yawrates]  = GenerateConditionLists(self.FACTOR_radiiPool, self.FACTOR_YawRate_offsets, self.TrialsPerCondition)

		self.TRIALSEQ_signed = trialsequence_signed #list of trialtypes in a randomised order. -ve = leftwards, +ve = rightwards.
		self.ConditionList_radii = cl_radii
		self.ConditionList_YawRate_offsets = cl_yawrates

		##### ADD GRASS TEXTURE #####
		gplane1 = setStage()
		self.gplane1 = gplane1		

		##### MAKE BEND OBJECTS #####
		[leftbends,rightbends] = BendMaker(self.FACTOR_radiiPool)
		self.leftbends = leftbends
		self.rightbends = rightbends 

		self.callback(viz.TIMER_EVENT,self.updatePositionLabel)
		self.starttimer(0,1.0/60.0,viz.FOREVER) #self.update position label is called every frame.
		self.UPDATELOOP = False

		#add audio files
		self.manual_audio = viz.addAudio('C:/VENLAB data/shared_modules/textures/490.wav') #high beep to signal change
		self.manual_audio.stoptime(.2) #cut it short for minimum interference.
		self.manual_audio.volume(.5)
		
		####### DATA SAVING ######
		datacolumns = ['ppid', 'radius','yawrate_offset','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'WheelCorrection', 'AutoFlag']
		self.datacolumns = datacolumns
		self.Output = None #dataframe that gets renewed each trial.		
		#self.Output = pd.DataFrame(columns=datacolumns) #make new empty EndofTrial data

		### parameters that are set at the start of each trial ####
		self.Trial_radius = 0
		self.Trial_YawRate_Offset = 0 				
		self.Trial_N = 0
		self.Trial_trialtype_signed = 0			
		self.Trial_Timer = 0 #keeps track of trial length. 
		self.Trial_BendObject = None		
		
		#### parameters that are updated each timestamp ####
		self.Current_pos_x = 0
		self.Current_pos_z = 0
		self.Current_yaw = 0
		self.Current_SWA = 0
		self.Current_Time = 0
		self.Current_RowIndex = 0
		self.Current_YawRate_seconds = 0
		self.Current_TurnAngle_frames = 0
		self.Current_distance = 0
		self.Current_dt = 0
		self.Current_WheelCorrection = 0 # mismatch between virtual yawrate and real wheel angle. 

		#playback variables.
		self.playbackindex = 0 #could use section index for this? 				
		self.playbackdata = "" #filename.
		self.OpenTrial("Midline_40_4.csv")
		self.AUTOMATION = True
		#for now, for ease use one file.
		self.SWA_readout = self.playbackdata.get("SWA")
		self.YR_readout = self.playbackdata.get("YawRate_seconds")
		self.playbacklength = len(self.SWA_readout)		

		self.callback(viz.EXIT_EVENT,self.CloseConnections) #if exited, save the data. 


		if self.DEBUG:
			#add text to denote status.
			self.txtStatus = viz.addText("Condition",parent = viz.SCREEN)
			self.txtStatus.setPosition(.7,.2)
			self.txtStatus.fontSize(36)		
			

	def runtrials(self):
		"""Loops through the trial sequence"""
		
		if self.EYETRACKING:
			filename = str(self.EXP_ID) + "_Calibration" #+ str(demographics[0]) + "_" + str(demographics[2]) #add experimental block to filename
			print (filename)
			yield run_calibration(comms, filename)
			yield run_accuracy(comms, filename)		

		self.driver = vizdriver.Driver(self.caveview)	
		viz.MainScene.visible(viz.ON,viz.WORLD)		
		
	
		if self.EYETRACKING: 
			comms.start_trial()
		
		for i, trialtype_signed in enumerate(self.TRIALSEQ_signed):
			#import vizjoy		
			print("Trial: ", str(i))
			print("TrialType: ", str(trialtype_signed))
			
			trialtype = abs(trialtype_signed)

			#trialtype is indexed from one. so need to minus one from it.
			trial_radii = self.ConditionList_radii[trialtype-1] #set radii for that trial
			trial_yawrate_offset = self.ConditionList_YawRate_offsets[trialtype-1] #set target number for the trial.

			print(str([trial_radii, trial_yawrate_offset]))

			txtDir = ""
			
			#print ("Length of bend array:", len(self.rightbends))

			radius_index = self.FACTOR_radiiPool.index(trial_radii)

			#choose correct road object.
			if trialtype_signed > 0: #right bend
				trialbend = self.rightbends[radius_index]
				txtDir = "R"
			else:
				#trialbend = self.leftbends[radius_index]
				#txtDir = "L"
				trialbend = self.rightbends[radius_index]
				txtDir = "R"

			trialbend.ToggleVisibility(viz.ON)
						
			if trial_radii > 0: #if trial_radii is above zero it is a bend, not a straight 
				msg = "Radius: " + str(trial_radii) + txtDir + '_' + str(trial_yawrate_offset)
			else:
				msg = "Radius: Straight" + txtDir + '_' + str(trial_yawrate_offset)
#			txtCondt.message(msg)	

			#update class#
			self.Trial_N = i
			self.Trial_radius = trial_radii
			self.Trial_YawRate_Offset = trial_yawrate_offset			
			self.Trial_BendObject = trialbend			

			#renew data frame.
			self.Output = pd.DataFrame(index = range(self.TrialLength*60), columns=self.datacolumns) #make new empty EndofTrial data

			yield viztask.waitTime(.5) #pause at beginning of trial

			self.driver.setAutomation(True)
			self.AUTOMATION = True
			self.Wheel.control_on()

			if self.DEBUG:
				self.txtStatus.message("Automation:" + str(self.AUTOMATION))

			#here we need to annotate eyetracking recording.

			self.UPDATELOOP = True #

			def PlaybackReached():
				"""checks for playback limit or whether automation has been disengaged"""

				end = False

				#check whether automation has been switched off. 				
				if self.playbackindex >= self.playbacklength:
					end = True

				return(end)
			
			def CheckDisengage():
				"""checks automation status of driver class """

				end = False
				auto = self.driver.getAutomation()
				if auto == False:
					
					self.AUTOMATION = auto
					#switch wheel control off, because user has disengaged
					#begin = timer()
					self.Wheel.control_off()
					#print ("WheelControlOff", timer() - begin)
					end = True
				
				return (end)

			#create viztask functions.
			waitPlayback = viztask.waitTrue( PlaybackReached )
			waitDisengage = viztask.waitTrue( CheckDisengage )

			
			d = yield viztask.waitAny( [ waitPlayback, waitDisengage ] )		
        
			if d.condition is waitPlayback:
				print ('Playback Limit Reached')
			elif d.condition is waitDisengage:
				print ('Automation Disengaged')
				
				if self.DEBUG:
					self.txtStatus.message("Automation:" + str(self.AUTOMATION))

				#begin = timer()
				viz.director(self.SingleBeep)
				#print ("SingleBeep: ", timer()-begin)
				#use waitAny again: check for running out of road or taking over.
				#begin = timer()
				def RoadRunout():
					"""temporary HACK function to check whether the participant has ran out of road"""

					end = False
					if self.Trial_Timer > 15:
						end = True
					
					return(end)

				waitRoad = viztask.waitTrue (RoadRunout)
				waitManual = viztask.waitTime(5)

				#print ("Create function: ", timer()- begin)

				d = yield viztask.waitAny( [ waitRoad, waitManual ] )
				if d.condition is waitRoad:
					print ('Run out of Road')
				elif d.condition is waitManual:
					print ('Manual Time Elapsed')

			##### END TRIAL ######
			
			self.UPDATELOOP = False
			
			self.Trial_BendObject.ToggleVisibility(viz.OFF)	

			##reset trial. Also need to annotate each eyetracking trial.			
			
			trialdata = self.Output.copy()
			fname = 'Data//OrcaPilot_' + str(self.Trial_radius) + '_' + str(self.Trial_N) + '.csv'

			#print (trialdata)
			#print (fname)
			viz.director(self.SaveData, trialdata, fname)
			
			#reset row index. and trial parameters
			self.Current_RowIndex = 0
			self.playbackindex = 0
			self.Trial_Timer = 0 

			self.ResetDriverPosition()
			#self.SaveData(trialdata)
	
		#loop has finished.
		CloseConnections(self.EYETRACKING)
		#viz.quit() 

	def getNormalisedEuler(self):
		"""returns three dimensional euler on 0-360 scale"""
		
		euler = self.caveview.getEuler()
		
		euler[0] = vizmat.NormAngle(euler[0])
		euler[1] = vizmat.NormAngle(euler[1])
		euler[2] = vizmat.NormAngle(euler[2])

		return euler	

	def ResetDriverPosition(self):
		"""Sets Driver Position and Euler to original start point"""
		self.driver.reset()

	def OpenTrial(self,filename):
		"""opens csv file"""

		print ("Loading file: " + filename)
		self.playbackdata = pd.read_csv("Data//"+filename)

	def RecordData(self):
		
		"""Records Data into Dataframe"""

		#datacolumns = ['ppid', 'radius','occlusion','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA']
		output = [self.PP_id, self.Trial_radius, self.Trial_YawRate_Offset, self.Trial_N, self.Current_Time, self.Trial_trialtype_signed, 
		self.Current_pos_x, self.Current_pos_z, self.Current_yaw, self.Current_SWA, self.Current_YawRate_seconds, self.Current_TurnAngle_frames, 
		self.Current_distance, self.Current_dt, self.Current_WheelCorrection, self.AUTOMATION] #output array.
		
		#print ("length of output: ", len(output))
		#print ("size of self.Output: ", self.Output.shape)

		#print(output)
		self.Output.loc[self.Current_RowIndex,:] = output #this dataframe is actually just one line. 		
	
	# def SaveData(self, data, filename):

	# 	"""Saves Current Dataframe to csv file"""

	# 	data = data.dropna() #drop any trailing space.		
	# 	data.to_csv(filename)

	def SaveData(self, data, filename):

		"""Saves Current Dataframe to csv file"""

		data = data.dropna() #drop any trailing space.		
		data.to_csv(filename)

		print ("Saved file: ", filename)

	def updatePositionLabel(self, num):
		
		"""Timer function that gets called every frame. Updates parameters for saving"""

		"""Here need to bring in steering bias updating from Trout as well"""
		dt = viz.elapsed()
		print ("elapsed:", dt)
		self.Trial_Timer = self.Trial_Timer + dt

		if self.UPDATELOOP:
		
			#print("UpdatingPosition...")	
			#update driver view.
			if self.AUTOMATION:
				
				newSWApos = self.SWA_readout[self.playbackindex]

				#print ("Setting SWA position: ", newSWApos)
				
				self.Wheel.set_position(newSWApos)				
				newyawrate = self.YR_readout[self.playbackindex]
				
				self.playbackindex += 1
				
			else:
				newyawrate = None
				
			#begin = timer()
			UpdateValues = self.driver.UpdateView(YR_input = newyawrate) #update view and return values used for update
			#print ("Update Values: ", timer() - begin)
			# get head position(x, y, z)
			pos = self.caveview.getPosition()				
			ori = self.getNormalisedEuler()	
										
			### #update Current parameters ####
			self.Current_pos_x = pos[0]
			self.Current_pos_z = pos[2]
			self.Current_SWA = UpdateValues[4]
			self.Current_yaw = ori[0]
			self.Current_RowIndex += 1
			self.Current_Time = viz.tick()
			self.Current_YawRate_seconds = UpdateValues[0]
			self.Current_TurnAngle_frames = UpdateValues[1]
			self.Current_distance = UpdateValues[2]
			self.Current_dt = UpdateValues[3]
			self.Current_WheelCorrection = UpdateValues[5]


			self.RecordData() #write a line in the dataframe.	
				

	def SingleBeep(self):
		"""play single beep"""
		self.manual_audio.play()

	def CloseConnections(self):
		
		"""Shuts down EYETRACKING and wheel threads then quits viz"""		
		
		print ("Closing connections")
		if self.EYETRACKING: 
			comms.stop_trial() #closes recording			
		
		#kill automation
		if self.AUTOWHEEL:
			self.Wheel.thread_kill() #This one is mission critical - else the thread will keep going 
			self.Wheel.shutdown()
		viz.quit()
	
if __name__ == '__main__':

	###### SET EXPERIMENT OPTIONS ######	
	EYETRACKING = False
	AUTOWHEEL = True
	PRACTICE = True	
	EXP_ID = "Orca18"
	DEBUG = True

	if PRACTICE == True: # HACK
		EYETRACKING = False 

	myExp = myExperiment(EYETRACKING, PRACTICE, EXP_ID, AUTOWHEEL, DEBUG)

	#viz.callback(viz.EXIT_EVENT,CloseConnections, myExp.EYETRACKING)

	viztask.schedule(myExp.runtrials())

