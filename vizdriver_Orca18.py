import viz
import vizact
import vizmat
import vizjoy
import viztask
import math as mt # python library
JOY_FIRE_BUTTONS = [100, 101, 102]
JOY_DIR_SWITCH_BUTTON = [5, 6]
KEY_FIRE_BUTTONS = [' ']
KEY_DIR_SWITCH_BUTTON = viz.KEY_DELETE

class Driver(viz.EventClass):
	def __init__(self, Cave):
		viz.EventClass.__init__(self)
				
		#self.__speed = 0.223 #metres per frame. equates to 13.4 m/s therefore 30mph.
		#8ms = 8/60 = .1333
		self.__speed = 8.0 #m./s
		self.__heading = 0.0
		self.__pause = -50 #pauses for 50 frames at the start of each trial
		
		self.__view = Cave
		# self.__view = viz.MainView.setPosition(0,1.20,0) #Grabs the main graphics window
		# self.__view = viz.MainView
		# self.__view.moverelative(viz.BODY_ORI)
		
		self.__automation = False

		self.__dir = 1.0 # direction of the vehicle (+: )
			
		#self.callback(viz.TIMER_EVENT,self.__ontimer)
		self.callback(viz.KEYDOWN_EVENT,self.keyDown) #enables control with the keyboard
		self.callback(vizjoy.BUTTONDOWN_EVENT,self.joyDown) 
		self.callback(vizjoy.MOVE_EVENT,self.joymove)
		
		#self.txtSWA = viz.addText("SWA",parent=viz.SCREEN)
		self.txtSWA = viz.addText("  ",parent=viz.SCREEN)
		self.txtSWA.setPosition(.45,.4)
		self.txtSWA.fontSize(36)
		
		#self.starttimer(0,0,viz.FOREVER)

		global joy
		joy = vizjoy.add()

		
	def toggleDir(self):
		if self.__dir > 0:
			self.__dir = -1.0
		else:
			self.__dir = 1.0
		
	def reset(self):
		
		self.__heading = 0.0
		self.__dir = 1.0
		turnrate = 0.0
		self.__view.reset(viz.BODY_ORI) 
				
		self.__view = viz.MainView
		
		self.__view.reset(viz.HEAD_POS|viz.BODY_ORI)
		self.__pause = -50
		
		#self.__view = viz.MainView.setPosition(0,1.20,0) ##CHANGE EYE-HEIGHT FROM HERE
		# self.__view = viz.MainView.setPosition(0,1.20,0) ##CHANGE EYE-HEIGHT FROM HERE
		# self.__view = viz.MainView
		# self.__view.moverelative(viz.BODY_ORI)
		data = joy.getPosition()
		data[0] = 0
		
		gas = data[1]

	def UpdateView(self):
		elapsedTime = viz.elapsed()

		yawrate = 0.0
		turnangle = 0.0
		distance = 0.0

		dt = elapsedTime
		#dt = 1.0/60.0 #not sure why but it's perceptually smoother with a constant. This shouldn't be the case.

		#Get steering wheel and gas position
		data = joy.getPosition()
		SteeringWheelValue = data[0] # on scale from -1 to 1.
		gas = data[1]

		if self.__automation:
			#keep heading up to date.
			ori = self.__view.getEuler()
			self.__heading = ori[0]

		elif not self.__automation:
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
			self.__dir = 1
			yawrate = self.__dir * SteeringWheelValue  * 35.0 #max wheel lock is 35degrees per s yawrate
			turnangle = yawrate * dt
			self.__heading += turnangle
		
			self.__pause = self.__pause+1
			#Update the viewpoint
			if self.__pause > 0:
								
				distance = self.__speed * dt

				#posnew = (0,0,self.__speed)
				posnew = (0,0,distance)
				eulernew = (self.__heading,0,0)
				
				self.__view.setPosition(posnew, viz.REL_LOCAL)
				self.__view.setEuler(eulernew) 
				
			else:
				self.__heading = 0.0
				self.__dir = 1.0
				turnangle = 0.0

		#return the values used in position update
		UpdateValues = []
		UpdateValues.append(yawrate)
		UpdateValues.append(turnangle)
		UpdateValues.append(distance)
		UpdateValues.append(dt)
		UpdateValues.append(SteeringWheelValue)

		return (UpdateValues)

	def keyDown(self,button):
		if button == KEY_DIR_SWITCH_BUTTON:
			self.toggleDir()		
		
	def joyDown(self,e):
		if e.button == JOY_DIR_SWITCH_BUTTON:
			return e.button			
		if e.button in JOY_FIRE_BUTTONS:
			button = e.button # do nothing

	def resetHeading(self):
		self.__heading = 0.0

	def setAutomation(self,Auto):

		"""flag to disconnect wheel and visuals"""
		self.__automation = Auto

	def getSpeed(self):
		return self.__speed

	def getPos(self):
		xPos = joy.getPosition()
		return xPos[0]#*90.0 ##degrees of steering wheel rotation 
		
	def getPause(self): ###added for flow manipulations
		return self.__pause
		
	def setSWA_visible(self):
		self.txtSWA.visible(viz.ON)
	
	def setSWA_invisible(self):
		self.txtSWA.visible(viz.OFF)
		
	def joymove(self,e):
	
		#translate position to SWA.		
	
		x = e.pos[0]*10		
		self.txtSWA.message(str(x))
			
