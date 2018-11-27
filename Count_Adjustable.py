import viz
import numpy as np
import vizmat
import transform
import math
import viztask
import pandas as pd

#import vizjoy
#Each trial should be an independent class. 


class Distractor(viz.EventClass):
	def __init__(self, filename, maxtargetnumber, ppid):
		viz.EventClass.__init__(self)

		#needs to be an eventclass for timer to work.				
		
		##PARAMETERS THAT DO NOT VARY PER TRIAL
		self.ppid = ppid
		self.filename = filename		
		self.AudioList = [] #load once at start. List of audio-files
		#letters = ['a','b','c','d','e','i','o']#,'f','g']#,'h','i','j','k','l']#,'m','n','o']
		#letters = ['a','b','k','h','f','i','o']#,'f','g']#,'h','i','j','k','l']#,'m','n','o'] #don't rhyme.

		self.letters = ['b','o','z','k','t','h','f','s','i','a','m','n','y','r','j'] #target letters are the front two. Need to be paired with three distractors.		

		l = len(self.letters)
		#self.LetterLength
		for i in range(l):
			a = self.letters[i]
			#self.AudioList.append(viz.addAudio('..\\textures\\audio-numbers\\' + a + '.wav'))		
			self.AudioList.append(viz.addAudio('C:\\VENLAB data\\shared_modules\\textures\\Alphabet_Sounds\\' + a + '.wav'))		

		self.Target_pool = self.letters[:maxtargetnumber] #returns list up to  maxtargetnumber
		self.Distractor_pool = self.letters[maxtargetnumber:]		

		#PAREMETERS THAT ARE SET AT THE START OF EACH TRIAL
		self.Trial_targets = [] #targets for that particular trial. 
		self.Trial_audioindexes = [] #empty list that is populated with indexes corresponding to places on the audio list. Targets will be the first N of the letter array, depending on trial number.
		self.Trial_targetoccurence_prob = 0 #trial parameters, target occurence
		self.Trial_targetnumber = 0 #trial parameters, target number		
		self.Trial_targetcounts = [] #empty list with actual self.Trial_targetnumber counts.
		self.Trial_EoTscores = [] #empty list with self.Trial_targetnumber user inputted counts.
		self.Trial_filename = "" #filename + trialN
		self.Trial_length = 20 #length of trial. Is usually constant.
		self.Trial_Timer = 0 #keeps track of trial length. 

		self.EndofTrial_Data = pd.DataFrame() #end of trial dataframe
		self.WithinTrial_Data = pd.DataFrame() #within trial dataframe. 		
		
		# PARAMETERS THAT VARY WITHIN TRIALS
		self.ON = 0 #flag denoting whether to record data
		self.targetDelay = [] #randomly varies between 1-1.5s
		self.currentaudio = None # currently heard stimuli
		self.currentaudio_type = None # currently heard stimuli
		self.ResponseStamp = 0	#time of response
		self.Stimuli_PlayedStamp = 0	#time of stimuli presentation
		self.delay = 1.25 #this is how quickly you want items repeated. Changes per stimuli. 
		self.Stimuli_Count = 0

		self.callback(viz.TIMER_EVENT,self.onTimer)		
		self.Stimuli_Timer =0 #between - presentation timer. 
		
		self.interval = 0.1 #delay randomly varies between 1 - 1.5 at .1 increments.		
		self.targetTimer = 0		
		self.targetInterval = 0
		self.starttimer(0,self.interval,viz.FOREVER)
				
		self.QuitFlag = 0
		
		self.ppresp = 0 #flag to say that participant has responded.
		
		self.EoTFlag = False #set to 1 when it is the EoT screen. 
		self.EoT_NumberofResponses = 0 #count to say how many counts have been inputted.
						
		###END OF TRIALS SCREEN
		self.EoTScreen = viz.addTexQuad(viz.SCREEN)
		self.EoTScreen.color(viz.BLACK)
		self.EoTScreen.setPosition(.5,.5)
		self.EoTScreen.setScale(100,100)
		self.EoTScreen.visible(viz.OFF)

		self.EndofTrial_Question = 'How many Xs did you hear? \n \n Press the RIGHT gear pad to register your count'
		self.Question = viz.addText(self.EndofTrial_Question, viz.SCREEN)
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

		# cannae remember what these do.				
		self.CurrentScore = -1 
		#self.TargetCount = 0
		self.TrialCount = 0
	
	def StartTrial(self, targetoccurence_prob, targetnumber, trialn, triallength):
		
		"""Sets parameters at the start of each trial, based on targetoccurence_prob and targetnumber"""
		
		self.Trial_targetoccurence_prob = targetoccurence_prob #trial parameters, target occurence probability
		self.Trial_targetnumber = targetnumber #trial parameters, target number		
		self.Trial_targetcounts = [0] * targetnumber #empty list with self.Trial_targetnumber counts
		self.Trial_EoTscores = [-1] * targetnumber
		self.Trial_filename = self.filename + "_" + str(trialn)
		self.Trial_length = triallength
		self.Trial_targets = list(np.random.choice(self.Target_pool, size=targetnumber, replace=False))
			
		#### CREATE DATA FRAMES ####
		EndofTrial_datacolumns = ['ppid'] #columns for end of trial dataframe		
		WithinTrial_datacolumns = ['ppid'] #columns for within trial dataframe. 
		#create columns for dataframe, depending on target number
		for i in range(1,targetnumber +1):
			EoTcolumn = 'EoTScore' + str(i)
			EndofTrial_datacolumns.append(EoTcolumn) 
			TargetCountcolumn = 'TargetCount' + str(i)
			EndofTrial_datacolumns.append(TargetCountcolumn) #columns for end of trial dataframe

			Targetcolumn = 'Target' + str(i)
			WithinTrial_datacolumns.append(Targetcolumn) #columns for within trial dataframe. 

		self.EndofTrial_Data = pd.DataFrame(columns=EndofTrial_datacolumns) #make new empty EndofTrial data

		WithinTrial_datacolumns.append('CurrentAudio')
		WithinTrial_datacolumns.append('RT')
		WithinTrial_datacolumns.append('ResponseCategory')

		self.WithinTrial_Data = pd.DataFrame(columns=WithinTrial_datacolumns) #make new empty EndofTrial data

		self.EoT_NumberofResponses = 0 # not sure what this logic is for yet.						
		self.ON = 1
		self.Stimuli_Timer = 0 #reset inter-presentation timer
		self.Trial_Timer = 0 #reset trial length to zero 		
		
	def onTimer(self,num):							
				
		if self.ON == 1:
		#print "self.Stimuli_Timer: " + str(self.Stimuli_Timer)
		#need to only play files sequentially.
			if self.Stimuli_Timer > self.delay:
				choice = np.random.randint(0,2)
				if choice == 1:	
					if self.Stimuli_Count < 1: 
						self.SetNewStimuli()
					else:
						self.DetectAudioResponse() #function that sets target, with delay parameters		
			
			self.Stimuli_Timer = self.Stimuli_Timer+self.interval	
			
			self.Trial_Timer = self.Trial_Timer + self.interval #timer to keep track of overall trial length
			if self.Trial_Timer > self.Trial_length:
				#here start end of trial screens. 
				self.EndofTrial() 						
	
	def getFlag(self):
		#return whether end of trial screen is on.
		"called get flag"
		return(self.EoTFlag)
	
	def getEoT_NumberofResponses(self):
		#return whether ppresponded.
		"called get response"
		return(self.EoT_NumberofResponses)

	def ChangeQuestionText(self):
		
		"""changes self.Question message based on targets in trial and number of responses"""
		
		target = str(self.Trial_targets[self.EoT_NumberofResponses])
		msg = str(self.EndofTrial_Question)
		msg = msg.replace('X', target)
		self.lblscore.message('-1')

		self.Question.message(msg)

	
	def EndofTrial(self):
		
		"""Throws black screen and wait for gearpads to be pressed"""
		
		self.ChangeQuestionText()
				
		self.EoTScreen_Visibility(viz.ON)	
		
		#tell class it is end of trial. 
		self.EoTFlag = True	
		self.ON = 0

	def EoTScreen_Visibility(self, visible = viz.ON):

		"""switches the EoTscreen visibility off or on"""
	
		self.EoTScreen.visible(visible)
		self.Question.visible(visible)
		self.lblscore.visible(visible)

	
	def SaveData(self):

		"""Call after all responses are recorded to save data to file"""

		##save all data to file.
		
		#record data					
		self.ON = 0						
				

		output = self.Trial_EoTscores + self.Trial_targetcounts #makes a list of the correct length
		output[::2] = self.Trial_EoTscores
		output[1::2] = self.Trial_targetcounts
		output.insert(0,self.ppid)

		self.EndofTrial_Data.loc[0,:] = output #this dataframe is actually just one line. 
		

		self.EndofTrial_Data.to_csv('//Data//' + str(self.filename) + '_EndofTrial.csv')
		self.WithinTrial_Data.to_csv('//Data//' + str(self.filename) + '_WithinTrial.csv')

		self.EoTScreen_Visibility(viz.OFF)
		
		#tell class it is end of trial. 
		self.EoTFlag = False				
		
	def DetectAudioResponse(self):

		"""Function determines whether there has been an appropriate response"""									

		print ("DetectAudioResponse called")
		
		print ("currentaudio_type", self.currentaudio_type)

		if self.currentaudio_type == 'T': #should have responded.

			target_index = self.Trial_targets.index(self.currentaudio) #retrieve index of target within current trial

			self.Trial_targetcounts[target_index] += 1 #increment target count. 
			if self.ppresp == 1:
				RT = self.ResponseStamp-self.Stimuli_PlayedStamp
				ResponseCategory = 1 #correctly responded.
			elif self.ppresp == 0:
				RT = -1
				ResponseCategory = 2 #did not respond when should have.
		
		elif self.currentaudio_type == 'D': #should NOT have responded.						
			if self.ppresp == 1:
				RT = self.ResponseStamp-self.Stimuli_PlayedStamp
				ResponseCategory = '3' #responded when shouldn't have.					
			elif self.ppresp == 0:
				RT = -1
				ResponseCategory = '4' #correct absence of response
				
		#the row size will change depending on target number.
		currentresponse = [self.currentaudio, RT, ResponseCategory] 
		output = self.Trial_targets + list(currentresponse)
		output.insert(0,self.ppid)
		self.WithinTrial_Data.loc[self.Stimuli_Count-1,:] = output		

		self.SetNewStimuli()
		
	def SetNewStimuli(self):
		
		"""Sets the delay and target for the next stimuli, based on the target occurence and current pool"""
		
		print ("SetNewStimuli called")

		choices = ['T','D']
		probabilities = [self.Trial_targetoccurence_prob, 1-self.Trial_targetoccurence_prob]
		self.currentaudio_type = np.random.choice(choices, p = probabilities)

		if self.currentaudio_type == 'T':
			self.currentaudio = np.random.choice(self.Trial_targets)
		elif self.currentaudio_type == 'D':
			self.currentaudio = np.random.choice(self.Distractor_pool)		
							
		self.Stimuli_PlayedStamp=viz.tick()
		
		print(self.currentaudio)
		sound1 = self.AudioList[self.letters.index(self.currentaudio)] #retrieve loaded sound file from list.		
		sound1.setTime(0)		
		viz.director(PlaySound,sound1)		

		self.Stimuli_Timer=0
		self.ppresp = 0		
		
		##set new delay. Random between 1-1.5
		jitter = np.random.randint(0,49)		
		self.delay = 1.0 + (jitter/100.0)				

		self.Stimuli_Count += 1


	#### THE FOLLOWING FUNCTIONS CONTROL THE DRIVER INTERACTING WITH THE WHEEL ######

	def keydown(self,button):
		
		"""records a button press response to stimuli"""
		
		if self.ON == 1:
			self.ResponseStamp = viz.tick()

			#can press any button for response		
			self.ppresp = 1			
			
			#print "responded: " + str(viz.tick())
			
	def gearpaddown(self,button):
		
		"""saves on-screen count"""	

		#TODO: change to accommodate multiple target iterations.

		print "Button: " + str(button) #6 is left. 5 is right. Participants can press any button for the response.
		
		if self.EoTFlag:

			self.Trial_EoTscores[self.EoT_NumberofResponses] = self.CurrentScore 				
			self.EoT_NumberofResponses += 1
			print("Recorded Count" + str(self.EoT_NumberofResponses))				
			self.ChangeQuestionText()														

			if self.EoT_NumberofResponses == self.Trial_targetnumber: #if all responses given, save data.
				self.EoTFlag = False
				self.SaveData()			
		
	def joymove(self,pos):
		
		"""translates steering wheel movement to movement of the label text"""
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
			
def PlaySound(myaudio):
	"""plays sound"""
	#print 'director:'
	myaudio.volume(1)
	myaudio.play()