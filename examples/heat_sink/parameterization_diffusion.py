
import numpy as np
import matplotlib.pyplot as plt

import sys

def draw_circle(boundary, vertex, radius):
  for i in range(max(vertex[0]-radius, 0), 
                 min(vertex[1]+radius, boundary.shape[1])):
    for j in range(max(vertex[1]-radius, 0), 
                   min(vertex[1]+radius, boundary.shape[1])):
      if (((i - vertex[0])**2 + 
           (j - vertex[1])**2)
          < radius**2):
        boundary[i, j] = 1.0

param_file = sys.argv[1] 
parameter = np.load(param_file)

boundary = np.zeros((256, 256))
for i in xrange(parameter.shape[0]/2):
  vertex = (int(256*parameter[3*i + 0]), int(256*parameter[3*i + 1]))
  radius = 10
  draw_circle(boundary, vertex, radius)

np.save(

#plt.imshow(boundary)
#plt.show()
