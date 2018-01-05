#!/usr/bin/env python

import sys
import numpy as np

# import latnet
sys.path.append('../deepdesign')
from controller import DeepDesignController


if __name__ == '__main__':
  ctr = DeepDesignController(param_script="heat_sink_boundary_generator.py", simulation_script="heat_sink_simulation.py")
  ctr.train()
 
