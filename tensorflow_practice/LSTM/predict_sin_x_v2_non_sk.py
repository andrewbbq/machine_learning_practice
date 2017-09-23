# tf.__version__  1.3.0
import numpy as np
import tensorflow as tf
from tensorflow.contrib.learn.python.learn.estimators.estimator import SKCompat
from tensorflow.contrib.layers import fully_connected
import matplotlib.pyplot as plt

learn = tf.contrib.learn
import time

NUM_UNITS = 8
NUM_LAYERS = 2

TIME_STEPS = 10
# 只有一个特征, 即数值本身
INPUT_SIZE=1
OUTPUT_SIZE=1


TRAINING_STEPS = 1000
BATCH_SIZE = 5

TRAINING_EXAMPLES = 10000
TESTING_EXAMPLES = 1000
SAMPLE_GAP = 0.01

TEST_START = TRAINING_EXAMPLES * SAMPLE_GAP
TEST_END = (TRAINING_EXAMPLES + TESTING_EXAMPLES) * SAMPLE_GAP

def generate_data(condition='train'):
    """
    :return:
     X:
        X.shape=(-1,10,1)
     Y:
        Y.shape=(-1,1)
    """
    X = []
    y = []
    if condition == 'train':
        sin_seq = np.sin(np.linspace(0, TEST_START, TRAINING_EXAMPLES, dtype=np.float32))
    else:
        sin_seq = np.sin(np.linspace(TEST_START, TEST_END, TRAINING_EXAMPLES, dtype=np.float32))
    for i in range(len(sin_seq) - TIME_STEPS - 1):
        tmp= sin_seq[i: i + TIME_STEPS]
        X.append(tmp)
        tmp=sin_seq[i + TIME_STEPS]
        y.append(tmp)
    X = np.array(X, dtype=np.float32)
    Y = np.array(y, dtype=np.float32)

    X=np.reshape(X,[-1,TIME_STEPS,INPUT_SIZE])
    Y=np.reshape(Y,[-1,OUTPUT_SIZE])
    return X,Y



def lstm_model(input_tensor,out_tensor):
    lstm_cell = tf.nn.rnn_cell.BasicLSTMCell(NUM_UNITS, state_is_tuple=True)


    input_tensor=tf.reshape(input_tensor, [-1, INPUT_SIZE])  # 需要将tensor转成2维进行计算，计算后的结果作为隐藏层的输入

    w_in=tf.get_variable('weight_input',shape=[INPUT_SIZE,NUM_UNITS],initializer=tf.truncated_normal_initializer())
    # 注意 shape=[NUM_UNITS,] 与 shape=[NUM_UNITS,1] 的严重不同!
    b_in=tf.get_variable('bias_input',shape=[NUM_UNITS, ],initializer=tf.zeros_initializer())

    w_out = tf.get_variable('weight_output', shape=[INPUT_SIZE, NUM_UNITS], initializer=tf.truncated_normal_initializer())
    b_out = tf.get_variable('b_output', shape=[NUM_UNITS,], initializer=tf.zeros_initializer())

    input_rnn = tf.matmul(input_tensor, w_in) + b_in
    input_rnn = tf.reshape(input_rnn, [-1, TIME_STEPS, NUM_UNITS])  # 将tensor转成3维，作为lstm cell的输入


    cell = tf.nn.rnn_cell.MultiRNNCell([lstm_cell] * NUM_LAYERS)
    cell = lstm_cell
    init_state = cell.zero_state(BATCH_SIZE, dtype=tf.float32)
    output_rnn, final_states = tf.nn.dynamic_rnn(cell, input_rnn,initial_state=init_state, dtype=tf.float32)

    # 在本问题中只关注最后一个时刻的输出结果
    """
    before: output_rnn.shape = (5,10,8), namely (BATCH_SIZE, TIME_STEPS, NUM_UNITS)
    after:  output_rnn.shape = (5,8) , namely (BATCH_SIZE , NUM_UNITS)
    """
    output_rnn=output_rnn[:,-1,:]

    # 创建一个全连接层，因为是回归问题, 输出的维度为1，None指的是不使用激活函数
    predictions = tf.contrib.layers.fully_connected(output_rnn, 1, None)

    # 将predictions和labels调整统一的shape
    # labels = tf.reshape(labels, [-1])
    predictions = tf.reshape(predictions, [-1,1])
    loss = tf.losses.mean_squared_error(predictions, out_tensor)

    train_op = tf.contrib.layers.optimize_loss(
        loss, tf.contrib.framework.get_global_step(),
        optimizer="Adagrad", learning_rate=0.1)

    return predictions, loss, train_op


# entry
timestamp = time.clock()

train_X, train_y = generate_data(condition='train')
test_X, test_y = generate_data(condition='test')



"""
Mean Square Error is: 0.00637664133682847
time cost : 11.2319511742214 s

"""
X = tf.placeholder(tf.float32, shape=[None, TIME_STEPS, INPUT_SIZE])
Y = tf.placeholder(tf.float32, shape=[None, OUTPUT_SIZE])

predictions, loss, train_op=lstm_model(X,Y)
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    # for step in 1000:
    #     if( (step+1) * BATCH_SIZE >= len(train_X) ):
    step=0
    batch_X=train_X[step*BATCH_SIZE : (step+1) * BATCH_SIZE]
    batch_y=train_y[step*BATCH_SIZE : (step+1) * BATCH_SIZE]
    loss_result,_=sess.run([loss,train_op],feed_dict={X:batch_X,Y:batch_y})

