"""
Unet example
"""
import numpy as np
import functools
import tensorflow as tf
import neural_network.tf_wrap as tf_wrap
from neural_network.tf_layer import tf_layer
from tensorflow.examples.tutorials.mnist import input_data

# these functions should be defined specifically for individal neural network
# example of the prediction function, defined using tensorflow lib
def tf_prediction_func( model ):
    #if model.arg is None:
    #    model.arg = [1.0, 1.0]
    # get data size
    NNlayer     = tf_layer()
    data_size   = int(model.data.get_shape()[1])
    im_shape    = (28, data_size//28)
    target_size = int(model.target.get_shape()[1])
    pool_len    = 2
    n_features  = 2
    out_size = data_size#n_features*data_size//(pool_len**4)
    y1_4d    = tf.reshape(model.data, [-1,im_shape[0],im_shape[1],1]) #reshape into 4d tensor
    # input size   [-1, im_shape[0],          im_shape[1],         1 ]
    # output size  [-1, im_shape[0],          im_shape[1], n_features ]
    conv1_12 = NNlayer.multi_convolution2d(y1_4d, cov_ker_size = (5,5), n_cnn_layers = 2, \
                                           in_n_features_arr  = (1,          n_features), \
                                           out_n_features_arr = (n_features, n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0],          im_shape[1],          n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    pool1    = NNlayer.pool(conv1_12, pool_size = [1, pool_len, pool_len, 1], \
                            pool_type = 'max_pool')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    conv2_12 = NNlayer.multi_convolution2d(pool1, cov_ker_size = (5,5), n_cnn_layers = 2, \
                                           in_n_features_arr  = (n_features, n_features), \
                                           out_n_features_arr = (n_features, n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len,      im_shape[1]/pool_len,      n_features ]
    # output size  [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    pool2    = NNlayer.pool(conv2_12, pool_size = [1, pool_len, pool_len, 1], \
                            pool_type = 'max_pool')
    # input size   [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    # output size  [-1, im_shape[0]/pool_len,      im_shape[1]/pool_len,      n_features ]
    up3      = NNlayer.deconvolution2d(pool2, cov_ker_size = (5,5), \
                                            in_n_features = n_features, out_n_features = n_features, \
                                            conv_strides = [1, pool_len, pool_len, 1], activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, 2*n_features ]
    merge3   = NNlayer.merge(conv2_12, up3, axis = 3, merge_type = 'concat')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, 2*n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    conv3_12 = NNlayer.multi_convolution2d(merge3, cov_ker_size = (5,5), n_cnn_layers = 2, \
                                           in_n_features_arr  = (2*n_features, n_features), \
                                           out_n_features_arr = (n_features,   n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0],          im_shape[1],          n_features ]
    up4      = NNlayer.deconvolution2d(conv3_12, cov_ker_size = (5,5), \
                                            in_n_features = n_features, out_n_features = n_features, \
                                            conv_strides = [1, pool_len, pool_len, 1], activate_type = 'ReLU')
    # input size   [-1, im_shape[0], im_shape[1], n_features ]
    # output size  [-1, im_shape[0], im_shape[1], 2*n_features ]
    merge4   = NNlayer.merge(conv1_12, up4, axis = 3, merge_type = 'concat')
    # input size   [-1, im_shape[0], im_shape[1], 2*n_features ]
    # output size  [-1, im_shape[0], im_shape[1], 1 ]
    conv4_12 = NNlayer.multi_convolution2d(merge4, cov_ker_size = (5,5), n_cnn_layers = 2, \
                                           in_n_features_arr  = (2*n_features, n_features), \
                                           out_n_features_arr = (n_features,   1), \
                                           pool_type = 'None', activate_type = 'sigmoid')
    # input data shape [-1,  data_size/4, 1, cnn_n_feature], output data shape [-1, out_size=n_features*data_size//4]
    y = tf.reshape(conv4_12, [-1, out_size]) #flatten
    # softmax output
    return y#tf.nn.softmax(y)

# example of the prediction function, defined using tensorflow lib
def tf_optimize_func( model ):
    model.arg = 0.5#[0.5, 0.5]
    loss = tf.reduce_sum(tf.pow(tf.subtract(model.prediction, model.target),2))
    optimizer = tf.train.RMSPropOptimizer(1e-4)
    # minimization apply to cross_entropy
    return optimizer.minimize(loss)

# example of the error function, defined using tensorflow lib
def tf_error_func( model ):
    model.arg = 1.0#[1.0, 1.0]
    #training accuracy
    correct_prediction = tf.pow(tf.subtract(model.prediction, model.target),2)
    return tf.reduce_mean(correct_prediction)

#############################

def test1():
    mnist  = input_data.read_data_sets('./data/MNIST_data/', one_hot=True)
    model  = tf_wrap.tf_model_top([None,  784], [None,  784], tf_prediction_func, tf_optimize_func, tf_error_func, arg = 0.5)
    for _ in range(100):
        model.test(mnist.test.images, mnist.test.images)
        for _ in range(100):
            batch_xs, batch_ys = mnist.train.next_batch(1000)
            model.train(batch_xs, batch_xs)
    model.save('../save_data/test_model_save')

def test2():
    mnist  = input_data.read_data_sets('./data/MNIST_data/', one_hot=True)
    model  = tf_wrap.tf_model_top([None,  784], [None,  784], tf_prediction_func, tf_optimize_func, tf_error_func, arg = 1.0)
    model.restore('../save_data/test_model_save')
    model.test(mnist.test.images, mnist.test.images)
#if __name__ == '__main__':
    #test1()
    #test2()
