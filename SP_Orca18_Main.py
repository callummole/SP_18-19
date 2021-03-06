"""
Script to run silent failure paradigm, with cognitive load. Every trial begins with a period of automation. 

The Class myExperiment handles execution of the experiment.

This script relies on the following modules:

For eyetracking - eyetrike_calibration_standard.py; eyetrike_accuracy_standard.py; also the drivinglab_pupil plugin.

For perspective correct rendering - myCave.py

For motion through the virtual world - vizdriver.py

"""
import sys,os
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
from timeit import default_timer as timer
import csv
import io #for efficient data saving
import numpy as np # numpy library - such as matrix calculation
import random # python library
import math as mt # python library
import pandas as pd
import matplotlib.pyplot as plt
import gzip

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

def GenerateBalancedConditionLists(radius, FACTOR_YawRate_offsets, repetitions, onset, simulated_ttlc):
	"""create dataframe with equal repetitions per yawrate offset """

	#only one factor. Yawrate offset

	simulated_ttlc_tiled = np.tile(simulated_ttlc, repetitions)  #tile to matchh yawrate offsets
	ConditionList_YawRate_offsets = np.tile(FACTOR_YawRate_offsets, repetitions)

	#print (ConditionList_YawRate_offsets)

	balanced_condition_list = pd.DataFrame(data = np.transpose([ConditionList_YawRate_offsets, simulated_ttlc_tiled]), columns = ['sab','simulated_ttlc'])

	#print (balanced_condition_list)

	trials = len(balanced_condition_list)

	#print("my trials: ", trials)
	direc = [1,-1]*int(np.ceil(trials/2.0)) #makes half left and half right. #if odd it should round up.
	#print ("length", len(direc))
	#print ("trials", trials)
	direc = direc[:trials]
	np.random.shuffle(direc) 	
	balanced_condition_list['bend'] = direc
	balanced_condition_list['radius'] = radius
	balanced_condition_list['design'] = 'balanced'
	balanced_condition_list['autofile_i'] = 0
	balanced_condition_list['onsettime'] = onset
	
	balanced_condition_list = balanced_condition_list.sample(frac=1).reset_index(drop=True)

	return(balanced_condition_list)

def GenerateSobolConditionLists():
	"""loads sobol generation from file. see TrackSimulation_sobol.py for details"""

	filename = "SimResults_samplesobol_onsettimes.csv"
	#columns are: yr_offset, file_i, onsettime, predicted_time_til_crossing
	#sobol_condition_list = np.genfromtxt(filename, delimiter=',')

	sobol_condition_list = pd.read_csv(filename, 
					sep=',', 
					names=["sab", "autofile_i", "onsettime", "simulated_ttlc"])

		
	#print(sobol_condition_list[1:10])

	trials = len(sobol_condition_list)
	direc = [1,-1]*(trials/2) #makes half left and half right.
	np.random.shuffle(direc) 	
	sobol_condition_list['bend'] = direc
	sobol_condition_list['design'] = 'random'
	sobol_condition_list['radius'] = 80
	sobol_condition_list['autofile_i'] = sobol_condition_list['autofile_i'] + 1 #increment autofile because index = 0 is reserved for balanced design

	#shuffle entire rows.
	sobol_condition_list = sobol_condition_list.sample(frac=1).reset_index(drop=True)

	return(sobol_condition_list)

# ground texture setting
def setStage():
	
	"""Creates grass textured groundplane"""
	
	###should set this hope so it builds new tiles if you are reaching the boundary.
	#fName = 'C:/VENLAB data/shared_modules/textures/strong_edge.bmp'
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
		rightbend = vizBend(startpos = start, rads = r, x_dir = 1, colour = grey, road_width=0, primitive_width=1.5, arc_angle = 1.5 * np.pi)#, texturefile='strong_edge_soft.bmp')
		rightbend.setAlpha(.25)
			
		rightbendlist.append(rightbend)

		leftbend = vizBend(startpos = start, rads = r, x_dir = -1, colour = grey, road_width=0, primitive_width=1.5, arc_angle = 1.5 * np.pi)#, texturefile='strong_edge_soft.bmp')
		
		leftbend.setAlpha(.25)	
		leftbendlist.append(leftbend)
			
	return leftbendlist,rightbendlist 

