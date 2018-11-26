import viz
import numpy as np
import vizmat
import transform
import math
import viztask

#import vizjoy
#Each trial should be an independent class. 


class Distractor(viz.EventClass):
	def __init__(self, filename):
		viz.EventClass.__init__(self)

		#needs to be an eventclass for timer to work.
		#self.callback(viz.EXIT_EVENT,self.EndTrial)
		
		##STEP 1: SETUP TASK							
		self.filename = filename
		self.ON = 0 #flag denoting whether to record data
		self.Target1='b' #Target1. Fixed across trials
		self.Target2='o' #Target2. Fixed across trials
		self.targetDelay = [] #randomly varies between 1-1.5s
		self.currenttarget = '-1' #-1 stimuli the pp is listening for
		self.currentaudio = '-1' # currently heard stimuli
		self.Target1Count = 0 #appearance count. Max 3 per trial.
		self.Target2Count = 0 #appearance count. Max 3 per trial.

		self.ResponseStamp = 0	#time of response
		self.DrawStamp = 0	#time of stimuli presentation
		
		self.callback(viz.TIMER_EVENT,self.onTimer)		
		self.Timer =0
		
		self.interval = 0.1 #delay randomly varies between 1 - 1.5 at .1 increments.
		self.delay = 1.25 #this is how quickly you want items repeated. Changes per stimuli. 
		
		self.targetTimer = 0		
		self.targetInterval = 0
		self.starttimer(0,self.interval,viz.FOREVER)
		
		
		self.out=""
		self.QuitFlag = 0
		
		self.ppresp = 0 #flag to say that participant has responded.
		
		self.EoTFlag = False #set to 1 when it is the EoT screen. 
		self.EoTResp = 0 #flag to say that pps have recorded.
		
		self.AudioList = [] #load once at start. List of audio-files
		#letters = ['a','b','c','d','e','i','o']#,'f','g']#,'h','i','j','k','l']#,'m','n','o']
		#letters = ['a','b','k','h','f','i','o']#,'f','g']#,'h','i','j','k','l']#,'m','n','o'] #don't rhyme.
		self.letters = ['b','o','a','k','t','h','f','s','i','z','m','n','y','r','j'] #target letters are the front two. Need to be paired with three distractors.
		l = len(self.letters)
		#self.LetterLength
		for i in range(l):
			a = self.letters[i]
			#self.AudioList.append(viz.addAudio('..\\textures\\audio-numbers\\' + a + '.wav'))		
			self.AudioList.append(viz.addAudio('..\\textures\\Alphabet_Sounds\\' + a + '.wav'))		
		
		self.TrialList = [0,1,2,3,4]
						
		###setup Two End-of-Trials screen.
		self.EoTScreen = viz.addTexQuad(viz.SCREEN)
		self.EoTScreen.color(viz.BLACK)
		self.EoTScreen.setPosition(.5,.5)
		self.EoTScreen.setScale(100,100)
		self.EoTScreen.visible(viz.OFF)

		self.Question = viz.addText('How many Bs did you hear? \n \n Press the LEFT gear pad to register your count', viz.SCREEN)
		self.Question.color(1,1,0)
		self.Question.setPosition(0.5,0.75)
		self.Question.fontSize(36)
		self.Question.alignment(viz.TEXT_CENTER_TOP)
		self.Question.visible(viz.OFF)
	
		self.lblscore = viz.addText('-1', viz.SCREEN)
		self.lblscore.setPosition(0.5,0.4)
		self.lblscore.fontSize(50)
		self.lblscore.alignment(viz.TEXT_CENTER_CENTER)
		self.lblscore.visible(viz.OFF)	
		
		self.EoTScore1 = -1
		self.EoTScore2 = -1
		self.CurrentScore = -1
		#self.TargetCount = 0
		self.TrialCount = 0
	
	def PickDistractors(self):
		
		#first two letters are targets. Routine picks three non-repeated distractors 
		l = len(self.letters)
		picked = False		
		d1 = 0
		d2 = 0
		d3 = 0
		while not picked:
			d = np.random.randint(2,l)
			if d1== 0:
				d1 = d #on the first step set d1
			elif d2 == 0 and d != d1: 
				d2 = d #on the second step set d2 if it is not repeated
			elif d3 == 0 and d != d1 and d != d2:
				d3 = d
				picked = True
		
		self.TrialList = [0,1,d1,d2,d3]
		
		
	def onTimer(self,num):							
				
