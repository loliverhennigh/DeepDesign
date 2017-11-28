#!/usr/bin/env python


#__docformat__ = 'restructuredtext'

from fipy import CellVariable, Grid2D, DiffusionTerm, Viewer

import matplotlib.pyplot as plt

import numpy as np

nx = 128
ny = 128

dx = 1.00

valueLeft = 0.
valueRight = 1.

mesh = Grid2D(dx = dx, nx = nx, ny = ny)

var = CellVariable(name = "solution variable",
                   mesh = mesh,
                   value = valueLeft)

# make random circle
radius = np.random.randint(5, 100)
#pos_x = np.random.randint(radius, nx - radius)
#pos_y = np.random.randint(radius, ny - radius)
pos_x = np.random.randint(0, nx)
pos_y = np.random.randint(0, ny)

X, Y = mesh.faceCenters
facesLeft = (mesh.facesRight & (radius**2 > ((X-pos_x)**2 + (Y-pos_y)**2)))
plt.imshow(np.array(mesh.facesRight).reshape((2,129,128))[1])
plt.show()
var.constrain(valueRight, facesLeft)

# zero temp at boundary
var.constrain(valueLeft, mesh.facesLeft)

if __name__ == '__main__':
    DiffusionTerm().solve(var)

    viewer = Viewer(vars=var, datamin=0., datamax=1.)
    viewer.plot()
    raw_input("finished")
