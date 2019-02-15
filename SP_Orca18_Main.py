"""
Script to run silent failure paradigm, with cognitive load. Every trial begins with a period of automation. 

The Class myExperiment handles execution of the experiment.

This script relies on the following modules:

For eyetracking - eyetrike_calibration_standard.py; eyetrike_accuracy_standard.py; also the drivinglab_pupil plugin.

For perspective correct rendering - myCave.py

For motion through the virtual world - vizdriver.py

"""

#doc strings needed
rootpath = 'C:\\VENLAB data\\shared_modules\\Logitech_force_feedback'
sys.path.append(rootpath)
rootpath = 'C:\\VENLAB data\\shared_modules'
sys.path.append(rootpath)
rootpath = 'C:\\VENLAB data\\shared_modules\\pupil\\capture_settings\\plugins\\drivinglab_pupil\\'
sys.path.append(rootpath)
rootpath = 'C:\\VENLAB data\\TrackMaker\\'
sys.path.append(rootpath)

#standard libraries
import sys
from timeit import default_timer as timer
import csv
import io #for efficient data saving
import numpy as np # numpy library - such as matrix calculation
import random # python library
import math as mt # python library
import pandas as pd
import matplotlib.pyplot as plt

#vizard libraries
import viz # vizard library
import viztask # vizard library
import vizshape
import vizact
import vizmat
import vizmatplot

#personal libraries
import vizdriver_Orca18 as vizdriver
import myCave
import Count_Adjustable #distractor task
from vizTrackMaker import vizBend, vizStraight
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

