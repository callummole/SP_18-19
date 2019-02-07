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
import Count_Adjustable #distractor task

rootpath = 'C:\\VENLAB data\\TrackMaker\\'
sys.path.append(rootpath)

from vizTrackMaker import vizBend, vizStraight
import random
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
	
def BendMaker(radlist, start):
	
	"""makes left and right roads  for for a given radii and return them in a list"""
	
	leftbendlist = []
	rightbendlist = []
	grey = [.6,.6,.6]	

	for r in radlist:
		rightbend = vizBend(startpos = start, rads = r, x_dir = 1, colour = grey, road_width=0, primitive_width=1.5)#, texturefile='strong_edge_soft.bmp')
		rightbend.setAlpha(.5)
			
		rightbendlist.append(rightbend)

		leftbend = vizBend(startpos = start, rads = r, x_dir = -1, colour = grey, road_width=0, primitive_width=1.5)#, texturefile='strong_edge_soft.bmp')
		
		leftbend.setAlpha(.5)	
		leftbendlist.append(leftbend)
			
	return leftbendlist,rightbendlist 

class myExperiment(viz.EventClass):

	def __init__(self, eyetracking, practice, exp_id, autowheel, debug, distractor_type = None, ppid = 1):

		viz.EventClass.__init__(self)
	
		self.EYETRACKING = eyetracking
		self.PRACTICE = practice		
		self.EXP_ID = exp_id
		self.AUTOWHEEL = autowheel
		self.DEBUG = debug
		if distractor_type == "None":
			distractor_type = None
		self.DISTRACTOR_TYPE = distractor_type

		if self.DISTRACTOR_TYPE not in (None, "Easy", "Hard"):
			raise Exception ("Unrecognised Distractor Type. Specify 'None', 'Easy', or 'Hard'. Case sensitive.")
			#pass
		
		###set distractor parameters.
		if self.DISTRACTOR_TYPE == "Easy":
			self.targetoccurence_prob = .4
			self.targetnumber = 1
		elif self.DISTRACTOR_TYPE == "Hard":
			self.targetoccurence_prob = .4
			self.targetnumber = 3
		self.StartScreenTime = 2		

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
		self.FACTOR_radiiPool = [40, 80] # A sharp and gradual bend
		#these offsets should yield lane crossing times of approximately [2.2s, 4.8s, 7s] (40r) and [2s, 4.5s, 7s] for 80s
		self.FACTOR_YawRate_offsets = [-5, 1, .5, 0, .5, 1, 5] #7 yawrate offsets, specified in degrees per second. 
		self.TrialsPerCondition = 6
		[trialsequence_signed, cl_radii, cl_yawrates]  = GenerateConditionLists(self.FACTOR_radiiPool, self.FACTOR_YawRate_offsets, self.TrialsPerCondition)

		self.TRIALSEQ_signed = trialsequence_signed #list of trialtypes in a randomised order. -ve = leftwards, +ve = rightwards.
		self.ConditionList_radii = cl_radii
		self.ConditionList_YawRate_offsets = cl_yawrates

		##### ADD GRASS TEXTURE #####
		gplane1 = setStage()
		self.gplane1 = gplane1		
		
		#### MAKE STRAIGHT OBJECT ####
		L = 16#2sec.
		self.Straight = vizStraight(startpos = [0,0], primitive_width=1.5, road_width = 0, length = L, colour = [.6, .6, .6])#, texturefile='strong_edge_soft.bmp')
		self.Straight.ToggleVisibility(viz.ON)
		self.Straight.setAlpha(.5)

		##### MAKE BEND OBJECTS #####
		[leftbends,rightbends] = BendMaker(self.FACTOR_radiiPool, self.Straight.RoadEnd)
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
		datacolumns = ['ppid', 'radius','yawrate_offset','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'WheelCorrection', 'SteeringBias', 'Closestpt', 'AutoFlag', 'AutoFile', 'OnsetTime']
		self.datacolumns = datacolumns		
		self.Output = None #dataframe that gets renewed each trial.		
		#self.Output = pd.DataFrame(columns=datacolumns) #make new empty EndofTrial data

		self.OnsetTimePool = np.arange(4, 6.25, step = .25) #from 4 to 6s in .25s increments. The straight is ~ 2s of travel, so this is 2-4s into the bend.

		### parameters that are set at the start of each trial ####
		self.Trial_radius = 0
		self.Trial_YawRate_Offset = 0 				
		self.Trial_N = 0
		self.Trial_trialtype_signed = 0			
		self.Trial_Timer = 0 #keeps track of trial length. 
		self.Trial_BendObject = None		
		self.Trial_playbackdata = []
		self.Trial_YR_readout = []
		self.Trial_playbacklength = 0
		self.Trial_playbackfilename = ""
		self.Trial_midline = [] #midline for the entire track.
		self.Trial_OnsetTime = 0 #onset time for the trial.
		
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
		self.Current_steeringbias = 0
		self.Current_closestpt = 0

		self.Current_playbackindex = 0  		
		#playback variables.
				
		#self.playbackdata = "" #filename.
		self.YR_readouts_40 = []
		self.SWA_readouts_40 = []
		self.YR_readouts_80 = []
		self.SWA_readouts_80 = []
		self.PlaybackPool40 = ["Midline_40_0.csv","Midline_40_1.csv","Midline_40_2.csv","Midline_40_3.csv","Midline_40_4.csv","Midline_40_5.csv"]
		self.PlaybackPool80 = ["Midline_80_0.csv","Midline_80_1.csv","Midline_80_2.csv","Midline_80_3.csv","Midline_80_4.csv","Midline_80_5.csv"]

		
		#pre-load playback data at start of experiment.
		for i, file40 in enumerate(self.PlaybackPool40):

			#load radii 40
			data40 = self.OpenTrial(file40)
			self.YR_readouts_40.append(data40.get("YawRate_seconds"))
			self.SWA_readouts_40.append(data40.get("SWA"))

			#load radii 80
			file80 = self.PlaybackPool80[i]
			data80 = self.OpenTrial(file80)
			self.YR_readouts_80.append(data80.get("YawRate_seconds"))
			self.SWA_readouts_80.append(data80.get("SWA"))

		self.AUTOMATION = True
		self.txtMode.message('A')

		self.callback(viz.EXIT_EVENT,self.CloseConnections) #if exited, save the data. 


		if self.DEBUG:
			#add text to denote status.
			self.txtStatus = viz.addText("Condition",parent = viz.SCREEN)
			self.txtStatus.setPosition(.7,.2)
			self.txtStatus.fontSize(36)		

		self.txtMode = viz.addText("Mode",parent=viz.SCREEN)
		self.txtMode.setBackdrop(viz.BACKDROP_OUTLINE)
		self.txtMode.setBackdropColor(viz.BLACK)
		#set above skyline so I can easily filter glances to the letter out of the data
		self.txtMode.setPosition(.05,.52)
		self.txtMode.fontSize(36)
		self.txtMode.color(viz.WHITE)
		self.txtMode.visible(viz.ON)
			

	def runtrials(self):
		"""Loops through the trial sequence"""
		
		if self.EYETRACKING:
			filename = str(self.EXP_ID) + "_Calibration" #+ str(demographics[0]) + "_" + str(demographics[2]) #add experimental block to filename
			print (filename)
			yield run_calibration(comms, filename)
			yield run_accuracy(comms, filename)	


		#set up distractor task
		if self.DISTRACTOR_TYPE is not None:
			Distractor = Count_Adjustable.Distractor("distractor_", self.targetnumber, ppid = 1, startscreentime = self.StartScreenTime)
		else:
			Distractor = None
		self.driver = vizdriver.Driver(self.caveview, Distractor)	

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
		
			self.driver.setAutomation(True)
			self.AUTOMATION = True
			self.txtMode.message('A')
			if self.AUTOWHEEL:
				self.Wheel.control_on()

			if self.DISTRACTOR_TYPE is not None:
				if i == 0: #the first trial.
					Distractor.StartTrial(self.targetoccurence_prob, self.targetnumber, trialn = i, triallength = 20, displayscreen=True)	#starts trial								
					yield viztask.waitTrue(Distractor.getStartFlag)
				else:
					Distractor.StartTrial(self.targetoccurence_prob, self.targetnumber, trialn = i, triallength = 20, displayscreen=False)	#starts trial								


			radius_index = self.FACTOR_radiiPool.index(trial_radii)

			#choose correct road object.
			if trialtype_signed > 0: #right bend
				trialbend = self.rightbends[radius_index]
				txtDir = "R"
			else:
				trialbend = self.leftbends[radius_index]
				txtDir = "L"
				#trialbend = self.rightbends[radius_index]
				#txtDir = "R"

			trialbend.ToggleVisibility(viz.ON)
						
			if trial_radii > 0: #if trial_radii is above zero it is a bend, not a straight 
				msg = "Radius: " + str(trial_radii) + txtDir + '_' + str(trial_yawrate_offset)
			else:
				msg = "Radius: Straight" + txtDir + '_' + str(trial_yawrate_offset)
#			txtCondt.message(msg)	

			#pick radius
			self.Trial_radius = trial_radii
			

			#pick file. Put this in dedicated function. TODO: Should open all of these at the start of the file to save on processing.
			if self.Trial_radius == 40:
				i = random.choice(range(len(self.YR_readouts_40)))
				self.Trial_YR_readout = self.YR_readouts_40[i]
				self.Trial_SWA_readout = self.SWA_readouts_40[i]
				self.Trial_playbackfilename = self.PlaybackPool40[i]
				

			elif self.Trial_radius == 80:
				i = random.choice(range(len(self.YR_readouts_80)))
				self.Trial_YR_readout = self.YR_readouts_80[i]
				self.Trial_SWA_readout = self.SWA_readouts_80[i]
				self.Trial_playbackfilename = self.PlaybackPool80[i]

			else:
				raise Exception("Something bad happened")

			
			#update class#
			self.Trial_N = i			
			self.Trial_YawRate_Offset = trial_yawrate_offset			
			self.Trial_BendObject = trialbend	
			self.Trial_trialtype_signed	= trialtype_signed
			self.Trial_playbacklength = len(self.Trial_YR_readout)				
			self.Trial_midline = np.vstack((self.Straight.midline, self.Trial_BendObject.midline))
			self.Trial_OnsetTime = np.random.choice(self.OnsetTimePool, size=1)

			#renew data frame.
			self.Output = pd.DataFrame(index = range(self.TrialLength*60), columns=self.datacolumns) #make new empty EndofTrial data

			yield viztask.waitTime(.5) #pause at beginning of trial

			if self.DEBUG:
				self.txtStatus.message("Automation:" + str(self.AUTOMATION))

			#here we need to annotate eyetracking recording.

			#start distractor task for that trial
						

			self.UPDATELOOP = True #

			def PlaybackReached():
				"""checks for playback limit or whether automation has been disengaged"""

				end = False

				#check whether automation has been switched off. 				
				if self.Current_playbackindex >= self.Trial_playbacklength:
					end = True

				return(end)
			
			def CheckDisengage():
				"""checks automation status of driver class """

				end = False
				auto = self.driver.getAutomation()
				if auto == False:
					
					self.AUTOMATION = auto
					self.txtMode.message('M')
					#switch wheel control off, because user has disengaged
					#begin = timer()
					if self.AUOTWHEEL:
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


			##### END STEERING TASK ######
			
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
			self.Current_playbackindex = 0
			self.Trial_Timer = 0 

			self.ResetDriverPosition()

			##### INITIALISE END OF TRIAL SCREEN FOR DISTRACTOR TASK #######
			if self.DISTRACTOR_TYPE is not None:
				if self.AUTOWHEEL:
					self.Wheel.control_off()
				Distractor.EndofTrial() #throw up the screen to record counts.
				###interface with End of Trial Screen		
				pressed = 0
				while pressed < self.targetnumber:
					
					#keep looking for gearpad presses until pressed reaches trial_targetnumber
					print ("waiting for gear press")
					yield viztask.waitTrue(self.driver.getGearPressed)
					pressed += 1
					print('pressed ' + str(pressed))							
					
					Distractor.gearpaddown()

					self.driver.setGearPressed(False)
										
					yield viztask.waitTime(.5)
					#Distractor.EoTScreen_Visibility(viz.OFF)
				Distractor.RecordCounts()
	
		#loop has finished.
		self.CloseConnections()
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
		playbackdata = pd.read_csv("Data//"+filename)
		return (playbackdata)

	def RecordData(self):
		
		"""Records Data into Dataframe"""

		#'ppid', 'radius','yawrate_offset','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'WheelCorrection', 'SteeringBias', 'Closestpt' 'AutoFlag', 'AutoFile'#		
		output = [self.PP_id, self.Trial_radius, self.Trial_YawRate_Offset, self.Trial_N, self.Current_Time, self.Trial_trialtype_signed, 
		self.Current_pos_x, self.Current_pos_z, self.Current_yaw, self.Current_SWA, self.Current_YawRate_seconds, self.Current_TurnAngle_frames, 
		self.Current_distance, self.Current_dt, self.Current_WheelCorrection, self.Current_steeringbias, self.Current_closestpt, self.AUTOMATION, self.Trial_playbackfilename, self.Trial_OnsetTime] #output array.
		
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

	def calculatebias(self):

		#TODO: cut down on processing but only selecting a window of points based on lastmidindex.
		midlinedist = np.sqrt(((self.Current_pos_x-self.Trial_midline[:,0])**2)+((self.Current_pos_z-self.Trial_midline[:,1])**2)) #get a 4000 array of distances from the midline
		idx = np.argmin(abs(midlinedist)) #find smallest difference. This is the closest index on the midline.	

		closestpt = self.Trial_midline[idx,:] #xy of closest point
		dist = midlinedist[idx] #distance from closest point				

		CurveOrigin = self.Trial_BendObject.CurveOrigin

		#Sign bias from assessing if the closest point on midline is closer to the track origin than the driver position. Since the track is an oval, closer = understeering, farther = oversteering.
		middist_from_origin = np.sqrt(((closestpt[0]-CurveOrigin[0])**2)+((closestpt[1]-CurveOrigin[1])**2))  #distance of midline to origin
		pos_from_trackorigin = np.sqrt(((self.Current_pos_x-CurveOrigin[0])**2)+((self.Current_pos_z-CurveOrigin[1])**2)) #distance of driver pos to origin
		distdiff = middist_from_origin - pos_from_trackorigin #if driver distance is greater than closest point distance, steering position should be understeering
		steeringbias = dist * np.sign(distdiff)     

		return steeringbias, idx

	def updatePositionLabel(self, num):
		
		"""Timer function that gets called every frame. Updates parameters for saving"""

		"""Here need to bring in steering bias updating from Trout as well"""
		dt = viz.elapsed()
		#print ("elapsed:", dt)

		#print ("frame elapsed:", viz.getFrameElapsed())
		self.Trial_Timer = self.Trial_Timer + dt

		if self.UPDATELOOP:
		
			#print("UpdatingPosition...")	
			#update driver view.
			if self.AUTOMATION:
				
				newSWApos = self.Trial_SWA_readout[self.Current_playbackindex]
				newSWApos *= np.sign(self.Trial_trialtype_signed) #flip if left hand bend

				if self.AUTOWHEEL:
					self.Wheel.set_position(newSWApos)	#set steering wheel to position.

				#print ("Setting SWA position: ", newSWApos)				
							
				newyawrate = self.Trial_YR_readout[self.Current_playbackindex]

				#add yawrateoffset.
				if self.Trial_Timer > self.Trial_OnsetTime: #2 seconds into the bend.
					newyawrate += self.Trial_YawRate_Offset
				
				self.Current_playbackindex += 1

				newyawrate *= np.sign(self.Trial_trialtype_signed) #flip if left hand bend
												
			else:
				newyawrate = None

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
			self.Current_steeringbias, self.Current_closestpt = self.calculatebias()

		#	print ("SteeringBIas:", self.Current_steeringbias)

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

	#distractor_type takes 'None', 'Easy' (1 target, 40% probability), and 'Hard' (3 targets, 40% probability)
	DISTRACTOR_TYPE = "Hard" #Case sensitive

	if PRACTICE == True: # HACK
		EYETRACKING = False 

	myExp = myExperiment(EYETRACKING, PRACTICE, EXP_ID, AUTOWHEEL, DEBUG, DISTRACTOR_TYPE)

	#viz.callback(viz.EXIT_EVENT,CloseConnections, myExp.EYETRACKING)

	viztask.schedule(myExp.runtrials())

