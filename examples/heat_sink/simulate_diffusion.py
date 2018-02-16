
import numpy as np
import matplotlib.pyplot as plt

import sys

input_file = sys.argv[1] 

dx=0.01        
dy=0.01     
a=0.5          
timesteps=500
t=0.

nx = int(1/dx)
ny = int(1/dy)

dx2=dx**2 
dy2=dy**2 

dt = dx2*dy2/( 2*a*(dx2+dy2) )

ui = np.zeros([nx,ny])
u = np.zeros([nx,ny])

for i in range(nx):
 for j in range(ny):
  if ( ( (i*dx-0.5)**2+(j*dy-0.5)**2 <= 0.1)
   & ((i*dx-0.5)**2+(j*dy-0.5)**2>=.05) ):
    ui[i,j] = 1

def evolve_ts(u, ui):
 u[1:-1, 1:-1] = ui[1:-1, 1:-1] + a*dt*( 
                (ui[2:, 1:-1] - 2*ui[1:-1, 1:-1] + ui[:-2, 1:-1])/dx2 + 
                (ui[1:-1, 2:] - 2*ui[1:-1, 1:-1] + ui[1:-1, :-2])/dy2 )
        
for i in xrange(timesteps):
  evolve_ts(u, ui)
  ui[:] = u[:]

plt.imshow(u)
plt.show()


