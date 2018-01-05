
import os
import process
import time
from lxml import etree
from termcolor import colored
from tqdm import *
from collections import Counter

class DataGenerator:
  def __init__(self, run_script, config):
    self.num_runs = config.num_runs
    self.needs_gpu = config.needs_gpu
    self.availible_cpu_cores = config.availible_cpu_cores
    self.availible_gpus = config.availible_gpus.split(',')
    self.start_time = 0

    self.sims = []

  def start_sim(self):
    for i in xrange(len(self.sims)):
      if self.needs_gpu:
      if self.sims[i].get_status() == "Not Started":
        self.pl[i].start(gpu)
        break

  def find_free_gpu(self):
    used_gpus = []
    for i in xrange(len(self.pl)):
      if self.pl[i].get_status() == "Running":
        used_gpus.append(self.pl[i].get_gpu())
    free_gpus = list(Counter(self.availible_gpus) - Counter(used_gpus)) 
    return free_gpus

  def num_finished_processes(self):
    proc = 0
    for i in xrange(len(self.pl)):
      if self.pl[i].get_status() == "Finished" and self.pl[i].get_return_status() == "SUCCESS":
        proc += 1
    return proc

  def num_failed_processes(self):
    proc = 0
    for i in xrange(len(self.pl)):
      if self.pl[i].get_status() == "Finished" and self.pl[i].get_return_status() == "FAIL":
        proc += 1
    return proc

  def num_running_processes(self):
    proc = 0
    for i in xrange(len(self.pl)):
      if self.pl[i].get_status() == "Running":
        proc += 1
    return proc

  def num_unstarted_processes(self):
    proc = 0
    for i in xrange(len(self.pl)):
      if self.pl[i].get_status() == "Not Started":
        proc += 1
    return proc

  def percent_complete(self):
    rc = -.01
    if self.num_finished_processes() > 0:
      rc = self.num_finished_processes() / float(len(self.pl))
    return rc * 100.0

  def run_time(self):
    return time.time() - self.start_time

  def time_left(self):
    tl = -1
    pc = self.percent_complete()
    if pc > 0:
      tl = (time.time() - self.start_time) * (1.0/(pc/100.0)) - self.run_time()
    return tl

  def time_string(self, tl):
    tl = int(tl)
    if tl < 0:
      tl = 0
    seconds = tl % 60 
    tl = (tl - seconds)/60
    mins = tl % 60 
    tl = (tl - mins)/60
    hours = tl % 24
    days = (tl - hours)/24
    return    ("(" + str(days).zfill(3) + ":" + str(hours).zfill(2) 
             + ":" + str(mins).zfill(2) + ":" + str(seconds).zfill(2) + ")")
 
  def update_pl_status(self):
    for i in xrange(len(self.pl)):
      self.pl[i].update_status()

  def print_que_status(self):
    os.system('clear')
    print("QUE STATUS")
    print(colored("Num Finished Success: " + str(self.num_finished_processes()), 'green'))
    print(colored("Num Finished Fail:    " + str(self.num_failed_processes()), 'red'))
    print(colored("Num Running:          " + str(self.num_running_processes()), 'yellow'))
    print(colored("Num Left:             " + str(self.num_unstarted_processes()), 'blue'))
    print(colored("Percent Complete:     " + str(self.percent_complete()), 'blue'))
    print(colored("Time Left (D:H:M:S):  " + self.time_string(self.time_left()), 'blue'))
    print(colored("Run Time  (D:H:M:S):  " + self.time_string(self.run_time()), 'blue'))
 
  def start_que_runner(self):
    self.start_time = time.time()
    while True:
      time.sleep(.1)
      free_gpus = self.find_free_gpu()
      for gpu in free_gpus:
        self.start_next(gpu)
      self.update_pl_status()
      self.print_que_status()
      
class Sim:
  def __init__(self, xml_filename, finish_script):
    root = etree.parse(xml_filename)
    command = root.find("cmd").text
    self.cmd = command
    self.xml_file = xml_filename
    self.finish_script = finish_script
    self.status = "Not Started"
    self.gpu = -1
    self.process = None
    self.return_status = "NONE"
    self.run_time = 0

  def start(self, gpu=0):
    with open(os.devnull, 'w') as devnull:
      self.process = ps.subprocess.Popen(self.cmd.split(' '), stdout=devnull, stderr=devnull, env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu)))
    self.pid = self.process.pid

    self.status = "Running"
    self.start_time = time.time()
    self.gpu = gpu

  def update_status(self):
    if self.status == "Running":
      self.run_time = time.time() - self.start_time
      if self.process.poll() is not None:
        self.status = "Finished"
        if self.process.poll() == 0:
          self.return_status = "SUCCESS"
          self.finish_script(self.xml_file)
        else:
          self.return_status = "FAIL"
  def get_pid(self):
    return self.pid

  def get_status(self):
    return self.status

  def get_gpu(self):
    return self.gpu

  def get_return_status(self):
    return self.return_status

  def print_info(self):
    print_string = (colored('cmd is ', 'blue') + ' '.join(self.cmd) + '\n').ljust(40)
    print_string = print_string + (colored('status ', 'blue') + self.status + '\n').ljust(30)
    if self.return_status == "SUCCESS":
      print_string = print_string + (colored('return status ', 'blue') + colored(self.return_status, 'green') + '\n').ljust(40)
    elif self.return_status == "FAIL":
      print_string = print_string + (colored('return status ', 'blue') + colored(self.return_status, 'red') + '\n').ljust(40)
    else:
      print_string = print_string + (colored('return status ', 'blue') + colored(self.return_status, 'yellow') + '\n').ljust(40)
    print_string = print_string + (colored('run time ', 'blue') + str(self.run_time)).ljust(40)
    print(print_string)



