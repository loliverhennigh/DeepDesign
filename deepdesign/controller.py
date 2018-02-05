
import sys

import tensorflow as tf

from latnetwork import LatNet
from data_queue import DataQueue
from config import LatNetConfigParser
from loss import Loss
from inputs import Inputs
from optimizer import Optimizer
from saver import Saver
from domain import Domain

class DeepDesignController(object):

    def __init__(self):

      self._config_parser = LatNetConfigParser()
      self._train_sim = train_sim
      self._eval_sim = eval_sim
     
      group = self._config_parser.add_group('Basic Stuff')
      group.add_argument('--mode', help='all modes', type=str,
            choices=['train', 'design', 'eval'], default='train')
      group.add_argument('--train_data_dir', help='train mode', type=str,
                        default='./')
      group.add_argument('--network_dir', help='all mode', type=str,
                        default='./network_checkpoint')
      
      group = self._config_parser.add_group('Network Details')
      group.add_argument('--input_shape', help='all mode', type=str,
                        default='512x512')
      group.add_argument('--output_shape', help='all mode', type=str,
                        default='512x512')
      group.add_argument('--network_name', help='all mode', type=str,
                        default='basic_network')

      group = self._config_parser.add_group('Network Train Details')
      group.add_argument('--train_epochs', help='all mode', type=int,
                        default=200)
      group.add_argument('--batch_size', help='all mode', type=int,
                        default=2)
      group.add_argument('--lr', help='all mode', type=float,
                        default=0.0015)
      group.add_argument('--optimizer', help='all mode', type=str,
                        default='adam')

      
      group = self._config_parser.add_group('Data Queue Details')
      group.add_argument('--max_queue', help='all mode', type=int,
                        default=100)
      group.add_argument('--nr_threads', help='all mode', type=int,
                        default=5)
      
      group = self._config_parser.add_group('Data Generate Details')
      group.add_argument('--nr_cpu_threads', help='all mode', type=int,
                        default=5)
      group.add_argument('--gpus', help='all mode', type=str
                        default='1')

    def run(self):

    def train(self):

      # make data set
      self.data_generator = DataGenerator(self.config, self.)
      self.data_generator.make_param_data(self._optimize_param)
      self.data_generator.make_sim_data(self._sim_param, self._sim)

      # make networks
      self.param_network = ParamNet(self.config)
      param_in, param_out = self.param_network.train_unroll()
      self.sim_network = SimNet(self.config)
      sim_in, sim_out = self.sim_network.train_unroll()

      # train sim network 
      self.sim_data_queue = ParamDataQueue(self.config)
      self.sim_optimizer = NetOptimizer(self.config, sim_in, sim_out)
      self.sim_optimizer.train(self.sim_data_queue, sim_in, sim_out) 

      # train param network
      self.param_data_queue = ParamDataQueue(self.config)
      self.param_optimizer = NetOptimizer(self.config)
      self.param_optimizer.train(self.param_data_queue)

    def design(self):

      # make networks
      self.param_network = ParamNet(self.config)
      self.param_network.set_optimize_param(self._param_setup)
      param_in, param_out = self.param_network.eval_unroll()

      self.sim_network = SimNet(self.config)
      self.sim_network.add_design_loss(self._design_loss)
      sim_out, loss_out = self.sim_network.unroll_design(param_out)

      # train param network
      self.design_optimizer = DesignOptimizer(self.config, param_in, sim_out, loss_out)
      self.design_optimizer.train()


    def eval_param(self):
      # make networks
      self.param_network = ParamNet(self.config)
      self.param_network.train_unroll()
      self.sim_network = SimNet(self.config)
      self.sim_network.train_unroll()

    def eval_sim(self):

    def eval_param_sim(self):





