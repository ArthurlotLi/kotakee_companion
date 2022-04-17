#
# augmented_train.py
#
# I'm back! Let's improve trigger word detection with some relatively
# straightforward audio augmentation. Please excuse the mess - a lot
# of this code is back from when I was working on this as one of my
# first machine learning projects. 
#
# Given an initial model, enter a continuous loop of training + 
# dataset augmentation in order to expose the model to various 
# augmented audio samples. Ideally, the model will become invariant
# to small changes such as pitch, tone, volume, etc. that will 
# mean better real world performance with different microphones and
# room acoustics.
#
# Please be advised I'm not gonna try to clean up my old code, I'm
# just here to improve my model a little bit becuase it's buggin' me
# that my web server has been ignoring me so much. 
#
# Usage:
# python augmented_train.py ./models/tr_model_13941.h5 1000 1

import tensorflow as tf
# For tensorflow - stop allocating the entire VRAM. 
config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth=True
sess = tf.compat.v1.Session(config=config)

from augmented_params import *
from augmented_dataset import *

from pathlib import Path
from tensorflow.keras.models import load_model
import argparse

def augmented_train(model_location: Path, loop_epochs: int, 
                    loop_total: int):
  """
  Given the location of an initial model for which to use in a warm
  start, loop for a specified number of times. With each loop, generate
  a brand new dataset from the raw data folder, with each sample being
  augmented, and train for a specified number of epochs. 

  This should generate checkpoints with which a chain test can be 
  executed to derive the best performing model out of the bunch on  
  the test set. 
  """ 
  print("[INFO] Augmented Train - Beginning routine for %d loops, with %d epochs per loop. Using model %s." 
    % (loop_total, loop_epochs, model_location))
  model = _load_existing_model(model_location)
  X, Y = create_augmented_dataset()


def _load_existing_model(model_location: Path):
  """
  Asserts that the model exists and returns it.
  """
  model = load_model(str(model_location))
  return model


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("model_location", type=Path)
  parser.add_argument("loop_epochs", type=int)
  parser.add_argument("loop_total", type=int)
  args = parser.parse_args()

  augmented_train(**vars(args))