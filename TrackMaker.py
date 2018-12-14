
import viz
import numpy as np

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