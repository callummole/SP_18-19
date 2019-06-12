import sys
rootpath = 'C:\\VENLAB data\\TrackMaker\\'
sys.path.append(rootpath)

import numpy as np
import matplotlib.pyplot as plt
import pdb
import pandas as pd
import io
import csv

import simTrackMaker

class vehicle:
    
    def __init__(self, initialyaw, speed, dt, yawrate_readout, Course):
            
        #self.pos = np.array([pos[0], pos[1]])
        self.yawrate_readout = yawrate_readout 
        self.playback_length = len(yawrate_readout)
        
        self.pos = np.array(Course[0])
        self.yaw = initialyaw #heading angle, radians
        self.speed = speed 
        self.dt = dt       
        self.midline = Course[1]
        self.trackorigin = Course[2]
        
        self.yawrate = 0
        
        self.pos_history = []
        self.yaw_history = []
        self.yawrate_history = []                
        self.error_history = []   
        self.closestpt_history = []         

        self.Course = Course      
        
        self.currenterror, self.closestpt = self.calculatebias()      

                # self.save_history()     
        

    def calculatebias(self):

        #TODO: cut down on processing but only selecting a window of points based on lastmidindex.
        midlinedist = np.sqrt(
            ((self.pos[0]-self.midline[:,0])**2)
            +((self.pos[1]-self.midline[:,1])**2)
            ) #get a 4000 array of distances from the midline
        idx = np.argmin(abs(midlinedist)) #find smallest difference. This is the closest index on the midline.	

        closestpt = self.midline[idx,:] #xy of closest point
        dist = midlinedist[idx] #distance from closest point				

        #Sign bias from assessing if the closest point on midline is closer to the track origin than the driver position. Since the track is an oval, closer = understeering, farther = oversteering.
        middist_from_origin = np.sqrt(
            ((closestpt[0]-self.trackorigin[0])**2)
            +((closestpt[1]-self.trackorigin[1])**2)
            )  #distance of midline to origin
        pos_from_trackorigin = np.sqrt(
            ((self.pos[0]-self.trackorigin[0])**2)
            +((self.pos[1]-self.trackorigin[1])**2)
            ) #distance of driver pos to origin
        distdiff = middist_from_origin - pos_from_trackorigin #if driver distance is greater than closest point distance, steering position should be understeering
        steeringbias = dist * np.sign(distdiff)     

        return steeringbias, closestpt


    def move_vehicle(self, newyawrate):           
        """update the position of the vehicle over timestep dt"""                        
                                 
        self.yawrate = newyawrate

        # self.yawrate = np.deg2rad(0.5) # np.random.normal(0, 0.001)

        maxheadingval = np.deg2rad(35.0) #in rads per second
        
        self.yawrate = np.clip(self.yawrate, -maxheadingval, maxheadingval)
        # print(self.yawrate)
        # self.yawrate = 0.0

        self.yaw = self.yaw + self.yawrate * self.dt  #+ np.random.normal(0, 0.005)
        
        #zrnew = znew*cos(omegaH) + xnew*sin(omegaH);
        #xrnew = xnew*cos(omegaH) - znew*sin(omegaH)

        x_change = self.speed * self.dt * np.sin(self.yaw)
        y_change = self.speed * self.dt * np.cos(self.yaw)
        
        self.pos = self.pos + np.array([x_change, y_change]) 

        self.currenterror, self.closestpt = self.calculatebias()
        
        self.save_history()
    
    def save_history(self):

        self.pos_history.append(self.pos)        
        self.yaw_history.append(self.yaw)
        self.yawrate_history.append(self.yawrate)
        self.error_history.append(self.currenterror)
        self.closestpt_history.append(self.closestpt)

    

def runSimulation(Course, yawrate_readout, yawrateoffset= 0, onsettime = 0):

    """run simulation and return RMS"""

    #Sim params
    fps = 60.0
    speed = 8.0
 
    yawrateoffset_rads = np.deg2rad(yawrateoffset)
   # print ("speed; ", speed)

    dt = 1.0 / fps
    run_time = 15 #seconds
    time = 0

    Car = vehicle(0.0, speed, dt, yawrate_readout, Course)

    i = 0

    print ("playback lenght", Car.playback_length)
    while (time < run_time) and (i < Car.playback_length):

        #print i

        time += dt              

        newyawrate = np.deg2rad(Car.yawrate_readout[i])
        
        if time > onsettime:
            newyawrate += yawrateoffset_rads
        
        Car.move_vehicle(newyawrate)                           

        i += 1

    return Car
    
    #RMS = np.sqrt(np.mean(steeringbias**2))

    #print ("RMS: ", RMS)

     

