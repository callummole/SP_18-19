import viz
import numpy as np
import vizmat
import transform
import math
import viztask
import pandas as pd

import threading

import winsound

#import vizjoy
#Each trial should be an independent class. 


class Distractor(viz.EventClass):
	def __init__(self, filename, maxtargetnumber, ppid, triallength, ntrials, startscreentime = 2):
		viz.EventClass.__init__(self)

		#needs to be an eventclass for timer to work.				
		self.callback(viz.EXIT_EVENT,self.CloseConnections) #if exited, save the data. 

		##PARAMETERS THAT DO NOT VARY PER TRIAL
		self.ppid = ppid
		self.filename = filename		
		self.AudioList = [] #load once at start. List of audio-files		
		self.StartScreen_DisplayTime = startscreentime #amount of seconds that the targets for that trial are shown.
						
		#letters = ['a','b','c','d','e','i','o']#,'f','g']#,'h','i','j','k','l']#,'m','n','o']
		#letters = ['a','b','k','h','f','i','o']#,'f','g']#,'h','i','j','k','l']#,'m','n','o'] #don't rhyme.

		self.letters = ['b','o','z','k','t','h','f','s','i','a','m','n','y','r','j'] #target letters are the front two. Need to be paired with three distractors.	

		

		l = len(self.letters)
		#self.LetterLength
		for i in range(l):
			a = self.letters[i]
			#self.AudioList.append(viz.addAudio('..\\textures\\audio-numbers\\' + a + '.wav'))		
			self.AudioList.append(viz.addAudio('C:\\VENLAB data\\shared_modules\\textures\\Alphabet_Sounds\\' + a + '.wav'))					

		self.SoundPlayer_threaded = SoundPlayer_threaded(self.AudioList) #load thread
		self.SoundPlayer_threaded.start() #start the threaed

		#self.myaudio = viz.playSound('C:\\VENLAB data\\shared_modules\\textures\\Alphabet_Sounds\\' + 'b' + '.wav', viz.SOUND_PRELOAD)

		self.Target_pool = self.letters[:maxtargetnumber] #returns list up to  maxtargetnumber
		self.Distractor_pool = self.letters[maxtargetnumber:]

		self.nTrials = ntrials		
		self.Trial_length = triallength #length of trial. Is usually constant.

		self.EndofTrial_Data, self.WithinTrial_Data = self.BuildDataFrames(maxtargetnumber)		
		self.MaxTargetNumber = maxtargetnumber

		#PARAMETERS THAT ARE SET AT THE START OF EACH TRIAL
		self.Trial_targets = [] #targets for that particular trial. 
		self.Trial_audioindexes = [] #empty list that is populated with indexes corresponding to places on the audio list. Targets will be the first N of the letter array, depending on trial number.
		self.Trial_targetoccurence_prob = 0 #trial parameters, target occurence
		self.Trial_targetnumber = 0 #trial parameters, target number		
		self.Trial_targetcounts = [] #empty list with actual self.Trial_targetnumber counts.
		self.Trial_EoTscores = [] #empty list with self.Trial_targetnumber user inputted counts.	
		self.Trial_N = 0			
		self.Trial_Timer = 0 #keeps track of trial length. 		

		self.StartScreen_Timer = 0
		#self.Trial_Index = 0 #count for number of Trails, to index Trial dataframe. Isn't needed as Trial_N gets passed on StartTrial. 
		
		# PARAMETERS THAT VARY WITHIN TRIALS
		self.ON = 0 #flag denoting whether to record data
		self.targetDelay = [] #randomly varies between 1-1.5s
		self.currentaudio = None # currently heard stimuli
		self.currentaudio_type = None # currently heard stimuli
		self.ResponseStamp = 0	#time of response
		self.Stimuli_PlayedStamp = 0	#time of stimuli presentation
		self.delay = 1.25 #this is how quickly you want items repeated. Changes per stimuli. 
		self.Overall_Stimuli_Index = 0 #count for number of stimuli, to index response dataframe.
		self.Trial_Stimuli_Index = 0 #count for number of stimuli, to index response dataframe.

		self.callback(viz.TIMER_EVENT,self.onTimer, priority = 0)		
		self.Stimuli_Timer =0 #between - presentation timer. 
		
		self.interval = 0.1 #delay randomly varies between 1 - 1.5 at .1 increments.		
		self.targetTimer = 0		
		self.targetInterval = 0
		self.starttimer(0,self.interval,viz.FOREVER)
				
		self.QuitFlag = 0
		
		self.ppresp = 0 #flag to say that participant has responded.
		
		self.EoTFlag = False #set to 1 when it is the EoT screen. 
		self.StartFlag = False #set to true when start screen time elapses
		self.EoT_NumberofResponses = 0 #count to say how many counts have been inputted.
						
		### END OF TRIALS SCREEN ###
		self.EoTScreen = viz.addTexQuad(viz.SCREEN)
		self.EoTScreen.color(viz.BLACK)
		self.EoTScreen.setPosition(.5,.6)
		self.EoTScreen.setScale(100,100)
		self.EoTScreen.visible(viz.OFF)

		self.EndofTrial_Question = 'How many Xs did you hear? \n \n Press a single gear pad to register your count'
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

		self.CurrentScore = -1 #for on-screen score to be submitted as user count.

		### START OF TRIALS SCREEN ####
		self.StartScreen = viz.addTexQuad(viz.SCREEN)
		self.StartScreen.color(viz.BLACK)
		self.StartScreen.setPosition(.5,.5)
		self.StartScreen.setScale(100,100)
		self.StartScreen.visible(viz.OFF)

		self.Start_msg = 'Listen out for: \n \n'
		self.Starttxt = viz.addText(self.Start_msg, viz.SCREEN)
		self.Starttxt.color(1,1,0)
		self.Starttxt.setPosition(0.5,0.5)
		self.Starttxt.fontSize(36)
		self.Starttxt.alignment(viz.TEXT_CENTER_TOP)
		self.Starttxt.visible(viz.OFF)
	
	def BuildDataFrames(self, maxtargetnumber):
		"""Builds EoT_Dataframe and WithinTrial_DataFrame"""

		#add info for individual trials
		#EndofTrial_Data has columns: ['ppid', 'targetoccurence','targetnumber','trialn', 'EoTScore1','TargetCount1'...'EoTScoreN','TargetCountN']
		#WithinTrial_Data has columns: ['ppid', 'targetoccurence','targetnumber','trialn', 'CurrentAudio','RT','ResponseCategory', 'Target1',...'TargetN']

		trialinfo_columns = ['ppid', 'targetoccurence','targetnumber','trialn']

		EoTcolumns = trialinfo_columns
		WithinTrialcolumns = trialinfo_columns + ['CurrentAudio','RT','ResponseCategory']
		for i in range(1,maxtargetnumber +1):

			EoTcolumn = 'EoTScore' + str(i)
			EoTcolumns.append(EoTcolumn) 
			TargetCountcolumn = 'TargetCount' + str(i)
			EoTcolumns.append(TargetCountcolumn) #columns for end of trial dataframe

			Targetcolumn = 'Target' + str(i)
			WithinTrialcolumns.append(Targetcolumn) #columns for within trial dataframe. 

		EndofTrial_Data = pd.DataFrame(columns=EoTcolumns) #make new empty EndofTrial data
		#WithinTrial_Data = pd.DataFrame(columns=WithinTrialcolumns) #make new empty EndofTrial data
		WithinTrial_Data = pd.DataFrame(index = range(self.nTrials*(self.Trial_length*2)), columns=WithinTrialcolumns) #pre-allocate plenty of space. 2 per second will be plenty resposnes

		return (EndofTrial_Data, WithinTrial_Data)
	
	def StartTrial(self, targetoccurence_prob, targetnumber, trialn, displayscreen = True):
		
		"""Sets parameters at the start of each trial, based on targetoccurence_prob and targetnumber"""
		
		print("Called StartTrial")

		self.Trial_targetoccurence_prob = targetoccurence_prob #trial parameters, target occurence probability
		self.Trial_targetnumber = targetnumber #trial parameters, target number		
		self.Trial_targetcounts = [0] * targetnumber #empty list with self.Trial_targetnumber counts
		self.Trial_EoTscores = [-1] * targetnumber
		self.Trial_N = trialn		
		self.Trial_targets = list(np.random.choice(self.Target_pool, size=targetnumber, replace=False))

		print("Trial targets: ", self.Trial_targets)

		#show start screen. Toggle whether you display the start screen or not.
		if displayscreen:
			self.ChangeStartMsg()
			self.StartScreen_Visibility(viz.ON)
			self.StartScreen_DisplayTime = 2
		else:
			self.StartScreen_DisplayTime = 0

		self.EoT_NumberofResponses = 0 # not sure what this logic is for yet.						
		
		self.StartScreen_Timer = 0 #reset start screen timer
		self.Stimuli_Timer = 0 #reset inter-presentation timer
		self.Trial_Timer = 0 #reset trial length to zero 		
		self.Trial_Stimuli_Index = 0
		
	def onTimer(self,num):							
								
		if self.ON == 1:
		#print "self.Stimuli_Timer: " + str(self.Stimuli_Timer)
		#need to only play files sequentially.
			if self.Stimuli_Timer > self.delay:
				
				#change random choice
				choice = np.random.randint(0,2)
				if choice == 1:	
					if self.Trial_Stimuli_Index < 1: 
						self.SetNewStimuli()
					else:
						self.DetectAudioResponse() #function that sets target, with delay parameters		
				
			self.Stimuli_Timer = self.Stimuli_Timer+self.interval	
			
			self.Trial_Timer = self.Trial_Timer + self.interval #timer to keep track of overall trial length
			
			if self.Trial_Timer > self.Trial_length:
				#here start end of trial screens. 
				self.EndofTrial() 						
		else:
			if not self.EoTFlag:
				if self.StartScreen_Timer > self.StartScreen_DisplayTime:
					#remove startscreen and start recording.
					self.StartFlag = True #flag for experiment class.
					self.StartScreen_Visibility(viz.OFF)
					self.ON = 1
				else:
					self.StartScreen_Timer += self.interval #increment StartScreenTimer by Timer interval

	
	def getFlag(self):
		#return whether end of trial screen is on.
		"called get flag"
		return(self.EoTFlag)

	def getStartFlag(self):
		#return whether end of trial screen is on.
		"called start flag"
		return(self.StartFlag)
	
	def getEoT_NumberofResponses(self):
		#return whether ppresponded.
		"called get response"
		return(self.EoT_NumberofResponses)

	def ChangeQuestionText(self):
		
		"""changes self.Question message based on targets in trial and number of responses"""
		
		target = str(self.Trial_targets[self.EoT_NumberofResponses])
		msg = str(self.EndofTrial_Question)
		msg = msg.replace('X', target.upper())
		self.lblscore.message('-1')

		self.Question.message(msg)

	def ChangeStartMsg(self):
		
		"""changes self.Start_msg based on self.Trial_targets"""

		#add targets msg string
		msg = str(self.Start_msg)
		for target in self.Trial_targets:
			msg = msg + target.upper() + '   '
		
		self.Starttxt.message(msg)
	
	def EndofTrial(self):
		
		"""Throws black screen and wait for gearpads to be pressed"""
		
		self.ChangeQuestionText()
				
		self.EoTScreen_Visibility(viz.ON)	
		
		#tell class it is end of trial. 
		self.EoTFlag = True	
		self.ON = 0
		self.StartFlag = False

	def EoTScreen_Visibility(self, visible = viz.ON):

		"""switches the EoTscreen visibility off or on"""
	
		self.EoTScreen.visible(visible)
		self.Question.visible(visible)
		self.lblscore.visible(visible)

	def StartScreen_Visibility(self, visible = viz.ON):

		"""switches the Start Screen visibility off or on"""
	
		self.StartScreen.visible(visible)
		self.Starttxt.visible(visible)

	def RecordCounts(self):
		"""save End of Trial counts to dataframe"""

		#do not record data					
		self.ON = 0		
		trialinfo = [self.ppid, self.Trial_targetoccurence_prob, self.Trial_targetnumber, self.Trial_N]		

		#Adds 'Nones' so that rows match with columns.
		Trial_EoTscores_output = list(self.Trial_EoTscores)
		while len(Trial_EoTscores_output) < self.MaxTargetNumber:
			Trial_EoTscores_output.append(None)

		Trial_targetcounts_output = list(self.Trial_targetcounts)	
		while len(Trial_targetcounts_output) < self.MaxTargetNumber:
			Trial_targetcounts_output.append(None)

		output = Trial_EoTscores_output + Trial_targetcounts_output #makes a list of the correct length
		output[::2] = Trial_EoTscores_output
		output[1::2] = Trial_targetcounts_output
		output = list(trialinfo) + output
		
		#Trial N gets incremented anyway.
		self.EndofTrial_Data.loc[self.Trial_N,:] = output #this dataframe is actually just one line. 		

		self.EoTScreen_Visibility(viz.OFF)
		
		#tell class it is end of trial. 
		self.EoTFlag = False
		
		print ("recorded counts")			

	def CloseConnections(self):

		"""kills threaded functions and saves data"""

		self.SaveData()

		self.SoundPlayer_threaded.thread_kill() #kill thread
		

	
	def SaveData(self):

		"""Call after all responses are recorded to save data to file"""

		##save all data to file.

		self.EndofTrial_Data.to_csv('Data//' + str(self.filename) + '_EndofTrial.csv')

		self.WithinTrial_Data = self.WithinTrial_Data.dropna() #drop trailing zeros
		self.WithinTrial_Data.to_csv('Data//' + str(self.filename) + '_WithinTrial.csv')

		print ("Saved Data")
		
	def DetectAudioResponse(self):

		"""Function determines whether there has been an appropriate response"""									

		print ("DetectAudioResponse called")
		
		print ("currentaudio_type", self.currentaudio_type)

		t = viz.tick()

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
		trialinfo = [self.ppid, self.Trial_targetoccurence_prob, self.Trial_targetnumber, self.Trial_N]		
		currentresponse = [self.currentaudio, RT, ResponseCategory] 

		Trial_targets_outputlist = list(self.Trial_targets)
		while len(Trial_targets_outputlist) < self.MaxTargetNumber:
			Trial_targets_outputlist.append(None)

		output = list(trialinfo) + list(currentresponse) + Trial_targets_outputlist
		
		self.WithinTrial_Data.loc[self.Overall_Stimuli_Index-1,:] = output		#this is takes about 3ms. Consider changing to csv writer.
		#https://stackoverflow.com/questions/41888080/python-efficient-way-to-add-rows-to-dataframe

		print("DetectResposne: ", viz.tick() - t)

		self.SetNewStimuli()
		
	def SetNewStimuli(self):
		
		"""Sets the delay and target for the next stimuli, based on the target occurence and current pool"""
		
		print ("SetNewStimuli called")

		t= viz.tick()

		choices = ['T','D']
		probabilities = [self.Trial_targetoccurence_prob, 1-self.Trial_targetoccurence_prob]
		self.currentaudio_type = np.random.choice(choices, p = probabilities)

		if self.currentaudio_type == 'T':
			self.currentaudio = np.random.choice(self.Trial_targets)
		elif self.currentaudio_type == 'D':
			self.currentaudio = np.random.choice(self.Distractor_pool)		
							
		self.Stimuli_PlayedStamp=viz.tick()
		
		print(self.currentaudio)

		
		# sound1 = self.AudioList[self.letters.index(self.currentaudio)] #retrieve loaded sound file from list.		
		# sound1.setTime(0)		
		# #viz.director(PlaySound,sound1)		
		# #viz.director(self.PlaySound2)

		# sound1.volume(1)		

		audioindex = self.letters.index(self.currentaudio)
		self.SoundPlayer_threaded.PlaySound(audioindex) #takes about 1.5 ms to call. Still occasionally drops frames.
		#self.SoundPlayer_threaded.PlaySound(1) #takes about 1.5 ms to call
		#sound1.play()

		self.Stimuli_Timer=0
		self.ppresp = 0		
		
		##set new delay. Random between 1-1.5
		jitter = np.random.randint(0,49)		
		self.delay = 1.0 + (jitter/100.0)				

		self.Overall_Stimuli_Index += 1
		self.Trial_Stimuli_Index += 1


		print ("SetNewStimuli: ", viz.tick() - t)

	#### THE FOLLOWING FUNCTIONS CONTROL THE DRIVER INTERACTING WITH THE WHEEL ######

	def keydown(self,button):
		
		"""records a button press response to stimuli"""
		
		if self.ON == 1:
			self.ResponseStamp = viz.tick()

			#can press any button for response		
			self.ppresp = 1			
			
			#print "responded: " + str(viz.tick())
			
	def gearpaddown(self,button=None):
		
		"""saves on-screen count"""	

		#TODO: change to accommodate multiple target iterations.

		print "Button: " + str(button) #6 is left. 5 is right. Participants can press any button for the response.
		
		if self.EoTFlag:

			self.Trial_EoTscores[self.EoT_NumberofResponses] = self.CurrentScore 				
			self.EoT_NumberofResponses += 1
			print("Recorded Count" + str(self.EoT_NumberofResponses))				

			if self.EoT_NumberofResponses < self.Trial_targetnumber:
				self.ChangeQuestionText()														
		
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
			
	def PlaySound2(self):
		"""plays sound"""
		#print 'director:'

		t = viz.tick()
		
		self.myaudio.play()
		

		print ("playsound proc time: ", viz.tick() - t)

		print ("playsound viztick: ", viz.tick())
		print ("playsound framenumber: ", viz.getFrameNumber())