#		if self.ON == 1:
		#print "self.Timer: " + str(self.Timer)
		#need to only play files sequentially.
		if self.Timer > self.delay:
			choice = np.random.randint(0,2)
			if choice == 1:			
				self.PlaySound() #function that sets target, with delay parameters		
		
		self.Timer = self.Timer+self.interval
		
#		elif self.ON == 0:
#			if self.Timer > 2: #start delay
#				sound1 = self.AudioList[int(self.currenttarget[0])-1]
#				print 'choose sound: ' + str(sound1) 				
#				sound1.volume(.5)
#				sound1.setTime(.25)		
#				sound1.stoptime(.6)
#				sound1.play()
			
		
	def keydown(self,button):
		#if key == ' ':
		
		if self.ON == 1:
			self.ResponseStamp = viz.tick()

			#can press any button for response		
			self.ppresp = 1			
			
			#print "responded: " + str(viz.tick())
			
	def gearpaddown(self,button):
		
		#if it is the end of trial then save response
		print "Button: " + str(button) #6 is left. 5 is right 
		if self.EoTFlag:
			
			if self.EoTResp == 0 and button==6: #if it's the first response make sure it is left
				self.EoTResp = 1
				self.EoTScore1 = self.CurrentScore
				print "Recorded T1"
				
				self.Question.message('How many Os did you hear? \n \n Press the RIGHT gear pad to register your count')
				self.lblscore.message('-1')
			
			elif self.EoTResp == 1 and button==5: #if it is the second response make sure it is right.
			
				self.EoTResp = 2
				self.EoTScore2 = self.CurrentScore
				print "Recorded T2"
				self.EndTrial()
			
		
	def joymove(self,pos):
		
		#if it is end of trial update score
		if self.EoTFlag:
			
			pos = pos[0]
			
			pos = (pos * 10) + 5 #wheelpos is between -1,1
			scale = 1
			scalepos = pos * scale
			
			roundpos = round(scalepos)							
			
			#print "round pos: " + str(roundpos)
			
			clamppos = viz.clamp(roundpos, 0, 10)
			
			self.CurrentScore = clamppos
			
			self.lblscore.message(str(clamppos))
										
			#print "score: " + str(self.EoTScore)
			
		
	def getFlag(self):
		#return whether end of trial screen is on.
		"called get flag"
		return self.EoTFlag
	
	def getEoTResp(self):
		#return whether ppresponded.
		"called get response"
		return self.EoTResp
	
	def EndofTrial(self):
		
		#throws screen up and waits.
		#set visible ON.	
		self.Question.message('How many Bs did you hear? \n \n Press the LEFT gear pad to register your count')
		self.lblscore.message('-1')
		self.EoTScreen.visible(viz.ON)
		self.Question.visible(viz.ON)
		self.lblscore.visible(viz.ON)		
		
		#tell class it is end of trial. 
		self.EoTFlag = True	
		self.ON = 0
	
	def EndTrial(self):
		##save all data to file.
		
		#record data			
		
		self.ON = 0		
		
		#add score to end of file.
		self.out = self.out + '\n' + str(self.EoTScore1) + '\t' + str(self.Target1Count) + '\t' + str(self.EoTScore2) + '\t' + str(self.Target2Count)
	
		fileproper=(self.filename+'_Distractor_' + str(self.TrialCount) + '.dat')
		# Opens nominated file in write mode
		path = viz.getOption('viz.publish.path','.')+'/data/'
		#		SpinCounter = 0 
		file = open(path + fileproper, 'w') 
		# Write the string to the output file
		file.write(self.out)                                     
		# Makes sure the file data is really written to the harddrive
		file.flush()                                        
		#print out
		file.close()							
		
		#reset flags.
		
		#Control these in main experiment