def plotCar(plt, Car):
    """Plot results of simulations"""

    positions = np.array(Car.pos_history)
                        
    steeringbias = np.array(Car.error_history)

    if max(abs(steeringbias)) > 1.5:
        plt.plot(positions[:,0], positions[:,1], 'ro', markersize=.2)						
    else:
        plt.plot(positions[:,0], positions[:,1], 'go', markersize=.2)		

def saveCar(OutputWriter, Car, radius, file, file_i, yr, onset):
    """save results of simulations"""
 
    datacolumns = ('radius','AutoFile','AutoFile_i','steering_angle_bias', 'OnsetTime','UID','World_x','World_z','SteeringBias','WorldYaw','YawRate_radspersec')

    UID = "{}_{}_{}_{}".format(radius,file_i, yr, onset)
    positions = np.array(Car.pos_history)
    World_x = positions[:,0]
    World_z = positions[:,1]
    steeringbias = np.array(Car.error_history)
    yaw = np.array(Car.yaw_history)
    yawrate = np.array(Car.yawrate_history)

    for row in range(len(positions)):
        output = (radius, file, file_i, yr, onset, UID,
        World_x[row],World_z[row],
        steeringbias[row],
        yaw[row],
        yawrate[row])

        OutputWriter.writerow(output)

    return(OutputWriter)
    	            
    
if __name__ == '__main__':
    

    
    #onset pool times
    OnsetTimePool = np.arange(5, 9.25, step = .25) 

    #yawrateoffsets = np.linspace(-10,10,200)
    yawrateoffsets = [-.2, .15, -9, -1.5]


    #radii
    myrads = [40, 80]

    
    datacolumns = ('radius','AutoFile','AutoFile_i','steering_angle_bias', 'OnsetTime','UID','World_x','World_z','SteeringBias','WorldYaw','YawRate_radspersec')

    #dataframe
    OutputFile = io.BytesIO()
    OutputWriter = csv.writer(OutputFile)
    OutputWriter.writerow(datacolumns) #write headers.


    for rads_i, radius in enumerate(myrads):
        
        L = 16#2sec.
        myStraight  = simTrackMaker.lineStraight(startpos = [0,0], length= 16)
        
        #Create Bend
        
        myBend = simTrackMaker.lineBend(startpos = myStraight.RoadEnd, rads = radius, x_dir = 1, road_width=3.0) 

        #midline and edges
        Course_RoadStart = myStraight.RoadStart
        Course_midline = np.vstack((myStraight.midline, myBend.midline))
        Course_OutsideLine = np.vstack(
            (myStraight.OutsideLine, myBend.OutsideLine)
            )
        Course_InsideLine = np.vstack((myStraight.InsideLine, myBend.InsideLine))
        Course_CurveOrigin = myBend.CurveOrigin
    
    
        #Temp HACK to store in list while I improve trackmaker.
        Course = [
            Course_RoadStart,
            Course_midline, Course_CurveOrigin,
            Course_OutsideLine, Course_InsideLine
            ]
    #

        #list of filenames
        if radius == 40:
            filename_list = ["Midline_40_0.csv","Midline_40_1.csv","Midline_40_2.csv","Midline_40_3.csv","Midline_40_4.csv","Midline_40_5.csv"]
            
        elif radius == 80:
            filename_list = ["Midline_80_0.csv","Midline_80_1.csv","Midline_80_2.csv","Midline_80_3.csv","Midline_80_4.csv","Midline_80_5.csv"]
        else:
            raise Exception('Unrecognised radius')
        
        for file_i, file in enumerate(filename_list):
            #loop through filename and onset times.
            playbackdata = pd.read_csv("Data//"+file) 	
            yawrate_readout = playbackdata.get("YawRate_seconds")

            for yr_i,yr in enumerate(yawrateoffsets):        
                for onset_i, onset in enumerate(OnsetTimePool):

                    
                    Car  = runSimulation(Course, yawrate_readout, yr, onset)

                    #save results
                    OutputWriter = saveCar(OutputWriter, Car, radius, file, file_i, yr, onset)

    OutputFile.seek(0)
    df = pd.read_csv(OutputFile) #grab bytesIO object.		
    df.to_csv('Data//Untouched_Trajectories.csv') #save to file.

    print ("Saved file")
                    

        
        

        

    