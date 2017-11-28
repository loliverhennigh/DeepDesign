
import numpy as np
import matplotlib.pyplot as plt
from lxml import etree
import glob
from tqdm import *
import sys
import os.path
import gc
import skfmm
import time
import psutil as ps
import shutil

from Queue import Queue
import threading

class DataQueue:
  def __init__(self, config, train_sim):

    # base dir where all the xml files are
    self.base_dir = config.sailfish_sim_dir
    self.train_sim = train_sim

    # configs
    self.batch_size      = config.batch_size
    self.num_simulations = config.num_simulations
    self.seq_length      = config.seq_length
    self.new_sim_epochs  = config.new_sim_epochs
    self.sim_renew       = 0
    self.iteration       = 0
    self.num_states      = 0

    # shape
    sim_shape = config.sim_shape.split('x')
    sim_shape = map(int, sim_shape)
    self.sim_shape = sim_shape
    input_shape = config.input_shape.split('x')
    input_shape = map(int, input_shape)
    self.input_shape = input_shape
 
    # lists to store the datasets
    self.geometries    = []
    self.lat_states    = []

    # make queue
    self.max_queue = config.max_queue
    self.queue = Queue() # to stop halting when putting on the queue
    self.queue_batches = []

    # Start threads
    for i in xrange(config.nr_threads):
      get_thread = threading.Thread(target=self.data_worker)
      get_thread.daemon = True
      get_thread.start()

    # create dataset
    if os.path.isdir(self.base_dir):
      shutil.rmtree(self.base_dir)
    self.create_dataset(range(self.num_simulations))

  def create_dataset(self, sim_nr):

    print("clearing old sim...")
    self.geometries = []
    self.lat_states = []
    self.queue_batches = []
    with self.queue.mutex:
      self.queue.queue.clear()
    for i in sim_nr:
      if os.path.isdir(self.base_dir + "sim_" + str(i)):
        shutil.rmtree(self.base_dir + "sim_" + str(i))

    if len(sim_nr) > 1:
      print("generating new simulations...")
      l = tqdm(sim_nr)
    else:
      print("generating new simulation...")
      l = sim_nr
    for i in l:
      with open(os.devnull, 'w') as devnull:
        save_dir = self.base_dir + "sim_" + str(i)
        p = ps.subprocess.Popen(('mkdir -p ' + save_dir).split(' '), stdout=devnull, stderr=devnull)
        p.communicate()
        # possibly run simulation multiple times to ensure that enough states are created
        while True:
          print('./' + self.train_sim.script_name + ' --run_mode=generate_data --sailfish_sim_dir=' + save_dir + "/flow")
          #p = ps.subprocess.Popen(('./' + self.train_sim.script_name + ' --mode=generate_data --sailfish_sim_dir=' + save_dir + "/flow").split(' '), stdout=devnull, stderr=devnull)
          p = ps.subprocess.Popen(('./' + self.train_sim.script_name + ' --run_mode=generate_data --sailfish_sim_dir=' + save_dir + "/flow").split(' '))
          p.communicate()
          lat_file = glob.glob(save_dir + "/*.0.cpoint.npz")
          if len(lat_file) > self.seq_length:
            break

    print("parsing new data")
    self.parse_data()

  def data_worker(self):
    while True:
      geometry_file, lat_files, pos, padding_decrease_seq = self.queue.get()

      # load geometry file
      geometry_array = np.load(geometry_file)
      geometry_array = geometry_array.astype(np.float32)
      geometry_array = geometry_array[:,1:-1,1:-1]
      geometry_array = np.expand_dims(geometry_array, axis=0)
      geometry_array = mobius_extract_pad(geometry_array, pos, self.input_shape[0]/2)

      # load flow file
      lat_out = []
      lat_in = None
      for i, lat_file in zip(lat_files):
        lat = np.load(lat_file)
        lat = lat.f.dist0a[:,1:-1,1:self.sim_shape[0]+1]
        lat = lat.astype(np.float32)
        lat = np.swapaxes(lat, 0, 1)
        lat = np.swapaxes(lat, 1, 2)
        lat = np.expand_dims(lat, axis=0)
        if i == 0:
          lat_in = mobius_extract_pad(lat, pos, self.input_shape[0]/2)
        lat = mobius_extract_pad(lat, pos, self.input_shape[0]/2 - padding_decrease_seq[i])
        lat_out.append(lat)
  
      # add to que
      self.queue_batches.append((geometry_array, lat_in, lat_out))
      self.queue.task_done()
 
  def parse_data(self): 
    # get list of all simulation runs
    sim_dir = glob.glob(self.base_dir + "*/")

    # clear lists
    self.geometries = []
    self.lat_states = []
    self.num_states = 0

    print("parsing dataset")
    for d in sim_dir:
      # get needed filenames
      geometry_file    = d + "flow_geometry.npy"
      lat_file = glob.glob(d + "*.0.cpoint.npz")
      lat_file.sort()
      self.num_states += len(lat_file)

      # check file for geometry
      if not os.path.isfile(geometry_file):
        continue

      if len(lat_file) == 0:
        continue

      # store name
      self.geometries.append(geometry_file)
      self.lat_states.append(lat_file)

  def minibatch(self, state_in=None, state_out=None, boundary=None, padding_decrease_seq=None):

    # check to see if new data is needed
    self.iteration += self.batch_size
    if self.iteration > (self.num_states * self.new_sim_epochs): 
      self.iteration -= self.new_sim_epochs * len(self.lat_states[self.sim_renew])
      self.create_dataset([self.sim_renew])
      self.sim_renew = (self.sim_renew + 1) % self.num_simulations

    # queue up data if needed
    for i in xrange(self.max_queue - len(self.queue_batches) - self.queue.qsize()):
      sim_index = np.random.randint(0, self.num_simulations)
      sim_start_index = np.random.randint(0, len(self.lat_states[sim_index])-self.seq_length)
      rand_pos = [np.random.randint(0, self.sim_shape[0]), np.random.randint(0, self.sim_shape[1])]
      self.queue.put((self.geometries[sim_index], 
                      self.lat_states[sim_index][sim_start_index:sim_start_index+self.seq_length], 
                      rand_pos, padding_decrease_seq))
   
    # possibly wait if data needs time to queue up
    while len(self.queue_batches) < self.batch_size:
      print("spending time waiting for queue")
      time.sleep(1.01)

    # generate batch of data in the form of a feed dict
    batch_boundary = []
    batch_state_in = []
    batch_state_out = []
    for i in xrange(self.batch_size): 
      batch_boundary.append(self.queue_batches[0][0].astype(np.float32))
      batch_state_in.append(self.queue_batches[0][1])
      batch_state_out.append(self.queue_batches[0][2])
      self.queue_batches.pop(0)

    # concate batches together
    new_batch_state_out = []
    for i in xrange(self.seq_length):
      new_batch_state_out.append(np.stack(batch_state_out[:][i], axis=0))
    batch_state_out = new_batch_state_out
    batch_state_in = np.stack(batch_state_in, axis=0)
    batch_boundary = np.stack(batch_boundary, axis=0)
    return {boundary:batch_boundary, state_in:batch_state_in, state_out:batch_state_out}

"""
#dataset = Sailfish_data("../../data/", size=32, dim=3)
dataset = Sailfish_data("/data/sailfish_flows/", size=512, dim=2)
#dataset.create_dataset()
dataset.parse_data()
batch_boundary, batch_data = dataset.minibatch(batch_size=8)
for i in xrange(100):
  batch_boundary, batch_data = dataset.minibatch(batch_size=8)
  time.sleep(.8)
  print("did batch")
  plt.imshow(batch_data[0,0,:,:,0])
  plt.show()
  plt.imshow(batch_data[0,0,:,:,1])
  plt.show()
  plt.imshow(batch_data[0,0,:,:,-1])
  plt.show()
  plt.imshow(batch_data[0,0,:,:,2])
  plt.show()
  plt.imshow(batch_data[0,0,:,:,-2])
  plt.show()
  plt.imshow(np.sum(batch_data[0,0], axis=2))
  print(np.sum(batch_data[0,0]))
  plt.show()
  plt.imshow(batch_boundary[0,0,:,:,0])
  plt.show()
"""


