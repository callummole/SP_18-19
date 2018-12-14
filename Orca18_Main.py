"""
Script to run silent failure paradigm, with cognitive load. Every trial begins with a period of automation. 

The Class myExperiment handles execution of the experiment.

This script relies on the following modules:

For eyetracking - eyetrike_calibration_standard.py; eyetrike_accuracy_standard.py; also the drivinglab_pupil plugin.

For perspective correct rendering - myCave.py

For motion through the virtual world - vizdriver.py

"""
import sys

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

def GenerateConditionLists(FACTOR_radiiPool, FACTOR_YawRate_offsets, TrialsPerCondition):
	"""Based on two factor lists and TrialsPerCondition, create a factorial design and return trialarray and condition lists"""

	NCndts = len(FACTOR_radiiPool) * len(FACTOR_YawRate_offsets)	
#	ConditionList = range(NCndts) 

	#automatically generate factor lists so you can adjust levels using the FACTOR variables
	ConditionList_radii = np.repeat(FACTOR_radiiPool, len(FACTOR_YawRate_offsets)	)
	ConditionList_YawRate_offsets = np.tile(FACTOR_YawRate_offsets, len(FACTOR_radiiPool)	)

	print (ConditionList_radii)
	print (ConditionList_YawRate_offsets)

	TotalN = NCndts * TrialsPerCondition

	TRIALSEQ = range(0,NCndts)*TrialsPerCondition
	np.random.shuffle(TRIALSEQ)

	direc = [1,-1]*(TotalN/2) #makes half left and half right.
	np.random.shuffle(direc) 

	TRIALSEQ_signed = np.array(direc)*np.array(TRIALSEQ)

	return (TRIALSEQ_signed, ConditionList_radii, ConditionList_YawRate_offsets)

# ground texture setting
def setStage(TILING = True):
	
	"""Creates grass textured groundplane"""
	
	# background color
	viz.clearcolor(viz.SKYBLUE)
	
	#CODE UP TILE-WORK WITH GROUNDPLANE.	
	##should set this up so it builds new tiles if you are reaching the boundary.
	fName = 'textures\\strong_edge.bmp'
	gtexture = viz.addTexture(fName)
	gtexture.wrap(viz.WRAP_T, viz.REPEAT)
	gtexture.wrap(viz.WRAP_S, viz.REPEAT)
	#add groundplane (wrap mode)
###UNCOMMENT FOR TILING
# Tiling saves memory by using two groundplane tiles instead of a massive groundplane. Since the drivers are essentially driving linearly forward, they cover a lot of distance across the z axis.
	gplane1 = viz.addTexQuad() ##
	tilesize = 1000 #half a km wide
	#planesize = tilesize/5
	planesize = tilesize/5.0
	gplane1.setScale(tilesize, tilesize*2, tilesize)
	gplane1.setEuler((0, 90, 0),viz.REL_LOCAL)
	#groundplane.setPosition((0,0,1000),viz.REL_LOCAL) #move forward 1km so don't need to render as much.
	matrix = vizmat.Transform()
	matrix.setScale( planesize, planesize*2, planesize )
	gplane1.texmat( matrix )
	#gplane1.texture(gtexture)
	gplane1.texture(gtexture)
	gplane1.visible(1)
#
	if TILING:
		gplane2 = gplane1.copy() #create duplicate.
		gplane2.setScale(tilesize, tilesize*2, tilesize)
		gplane2.setEuler((0, 90, 0),viz.REL_LOCAL)
		#groundplane.setPosition((0,0,1000),viz.REL_LOCAL) #move forward 1km so don't need to render as much.
		gplane2.texmat( matrix )
		#gplane1.texture(gtexture)
		gplane2.texture(gtexture)
		gplane2.visible(1)
		gplane2.setPosition(0,0,tilesize*2)
		gplane2.zoffset(-1)
	else:
		gplane2 = []
	
	return(gplane1, gplane2)