#		self.EoTScreen.visible(viz.OFF)
#		self.Question.visible(viz.OFF)
#		self.lblscore.visible(viz.OFF)
		
		#tell class it is end of trial. 
		self.EoTFlag = False
		
		self.TrialCount = self.TrialCount + 1
		self.EoTScore1 = -1
		self.EoTScore2 = -1
	
	def StartTrial(self):
		
		###CALL THIS FUNCTION AT THE START OF EACH TRIAL
		
		##it resets the target count, chooses a new target. Makes sure the target isn't the same as previous trials.
		
		#self.ON = 0 #do not record until target chosen.
		self.EoTResp = 0
		#oldtarget = str(self.currenttarget)
		self.out=""
		self.Target1Count = 0
		self.Target2Count = 0
		
		self.PickDistractors() #choose new distractors,
		
		##select target
#		#ChangeDisplayedNumber
#		picked = False
#		nums = [1,2,3,4,5]#,6,7,8,9] 
#		while not picked:			
#			#self.currenttarget = str(np.random.randint(1,10))			
#			self.currenttarget = str(np.random.randint(1,5))			
#			if  self.currenttarget <> oldtarget:
#					picked = True					
		
		#sound1 = self.AudioList[int(self.currenttarget[0])-1]
		#print 'choose sound: ' + str(sound1) 
		
		#viz.waittime(2.0)
		#sound1.volume(.5)
		#sound1.volume(2)
		#sound1.setTime(.25)		
		#sound1.setTime(0)		
		#sound1.stoptime(.6)
		#sound1.stoptime()
		#viz.director(PlayDirector,sound1)
		#sound1.play()
				
		self.ON = 1
		self.Timer = 0
		
	def PlaySound(self):
		
		#print "play sound called"
		
		##plays sound and records the response if correct (similar to old 'SetSum').
		##function needs to select a new sound which is different to the old sound. and also detect the response time.
		
		oldaudio = str(self.currentaudio)
		if self.ON == 1: #only repeat sound if during a trial.
			
			#record response to previous number
			if self.currentaudio == self.Target1: #correct pairing.
				self.Target1Count = self.Target1Count + 1 #increment target count.
				if self.ppresp == 1:
					RT = self.ResponseStamp-self.DrawStamp
					correct = '1' #correctly responded.
				elif self.ppresp == 0:
					RT = -1
					correct = '2' #did not respond when should have.
			elif self.currentaudio == self.Target2:
				self.Target2Count = self.Target2Count + 1 #increment target count.
				if self.ppresp == 1:
					RT = self.ResponseStamp-self.DrawStamp
					correct = '1' #correctly responded.
				elif self.ppresp == 0:
					RT = -1
					correct = '2' #did not respond when should have.
			else:
				if self.ppresp == 1:
					RT = self.ResponseStamp-self.DrawStamp
					correct = '3' #responded when shouldn't have.					
				elif self.ppresp == 0:
					RT = -1
					correct = '4' #correct absence of response
			
			self.out = self.out + self.Target1 + '\t' + self.Target2 + '\t' + self.currentaudio + '\t' + str(RT) + '\t' + correct + '\t' + '\n'
		
		
			#Playnewsound. Ensure it isn't a repeat.
			#pick from the Trial List.
			picked = False			
			l = len(self.TrialList)
			while not picked:			
				i = np.random.randint(0,l)				
				j = self.TrialList[i]
				self.currentaudio = self.letters[j]
				if  self.currentaudio != oldaudio:
					picked = True
			
			self.DrawStamp=viz.tick()
			#print "draw: " + str(viz.tick())
			print self.currentaudio
			sound1 = self.AudioList[j]
			#print 'sound: ' + str(sound1) 
			#sound1.volume(.5)
			#sound1.volume(1)
			#sound1.setTime(.25)		
			sound1.setTime(0)		
			#sound1.stoptime(.6)
			#sound1.stoptime()
			viz.director(PlayDirector,sound1)
			#sound1.play()
		
			#sound1.play()
			
			self.Timer=0
			self.ppresp = 0		
			
			##set new delay. Random between 1-1.5
			jitter = np.random.randint(0,49)		
			self.delay = 1.0 + (jitter/100.0)						
			

def PlayDirector(myaudio):
	
	#print 'director:'
	myaudio.volume(1)
	myaudio.play()