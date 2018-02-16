
import numpy as np

def draw_circle(boundary, vertex, radius):
  for i in range(max(vertex[0]-radius, 0), 
                 min(vertex[1]+radius, boundary.shape[1])):
    for j in range(max(vertex[1]-radius, 0), 
                   min(vertex[1]+radius, boundary.shape[1])):
      if (((i - vertex[0])**2 + 
           (j - vertex[1])**2)
          < radius**2):
        boundary[i, j] = 1.0

class DiffuionDataMaker(DataMaker):

  def params_to_geometry(self, params):
    boundary = np.zeros((256, 256))
    for i in xrange(parameter.shape[0]/2):
      vertex = (int(256*parameter[3*i + 0]), int(256*parameter[3*i + 1]))
      radius = 10
      draw_circle(boundary, vertex, radius)
    return boundary

  def geometry_to_simulation(self, geometry):
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

    return u
    