#	##To save CPU I could move a small quad with the person.
#	gsizex = 50 #groundplane size, metres squared
#	gsizez = 160 #clipped at 150.
#	#groundplane = vizshape.addPlane(size=(gsize[0],gsize[1]),axis=vizshape.AXIS_Y,cullFace=True) ##make groundplane
#	#draw black quad
#	#groundplane.texture(viz.add('black.bmp')) #make groundplane black
#	viz.startLayer(viz.QUADS)
#	viz.vertexColor(viz.BLACK)
#	viz.vertex(0-gsizex,0,0)	
#	viz.vertex(0-gsizex,0,+gsizez)
#	viz.vertex(0+gsizex,0,+gsizez)
#	viz.vertex(0+gsizex,0,0)
#	groundplane = viz.endLayer()
#	groundplane.dynamic()
#	groundplane.visible(1)
#	link = viz.link(viz.MainView,groundplane)
#	link.clampPosY(0)
#	
#	
#	
##	#NEED TO TILE THIS DOTS & JUST BEYOND
##
#	#Build dot plane to cover black groundplane
#	ndots = 100000 #arbitrarily picked. perhaps we could match dot density to K & W, 2013? 
#	dsize = 5000
#	viz.startlayer(viz.POINTS)
#	viz.vertexColor(viz.WHITE)	
#	viz.pointSize(2)
#	for i in range (0,ndots):
#		x =  (random.random() - .5)  * dsize
#		z = (random.random() - .5) * dsize
#		viz.vertex([x,0,z])
#	
#	dots = viz.endLayer()
#	dots.setPosition(0,0,0)
#	dots.visible(1)
class Bend():
	def __init__(self, startpos, size, rads, array, sign = 1, colour = viz.WHITE, primitive = viz.QUAD_STRIP, primitive_width=None, road_width = 3.0):
		"""Returns a  bend of a specific road width, with functions to set the visibility, position, or Euler of both edges at once"""	

		#make sign -1 if you want a left bend.
		#improve to have a flag if it's a quad, and the quad width.

		self.RoadOrigin = startpos
		self.RoadSize_Pts = size
		self.RoadWidth = road_width		
		self.HalfRoadWidth = road_width/2.0		
		self.Rads = rads
		self.RoadArray = array 
		self.BendDirection = sign #left or right [-1,1]
		self.colour = colour
		self.primitive = primitive
		self.primitive_width = primitive_width
		
		self.InsideEdge_Rads = self.Rads-(self.HalfRoadWidth)
		self.InsideEdge_Origin = [self.RoadOrigin[0]-self.HalfRoadWidth,.1, self.RoadOrigin[2]] 

		self.OutsideEdge_Rads = self.Rads+(self.RoadWidth/2.0)
		self.OutsideEdge_Origin = [self.RoadOrigin[0]+self.HalfRoadWidth,.1, self.RoadOrigin[2]]


		#put default widths if not given
		if primitive_width is None:
			if primitive == viz.QUAD_STRIP:
				primitive_width = .05
				self.primitive_width = primitive_width 
					
			elif primitive == viz.LINE_STRIP:
				self.primitive_width = 2
				viz.linewidth(self.primitive_width)
				primitive_width = 0 #so I can use the same code below for both primitive types.		

		self.InsideEdge = self.EdgeMaker(self.InsideEdge_Origin, self.InsideEdge_Rads, primitive_width)
		self.OutsideEdge = self.EdgeMaker(self.OutsideEdge_Origin, self.OutsideEdge_Rads, primitive_width)

		#make it so both edges have the same center. The setCenter is in local coordinates
		self.InsideEdge.setCenter([-self.HalfRoadWidth, 0, 0])
		self.OutsideEdge.setCenter([+self.HalfRoadWidth, 0, 0])		

	def EdgeMaker(self, startpos, rads, primitive_width):
		"""function returns a bend edge"""
		i = 0
		viz.startlayer(self.primitive) 	
		
		viz.vertex(startpos[0], .1, startpos[2]) #start at end of straight
		while i < self.RoadSize_Pts:			
			x1 = ((rads-primitive_width)*np.cos(self.RoadArray[i])) #+ BendRadius
			z1 = self.BendDirection*((rads-primitive_width)*np.sin(self.RoadArray[i])) + startpos[2]
			
			#print (z1[i])			
			viz.vertex(x1, .1, z1)				
			viz.vertexcolor(self.colour)

			if self.primitive == viz.QUAD_STRIP:
				x2 = ((rads+primitive_width)*np.cos(self.RoadArray[i])) #+ BendRadius
				z2 = self.BendDirection*((rads+primitive_width)*np.sin(self.RoadArray[i])) + startpos[2]
				viz.vertex(x2, .1, z2)				
				viz.vertexcolor(self.colour)

			i += 1
			
		Bend = viz.endlayer()

		return Bend

	def ToggleVisibility(self, visible = viz.ON):
		"""switches bends off or on"""

		self.InsideEdge.visible(visible)
		self.OutsideEdge.visible(visible)
	
