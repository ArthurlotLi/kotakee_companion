# 
# test_model.py
#
# Small utility program to run a specified model iteration
# against dev set to see accuracy. 

import os
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

class TestModel():
  #X_dev_location = "./XY_dev/X_dev.npy"
  #Y_dev_location = "./XY_dev/Y_dev.npy"
  X_dev_location = "./XY_dev_kotakee/X_dev_kotakee.npy"
  Y_dev_location = "./XY_dev_kotakee/Y_dev_kotakee.npy"

  # Optionally takes in the X_dev and Y_dev in the case that a series
  # of training sessions is occuring to reduce overhead of 
  # initialization.
  def test_model(self, model_path, iternum = 1, X_dev = None, Y_dev = None, use_gpu = True):
    if use_gpu is False:
      # Expliclty stop the GPU from being utilized. Use this option
      # in the case that your dev set is really small. 
      # In case you have a CUDA enabled GPU and don't want to use it. 
      os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 

    # Load pretrained model
    if(int(iternum) <= 0):
      # If we're using 0 or less, we're using the pretrained model.
      # If so, we need to adjust becuase it was trained in tf1 and
      # we're using tf2. 
      tf.compat.v1.disable_v2_behavior()
      model = tf.compat.v1.keras.models.load_model(model_path)
    else:
      # Load our model. 
      model = load_model(model_path)
    if(model is None):
      print('[ERROR] Unable to load trigger word detection model. Path: '+ model_path +' Stopping...')
      return
    
    # Load the dev datset if it wasn't passed in. 
    if X_dev is None or Y_dev is None:
      try:
        print("[INFO] Loading dev dataset X file " + self.X_dev_location + "...")
        X_dev = np.load(self.X_dev_location)
        print("[INFO] Loading dev dataset Y file " + self.Y_dev_location + "...")
        Y_dev = np.load(self.Y_dev_location)
        print("[DEBUG] X_dev.shape is:", X_dev.shape)  
        print("[DEBUG] Y_dev.shape is:", Y_dev.shape) 
      except:
        print("[WARN] Error loading X_dev and/or Y/dev.")
        return -1
    
    loss, acc = model.evaluate(X_dev, Y_dev)
    print("[INFO] Dev set accuracy is: ", acc) 
    return acc

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('path')
  args = parser.parse_args()

  test_model = TestModel()
  test_model.test_model(args.path)
  """
  parser = argparse.ArgumentParser()
  parser.add_argument('iternum')
  parser.add_argument('-c', action='store_true', default=False)
  args = parser.parse_args()

  iternum = int(args.iternum)
  use_checkpointed_model = args.c

  models_path = './models'
  
  if(use_checkpointed_model):
    model_path = models_path + '/tr_model_weights_'+str(iternum) +'.h5'
  else:
    model_path = models_path + '/tr_model_'+str(iternum) +'.h5'

  test_model = TestModel()
  test_model.test_model(model_path)
  """