
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

class DesignController(object):
    """Controls the execution of a LN simulation."""

    def __init__(self, eval_sim=None, train_sim=None):

      self._config_parser = LatNetConfigParser()
      self._train_sim = train_sim
      self._eval_sim = eval_sim
     
      group = self._config_parser.add_group('Basic Stuff')
      group.add_argument('--run_mode', help='all modes', type=str,
            choices=['generate_data', 'train', 'eval'], default='train')
      group.add_argument('--sailfish_sim_dir', help='train mode', type=str,
                        default='/data/sailfish_sim/')
      group.add_argument('--latnet_network_dir', help='all mode', type=str,
                        default='./network_checkpoint')
      group.add_argument('--latnet_sim_dir', help='eval mode', type=str,
                        default='./latnet_simulation')

      
      group = self._config_parser.add_group('Network Details')
      group.add_argument('--network_name', help='all mode', type=str,
                        default='basic_network')

      group = self._config_parser.add_group('Simulation Details')
      group.add_argument('--sim_shape', help='all mode', type=str,
                        default='512x512')
      group.add_argument('--visc', help='all mode', type=float,
                        default=0.1)
      group.add_argument('--max_sim_iters', help='all mode', type=int,
                        default=50000)
      group.add_argument('--lb_to_ln', help='all mode', type=int,
                        default=120)

      group = self._config_parser.add_group('Saver Details')
      group.add_argument('--save_freq', help='all mode', type=int, 
                        default=1000)

      group = self._config_parser.add_group('Train Details')
      group.add_argument('--seq_length', help='all mode', type=int, 
                        default=5)
      group.add_argument('--batch_size', help='all mode', type=int,
                        default=2)
      group.add_argument('--optimizer', help='all mode', type=str,
                        default='adam')
      group.add_argument('--lr', help='all mode', type=float,
                        default=0.0015)
      group.add_argument('--train_iterations', help='all mode', type=int,
                        default=1000000)

      group = self._config_parser.add_group('Data Queue Details')
      group.add_argument('--gpu_fraction', help='all mode', type=float,
                        default=0.85)
      group.add_argument('--num_simulations', help='all mode', type=int,
                        default=2)
      group.add_argument('--max_queue', help='all mode', type=int,
                        default=100)
      group.add_argument('--new_sim_epochs', help='all mode', type=int,
                        default=100)
      group.add_argument('--nr_threads', help='all mode', type=int,
                        default=5)

      group = self._config_parser.add_group('Input Details')
      group.add_argument('--input_shape', help='all mode', type=str,
                         default='256x256')
      group.add_argument('--lattice_q', help='all mode', type=int,
            choices=[9], default=9)


    def _finish_simulation(self, subdomains, summary_receiver):
      pass

    def _load_sim(self):
      pass

    def run(self):

      # parse config
      args = sys.argv[1:]
      self.config = self._config_parser.parse(args)
     
      if self.config.run_mode == "train":
        self.train(self.config)
      elif self.config.run_mode == "eval":
        self.eval(self.config)
      elif self.config.run_mode == "design":
        self.design(self.config)

    def train(self, config):

      self.network = LatNet(self.config)

      with tf.Graph().as_default():

        # global step counter
        global_step = tf.get_variable('global_step', [], 
                          initializer=tf.constant_initializer(0), trainable=False)

        # make inputs
        self.inputs = Inputs(self.config)
        self.state_in, self.state_out = self.inputs.state_seq(self.network.state_padding_decrease_seq())
        self.boundary = self.inputs.boundary()

        # make network pipe
        self.pred_state_out = self.network.unroll(self.state_in, self.boundary)

        # make loss
        self.loss = Loss(self.config)
        self.total_loss = self.loss.mse(self.state_out, self.pred_state_out)

        # make train op
        all_params = tf.trainable_variables()
        self.optimizer = Optimizer(self.config)
        self.optimizer.compute_gradients(self.total_loss, all_params)
        self.train_op = self.optimizer.train_op(all_params, global_step)

        # start session 
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=.8)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
        init = tf.global_variables_initializer()
        sess.run(init)

        # make saver
        graph_def = sess.graph.as_graph_def(add_shapes=True)
        self.saver = Saver(self.config, self.network.network_config, graph_def)
        self.saver.load_checkpoint(sess)

        # construct dataset
        self.dataset = DataQueue(self.config, self._train_sim)

        # train
        for i in xrange(sess.run(global_step), self.config.train_iterations):
          _, l = sess.run([self.train_op, self.total_loss], 
                          feed_dict=self.dataset.minibatch(self.state, self.boundary))
          if i % 100 == 0:
            print("current loss is " + str(l))
            print("current step is " + str(i))

          if i % self.config.save_feq == 0:
            print("saving...")
            self.saver.save_summary(sess, self.dataset.minibatch(self.state, self.boundary), sess.run(global_step))
            self.saver.save_checkpoint(sess, int(sess.run(global_step)))

    def eval(self, config):

      self.network = LatNet(self.config)

      with tf.Graph().as_default():

        # make inputs
        self.inputs = Inputs(self.config)
        self.state = self.inputs.state()
        self.boundary = self.inputs.boundary()

        # make network pipe
        self.y_1, self.compressed_boundary, self.x_2, self.y_2 = self.network.continual_unroll(self.state, self.boundary)

        # start session 
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=1.0)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
        init = tf.global_variables_initializer()
        sess.run(init)

        # make saver
        graph_def = sess.graph.as_graph_def(add_shapes=True)
        self.saver = Saver(self.config, self.network.network_config, graph_def)
        self.saver.load_checkpoint()

        # run simulation
        y_1_g, small_boundary_mul_g, small_boundary_add_g = sess.run([self.y_1, self.small_boundary_mul, self.small_boundary_add], feed_dict=fd)
        for i in xrange(self.config.max_iters):
          _, l = sess.run([self.train_op, self.total_loss], 
                          feed_dict=self.dataset.minibatch(self.state, self.boundary))

    def design(self, config):


