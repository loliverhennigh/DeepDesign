
"""functions used to construct different optimizers

Function borrowed and modified from https://github.com/openai/pixel-cnn
"""

import tensorflow as tf
import numpy as np

FLAGS = tf.app.flags.FLAGS

class Optimizer:

  def __init__(self, config):
    self.lr = config.lr
    if config.optimizer == "adam":
      self.train_op = self.adam_updates

  def compute_gradients(self, loss, params):
    self.gradients = tf.gradients(loss, params)

  def adam_updates(self, params, global_step, mom1=0.9, mom2=0.999):
    ''' Adam optimizer '''
    updates = []
    t = tf.Variable(1., 'adam_t')
    for p, g in zip(params, self.gradients):
      mg = tf.Variable(tf.zeros(p.get_shape()), p.name + '_adam_mg')
      if mom1>0:
        v = tf.Variable(tf.zeros(p.get_shape()), p.name + '_adam_v')
        v_t = mom1*v + (1. - mom1)*g
        v_hat = v_t / (1. - tf.pow(mom1,t))
        updates.append(v.assign(v_t))
      else:
        v_hat = g
      mg_t = mom2*mg + (1. - mom2)*tf.square(g)
      mg_hat = mg_t / (1. - tf.pow(mom2,t))
      g_t = v_hat / tf.sqrt(mg_hat + 1e-8)
      p_t = p - self.lr * g_t
      updates.append(mg.assign(mg_t))
      updates.append(p.assign(p_t))
    updates.append(t.assign_add(1))
    updates.append(global_step.assign_add(1))
    return tf.group(*updates)

