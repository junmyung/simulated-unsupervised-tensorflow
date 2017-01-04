import tensorflow as tf
import tensorflow.contrib.slim as slim
from tensorflow.contrib.framework import add_arg_scope

SE_loss = tf.nn.sparse_softmax_cross_entropy_with_logits

def int_shape(x):
  return list(map(int, x.get_shape()[1: ]))

def normalize(layer):
  return layer/127.5 - 1.

def denormalize(layer):
  return (layer + 1.)/2.

def _update_dict(layer_dict, scope, layer):
  name = "{}/{}".format(tf.get_variable_scope().name, scope)
  layer_dict[name] = layer

def image_from_paths(paths, shape, is_grayscale=True):
  filename_queue = tf.train.string_input_producer(paths)
  reader = tf.WholeFileReader()
  filename, data = reader.read(filename_queue)
  image = tf.image.decode_png(data, channels=3, dtype=tf.uint8)
  if is_grayscale:
    image = tf.image.rgb_to_grayscale(image)
  image.set_shape(shape)
  return tf.to_float(image)

@add_arg_scope
def resnet_block(
    inputs, scope, num_outputs=64, kernel_size=[3, 3],
    stride=[1, 1], padding="SAME", layer_dict={}):
  with tf.variable_scope(scope):
    layer = conv2d(
        inputs, num_outputs, kernel_size, stride,
        padding=padding, activation_fn=tf.nn.relu, scope="conv1")
    layer = conv2d(
        inputs, num_outputs, kernel_size, stride,
        padding=padding, activation_fn=None, scope="conv2")
    outputs = tf.nn.relu(tf.add(inputs, layer))
  _update_dict(layer_dict, scope, outputs)
  return outputs

@add_arg_scope
def repeat(inputs, repetitions, layer, layer_dict={}, **kargv):
  outputs = slim.repeat(inputs, repetitions, layer, **kargv)
  _update_dict(layer_dict, kargv['scope'], outputs)
  return outputs

@add_arg_scope
def conv2d(inputs, num_outputs, kernel_size, stride,
           layer_dict={}, activation_fn=None,
           #weights_initializer=tf.random_normal_initializer(0, 0.001),
           weights_initializer=tf.contrib.layers.xavier_initializer(),
           scope=None, name="", reuse=False, **kargv):
  if True:
    outputs = slim.conv2d(
        inputs, num_outputs, kernel_size,
        stride, activation_fn=activation_fn, 
        weights_initializer=weights_initializer,
        biases_initializer=tf.zeros_initializer, scope=scope, **kargv)
  else:
    with tf.variable_scope(scope, reuse=reuse):
      if type(kernel_size) == int:
        kernel_size = [kernel_size, kernel_size]
      if type(stride) == int:
        stride = [stride, stride]
      V = tf.get_variable('V', kernel_size+[int(inputs.get_shape()[-1]), num_outputs],
                          tf.float32, tf.random_normal_initializer(0, 0.05), trainable=True)
      hidden = tf.nn.conv2d(inputs, V, [1]+stride+[1], "SAME")
      bias = tf.constant(0.0, shape=[num_outputs])
      outputs = tf.nn.bias_add(hidden, bias)
      if activation_fn:
        outputs = activation_fn(outputs)
  if name:
    scope = "{}/{}".format(name, scope)
  _update_dict(layer_dict, scope, outputs)
  return outputs

@add_arg_scope
def max_pool2d(inputs, kernel_size=[3, 3], stride=[1, 1],
               layer_dict={}, scope=None, name="", **kargv):
  outputs = slim.max_pool2d(inputs, kernel_size, stride, **kargv)
  if name:
    scope = "{}/{}".format(name, scope)
  _update_dict(layer_dict, scope, outputs)
  return outputs

@add_arg_scope
def tanh(inputs, layer_dict={}, name=None, **kargv):
  outputs = tf.nn.tanh(inputs, name=name, **kargv)
  _update_dict(layer_dict, name, outputs)
  return outputs
