"""2D flow around a object in a channel.

Lift and drag coefficients of the object are measured using the
momentum exchange method.

Fully developed parabolic profile is prescribed at the inflow and
a constant pressure condition is prescribed at the outflow.

The results can be compared with:
    [1] M. Breuer, J. Bernsdorf, T. Zeiser, F. Durst
    Accurate computations of the laminar flow past a object
    based on two different methods: lattice-Boltzmann and finite-volume
    Int. J. of Heat and Fluid Flow 21 (2000) 186-196.
"""
from __future__ import print_function

import sys
sys.path.append('../sailfish/')

import numpy as np
import time

from sailfish.subdomain import Subdomain2D
from sailfish.node_type import NTHalfBBWall, NTEquilibriumVelocity, NTEquilibriumDensity, DynamicValue, NTFullBBWall
from sailfish.controller import LBSimulationController
from sailfish.lb_base import ForceObject
from sailfish.lb_single import LBFluidSim
from sailfish.sym import S
import binvox_rw
import matplotlib.pyplot as plt
import glob
import os

def clean_files(filename, size):
  # list all saved files
  print("waiting for files saving to chetch up")
  time.sleep(4.0)
  files = glob.glob(filename + ".0.*")
  files.sort()
  steady_flow_file = files[-1]

  # convert the last flow to the proper save formate
  steady_flow_array = np.load(steady_flow_file)
  velocity_array = steady_flow_array.f.v
  pressure_array = np.expand_dims(steady_flow_array.f.rho, axis=0)
  velocity_array[np.where(np.isnan(velocity_array))] = 0.0
  pressure_array[np.where(np.isnan(pressure_array))] = 1.0
  pressure_array = pressure_array - 1.0
  steady_flow_array = np.concatenate([velocity_array, pressure_array], axis=0)
  steady_flow_array = np.swapaxes(steady_flow_array, 0, 1)
  steady_flow_array = np.swapaxes(steady_flow_array, 1, 2)
  steady_flow_array = steady_flow_array[:,size/2:5*size/2]
  np.nan_to_num(steady_flow_array, False)
  steady_flow_array = steady_flow_array.astype(np.float32)
  np.save(filename + "_steady_flow", steady_flow_array) 

  # clean files
  rm_files = files
  for f in rm_files:
    os.remove(f)

class BoxSubdomain(Subdomain2D):
  #bc = NTHalfBBWall
  bc = NTFullBBWall
  max_v = 0.1

  def boundary_conditions(self, hx, hy):

    walls = (hy == 0) | (hy == self.gy - 1)
    self.set_node(walls, self.bc)

    H = self.config.lat_ny
    hhy = S.gy - self.bc.location
    self.set_node((hx == 0) & np.logical_not(walls),
                  NTEquilibriumVelocity(
                  DynamicValue(4.0 * self.max_v / H**2 * hhy * (H - hhy), 0.0)))
    self.set_node((hx == self.gx - 1) & np.logical_not(walls),
                  NTEquilibriumDensity(1))

    L = self.config.vox_size
    model = self.load_vox_file(self.config.vox_filename)
    model = np.pad(model, ((L/2,L/2),(L, 6*L)), 'constant', constant_values=False)
    self.set_node(model, self.bc)

    # save boundary
    geometry_array = model.astype(np.uint8)
    geometry_array = geometry_array[1:-1,L/2+1:5*L/2+1]
    geometry_array = np.expand_dims(geometry_array, axis=-1)
    np.save(self.config.output + "_boundary", geometry_array)

  def initial_conditions(self, sim, hx, hy):
    H = self.config.lat_ny
    sim.rho[:] = 1.0
    sim.vy[:] = 0.0

    hhy = hy - self.bc.location
    sim.vx[:] = 4.0 * self.max_v / H**2 * hhy * (H - hhy)

  def load_vox_file(self, vox_filename):
    # if the file is .binvox slice the middle of it
    if vox_filename[-3:] == "vox":
      with open(vox_filename, 'rb') as f:
        model = binvox_rw.read_as_3d_array(f)
        model = model.data[:,:,model.dims[2]/2]
      model = np.array(model, dtype=np.int)
    # if the file is .npy assume that it is 2D 0s and 1s
    elif vox_filename[-3:] == "npy":
      model = np.load(vox_filename)
      model = model[...,0]
    model = np.pad(model, ((1,1),(1, 1)), 'constant', constant_values=False)
    return model

class BoxSimulation(LBFluidSim):
  subdomain = BoxSubdomain

  @classmethod
  def add_options(cls, group, defaults):
    group.add_argument('--vox_filename',
            help='name of vox file to run ',
            type=str, default="test.vox")
    group.add_argument('--vox_size',
            help='size of vox file to run ',
            type=int, default=32)

  @classmethod
  def update_defaults(cls, defaults):
    defaults.update({
      'max_iters': 300000,
      'output_format': 'npy',
      'output': 'test_flow',
      'every': 10000,
      })

  @classmethod
  def modify_config(cls, config):
    config.lat_nx = config.vox_size*8
    config.lat_ny = config.vox_size*2
    config.visc   = 0.03 * (config.lat_ny/100.0)
    print(config.visc)

  def __init__(self, *args, **kwargs):
    super(BoxSimulation, self).__init__(*args, **kwargs)

    L = self.config.vox_size
    margin = 5
    self.add_force_oject(ForceObject(
      (L-margin,  L/2 - margin),
      (2*L + margin, 3*L/2 + margin)))

    subdomain = BoxSubdomain
    print('Re = %2.f' % (BoxSubdomain.max_v * L / self.config.visc))

  def record_value(self, iteration, force, C_D, C_L):
    print("c_d")
    print(C_D)
    print("c_l")
    print(C_L)

  prev_f = None
  every = 500
  def after_step(self, runner):
    if self.iteration % self.every == 0:
      runner.update_force_objects()
      for fo in self.force_objects:
        runner.backend.from_buf(fo.gpu_force_buf)
        f = fo.force()

        # Compute drag and lift coefficients.
        C_D = (2.0 * f[0] / (self.config.lat_nx * BoxSubdomain.max_v**2))
        C_L = (2.0 * f[1] / (self.config.lat_ny * BoxSubdomain.max_v**2))
        self.record_value(runner._sim.iteration, f, C_D, C_L)

        if self.prev_f is None:
          self.prev_f = np.array(f)
        else:
          f = np.array(f)

          # Terminate simulation when steady state has
          # been reached.
          diff = np.abs(f - self.prev_f) / (np.abs(f) + 0.001)

          print(diff)
          if np.all(diff < 7e-4) or (self.config.max_iters < self.iteration + 501):
            clean_files(self.config.output, self.config.vox_size)
            runner._quit_event.set()
          self.prev_f = f


if __name__ == '__main__':
  ctrl = LBSimulationController(BoxSimulation)
  ctrl.run()