def BendMaker(radlist):
	
	"""makes left and right roads  for for a given radii and return them in a list"""
	
	#needs to work with an array of radii

	rdsize = 500 # Hz size for curve length	
	#left_array= np.arange(0.0, np.pi*1000)/1000
	left_array= np.linspace(0.0, np.pi,rdsize)
	#right_array = np.arange(np.pi*1000, 0.0, -1)/1000  ##arange(start,stop,step). Array with 3142(/1000) numbers
	right_array = np.linspace(np.pi, 0.0, rdsize)  ##arange(start,stop,step). Array with 3142(/1000) numbers
		
	leftbendlist = []
	rightbendlist = []
	grey = [.8,.8,.8]
	startpos = [0,0,0]

	for r in radlist:
		rightbend = Bend(startpos = startpos, size = rdsize, rads = r, array = right_array, sign = 1, colour = grey)
			
		rightbendlist.append(rightbend)

		leftbend = Bend(startpos = startpos, size = rdsize, rads = r, array = left_array, sign = -1, colour = grey)
			
		leftbendlist.append(leftbend)
	
	return leftbendlist,rightbendlist 

class myExperiment(viz.EventClass):

	def __init__(self, eyetracking, practice, tiling, exp_id, ppid = 1):

		viz.EventClass.__init__(self)
	
		self.EYETRACKING = eyetracking
		self.PRACTICE = practice
		self.TILING = tiling
		self.EXP_ID = exp_id

		if EYETRACKING == True:	
			LoadEyetrackingModules()

		self.PP_id = ppid
		self.VisibleRoadTime = 2.5 #length of time that road is visible. Constant throughout experiment
	
		#### PERSPECTIVE CORRECT ######
		self.caveview = LoadCave() #this module includes viz.go()

		##### SET CONDITION VALUES #####
		self.FACTOR_radiiPool = [300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000, 3300, 3600,-1] #13 radii conditions. 300m steps.
		self.FACTOR_YawRate_offsets = [0, .5, 1] #3 occlusion conditions
		self.TrialsPerCondition = 10	
		[trialsequence_signed, cl_radii, cl_occl]  = GenerateConditionLists(self.FACTOR_radiiPool, self.FACTOR_YawRate_offsets, self.TrialsPerCondition)

		self.TRIALSEQ_signed = trialsequence_signed #list of trialtypes in a randomised order. -ve = leftwards, +ve = rightwards.
		self.ConditionList_radii = cl_radii
		self.ConditionList_YawRate_offsets = cl_occl

		##### ADD GRASS TEXTURE #####
		[gplane1, gplane2] = setStage(TILING)
		self.gplane1 = gplane1
		self.gplane2 = gplane2

		##### MAKE BEND OBJECTS #####
		[leftbends,rightbends] = BendMaker(self.FACTOR_radiiPool)
		self.leftbends = leftbends
		self.rightbends = rightbends 

		self.callback(viz.TIMER_EVENT,self.updatePositionLabel)
		self.starttimer(0,0,viz.FOREVER) #self.update position label is called every frame.
		
		####### DATA SAVING ######
		datacolumns = ['ppid', 'radius','occlusion','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','YawRate_seconds','TurnAngle_frames','Distance_frames','dt', 'BendVisible']
		self.Output = pd.DataFrame(columns=datacolumns) #make new empty EndofTrial data

		### parameters that are set at the start of each trial ####
		self.Trial_radius = 0
		self.Trial_occlusion = 0 				
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
		self.Current_BendVisibleFlag = 0
		self.Current_YawRate_seconds = 0
		self.Current_TurnAngle_frames = 0
		self.Current_distance = 0
		self.Current_dt = 0

		self.callback(viz.EXIT_EVENT,self.SaveData) #if exited, save the data. 

	def runtrials(self):
		"""Loops through the trial sequence"""
		
		if self.EYETRACKING:
			filename = str(self.EXP_ID) + "_Calibration" #+ str(demographics[0]) + "_" + str(demographics[2]) #add experimental block to filename
			print (filename)
			yield run_calibration(comms, filename)
			yield run_accuracy(comms, filename)		

		self.driver = vizdriver.Driver(self.caveview)	

		
		viz.MainScene.visible(viz.ON,viz.WORLD)		
	
		#add text to denote conditons.
		txtCondt = viz.addText("Condition",parent = viz.SCREEN)
		txtCondt.setPosition(.7,.2)
		txtCondt.fontSize(36)		

		if self.EYETRACKING:
			comms.start_trial()
		
		for i, trialtype_signed in enumerate(self.TRIALSEQ_signed):
			#import vizjoy		
			print("Trial: ", str(i))
			print("TrialType: ", str(trialtype_signed))
			
			trialtype = abs(trialtype_signed)

			trial_radii = self.ConditionList_radii[trialtype] #set radii for that trial
			trial_occl = self.ConditionList_YawRate_offsets[trialtype] #set target number for the trial.

			print(str([trial_radii, trial_occl]))

			txtDir = ""
			
			print ("Length of bend array:", len(self.rightbends))

			radius_index = self.FACTOR_radiiPool.index(trial_radii)

			#choose correct road object.
			if trialtype_signed > 0: #right bend
				trialbend = self.rightbends[radius_index]
				txtDir = "R"
			else:
				trialbend = self.leftbends[radius_index]
				txtDir = "L"
						
			if trial_radii > 0: #if trial_radii is above zero it is a bend, not a straight 
				msg = "Radius: " + str(trial_radii) + txtDir + '_' + str(trial_occl)
			else:
				msg = "Radius: Straight" + txtDir + '_' + str(trial_occl)
			txtCondt.message(msg)	

			#update class#
			self.Trial_N = i
			self.Trial_radius = trial_radii
			self.Trial_occlusion = trial_occl			
			self.Trial_BendObject = trialbend			

			# Define a function that saves data
			
			#translate bend to driver position.
			driverpos = viz.MainView.getPosition()
			print driverpos
			trialbend.setPosition(driverpos[0],0, driverpos[2])
					
			#now need to set orientation
			driverEuler = viz.MainView.getEuler()
			trialbend.setEuler(driverEuler, viz.ABS_GLOBAL)		
			
			#will need to save initial vertex for line origin, and Euler. Is there a nifty way to save the relative position to the road?
			self.driver.setSWA_invisible()		
			
			yield viztask.waitTime(trial_occl) #wait an occlusion period. Will viztask waitime work within a class? 
			
			trialbend.visible(1)
			
			yield viztask.waitTime(self.VisibleRoadTime-trial_occl) #after the occlusion add the road again. 2.5s to avoid ceiling effects.
			
			trialbend.visible(0)
			#driver.setSWA_visible()
			
			def checkCentred():
				
				centred = False
				x = self.driver.getPos()
				if abs(x) < .5:
					centred = True						
				
				return (centred)
			
			##wait a while
			print "waiting"
			#TODO: Recentre the wheel on automation.

			yield viztask.waitTrue(checkCentred)
			print "waited"
			
			self.driver.setSWA_visible()
			yield viztask.waitTime(2) #wait for input .		
	
		#loop has finished.
		CloseConnections(self.EYETRACKING)
		#viz.quit() 

	def RecordData(self):
		
		"""Records Data into Dataframe"""

		#datacolumns = ['ppid', 'radius','occlusion','trialn','timestamp','trialtype_signed','World_x','World_z','WorldYaw','SWA','BendVisible']
		output = [self.PP_id, self.Trial_radius, self.Trial_occlusion, self.Trial_N, self.Current_Time, self.Trial_trialtype_signed, 
		self.Current_pos_x, self.Current_pos_z, self.Current_yaw, self.Current_SWA, self.Current_YawRate_seconds, self.Current_TurnAngle_frames, 
		self.Current_distance, self.Current_dt, self.Current_BendVisibleFlag] #output array.
		
		self.Output.loc[self.Current_RowIndex,:] = output #this dataframe is actually just one line. 		
	
	def SaveData(self):

		"""Saves Current Dataframe to csv file"""
		self.Output.to_csv('Data//Pilot.csv')

	def updatePositionLabel(self, num):
		
		"""Timer function that gets called every frame. Updates parameters for saving and moves groundplane if TILING mode is switched on"""

		#print("UpdatingPosition...")	
		#update driver view.
		UpdateValues = self.driver.UpdateView() #update view and return values used for update
		
		# get head position(x, y, z)
		pos = viz.get(viz.HEAD_POS)
		pos[1] = 0.0 # (x, 0, z)
		# get body orientation
		ori = viz.get(viz.BODY_ORI)		
									
		### #update Current parameters ####
		self.Current_pos_x = pos[0]
		self.Current_pos_z = pos[2]
		self.Current_SWA = UpdateValues[4]
		self.Current_yaw = ori
		self.Current_RowIndex += 1
		self.Current_Time = viz.tick()
		self.Current_YawRate_seconds = UpdateValues[0]
		self.Current_TurnAngle_frames = UpdateValues[1]
		self.Current_distance = UpdateValues[2]
		self.Current_dt = UpdateValues[3]

		if self.Trial_BendObject is not None:
			self.Current_BendVisibleFlag = self.Trial_BendObject.getVisible()	
		else:
			self.Current_BendVisibleFlag = None


		self.RecordData() #write a line in the dataframe.
	
		if self.TILING:
		
			#check if groundplane is culled, and update it if it is. 
			if viz.MainWindow.isCulled(self.gplane1):
				#if it's not visible, move ahead 50m from the driver.
				
				print 'attempting to shift gplane1'
				#translate bend to driver position.
				driverpos = viz.MainView.getPosition()
				self.gplane1.setPosition(driverpos[0],0, driverpos[2],viz.ABS_GLOBAL) #bring to driver pos
				
				#now need to set orientation
				#driverEuler = viz.MainView.getEuler()
				self.gplane1.setEuler(driverEuler[0],0,0, viz.ABS_GLOBAL)		
				
				self.gplane1.setPosition(0,0, 30, viz.REL_LOCAL) #should match up to the tilesize * 3
				
				
				self.gplane1.setEuler(0,90,0, viz.REL_LOCAL) #rotate to ground plane	
				
			if viz.MainWindow.isCulled(self.gplane2):
				#if it's not visible, move ahead 50m from the driver.
				
				print 'attempting to shift gplane2'
				#translate bend to driver position.
				driverpos = viz.MainView.getPosition()
				self.gplane2.setPosition(driverpos[0],0, driverpos[2],viz.ABS_GLOBAL) #bring to driver pos
				
				#now need to set orientation
				#driverEuler = viz.MainView.getEuler()
				self.gplane2.setEuler(driverEuler[0],0,0, viz.ABS_GLOBAL)		
				
				self.gplane2.setPosition(0,0, 30, viz.REL_LOCAL) #should match up to the tilesize y size of the other tile.
				
				self.gplane2.setEuler(0,90,0, viz.REL_LOCAL) #rotate to ground plane		

def CloseConnections(EYETRACKING):
	
	"""Shuts down EYETRACKING and wheel threads then quits viz"""		
	
	print ("Closing connections")
	if EYETRACKING: 
	 	comms.stop_trial() #closes recording			
	
	#kill automation
	viz.quit()
	
if __name__ == '__main__':

	###### SET EXPERIMENT OPTIONS ######	
	EYETRACKING = True
	PRACTICE = True
	TILING = False
	EXP_ID = "Orca18"

	if PRACTICE == True: # HACK
		EYETRACKING = False 

	myExp = myExperiment(EYETRACKING, PRACTICE, EXP_ID)

	viz.callback(viz.EXIT_EVENT,CloseConnections, myExp.EYETRACKING)

	viztask.schedule(myExp.runtrials())

