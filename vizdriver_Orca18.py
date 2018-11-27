import viz
import vizact
import vizmat
import vizjoy
import viztask
import math as mt # python library
import socket
import time
import numpy as np # numpy library - such as matrix calculation

JOY_FIRE_BUTTONS = [100, 101, 102]
JOY_DIR_SWITCH_BUTTON = [5, 6]
KEY_FIRE_BUTTONS = [' ']
KEY_DIR_SWITCH_BUTTON = viz.KEY_DELETE
KEY_PAUSE_SWITCH_BUTTON = 'r'

class Driver(viz.EventClass):
	def __init__(self):
		viz.EventClass.__init__(self)
		
		self.__speed = 0.223 #metres per frame. equates to 13.4 m/s therefore 30mph.
		#self.__speed = 0.0
		self.__heading = 0.0
		self.__turnrate = 0.0
		self.__pause = -50 #pauses for 50 frames at the start of each trial
		
		self.__view = viz.MainView.setPosition(0,1.20,0) #Grabs the main graphics window
		self.__view = viz.MainView
		self.__view.moverelative(viz.BODY_ORI)
		
		self.__dir = 1.0 # direction of the vehicle (+: )
		
		self.__P_GAIN = 2.0 # control gain
		
		self.__Distractor = [] #placeholder.

		self.__totalTime = 0.0
		self.__RoadCentre_X = 0.0
		self.__RoadCentre_Z = 0.0
		self.__VehicleCentre_X = 0.0
		self.__VehicleCentre_Z = 0.0
		self.__absFixationAngle = 0.0
		
		self.outvalue = 0 #control input value
		self.__DrivingTotalTime = 100.0 #Auto+Manual Duration
		self.__AutoDrivingTime = 0.0 #Automation Duration
		self.__TrialType = 0
		self.__SteeringBasis = 0
		self.__PAUSE_FLAG = 0 # immediatly pause flag
		self.__Input_Flag = 0
		
		#time.sleep(0.5)
		self.__soundFlag = 1
		
		self.callback(viz.TIMER_EVENT,self.__ontimer)
		self.callback(viz.KEYDOWN_EVENT,self.keyDown) #enables control with the keyboard
		self.callback(vizjoy.BUTTONDOWN_EVENT,self.joyDown) 
		self.callback(vizjoy.MOVE_EVENT,self.joymove)
		
		self.starttimer(0,0,viz.FOREVER)

		global joy
		joy = vizjoy.add()

		# force feedback function
		joy.setAutoCenter(True)

	def setDistractor(self, Distractor):
		"""Set Distractor class for joystick callbacks"""

		self.__Distractor = Distractor
		
	def toggleDir(self):
		if self.__dir > 0:
			self.__dir = -1.0
		else:
			self.__dir = 1.0
		
	def reset(self):
		
		self.__heading = 0.0
		self.__dir = 1.0
		self.__turnrate = 0.0
		self.__view.reset(viz.BODY_ORI) 
		
		self.__totalTime = 0.0
		self.__RoadCentre_X = 0.0
		self.__RoadCentre_Z = 0.0
		self.__VehicleCentre_X = 0.0
		self.__VehicleCentre_Z = 0.0
		self.__absFixationAngle = 0.0
		self.__PAUSE_FLAG = 0
		self.__Input_Flag = 0
		
		self.outvalue = 0		
		self.__soundFlag = 0
		
		self.__view = viz.MainView
		
		self.__view.reset(viz.HEAD_POS|viz.BODY_ORI)
		self.__pause = -50
		
		self.__view = viz.MainView.setPosition(0,1.20,0) ##CHANGE EYE-HEIGHT FROM HERE
		self.__view = viz.MainView
		self.__view.moverelative(viz.BODY_ORI)
		data = joy.getPosition()
		data[0] = 0
		
		gas = data[1]
		
	# fixpoint insert
	def function_insert(self, RoadCentreX, RoadCentreZ, VehicleCentreX, VehicleCentreZ):
		self.__RoadCentre_X = RoadCentreX
		self.__RoadCentre_Z = RoadCentreZ
		self.__VehicleCentre_X = VehicleCentreX
		self.__VehicleCentre_Z = VehicleCentreZ

		self.__absFixationAngle = mt.atan2(self.__RoadCentre_X - self.__VehicleCentre_X, self.__RoadCentre_Z - self.__VehicleCentre_Z)

	
		
	# setting trialtype
	def function_Trialtype(self, type):
		self.__TrialType = type
	
	# Return total time function to synchronise with Yuki.py
	def return_totaltime(self):
		return self.__totalTime 

	# Return turnrate function to synchronise with Yuki.py
	def return_turnrate(self):
		return self.__turnrate 
	
	# Return pause flag
	def return_puseflag(self):
		return self.__PAUSE_FLAG

	def __ontimer(self,num):
		elapsedTime = viz.elapsed()
	
		#Get steering wheel and gas position
		data = joy.getPosition()
		gas = data[1]

		if viz.key.isDown(viz.KEY_UP):
			gas = -5
		elif viz.key.isDown(viz.KEY_DOWN):
			gas = 5
		if viz.key.isDown(viz.KEY_LEFT): #rudimentary control with the left/right arrows. 
			data[0] = -1
		elif viz.key.isDown(viz.KEY_RIGHT):
			data[0] = 1
		