def PlaySound(myaudio):
	"""plays sound"""
	#print 'director:'

	t = viz.tick()
	myaudio.volume(1)
	myaudio.play()

	print ("playsound proc time: ", viz.tick() - t)

	print ("playsound viztick: ", viz.tick())
	print ("playsound framenumber: ", viz.getFrameNumber())


class SoundPlayer_threaded(threading.Thread):

	def __init__(self, audiolist):
		
		threading.Thread.__init__(self)

		self.thread_init()		
		self.AudioFiles = audiolist	
		
		#add any other beeps
		self.manual_audio = viz.addAudio('C:\\VENLAB data\\shared_modules\\textures\\490.wav') #high beep to signal change
		self.manual_audio.stoptime(.2) #cut it short for minimum interference.
		self.manual_audio.volume(.5)
		
	def thread_init(self):
		"""Initialise the thread"""
		self.__thread_live = True
		
	def thread_kill(self):
		"""Turn the thread loop off"""
		self.__thread_live = False


	def PlaySound(self,audioindex):

		t = viz.tick()
		myaudio = self.AudioFiles[audioindex]
		myaudio.play()	
		

		#playsound('C:\\VENLAB data\\shared_modules\\textures\\Alphabet_Sounds\\' + 'b' + '.wav')

		#winsound.PlaySound('C:\\VENLAB data\\shared_modules\\textures\\Alphabet_Sounds\\' + 'b' + '.wav', winsound.SND_FILENAME)

		print ("PLAY SOUND: ", viz.tick() - t)

	def SingleBeep(self):
		"""play single beep"""

		t = viz.tick()
		self.manual_audio.play()

		print ("SINGLE BEEP: ", viz.tick() - t)