f = lambda t: np.exp(-1/t)*(t > 0)
_smooth_step = lambda t: f(t)/(f(t) + f(1 - t))
def smooth_step(t):
	if t <= 0: return 0.0
	if t >= 1: return 1.0
	return _smooth_step(t)

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

		if self.DISTRACTOR_TYPE not in (None, "Easy", "Hard","Middle"):
			raise Exception ("Unrecognised Distractor Type. Specify 'None', 	'Easy', or 'Hard'. Case sensitive.")
			#pass
		
		###set distractor parameters.
		if self.DISTRACTOR_TYPE == "Easy":
			self.targetoccurence_prob = .4
			self.targetnumber = 1
		elif self.DISTRACTOR_TYPE == "Hard":
			self.targetoccurence_prob = .4
			self.targetnumber = 3
		elif self.DISTRACTOR_TYPE == "Middle":
			self.targetoccurence_prob = .4
			self.targetnumber = 2

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
		#For rerun only use on radii. I cannot think of a strong reason to use 40 or 80. I have arbitrarily picked 40 so that you navigate more of the bend
	

		"""
		**********EXPERIMENT DESIGN*********

		We adopt a hybrid experiment design of two sub-experiments.

		The first (50% of the hybrid) experiment (BALANCED) is a factorial design (5 SAB levels, 3 Loads) without jitter (fixed onset time at 6 s, fixed automated trajectory at 'Midline_40_0.csv'), with 6 repetitions per trial so we have repetitions of participant performance at identical trajectories for hypotheses testing.

		The second experiment (RANDOM) includes the three levels of cognitive load, but dispenses with levels with SAB. Instead, it treats SAB as a continuous measure from which it samples quasi-randomly in a SOBEL fashion, with jitter induced by variable onset times and automated trajectories. The second experiment explores the parameters space more widely for modelling purposes.


		***TAKEOVER DESIGN NOTES***
		#Estimates based on Zhang et al., (2019) preprint.https://www.researchgate.net/publication/325218061_Determinants_of_take-over_time_from_automated_driving_A_meta-analysis_of_129_studies
		#The average takeover time is around 2.72 s. The mode is around 2 - 2.25s. Auditory distraction effect size is around .4s

		#We want them taking over 50% of the time, so that they feel that they can at least partly trust the system.

		#Onset time pool is from 5 to 9s in .25s increments. The straight is ~ 2s of travel, so this is 3-7s into the bend. 
		#Trial time is 15s, so this onset range gives a minimum of 6s of bend travel, and a maximum of 10s of bend travel. 

		#offsets chosen for trials that do not intend to cross the road need to keep within the road within 11s.

		#For offsets that cross the road, let's pick one that produces maximally quick responses (1 s), through to responses that require more judgement (4 - 8 s)

		*****CHOOSING STEERING ANGLE BIASES (yawrate offsets)*****

		When decided the limits of steering angle biases, we thought that the limit case of severity should be 'straight ahead' failure. On the first run the sudden failure of was unnecessarily severe and caused capping of steering wheel angles.

		At 8m/s with a bend radius of 80 the yaw rate is: 8 / 80 = 5.72  degrees per second, which has a ttlc of 2.016 and also will have the capping confound. With the gradual onset duration of .5s there is a ttlc of ~ 2.23 s.

		Using simulations (TrackSimulation.py; PlottingOnsetTimeSimulations_balancedparameters.py) we choose the sab values that correspond to the 5 equally spaced ttlcs from 2.23 s to 10 s.

		ttlc: 2.23333333,  4.68333333,  7.1       ,  9.5       , 12.15          
		sab: -5.72957795, -1.19868047, -0.52191351, -0.3039716 , -0.20073596


		Failure parameters from first run:
		YR OFFSET (deg /s)	40m radius		80m radius		category
		-.2				~11s			~11s			stay		
		.15				~11s			~12s			stay


		-9				~1.6s			~1.5s			leave - urgent  (yawrate for turning the bend is about 11 deg/s for 40m and 6 deg/s for 80m)
		-1.5			~4s				~3.8s			leave - middle

		"""
		sobol_condition_list = GenerateSobolConditionLists()
		self.FACTOR_YawRate_offsets = [-5.72957795, -1.19868047, -0.52191351, -0.3039716] 
		simulated_ttlc = [2.23333333,  4.68333333,  7.1,  9.5]
		self.TrialsPerCondition = trialspercondition
		self.FACTOR_radiiPool = [80]

		balanced_condition_list = GenerateBalancedConditionLists(radius = 80, FACTOR_YawRate_offsets = self.FACTOR_YawRate_offsets, repetitions = self.TrialsPerCondition, onset = 6,
		simulated_ttlc = simulated_ttlc)

		#make sure they are in the right column order before concatenation.
		cols = list(sobol_condition_list.columns.values)
		balanced_condition_list = balanced_condition_list[cols]		

		self.TRIALSEQ_df =  pd.concat([sobol_condition_list, balanced_condition_list])

		self.TRIALSEQ_df = self.TRIALSEQ_df.sample(frac=1).reset_index(drop=True) #data frame for trial sequence.

		self.total_trials = len(self.TRIALSEQ_df.index)

		##### ADD GRASS TEXTURE #####
		gplane1 = setStage()
		self.gplane1 = gplane1		
		
		#### MAKE STRAIGHT OBJECT ####
		L = 16#2sec.
		self.Straight = vizStraight(
			startpos = [0,0], primitive_width=1.5, road_width = 0, length = L, colour = [.6, .6, .6]
			)#, texturefile='strong_edge_soft.bmp')
		self.Straight.ToggleVisibility(viz.ON)
		self.Straight.setAlpha(.25)

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

		##TRIALSEQ_df as column names = ('autofile_i','bend','design','onsettime','radius','sab','simulated_ttlc')

		datacolumns = ('autofile_i','bend','design','onsettime','radius','sab','simulated_ttlc','ppid','trialn','timestamp_exp', 'timestamp_trial','world_x','world_z','world_yaw','swa', 'yawrate_seconds','turnangle_frames','distance_frames','dt','wheelcorrection', 'steeringbias', 'closestpt', 'autoflag', 'autofile','cogload')
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


		##### add calibration marker #####
		imagepath = 'C:/VENLAB data/shared_modules/textures/'
		fn = imagepath + 'calibmarker_white.png' #seems to work best with this one. 			

		def loadimage(fn):
			"""Loads a and scales a texture from a given image path""" 
			defaultscale = 800.0/600.0
			aspect = 1920.0 / 1080.0		
			scale = aspect/defaultscale
			ttsize = 1
			pt = viz.add(viz.TEXQUAD, viz.SCREEN)
			pt.scale(ttsize, ttsize*scale, ttsize)
			pt.texture(viz.add(fn))
			
			pt.visible(0)
			return (pt)

		self.calib_pt = loadimage(fn)
		self.calib_pt.visible(0)
		self.calib_pt.translate(.5,.4)

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
		self.Trial_autofile_i = ""
		self.Trial_dir = 0
		self.Trial_midline = [] #midline for the entire track.
		self.Trial_OnsetTime = 0 #onset time for the trial.
		self.Trial_SaveName = "" #filename for saving data
		self.Trial_design = "" #balanced or random
		self.Trial_simulatedttlc = 0 #simulated time to lane crossing.
		
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

		#"Midline_80_1" is reserved for the balanced design.
		#_2 to _5 are for the random design.
		self.PlaybackPool80 = ["Midline_80_1.csv","Midline_80_2.csv","Midline_80_3.csv","Midline_80_4.csv","Midline_80_5.csv"]

		#pre-load playback data at start of experiment.
		"""
		for i, file40 in enumerate(self.PlaybackPool40):

			#load radii 40
			data40 = self.OpenTrial(file40)
			self.YR_readouts_40.append(data40.get("YawRate_seconds"))
			self.SWA_readouts_40.append(data40.get("SWA"))

		"""

		self.markers = []

		for i, file80 in enumerate(self.PlaybackPool80):
			#load radii 80
			file80 = self.PlaybackPool80[i]
			data80 = self.OpenTrial(file80)
			self.YR_readouts_80.append(data80.get("YawRate_seconds"))
			self.SWA_readouts_80.append(data80.get("SWA"))

		self.AUTOMATION = True
		self.txtMode.message('A')

		#self.callback(viz.EXIT_EVENT,self.CloseConnections) #if exited, save the data. 

		if self.DEBUG:
			#add text to denote trial status.
			self.txtTrial = viz.addText("Condition",parent = viz.SCREEN)
			self.txtTrial.setPosition(.7,.35)
			self.txtTrial.fontSize(36)
			self.txtTrial.visible(viz.OFF)

			#add text to denote condition status
			self.txtCurrent = viz.addText("Current",parent = viz.SCREEN)
			self.txtCurrent.setPosition(.2,.15)
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

		viz.MainScene.visible(viz.ON,viz.WORLD)		
		viz.mouse.setVisible(viz.OFF) #switch mouse off
		viz.clearcolor(viz.SKYBLUE) #HACK, since eyetracker background is white.
		if self.EYETRACKING: 
			#pass it the filename, and also the timestamp.
			et_file = str(self.EXP_ID) + '_' + str(self.PP_id) #one file for the whole task.
			self.comms.start_trial(fname = et_file, timestamp = viz.tick())

		if self.EYETRACKING:
			#viz.MainScene.visible(viz.OFF,viz.WORLD)
						
			#remove straight
			self.Straight.ToggleVisibility(0)	
			filename = str(self.EXP_ID) + "_Calibration_" + str(self.PP_id) #+ str(demographics[0]) + "_" + str(demographics[2]) #add experimental block to filename
			print (filename)
			
			# Start logging the pupil data
			pupilfile = gzip.open(
				os.path.join("Data", filename + ".pupil.jsons.gz"),
				'a')
					
			closer = pupil_logger.start_logging(pupilfile, timestamper=viz.tick)
			
			def stop_pupil_logging():
				closer()
				pupilfile.close()
			EXIT_CALLBACKS.insert(0, stop_pupil_logging)
						
			yield run_calibration(self.comms, filename)			
			yield run_accuracy(self.comms, filename)
			

			#put straight visible
			self.Straight.ToggleVisibility(1)	
		#add message after calibration to give the experimenter and participant time to prepare for the simulation.

			self.markers = Markers()

			#set up distractor task
		if self.DISTRACTOR_TYPE is not None:
			distractorfilename = str(self.EXP_ID) + '_' + str(self.PP_id) + '_distractor_'
			Distractor = Count_Adjustable.Distractor(distractorfilename, self.targetnumber, ppid = 1, startscreentime = self.StartScreenTime, triallength = np.inf, ntrials = len(self.TRIALSEQ_df.index))
		else:
			Distractor = None

		#set up scene before eyetracking	
		self.driver = vizdriver.Driver(self.caveview, Distractor)		

		viz.message('\t\tYou will now begin the experiment \n\n The automated vehicle will attempt to navigate a series of bends. \nYour task as the supervisory driver is to make sure the vehicle stays within the road edges. \nDuring automation please keep your hands loosely on the wheel. \nYou may take control by pressing the gear pads. \nOnce pressed, you will immediately be in control of the vehicle \n\n Please fixate the centre of the calibration point in between trials')			
		self.ToggleTextVisibility(viz.ON)	

				
	

		
		
		for i, trial in self.TRIALSEQ_df.iterrows():

			#if half-way through do accuracy test.
					#Trial loop has finished.
			if i == int(np.round(self.total_trials/2,0)):
				if self.EYETRACKING:
					self.markers.markers_visibility(0) #remove markers for calibration
					self.Straight.ToggleVisibility(0)	

					accuracy_filename = filename + '_middle'
					yield run_accuracy(self.comms, accuracy_filename)
					yield viztask.waitTime(1) #a second pause before going into 

					self.markers.markers_visibility(1) #remove markersthe next trial 
					self.Straight.ToggleVisibility(1)	
				
			#import vizjoy		

			print("Trialn: ", str(i))
			
			print("current trial:", trial)

			#trial is now a row from a dataframe
			print("current trial radius:", trial["radius"])
			trial_radii = trial['radius'] 
			trial_yawrate_offset = trial['sab']
			trial_dir = trial['bend']
			
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
					yield viztask.waitTrue(Distractor.getPlaySoundFlag)

					self.ToggleTextVisibility(viz.ON)

					
				else:
					Distractor.StartTrial(self.targetoccurence_prob, self.targetnumber, trialn = i, displayscreen=False)	#starts trial								
				


			radius_index = self.FACTOR_radiiPool.index(trial_radii)

			#choose correct road object.

			if trial_dir > 0: #right bend
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

			self.Trial_autofile_i = int(trial['autofile_i'])


			self.Trial_YR_readout = self.YR_readouts_80[self.Trial_autofile_i ]
			self.Trial_SWA_readout = self.SWA_readouts_80[self.Trial_autofile_i]
			self.Trial_playbackfilename = self.PlaybackPool80[self.Trial_autofile_i]
				
			"""
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

			"""

			
			#update class#
			self.Trial_simulatedttlc = trial['simulated_ttlc']
			self.Trial_design = trial['design']
			self.Trial_dir = trial_dir
			self.Trial_N = i			
			self.Trial_YawRate_Offset = trial_yawrate_offset			
			self.Trial_BendObject = trialbend	
			self.Trial_trialtype_signed	= trial_dir
			self.Trial_playbacklength = len(self.Trial_YR_readout)				
			self.Trial_midline = np.vstack(
				(self.Straight.midline, self.Trial_BendObject.midline)
				)
			self.Trial_OnsetTime = trial['onsettime']	
			#self.Trial_OnsetTime = np.random.choice(self.OnsetTimePool, size=1)[0]
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

			#annotate eyetracking
			if self.EYETRACKING:
					#remove calib_pt and wait a further .5 s	
					#TODO: add 1 s calibration dot.
					self.calib_pt.visible(1)
					yield viztask.waitTime(1.5) #pause at beginning of trial
					self.calib_pt.visible(0)
					yield viztask.waitTime(.5) #pause at beginning of trial

			if self.DEBUG:
				conditionmessage = 'SAB: ' + str(self.Trial_YawRate_Offset) + \
				'\nRadius: ' +str(self.Trial_radius) + \
				'\nOnsetTime: ' + str(self.Trial_OnsetTime) + \
				'\nAutoFile: ' + str(self.Trial_autofile_i) + \
				'\nsim TTLC: ' + str(self.Trial_simulatedttlc) + \
				'\nDesign: ' + str(self.Trial_design) + \
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

					if self.EYETRACKING:
						self.comms.annotate('Disengage_' + self.Trial_SaveName)	
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

				#switch text off 
				self.ToggleTextVisibility(viz.OFF)

				Distractor.EndofTrial() #throw up the screen to record counts.
				
				# Pause before the query screen to avoid
				# spurious presses carrying over from the
				# task.
				# Hack the screen to be blank
				Distractor.EoTScreen.visible(viz.ON)
				Distractor.Question.visible(viz.OFF)
				Distractor.lblscore.visible(viz.OFF)
				yield viztask.waitTime(1.0)
				Distractor.EoTScreen_Visibility(viz.ON)
				
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

				self.ToggleTextVisibility(viz.ON)

			#annotate eyetracking
			if self.EYETRACKING:
				self.comms.annotate('End_' + self.Trial_SaveName)
	
		#Trial loop has finished.
		if self.EYETRACKING:
			self.markers.remove_markers() #remove markers
			self.Straight.ToggleVisibility(0)
			accuracy_filename = filename + '_end'
			yield run_accuracy(self.comms, accuracy_filename)
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

		output = (self.Trial_autofile_i, self.Trial_dir, self.Trial_design,self.Trial_OnsetTime, self.Trial_radius, self.Trial_YawRate_Offset,
		self.Trial_simulatedttlc,self.PP_id, self.Trial_N, self.Current_Time, self.Trial_Timer, self.Current_pos_x, self.Current_pos_z, self.Current_yaw, self.Current_SWA, self.Current_YawRate_seconds, self.Current_TurnAngle_frames, self.Current_distance, self.Current_dt, self.Current_WheelCorrection, self.Current_steeringbias, self.Current_closestpt, self.AUTOMATION, self.Trial_playbackfilename, str(self.DISTRACTOR_TYPE)) #output array
		
		
		#self.OutputWriter.loc[self.Current_RowIndex,:] = output #this dataframe is actually just one line. 		
		self.OutputWriter.writerow(output)  #output to csv. any quicker?

	def SaveData(self, data = None, filename = None):

		"""Saves Current Dataframe to csv file"""

		# data = data.dropna() #drop any trailing space.		
		# data.to_csv(filename)

		data.seek(0)
		df = pd.read_csv(data) #grab bytesIO object.		
		
		fileext = '.csv'
		file_path = 'Data//' + filename 
		complete_path = file_path + fileext
		if os.path.exists(complete_path):
			
			rint = np.random.randint(1, 100)
			complete_path = file_path + '_copy_' + str(rint) + fileext			

		df.to_csv(complete_path) #save to file.

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

				#if self.Trial_Timer > self.Trial_OnsetTime: #2 seconds into the bend.
				time_after_onset = self.Trial_Timer - self.Trial_OnsetTime
				transition_duration = .5
				if time_after_onset > 0:
					newyawrate += smooth_step(time_after_onset/transition_duration)*self.Trial_YawRate_Offset #positive offset = greater oversteering.
				
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
				currentmessage = 'TrialTime: ' + str(round(self.Trial_Timer,2)) + '\nLanePos: ' + str(round(self.Current_steeringbias,2))
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
			#self.pupil_killer()
		
		#kill automation
		if self.AUTOWHEEL:
			self.Wheel.thread_kill() #This one is mission critical - else the thread will keep going 
			self.Wheel.shutdown()		

		viz.quit()
	
