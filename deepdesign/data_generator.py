
import os
import process
import time
from lxml import etree
from termcolor import colored
from tqdm import *
from collections import Counter

class DataGenerator:
  def __init__(self, config, run_script):
    self.running_p = []

    self.run_script          = run_script
    self.save_dir            = config.save_dir + '/' + run_script.split('.')[0] + '/'
    self.num_runs            = config.num_runs
    self.needs_gpu           = config.needs_gpu
    self.availible_cpu_cores = config.availible_cpu_cores
    self.availible_gpus      = map(int, config.availible_gpus.split(','))

  def find_free_gpu(self):
    used_gpus = []
    for p in self.running_p:
      if p.get_status() == "Running":
        used_gpus.append(p.get_gpu())
    free_gpus = list(Counter(self.availible_gpus) - Counter(used_gpus)) 
    return free_gpus

  def find_free_cpu(self):
    return self.availible_cpu_cores - len(self.running_p)

  def start_process(self, gpu=0):
    all_files = glob.glob(self.save_dir + '*.npz')
    while True:
      save_file = self.save_dir + str(np.random.randint(0,1000000)).zfill(6)
      if save_file + ".npz" not in all_files:
        break
    
    proc = Process([self.run_script, '--save_file=' + save_file])
    proc.start()
    self.running_p.append(proc)

  def needed_runs_left(self):
    all_files = glob.glob(self.save_dir + '*.npz')
    return len(all_files) - self.num_runs
   
  def update_p_status(self):
    for p in self.running_p:
      p.update_status()

  def remove_finised_p(self):
    remove_list = []
    for i in xrange(len(self.running_p)):
      if self.running_p[i].status == "Finished":
        remove_list.append(i)
    self.running_p = [i for j, i in enumerate(self.running_p) if j not in remove_list]
    
  def start_que_runner(self):
    self.start_time = time.time()
    needed_simulations = self.needed_runs_left()
    for i in tqdm(xrange(needed_simulations)):
      while True:
        if self.needs_gpu:
          free_gpus = self.find_free_gpu()
          if len(free_gpus) > 0:
            self.start_gpu(free_gpus[0])
            break
        else:
          if find_free_cpu > 0:
            self.start_cpu()
        time.sleep(.1)

class Process:
  def __init__(self, cmd):
    self.cmd = cmd
    self.status = "Not Started"
    self.gpu = -1
    self.process = None
    self.return_status = "NONE"

  def start(self, gpu=0):
    self.process = ps.subprocess.Popen(self.cmd, stdout=ps.subprocess.PIPE)
    self.pid = self.process.pid

    self.status = "Running"
    self.start_time = time.time()
    self.gpu = gpu

  def update_status(self):
    if self.status == "Running":
      if self.process.poll() is not None:
        self.status = "Finished"
        if self.process.poll() == 0:
          self.return_status = "SUCCESS"
        else:
          self.return_status = "FAIL"

  def get_pid(self):
    return self.pid

  def get_status(self):
    return self.status

  def get_gpu(self):
    return self.gpu

