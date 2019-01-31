"""Module that returns course arrays for simulations"""

import numpy as np

class Bend():

    def __init__(self, startpos, rads, size = 500,  x_dir = 1, z_dir = 1, road_width = 3.0):
        """Returns a  Bend array with lines for middle and edges"""

        self.RoadStart = startpos
        self.RoadSize_Pts = size
        self.RoadWidth = road_width		
        if self.RoadWidth == 0:
            self.HalfRoadWidth = 0
        else:
            self.HalfRoadWidth = road_width/2.0		
            self.Rads = rads
            self.X_direction = x_dir

        if self.X_direction > 0:
            self.RoadArray = np.linspace(np.pi, 0.0, self.RoadSize_Pts) #right bend
        else:
            self.RoadArray = np.linspace(0.0, np.pi, self.RoadSize_Pts)  #left bend

        self.Z_direction = z_dir #[1, -1] 

        self.midline = self.LineMaker(self.Rads)
        self.OutsideLine = self.LineMaker(self.Rads + self.HalfRoadWidth)
        self.InsideLine = self.LineMaker(self.Rads - self.HalfRoadWidth)

        translate = self.Rads * self.X_direction

        self.CurveOrigin = np.add(self.RoadStart, [translate,0])

        self.midline[:,0] = np.add(self.midline[:,0], translate)
        self.OutsideLine[:,0] = np.add(self.OutsideLine[:,0], translate)
        self.InsideLine[:,0] = np.add(self.InsideLine[:,0], translate)


    def LineMaker(self, Rads):
        """returns a xz array for a line"""
        #make midline        
        line = np.zeros((int(self.RoadSize_Pts),2))
        line[:,0] = Rads*np.cos(self.RoadArray)
        line[:,1] = self.Z_direction*Rads*np.sin(self.RoadArray)

        return line