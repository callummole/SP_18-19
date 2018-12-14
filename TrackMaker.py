
import viz
import numpy as np

class Bend():

    def __init__(self, startpos, rads, size = 500,  x_dir = 1, z_dir = 1, colour = viz.WHITE, primitive = viz.QUAD_STRIP, primitive_width=None, road_width = 3.0):
        """Returns a  bend of a specific road width, with functions to set the visibility, position, or Euler of both edges at once"""	

        #make sign -1 if you want a left bend.
        #improve to have a flag if it's a quad, and the quad width.

        self.RoadStart = startpos
        self.RoadSize_Pts = size
        self.RoadWidth = road_width		
        self.HalfRoadWidth = road_width/2.0		
        self.Rads = rads
        self.X_direction = x_dir

        if self.X_direction > 0:
            self.RoadArray = np.linspace(np.pi, 0.0, self.RoadSize_Pts) #right bend
        else:
            self.RoadArray = np.linspace(0.0, np.pi, self.RoadSize_Pts)  #left bend

        self.Z_direction = z_dir #[1, -1] 
        self.colour = colour
        self.primitive = primitive
        self.primitive_width = primitive_width
        self.CurveOrigin = self.RoadStart + ([self.Rads, 0] * self.X_direction)

        self.InsideEdge_Rads = self.Rads-(self.HalfRoadWidth)
        self.InsideEdge_Start = [self.RoadStart[0]-self.HalfRoadWidth,.1, self.RoadStart[1]] 

        self.OutsideEdge_Rads = self.Rads+(self.RoadWidth/2.0)
        self.OutsideEdge_Start = [self.RoadStart[0]+self.HalfRoadWidth,.1, self.RoadStart[1]]


        #put default widths if not given
        if primitive_width is None:
            if primitive == viz.QUAD_STRIP:
                primitive_width = .05
                self.primitive_width = primitive_width 

            elif primitive == viz.LINE_STRIP:
                self.primitive_width = 2
                viz.linewidth(self.primitive_width)
                primitive_width = 0 #so I can use the same code below for both primitive types.		

        self.InsideEdge = self.EdgeMaker(self.InsideEdge_Start, self.InsideEdge_Rads, primitive_width)
        self.OutsideEdge = self.EdgeMaker(self.OutsideEdge_Start, self.OutsideEdge_Rads, primitive_width)

        #make it so both edges have the same center. The setCenter is in local coordinates
        self.InsideEdge.setCenter([-self.HalfRoadWidth, 0, 0])
        self.OutsideEdge.setCenter([+self.HalfRoadWidth, 0, 0])		
        self.midline = self.MidlineMaker()

    def EdgeMaker(self, startpos, rads, primitive_width):
        """function returns a bend edge"""
        i = 0
        viz.startlayer(self.primitive) 	

        viz.vertex(startpos[0], .1, startpos[1]) 
        while i < self.RoadSize_Pts:			
            x1 = ((rads-primitive_width)*np.cos(self.RoadArray[i])) #+ BendRadius
            z1 = self.Z_direction*((rads-primitive_width)*np.sin(self.RoadArray[i])) + startpos[2]

            #print (z1[i])			
            viz.vertex(x1, .1, z1)				
            viz.vertexcolor(self.colour)

            if self.primitive == viz.QUAD_STRIP:
                x2 = ((rads+primitive_width)*np.cos(self.RoadArray[i])) #+ BendRadius
                z2 = self.Z_direction*((rads+primitive_width)*np.sin(self.RoadArray[i])) + startpos[2]
                viz.vertex(x2, .1, z2)				
                viz.vertexcolor(self.colour)

            i += 1

        Bend = viz.endlayer()

        return Bend

    def MidlineMaker(self):
        """returns midline"""
        #make midline
        i=0
        midline = np.zeros((int(self.RoadSize_Pts),2))
        while i < self.RoadSize_Pts:
            x = self.Rads*np.cos(self.RoadArray)
            z = self.Rads*np.sin(self.RoadArray)
            midline[i,0] = x
            midline[i,1] = z		    		
            i += 1
        return midline

    def ToggleVisibility(self, visible = viz.ON):
        """switches bends off or on"""

        self.InsideEdge.visible(visible)
        self.OutsideEdge.visible(visible)