"""
Practice file for Orca18_Main, silent failure paradigm.


Sinusoidal road. Three manual trials. Three automation trials where they can takeover by gear pad press.



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

import csv, io #for efficient data saving

import vizmatplot
import matplotlib.pyplot as plt

rootpath = 'C:\\VENLAB data\\TrackMaker\\'
sys.path.append(rootpath)

from vizTrackMaker import vizBend, vizStraight
import random
#import PPinput

def LoadEyetrackingModules():

	"""load eyetracking modules and check connection"""

	###Connect over network to eyetrike and check the connection
	comms = pupil_comms() #Initiate a communication with eyetrike	
	#Check the connection is live
	connected = comms.check_connection()

	if not connected:
		print("Cannot connect to Eyetrike. Check network")
		raise Exception("Could not connect to Eyetrike")
	else:
		pass	

	return(comms)
	
	
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
	fName = 'C:/VENLAB data/shared_modules/textures/ground_moon.png'
	
	# add groundplane (wrap mode)
	groundtexture = viz.addTexture(fName)
	groundtexture.wrap(viz.WRAP_T, viz.REPEAT)	
	groundtexture.wrap(viz.WRAP_S, viz.REPEAT)	
	groundtexture.anisotropy(16)
	
	groundplane = viz.addTexQuad() ##ground for right bends (tight)
	tilesize = 500
	#planesize = tilesize/5
	planesize = 40
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
		rightbend.setAlpha(.25)
			
		rightbendlist.append(rightbend)

		leftbend = vizBend(startpos = start, rads = r, x_dir = -1, colour = grey, road_width=0, primitive_width=1.5)#, texturefile='strong_edge_soft.bmp')
		
		leftbend.setAlpha(.25)	
		leftbendlist.append(leftbend)
			
	return leftbendlist,rightbendlist 

class myExperiment(viz.EventClass):

	def __init__(self, eyetracking, practice, exp_id, autowheel, debug, debug_plot, distractor_type = None, ppid = 1):

		viz.EventClass.__init__(self)
	
		self.EYETRACKING = eyetracking
		self.PRACTICE = practice		
		self.EXP_ID = exp_id
		self.AUTOWHEEL = autowheel
		self.DEBUG = debug
		self.DEBUG_PLOT = debug_plot
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

		if EYETRACKING:	
			#eyetracking modules loaded
			self.comms = LoadEyetrackingModules()

		self.PP_id = ppid
		self.TrialLength = 15 #length of time that road is visible. Constant throughout experiment
	
		#### PERSPECTIVE CORRECT ######
		self.caveview = LoadCave() #this module includes viz.go()

		
		if self.AUTOWHEEL:
			self.Wheel = LoadAutomationModules()
		else:
			self.Wheel = None		

		#BirdsEye
		#self.caveview.setPosition([60,100,0])
		#self.caveview.setEuler([0,90,0])


		##### SET CONDITION VALUES #####
		self.BendRadius = 60	 # 60m radii sinusoidal
		
		self.TRIAL_SEQ = [1, 2, 2] #1 = manual, 2 = automated.		

		##### ADD GRASS TEXTURE #####
		gplane1 = setStage()
		self.gplane1 = gplane1		
		
		#### MAKE TRACK ####
		self.InitialPosition_xz = [-120, 0]
		alpha = .5

		##First straight
		L = 16#2sec.
		grey = [.6, .6, .6]
		self.Straight1 = vizStraight(startpos = self.InitialPosition_xz, primitive_width=1.5, road_width = 0, length = L, colour = grey)#, texturefile='strong_edge_soft.bmp')
		self.Straight1.ToggleVisibility(viz.ON)
		self.Straight1.setAlpha(alpha)
		print ("Straight1 end: ", self.Straight1.RoadEnd)

		#first bend
		self.RightBend = vizBend(startpos = self.Straight1.RoadEnd, rads = self.BendRadius, x_dir = 1, colour = grey, road_width=0, primitive_width=1.5)#, texturefile='strong_edge_soft.bmp')
		self.RightBend.ToggleVisibility(viz.ON)
		self.RightBend.setAlpha(alpha)
		print ("RightBend end: ", self.RightBend.RoadEnd)

		#second straight
		self.Straight2 = vizStraight(startpos = self.RightBend.RoadEnd, primitive_width=1.5, road_width = 0, length = L, colour = grey, z_dir=-1)#, texturefile='strong_edge_soft.bmp')
		self.Straight2.ToggleVisibility(viz.ON)
		self.Straight2.setAlpha(alpha)
		print ("Straight2 end: ", self.Straight2.RoadEnd)

		#final bend
		self.LeftBend = vizBend(startpos = self.Straight2.RoadEnd, rads = self.BendRadius, x_dir = 1, z_dir=-1, colour = grey, road_width=0, primitive_width=1.5)#, texturefile='strong_edge_soft.bmp')		
		self.LeftBend.ToggleVisibility(viz.ON)
		self.LeftBend.setAlpha(alpha)

		print ("LeftBend end: ", self.LeftBend.RoadEnd)

		self.callback(viz.TIMER_EVENT,self.updatePositionLabel, priority = -1)
		self.starttimer(0,1.0/60.0,viz.FOREVER) #self.update position label is called every frame.

		
		self.manual_trial_length = 50

		self.UPDATELOOP = False

		#add audio files
		self.manual_audio = 'C:\\VENLAB data\\shared_modules\\textures\\490_200ms.wav'
		viz.playSound(self.manual_audio, viz.SOUND_PRELOAD)		
		
		####### DATA SAVING ######
		#datacolumns = ['ppid', 'radius','yawrate_offset','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'WheelCorrection', 'SteeringBias', 'Closestpt', 'AutoFlag', 'AutoFile', 'OnsetTime']
		datacolumns = ('ppid','trialn','timestamp_exp','timestamp_trial','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'WheelCorrection', 'AutoFlag')
		self.datacolumns = datacolumns		
		self.OutputWriter = None #dataframe that gets renewed each trial.
		self.OutputFile = None #for csv.		
		#self.OutputWriter = pd.DataFrame(columns=datacolumns) #make new empty EndofTrial data		

		
		self.txtMode = viz.addText("Mode",parent=viz.SCREEN)
		self.txtMode.setBackdrop(viz.BACKDROP_OUTLINE)
		self.txtMode.setBackdropColor(viz.BLACK)
		#set above skyline so I can easily filter glances to the letter out of the data
		self.txtMode.setPosition(.05,.52)
		self.txtMode.fontSize(36)
		self.txtMode.color(viz.WHITE)
		self.txtMode.visible(viz.OFF)

		### parameters that are set at the start of each trial ####
		self.Trial_YawRate_Offset = 0 				
		self.Trial_N = 0
		self.Trial_trialtype_signed = 0			
		self.Trial_Timer = 0 #keeps track of trial length. 			
		self.Trial_playbackdata = []
		self.Trial_playbacklength = 0
		self.Trial_playbackfilename = ""
		self.Trial_SaveName = "" #filename for saving data
		
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
		#self.Current_steeringbias = 0
		#self.Current_closestpt = 0

		self.Current_playbackindex = 0  		
		#playback variables.
				
		#self.playbackdata = "" #filename.
		
		self.YR_readout = []
		self.SWA_readout = []
		
		self.Playbackfile = "Orca18_PRAC_prerecorded.csv"
				
		#pre-load playback data at start of experiment.
		data = self.OpenTrial(self.Playbackfile)
		self.YR_readout = data.get("YawRate_seconds")
		self.SWA_readout = data.get("SWA")

		self.AUTOMATION = True
		self.txtMode.message('A')

		self.callback(viz.EXIT_EVENT,self.CloseConnections) #if exited, save the data. 

		if self.DEBUG:
			#add text to denote trial status.
			self.txtTrial = viz.addText("Condition",parent = viz.SCREEN)
			self.txtTrial.setPosition(.7,.2)
			self.txtTrial.fontSize(36)
			self.txtTrial.visible(viz.OFF)

			#add text to denote condition status
			self.txtCurrent = viz.addText("Current",parent = viz.SCREEN)
			self.txtCurrent.setPosition(.2,.2)
			self.txtCurrent.fontSize(36)
			self.txtCurrent.visible(viz.OFF)

			
			if self.DEBUG_PLOT:
				#for inset plot

				self.plotinterval = .2 #in seconds, amount of time to redraw plot.
				self.plottimer = 0 #to control interval.
				fig = plt.figure() #create figure
				self.plot_ax = fig.add_subplot(111) #add axes
				plt.title('Debug')
				plt.xlabel('Xpos')
				plt.ylabel('Zpos')

				#add a texture for a figure
				self.fig_texture = vizmatplot.Texture(fig)

				# Create quad to render plot texture
				quad = viz.addTexQuad(texture=self.fig_texture, parent = viz.SCREEN, size = 400)
				quad.setPosition(.5,.8)

				
				self.plot_positionarray_x, self.plot_positionarray_z, self.plot_closestpt_x,  self.plot_closestpt_z = [], [], [], [] #arrays to store plot data in

				self.dots_position, = self.plot_ax.plot(self.plot_positionarray_x, self.plot_positionarray_z, 'ko', markersize = .5)
				self.dots_closestpt, = self.plot_ax.plot(self.plot_closestpt_x, self.plot_closestpt_z, 'bo', markersize = .2)
				self.line_midline, = self.plot_ax.plot([],[],'r-')
				self.dot_origin, = self.plot_ax.plot([], [], 'b*', markersize = 5)	
							

	def runtrials(self):
		"""Loops through the trial sequence"""
		
		if self.EYETRACKING:
			viz.MainScene.visible(viz.OFF,viz.WORLD)		
			filename = str(self.EXP_ID) + "_Calibration_" + str(self.PP_id) #+ str(demographics[0]) + "_" + str(demographics[2]) #add experimental block to filename
			print (filename)
			yield run_calibration(self.comms, filename)
			yield run_accuracy(self.comms, filename)	


		#set up distractor task
		if self.DISTRACTOR_TYPE is not None:
			Distractor = Count_Adjustable.Distractor("distractor_", self.targetnumber, ppid = 1, startscreentime = self.StartScreenTime, triallength = 15, ntrials = len(self.TRIALSEQ_signed))
		else:
			Distractor = None
		self.driver = vizdriver.Driver(self.caveview, Distractor)	
		self.driver.reset(position = self.InitialPosition_xz) #reset position.

		viz.MainScene.visible(viz.ON,viz.WORLD)		
		
		

		self.ToggleTextVisibility(viz.ON)
	
		if self.EYETRACKING: 
			#pass it the filename, and also the timestamp.
			et_file = str(self.EXP_ID) + '_' + str(self.PP_id) #one file for the whole task.
			self.comms.start_trial(fname = et_file, timestamp = viz.tick())
		
		for i, trialtype in enumerate(self.TRIAL_SEQ):
			#import vizjoy		
			print("Trial: ", str(i))
			print("TrialType: ", str(trialtype))
			
			viz.mouse.setVisible(viz.ON)
			if trialtype == 2: #automation

				self.driver.setAutomation(True)
				self.AUTOMATION = True
				self.txtMode.message('A')

				if self.AUTOWHEEL:
					self.Wheel.control_on()
				
				viz.message('\t\tTRIAL INSTRUCTIONS \n\nThe automated system will now drive. Please keep your hands loosely on the wheel. When you are ready, you may take over control of the vehicle by pressing the gear pads.\n\nOnce pressed, you will immediately be in control of the vehicle')	

			else: #manual
				self.driver.setAutomation(False)
				self.AUTOMATION = False
				self.txtMode.message('M')

				if self.AUTOWHEEL:
					self.Wheel.control_off()

				viz.message('\t\tTRIAL INSTRUCTIONS \n\nFor this practice you have manual control of the vehicle. Please get a feel for the simulation, but stay within the road-edges.')	

			viz.mouse.setVisible(viz.OFF)

			if self.DISTRACTOR_TYPE is not None:
				if i == 0: #the first trial.			
					
					#annotate eyetracking
					if self.EYETRACKING:
						self.comms.annotate("DistractorScreen")	
					
					
					#switch texts off for the first trial.


					self.ToggleTextVisibility(viz.OFF)

					Distractor.StartTrial(self.targetoccurence_prob, self.targetnumber, trialn = i, displayscreen=True)	#starts trial								
					yield viztask.waitTrue(Distractor.getStartFlag)

					self.ToggleTextVisibility(viz.ON)
				else:
					Distractor.StartTrial(self.targetoccurence_prob, self.targetnumber, trialn = i, displayscreen=False)	#starts trial								
						
			#pick file. Put this in dedicated function. TODO: Should open all of these at the start of the file to save on processing.
			
			#update class#
			self.Trial_N = i			
			self.Trial_playbacklength = len(self.YR_readout)				
			self.Trial_SaveName = str(self.EXP_ID) + '_' + str(self.PP_id) + '_' + str(self.Trial_N)

			#renew data frame.
			#self.OutputWriter = pd.DataFrame(index = range(self.TrialLength*60), columns=self.datacolumns) #make new empty EndofTrial data

			#renew csv writer			
			self.OutputFile = io.BytesIO()
			self.OutputWriter = csv.writer(self.OutputFile)
			self.OutputWriter.writerow(self.datacolumns) #write headers.

			
			#annotate eyetracking
			if self.EYETRACKING:
					self.comms.annotate('Start_' + self.Trial_SaveName)	

			yield viztask.waitTime(.5) #pause at beginning of trial

			if self.DEBUG:
				conditionmessage = 'YR_offset: ' + str(self.Trial_YawRate_Offset) + \
				'\nTask: ' + str(self.DISTRACTOR_TYPE) 
				self.txtTrial.message(conditionmessage)
	
				if self.DEBUG_PLOT:
					#realtime plot.
					self.line_midline.set_data(self.Trial_midline[:,0], self.Trial_midline[:,1])
					self.dot_origin.set_data(self.Trial_BendObject.CurveOrigin[0],self.Trial_BendObject.CurveOrigin[1])
					self.plot_ax.axis([min(self.Trial_midline[:,0])-10,max(self.Trial_midline[:,0])+10,min(self.Trial_midline[:,1])-10,max(self.Trial_midline[:,1])+10])  #set axis limits

					self.plot_positionarray_x, self.plot_positionarray_z, self.plot_closestpt_x,  self.plot_closestpt_z = [], [], [], [] #arrays to store plot data in
						
			self.UPDATELOOP = True #

			def PlaybackReached():
				"""checks for playback limit"""

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
					if self.AUTOWHEEL:
						self.Wheel.control_off()
						#pass
					#print ("WheelControlOff", timer() - begin)
					end = True
				
				return (end)

			#create viztask functions.
			waitPlayback = viztask.waitTrue( PlaybackReached )
			waitDisengage = viztask.waitTrue( CheckDisengage )

			if trialtype == 2:
				d = yield viztask.waitAny( [ waitPlayback, waitDisengage ] )		

				if d.condition is waitPlayback:
					print ('Playback Limit Reached')
				elif d.condition is waitDisengage:
					print ('Automation Disengaged')
				
					self.SingleBeep()
					
					def RoadRunout():
						"""temporary HACK function to check whether the participant has ran out of road"""

						end = False
						if self.Trial_Timer > self.manual_trial_length:
							end = True
						
						return(end)

					waitRoad = viztask.waitTrue (RoadRunout)
					waitManual = viztask.waitTime(5)

					d = yield viztask.waitAny( [ waitRoad, waitManual ] )
					if d.condition is waitRoad:
						print ('Run out of Road')
					elif d.condition is waitManual:
						print ('Manual Time Elapsed')

			else: #manual control.
				yield viztask.waitTime(self.manual_trial_length)		
        
			
			##### END STEERING TASK ######


			
			self.UPDATELOOP = False
			
			##reset trial. Also need to annotate each eyetracking trial.											
			viz.director(self.SaveData, self.OutputFile, self.Trial_SaveName)			

			if self.AUTOWHEEL:
					self.Wheel.control_off()
			
			self.ResetTrialAndDriver() #reset parameters for beginning of trial

			##### INITIALISE END OF TRIAL SCREEN FOR DISTRACTOR TASK #######
			if self.DISTRACTOR_TYPE is not None:

				#annotate eyetracking
				if self.EYETRACKING:
					self.comms.annotate('Distractor_' + self.Trial_SaveName)	

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

			#annotate eyetracking
			if self.EYETRACKING:
				self.comms.annotate('End_' + self.Trial_SaveName)	
	
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

	def ResetTrialAndDriver(self):
		"""Sets Driver Position and Euler to original start point, and resets trial parameters"""

		#reset row index. and trial parameters
		self.Current_RowIndex = 0
		self.Current_playbackindex = 0
		self.Trial_Timer = 0 

		self.driver.reset(position = self.InitialPosition_xz)

	def OpenTrial(self,filename):
		"""opens csv file"""

		print ("Loading file: " + filename)
		playbackdata = pd.read_csv("Data//"+filename)
		return (playbackdata)

	def RecordData(self):
		
		"""Records Data into Dataframe"""

		#'ppid', 'radius','yawrate_offset','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'WheelCorrection', 'SteeringBias', 'Closestpt' 'AutoFlag', 'AutoFile'#		
		# output = [self.PP_id, self.Trial_radius, self.Trial_YawRate_Offset, self.Trial_N, self.Current_Time, self.Trial_trialtype_signed, 
		# self.Current_pos_x, self.Current_pos_z, self.Current_yaw, self.Current_SWA, self.Current_YawRate_seconds, self.Current_TurnAngle_frames, 
		# self.Current_distance, self.Current_dt, self.Current_WheelCorrection, self.Current_steeringbias, self.Current_closestpt, self.AUTOMATION, self.Trial_playbackfilename, self.Trial_OnsetTime] #output array.

		output = (self.PP_id, self.Trial_N, self.Current_Time, self.Trial_Timer, self.Current_pos_x, 
		self.Current_pos_z, self.Current_yaw, self.Current_SWA, self.Current_YawRate_seconds, self.Current_TurnAngle_frames, 
		self.Current_distance, self.Current_dt, self.Current_WheelCorrection, self.AUTOMATION) #output array
		
		
		#self.OutputWriter.loc[self.Current_RowIndex,:] = output #this dataframe is actually just one line. 		
		self.OutputWriter.writerow(output)  #output to csv. any quicker?

	def SaveData(self, data = None, filename = None):

		"""Saves Current Dataframe to csv file"""

		# data = data.dropna() #drop any trailing space.		
		# data.to_csv(filename)

		data.seek(0)
		df = pd.read_csv(data) #grab bytesIO object.		
		df.to_csv('Data//' + filename + '.csv') #save to file.

		print ("Saved file: ", filename)

	def calculatebias(self):


		"""currently cannot calculate bias on complicated tracks very easily, since the Origin changes
		
		TODO: work on bias calculation for complicated tracks.
		"""
		
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

		steeringbias *= np.sign(self.Trial_trialtype_signed)

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
				
				newSWApos = self.SWA_readout[self.Current_playbackindex]

				if self.AUTOWHEEL:
					self.Wheel.set_position(newSWApos)	#set steering wheel to position.
							
				newyawrate = self.YR_readout[self.Current_playbackindex]
				
				self.Current_playbackindex += 1
			else:
				newyawrate = None
			
			UpdateValues = self.driver.UpdateView(YR_input = newyawrate) #update view and return values used for update

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
			#update txtCurrent.
			if self.DEBUG:
				currentmessage = 'TrialTime: ' + str(round(self.Trial_Timer,2)) + \
					'\nLanePos: ' + str(round(self.Current_steeringbias,2))
				self.txtCurrent.message(currentmessage)

				if self.DEBUG_PLOT:
					#add to plot position array
					self.plot_positionarray_x.append(self.Current_pos_x)
					self.plot_positionarray_z.append(self.Current_pos_z)
					midpos = self.Trial_midline[self.Current_closestpt]
					self.plot_closestpt_x.append(midpos[0])
					self.plot_closestpt_z.append(midpos[1])

					if self.plottimer > self.plotinterval:
						self.UpdatePlot()
						self.plottimer = 0
					
					self.plottimer += viz.elapsed()

			self.RecordData() #write a line in the dataframe.	
				
	
	def UpdatePlot(self):
		"""for debugging, update inset plot in real-time"""

		# Update plot data
		self.dots_position.set_data(self.plot_positionarray_x, self.plot_positionarray_z)
		self.dots_closestpt.set_data(self.plot_closestpt_x, self.plot_closestpt_z)

		self.fig_texture.redraw()

	def SingleBeep(self):
		"""play single beep"""

		viz.playSound(self.manual_audio)

	def ToggleTextVisibility(self, visible = viz.ON):

		"""toggles onscreen text"""
		
		self.txtMode.visible(visible)

		if self.DEBUG:
			self.txtTrial.visible(visible)
			self.txtCurrent.visible(visible)

	def CloseConnections(self):
		
		"""Shuts down EYETRACKING and wheel threads then quits viz"""		
		
		print ("Closing connections")
		if self.EYETRACKING: 
			self.comms.stop_trial() #closes recording			
		
		#kill automation
		if self.AUTOWHEEL:
			self.Wheel.thread_kill() #This one is mission critical - else the thread will keep going 
			self.Wheel.shutdown()		

		viz.quit()
	
if __name__ == '__main__':

	###### SET EXPERIMENT OPTIONS ######	
	EYETRACKING = False
	AUTOWHEEL = True
	PRACTICE = False	#keep false. no practice trial at the moment.
	EXP_ID = "Orca18_PRAC"
	DEBUG = False #Will crash if set to True in the practice file.
	DEBUG_PLOT = False #flag for the debugger plot. only active if Debug == True. #Will crash if set to True in the practice file.

	#distractor_type takes 'None', 'Easy' (1 target, 40% probability), and 'Hard' (3 targets, 40% probability)
	#DISTRACTOR_TYPE = "Hard" #Case sensitive
	#DISTRACTOR_TYPE = "Easy" #Case sensitive
	DISTRACTOR_TYPE = None #Case sensitive

	#EXP_ID = EXP_ID + '_' + str(DISTRACTOR_TYPE)
	PP_ID = viz.input('Participant code: ')

	if PRACTICE == True: # HACK
		EYETRACKING = False 

	if EYETRACKING:
		from eyetrike_calibration_standard import Markers, run_calibration
		from eyetrike_accuracy_standard import run_accuracy
		from UDP_comms import pupil_comms

	myExp = myExperiment(EYETRACKING, PRACTICE, EXP_ID, AUTOWHEEL, DEBUG, DEBUG_PLOT, DISTRACTOR_TYPE, ppid = PP_ID)

	#viz.callback(viz.EXIT_EVENT,CloseConnections, myExp.EYETRACKING)

	viztask.schedule(myExp.runtrials())

