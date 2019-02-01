import numpy as np
import matplotlib.pyplot as plt
import pdb
import pandas as pd
import sys
rootpath = 'C:\\VENLAB data\\TrackMaker\\'
sys.path.append(rootpath)
from simTrackMaker import Bend

class vehicle:
    
    def __init__(self, initialyaw, speed, dt, yawrate_readout, Course):
            
        #self.pos = np.array([pos[0], pos[1]])
        self.yawrate_readout = yawrate_readout 
        self.playback_length = len(yawrate_readout)
        
        self.pos = np.array([Course.RoadStart[0], Course.RoadStart[1]])
        self.yaw = initialyaw #heading angle, radians
        self.speed = speed 
        self.dt = dt       
        self.trackorigin = Course.CurveOrigin
        
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
        midlinedist = np.sqrt(((self.pos[0]-self.Course.midline[:,0])**2)+((self.pos[1]-self.Course.midline[:,1])**2)) #get a 4000 array of distances from the midline
        idx = np.argmin(abs(midlinedist)) #find smallest difference. This is the closest index on the midline.	

        closestpt = self.Course.midline[idx,:] #xy of closest point
        dist = midlinedist[idx] #distance from closest point				

        #Sign bias from assessing if the closest point on midline is closer to the track origin than the driver position. Since the track is an oval, closer = understeering, farther = oversteering.
        middist_from_origin = np.sqrt(((closestpt[0]-self.trackorigin[0])**2)+((closestpt[1]-self.trackorigin[1])**2))  #distance of midline to origin
        pos_from_trackorigin = np.sqrt(((self.pos[0]-self.trackorigin[0])**2)+((self.pos[1]-self.trackorigin[1])**2)) #distance of driver pos to origin
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

    

def runSimulation(Course, yawrate_readout, yawrateoffset= 0):

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
    onset = 0 #in seconds
    crossed = False
    time_til_crossing = -1
    while time < run_time and crossed == False:
        
       # print i
        time += dt        
       
        i += 1

        newyawrate = np.deg2rad(Car.yawrate_readout[i])
        
        if time > onset:
            newyawrate += yawrateoffset_rads
        
        Car.move_vehicle(newyawrate)           
        
        if crossed == False and abs(Car.currenterror) > 1.5:
            time_til_crossing = time - onset
            crossed = True

    return Car, time_til_crossing
    
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


        
    
    
if __name__ == '__main__':
    
    #Create Bend
    myrads = 80
    Course = Bend(startpos = [0,0], rads = myrads, x_dir = 1, road_width=3.0) 
    
    #Plot Bend
    plt.figure(1)
    plt.plot(Course.midline[:,0], Course.midline[:,1], '--k')
    
    xlimits = Course.CurveOrigin[0]*2
        
    plt.xlim([0-5, xlimits+5])
    plt.ylim([-Course.CurveOrigin[0]-5, Course.CurveOrigin[1]*2 + Course.CurveOrigin[0]+5])
    plt.plot(Course.OutsideLine[:,0], Course.OutsideLine[:,1],'-k')
    plt.plot(Course.InsideLine[:,0], Course.InsideLine[:,1],'-k')
    plt.axis('equal')    
    plt.title("Radius: " + str(myrads))
#
    if myrads == 40:
        filename = "Midline_40_4.csv" 
    elif myrads == 80:
        filename = "Midline_80_3.csv"
    else:
        raise Exception('Unrecognised radius')
    playbackdata = pd.read_csv("Data//"+filename) 	
    yawrate_readout = playbackdata.get("YawRate_seconds")

    #yawrateoffsets = [-2, -1, 0, 1, 2] #in degrees per second
    yawrateoffsets = np.linspace(-10,10,200)
    simResults = np.empty([len(yawrateoffsets),2])
    
    for i,yr in enumerate(yawrateoffsets):        
        Car, t = runSimulation(Course, yawrate_readout, yr)
        #Plot Car
        plotCar(plt, Car)

        simResults[i] = [yr, t]        
        print ("Yr: ", yr, "Time til Crossing: ", t)

    plt.savefig(str(myrads) + '_Trajs.png', dpi=800)
    #plt.show()
    
    np.savetxt("SimResults_"+str(myrads)+".csv", simResults, delimiter=",")

    #plot yr and time til crossing functions.
    plt.figure(2)
    plt.plot(simResults[:,0], simResults[:,1], 'k-')
    plt.xlabel("Yaw Rate Offset (deg/s)")
    plt.ylabel("Time from Onset to Lane Crossing (s)")
    plt.title("Radius: " + str(myrads))
    plt.savefig(str(myrads) + '_Sims.png', dpi = 300)
    #plt.show()
    

    