
import numpy as np
import cv2
import matplotlib.pyplot as plt

import argparse
import sys

import heat_sink_boundary_creator as boundary_creator

if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('--save_file', type=str, default='test_out')
  configs = parser.parse_args()

  boundary = np.load(configs.load_file)['outputs']

  np.savez(configs.save_file, inputs=boundary, outputs=boundary)

  

