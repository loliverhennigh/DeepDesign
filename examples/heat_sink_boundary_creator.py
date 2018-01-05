
import numpy as np
import cv2
import matplotlib.pyplot as plt

import argparse
import sys

def draw_triangle(boundary, vertex_1, vertex_2, vertex_3):
  # just using cv2 imp
  triangle = np.array([[vertex_1[1],vertex_1[0]],[vertex_2[1],vertex_2[0]],[vertex_3[1],vertex_3[0]]], np.int32)
  triangle = triangle.reshape((-1,1,2))
  cv2.fillConvexPoly(boundary,triangle,1)
  return boundary

def make_boundary(params, shape):
  boundary = np.zeros(shape).astype(np.uint8)
  for i in xrange(len(params)/6):
    vertex_1 = [int(params[i*6 + 0] * boundary.shape[0]), int(params[i*6 + 1] * boundary.shape[1])]
    vertex_2 = [int(params[i*6 + 2] * boundary.shape[0]), int(params[i*6 + 3] * boundary.shape[1])]
    vertex_3 = [int(params[i*6 + 4] * boundary.shape[0]), int(params[i*6 + 5] * boundary.shape[1])]
    boundary = draw_triangle(boundary, vertex_1, vertex_2, vertex_3)

  return boundary.astype(np.float32)

if __name__ == '__main__':

  num_triangles = 10
  shape = [128,128]

  parser = argparse.ArgumentParser()
  parser.add_argument('--save_file', type=str, default='test')
  parser.add_argument('--param_file', type=str, default='')
  configs = parser.parse_args()

  if configs.param_file is not '':
    with open(configs.param_file) as f:
      params = f.read()
      params.split(',')
      params = np.array(map(float, params))
  else:
    params = np.random.rand(num_triangles * 6)

  boundary = make_boundary(params, shape)

  np.savez(configs.save_file, param=params, outputs=boundary)