if __name__ == '__main__':

	###### SET EXPERIMENT OPTIONS ######	
	EXIT_CALLBACKS = [] #list for functions to call on programme exit

	AUTOWHEEL = True
	PRACTICE = False	#keep false. no practice trial at the moment.
	EXP_ID = "Orca19" #Orca18 for original dataset. Orca19 for rerun.
	DEBUG = False
	DEBUG_PLOT = False #flag for the debugger plot. only active if Debug == True.

	#SP CHANGE HERE
	EYETRACKING = True
	
	#distractor_type takes 'None', 'Easy' (1 target, 40% probability), and 'Hard' (3 targets, 40% probability)
	#DISTRACTOR_TYPE = "Hard" #Case sensitive
	#DISTRACTOR_TYPE = "Easy" #Case sensitive
	DISTRACTOR_TYPE = "Middle" #PICK THIS FOR TWO TARGETS
	#DISTRACTOR_TYPE = None #Case sensitive. Shouldn't have speech marks since None is a special word.
	#BLOCK = 1 #SP. change to one or two.

	#determine amount of trials
	
	
	#if DISTRACTOR_TYPE is None:
#		trials = 3
		#trials = 6
	#else:
#		trials = 6
	
	trials = 6 #results in about five minutes quicker than six repetitions.

	if DISTRACTOR_TYPE is None:
		EXP_ID = EXP_ID + '_' + str(DISTRACTOR_TYPE) #+ '_' + str(BLOCK) #build string for file saving.
	else:
		EXP_ID = EXP_ID + '_' + str(DISTRACTOR_TYPE) #build string for file saving.

	PP_ID = viz.input('Participant code: ') #add participant code

	if PRACTICE == True: # HACK
		EYETRACKING = False 

	if EYETRACKING:
		from eyetrike_calibration_standard import Markers, run_calibration
		from eyetrike_accuracy_standard import run_accuracy
		from UDP_comms import pupil_comms
		import pupil_logger
	

	myExp = myExperiment(
		EYETRACKING, PRACTICE, EXP_ID, AUTOWHEEL, DEBUG, DEBUG_PLOT, DISTRACTOR_TYPE, ppid = PP_ID, trialspercondition=trials
		)

	
EXIT_CALLBACKS.append(myExp.CloseConnections)
def do_exit_callback():
	for cb in EXIT_CALLBACKS:
		cb()

viz.callback(viz.EXIT_EVENT,do_exit_callback)

viztask.schedule(myExp.runtrials())