def GenerateConditionLists(FACTOR_radiiPool, FACTOR_YawRate_offsets,        	TrialsPerCondition):
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

	def __init__(self, eyetracking, practice, exp_id, autowheel, debug, 		debug_plot, distractor_type = None, ppid = 1, trialspercondition = 6):

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
			raise Exception ("Unrecognised Distractor Type. Specify 'None', 	'Easy', or 'Hard'. Case sensitive.")
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
		self.TrialLength = 15 #length of time that road is visible. Constant throughout experiment. Needs to match pre-recorded midline trajectories.
	
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
		#Estimates based on Zhang et al., (2019) preprint.https://www.researchgate.net/publication/325218061_Determinants_of_take-over_time_from_automated_driving_A_meta-analysis_of_129_studies
		#The average takeover time is around 2.72 s. The mode is around 2 - 2.25s. Auditory distraction effect size is around .4s

		#We want them taking over 50% of the time, so that they feel that they can at least partly trust the system.
		#The original design had 3 small offsets that do not need takeover, and 3 larger offsets (generally understeer) that need takeover.

		#Onset time pool is from 4 to 6s in .25s increments. The straight is ~ 2s of travel, so this is 2-4s into the bend. 
		#Trial time is 15s, so this onset range gives a minimum of 9s of bend travel, and a maximum of 11s of bend travel. 
		self.OnsetTimePool = np.arange(5, 9.25, step = .25) #

		#offsets chosen for trials that do not intend to cross the road need to keep within the road within 11s.
		#For offsets that cross the road, let's pick one that produces maximally quick responses (1 s), through to responses that require more judgement (4 - 8 s)
		"""
		PREDICTIONS FOR TIME TIL CROSSING THE ROAD EDGES

		YR OFFSET (m/s)	40m radius		80m radius		category
		-.2				~11s			~11s			stay
		-.05			~inf			~inf			stay
		.15				~11s			~12s			stay


		-9				~1.6s			~1.5s			leave - urgent  (yawrate for turning the bend is about 11 deg/s for 40m and 6 deg/s for 80m)
		-1.5			~4s				~3.8s			leave - middle
		-.5				~7.5s			~7s				leave - non urgent

		"""

		self.FACTOR_YawRate_offsets = [-.2, -.05, .15, -9, -1.5, -.5] #6 yawrate offsets, specified in degrees per second. 
		self.TrialsPerCondition = trialspercondition
		[trialsequence_signed, cl_radii, cl_yawrates]  = GenerateConditionList(
			self.FACTOR_radiiPool, self.FACTOR_YawRate_offsets, self.TrialsPerCondition
			)

		self.TRIALSEQ_signed = trialsequence_signed #list of trialtypes in a randomised order. -ve = leftwards, +ve = rightwards.
		self.ConditionList_radii = cl_radii
		self.ConditionList_YawRate_offsets = cl_yawrates

		##### ADD GRASS TEXTURE #####
		gplane1 = setStage()
		self.gplane1 = gplane1		
		
		#### MAKE STRAIGHT OBJECT ####
		L = 16#2sec.
		self.Straight = vizStraight(
			startpos = [0,0], primitive_width=1.5, road_width = 0, length = L, colour = [.6, .6, .6]
			)#, texturefile='strong_edge_soft.bmp')
		self.Straight.ToggleVisibility(viz.ON)
		self.Straight.setAlpha(.5)

		##### MAKE BEND OBJECTS #####
		[leftbends,rightbends] = BendMaker(
			self.FACTOR_radiiPool, self.Straight.RoadEnd
			)
		self.leftbends = leftbends
		self.rightbends = rightbends 

		self.callback(viz.TIMER_EVENT,self.updatePositionLabel, priority = -1)
		self.starttimer(0,1.0/60.0,viz.FOREVER) #self.update position label is called every frame.
		
		self.UPDATELOOP = False

		#add audio files
		self.manual_audio = 'C:\\VENLAB data\\shared_modules\\textures\\490_200ms.wav'
		viz.playSound(self.manual_audio, viz.SOUND_PRELOAD)		
		
		####### DATA SAVING ######
		#datacolumns = ['ppid', 'radius','yawrate_offset','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'WheelCorrection', 'SteeringBias', 'Closestpt', 'AutoFlag', 'AutoFile', 'OnsetTime']
		datacolumns = ('ppid', 'radius','yawrate_offset','trialn','timestamp',	'trialtype_signed','World_x','World_z','WorldYaw','SWA',			'YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 		'WheelCorrection', 'SteeringBias', 'Closestpt', 'AutoFlag', 		'AutoFile', 'OnsetTime')
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
		self.Current_steeringbias = 0
		self.Current_closestpt = 0

		self.Current_playbackindex = 0  		
		#playback variables.
				
		#self.playbackdata = "" #filename.
		self.YR_readouts_40 = []
		self.SWA_readouts_40 = []
		self.YR_readouts_80 = []
		self.SWA_readouts_80 = []
		self.PlaybackPool40 = ["Midline_40_0.csv","Midline_40_1.csv",			"Midline_40_2.csv","Midline_40_3.csv","Midline_40_4.csv",			"Midline_40_5.csv"]
		self.PlaybackPool80 = ["Midline_80_0.csv","Midline_80_1.csv",			"Midline_80_2.csv","Midline_80_3.csv","Midline_80_4.csv",			"Midline_80_5.csv"]

		
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

				self.dots_position, = self.plot_ax.plot(
					self.plot_positionarray_x, self.plot_positionarray_z, 'ko',markersize = .5
					)
				self.dots_closestpt, = self.plot_ax.plot(
					self.plot_closestpt_x, self.plot_closestpt_z, 'bo', markersize = .2
					)
				self.line_midline, = self.plot_ax.plot([],[],'r-')
				self.dot_origin, = self.plot_ax.plot(
					[], [], 'b*', markersize = 5
					)	
							

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

		viz.MainScene.visible(viz.ON,viz.WORLD)		
		viz.mouse.setVisible(viz.OFF) #switch mouse off

		self.ToggleTextVisibility(viz.ON)
	
		if self.EYETRACKING: 
			#pass it the filename, and also the timestamp.
			et_file = str(self.EXP_ID) + '_' + str(self.PP_id) #one file for the whole task.
			self.comms.start_trial(fname = et_file, timestamp = viz.tick())
		
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
			self.Trial_OnsetTime = np.random.choice(self.OnsetTimePool, size=1)[0]
			self.Trial_SaveName = str(self.EXP_ID) + '_' + str(self.PP_id) + '_' + str(self.Trial_radius) + '_' + str(self.Trial_N)

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
				'\nRadius: ' +str(self.Trial_radius) + \
				'\nOnsetTime: ' + str(self.Trial_OnsetTime) + \
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
					if self.AUTOWHEEL:
						self.Wheel.control_off()
						#pass
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
				
				self.SingleBeep()
				
				def RoadRunout():
					"""temporary HACK function to check whether the participant has ran out of road"""

					end = False
					if self.Trial_Timer > self.TrialLength:
						end = True
					
					return(end)

				#waitRoad = viztask.waitTrue (RoadRunout)
				#waitManual = viztask.waitTime(5)

				#d = yield viztask.waitAny( [ waitRoad, waitManual ] )

				yield viztask.waitTrue (RoadRunout)
				print ("Run out of Road")
				#if d.condition is waitRoad:
				#	print ('Run out of Road')
				#elif d.condition is waitManual:
				#	print ('Manual Time Elapsed')

			##### END STEERING TASK ######


			
			self.UPDATELOOP = False
			
			self.Trial_BendObject.ToggleVisibility(viz.OFF)	

			##reset trial. Also need to annotate each eyetracking trial.											
			viz.director(self.SaveData, self.OutputFile, self.Trial_SaveName)			
			
			self.ResetTrialAndDriver() #reset parameters for beginning of trial

			##### INITIALISE END OF TRIAL SCREEN FOR DISTRACTOR TASK #######
			if self.DISTRACTOR_TYPE is not None:

				#annotate eyetracking
				if self.EYETRACKING:
					self.comms.annotate('Distractor_' + self.Trial_SaveName)	

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

		self.driver.reset()

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

		output = (
			self.PP_id, self.Trial_radius, self.Trial_YawRate_Offset, self.Trial_N, self.Current_Time, self.Trial_trialtype_signed, 
			self.Current_pos_x, self.Current_pos_z, self.Current_yaw, self.Current_SWA, self.Current_YawRate_seconds, self.Current_TurnAngle_frames, 
			self.Current_distance, self.Current_dt, self.Current_WheelCorrection, self.Current_steeringbias, self.Current_closestpt, self.AUTOMATION, self.Trial_playbackfilename, self.Trial_OnsetTime
			) #output array
		
		
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
		
		#get a 4000 array of distances from the midline
		midlinedist = np.sqrt(
			((self.Current_pos_x-self.Trial_midline[:,0])**2)
			+((self.Current_pos_z-self.Trial_midline[:,1])**2)
			) 
		idx = np.argmin(abs(midlinedist)) #find smallest difference. This is the closest index on the midline.	

		closestpt = self.Trial_midline[idx,:] #xy of closest point
		dist = midlinedist[idx] #distance from closest point				
		CurveOrigin = self.Trial_BendObject.CurveOrigin

		#Sign bias from assessing if the closest point on midline is closer to the track origin than the driver position. Since the track is an oval, closer = understeering, farther = oversteering.
		middist_from_origin = np.sqrt(
			((closestpt[0]-CurveOrigin[0])**2)
			+((closestpt[1]-CurveOrigin[1])**2)
			)  #distance of midline to origin
		pos_from_trackorigin = np.sqrt(
			((self.Current_pos_x-CurveOrigin[0])**2)
			+((self.Current_pos_z-CurveOrigin[1])**2)
			) #distance of driver pos to origin
		#if driver distance is greater than closest point distance, steering position should be understeering
		distdiff = middist_from_origin - pos_from_trackorigin 
		steeringbias = dist * np.sign(distdiff)     

		steeringbias *= np.sign(self.Trial_trialtype_signed)

		return steeringbias, idx

	def updatePositionLabel(self, num):
		
		"""Timer function that gets called every frame. Updates parameters for saving"""

		"""Here need to bring in steering bias updating from Trout as well"""
	

		if self.UPDATELOOP:

			dt = viz.elapsed()
			#print ("elapsed:", dt)

			#print ("frame elapsed:", viz.getFrameElapsed())
			self.Trial_Timer = self.Trial_Timer + dt
		
			#print("UpdatingPosition...")	
			#update driver view.
			if self.AUTOMATION:
				
				newSWApos = self.Trial_SWA_readout[self.Current_playbackindex]
				newSWApos *= np.sign(self.Trial_trialtype_signed) #flip if left hand bend

				if self.AUTOWHEEL:
					self.Wheel.set_position(newSWApos)	#set steering wheel to position.
							
				newyawrate = self.Trial_YR_readout[self.Current_playbackindex]

				#add yawrateoffset.
				if self.Trial_Timer > self.Trial_OnsetTime: #2 seconds into the bend.
					newyawrate += self.Trial_YawRate_Offset #positive offset = greater oversteering.
				
				self.Current_playbackindex += 1

				newyawrate *= np.sign(self.Trial_trialtype_signed) #flip if left hand bend
												
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
			self.Current_steeringbias, self.Current_closestpt = self.calculatebias()

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
		self.dots_position.set_data(
			self.plot_positionarray_x, self.plot_positionarray_z
			)
		self.dots_closestpt.set_data(
			self.plot_closestpt_x, self.plot_closestpt_z
			)

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
	EYETRACKING = False#True
	AUTOWHEEL = True
	PRACTICE = False	#keep false. no practice trial at the moment.
	EXP_ID = "Orca18"
	DEBUG = True
	DEBUG_PLOT = False #flag for the debugger plot. only active if Debug == True.


	#SP CHANGE HERE
	
	#distractor_type takes 'None', 'Easy' (1 target, 40% probability), and 'Hard' (3 targets, 40% probability)
	DISTRACTOR_TYPE = "Hard" #Case sensitive
	#DISTRACTOR_TYPE = "Easy" #Case sensitive
	#DISTRACTOR_TYPE = None #Case sensitive. Shouldn't have speech marks since None is a special word.
	BLOCK = 1 #SP. change to one or two.

	#determine amount of trials
	if DISTRACTOR_TYPE is None:
		trials = 3
	else:
		trials = 6

	if DISTRACTOR_TYPE is None:
		EXP_ID = EXP_ID + '_' + str(DISTRACTOR_TYPE) + '_' + str(BLOCK) #build string for file saving.
	else:
		EXP_ID = EXP_ID + '_' + str(DISTRACTOR_TYPE) #build string for file saving.

	PP_ID = viz.input('Participant code: ') #add participant code

	if PRACTICE == True: # HACK
		EYETRACKING = False 

	if EYETRACKING:
		from eyetrike_calibration_standard import Markers, run_calibration
		from eyetrike_accuracy_standard import run_accuracy
		from UDP_comms import pupil_comms
	

	myExp = myExperiment(
		EYETRACKING, PRACTICE, EXP_ID, AUTOWHEEL, DEBUG, DEBUG_PLOT, DISTRACTOR_TYPE, ppid = PP_ID, trialspercondition=trials
		)

	#viz.callback(viz.EXIT_EVENT,CloseConnections, myExp.EYETRACKING)

	viztask.schedule(myExp.runtrials())