#		#Compute drag
#		drag = self.__speed / 300.0

		self.__totalTime = 0
		#self.__totalTime += elapsedTime
		self.__turnrate = 0.0
		
		#Update heading
		
		# make beep (2.5 seconds)
		if self.__totalTime > (self.__AutoDrivingTime - 2.5) and self.__soundFlag == 0:
			self.__soundFlag = 1
			# 0: standby state,     1: make beep (3 sec)
			# 2: make beep (1 sec), 3: finishing programme
		
		# make beep (1.0 second)
		# TotalDrivingTime = self.__DrivingTotalTime
		if self.__totalTime > (self.__DrivingTotalTime - 1.0) and self.__soundFlag == 1:
			self.__soundFlag = 2
			# 0: standby state,     1: make beep (3 sec)
			# 2: make beep (1 sec), 3: finishing programme
			
		if(self.__totalTime < self.__AutoDrivingTime):
			# automated driving
			
			# setting biased value
			# we have to adjust values based on velocity, road condition, fixation distance, gain
			
			# .027 is for 1.25 m from centreline
			#.146 is for a 2.5m understeering position.
			UnderOverSteeringValue = 0
			if self.__TrialType > 0: # right bend
				#UnderOverSteeringValue = -0.027 #obtained from trial and error. print lateral deviation on updatepositionlabel.
				UnderOverSteeringValue = -.146 #obtained from trial and error. print lateral deviation on updatepositionlabel.
			elif self.__TrialType < 0: # left bend
				#UnderOverSteeringValue = 0.027
				UnderOverSteeringValue = .146
			
			"""
			# following values are for 0.5 m from centreline
			UnderOverSteeringValue = 0
			if self.__TrialType > 0: # right bend
				UnderOverSteeringValue = 0.0466
			elif self.__TrialType < 0: # left bend
				UnderOverSteeringValue = -0.0466
			"""

			# P control of visual diriction 
			self.__turnrate = self.__P_GAIN * (self.__absFixationAngle - self.__heading*mt.pi/180 + UnderOverSteeringValue)
			
			"""
			# translate value into steering value
			CorrectValue = 3.0
			self.outvalue = int(self.__turnrate*180/mt.pi*100/9.0 * CorrectValue)
			print self.outvalue
			
			# maximum steering value is pm 1000
			if abs(self.outvalue) > 1000:
				if np.sign(self.outvalue) == 1:
					self.outvalue = 1000
				else:
					self.outvalue = -1000
			
			# steering value
			if self.__TrialType > 0: # right bend
				self.outvalue = 400
			elif self.__TrialType < 0: # left bend
				self.outvalue = -400

			# when output is not converged, sending value is restricted
			if abs(self.outvalue) > 10:
				# send data via UDP
				# 1024: standby state,         1025: steer initialization
				# 1026: finishing programme,  other: steering input value
				self.udpsend1.SEND_DATA(self.outvalue)
			"""
	
			
			# difference between input value and real steering wheel angle
			self.__SteeringBasis = self.__turnrate - self.__dir * (data[0])  * elapsedTime * 35

		else:
			# manual driving
			# force feedback function
			joy.setAutoCenter(True)
			
			self.__turnrate = self.__dir * (data[0])  * elapsedTime * 35 #translating steering wheel angle to heading change.
			
			# add bisis value not to connect discontinuously
			self.__turnrate += self.__SteeringBasis


		self.__heading += self.__turnrate
		
		#print elapsedTime
		#print self.__turnrate
		"""
		print "Total Time:        %f [s]" %self.__totalTime
		print "Heading:           %f [rad]" %(self.__heading*mt.pi/180)
		print "Road Centre X:     %f [m]" %self.__RoadCentre_X
		print "Road Centre Z:     %f [m]" %self.__RoadCentre_Z
		print "Vehicle Centre X:  %f [m]" %self.__VehicleCentre_X
		print "Vehicle Centre Z:  %f [m]" %self.__VehicleCentre_Z
		print "Control Angle:     %f [rad]" %(self.__absFixationAngle - self.__heading*mt.pi/180)
		print " "
		"""
		
		self.__pause = self.__pause+1
		#Update the viewpoint
		if self.__pause > 0:
			posnew = (0,0,self.__speed)
			eulernew = (self.__heading,0,0)
			self.__view.setPosition(posnew, viz.REL_LOCAL)
			self.__view.setEuler(eulernew, viz.REL_LOCAL)
				
		else:
			self.__heading = 0.0
			self.__dir = 1.0
			self.__turnrate = 0.0

	def keyDown(self,button):
		global PAUSE_FLAG
		if button == KEY_DIR_SWITCH_BUTTON:
			self.toggleDir()
		elif button == viz.KEY_ESCAPE:
			self.udpsend1.SEND_DATA(1026)
			self.udpsend2.SEND_DATA(3)
		elif button == KEY_PAUSE_SWITCH_BUTTON:
			self.__PAUSE_FLAG = 1
		
	def joyDown(self,e):
		if e.button == JOY_DIR_SWITCH_BUTTON:
			return e.button			
		if e.button in JOY_FIRE_BUTTONS:
			button = e.button # do nothing
			
					
		#left red buttons are 8,21,23. right red buttons are 7,20,22:
			#if buttons are left or right, call distractor task.
		if e.button in [8,7,21,23,20,22]:
			self.__Distractor.keydown(e.button)
		
		if e.button in [5,6]: #gearpads are 5&6
			self.__Distractor.gearpaddown()
			
	def joymove(self,e):
		
		end_of_trial_flag = self.__Distractor.getFlag()
		
		#if end of trial screen on.
		if end_of_trial_flag:
			self.__Distractor.joymove(e.pos)

	def getPos(self):
		xPos = joy.getPosition()
		return xPos[0]*90.0 ##degrees of steering wheel rotation 
	
	def getPause(self): ###added for flow manipulations
		return self.__pause
	
	def getJoy(self):
		return joy


class waitJoyButtonDown( viztask.Condition ):
	
	
	def __init__( self, button, joy ):
		#self.__joy = joy
		self._button = button
		self._joy = joy

	def update( self ):
		return self._joy.isButtonDown(self._button)