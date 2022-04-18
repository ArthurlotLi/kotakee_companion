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
# python augmented_train.py ./model_checkpoints/tr_model_13941.h5 300 10

from augmented_params import *
from augmented_dataset import *

from pathlib import Path
from tensorflow.keras.models import load_model, save_model
import argparse
from tensorflow.keras.callbacks import ModelCheckpoint
from multiprocessing import Process, Queue

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

  ret_dict = {}
  queue = Queue()
  queue.put(ret_dict)

  # Loop around and then finish. Each instance needs to be run as
  # it's own subprocess, because tensorflow doesn't know when to release
  # memory... We can't load the model outside of the process, so just
  # pass in the location and get back the location of the updated model.
  for i in range(0, loop_total):
    p = Process(target = augmented_train_loop, 
                args = (queue, i, model_location, loop_total, loop_epochs))
    # Kick the process off
    p.start()
    # Wait for the process to finish. 
    p.join()
    # Get the output model. 
    ret_dict_result = queue.get()
    model_location = ret_dict_result["model"]

def augmented_train_loop(queue, i, model_location, loop_total, loop_epochs):
  """
  Inner function for training. Each go around, create an augmented
  dataset and fit the model on that dataset for x epochs. Return the
  model to be fed back to us once more. 
  """
  print("\n[INFO] Augmented Train - Starting loop %d out of %d.\n" % (i+1, loop_total))
  # Leave everything about the model the same.
  model = _load_existing_model(model_location)

  X, Y = create_augmented_dataset()

  # Apply MCP. Each checkpoint is named the same as the input file,
  # with a # indicating which loop iteration it was generated during.
  # The rest of the filename goes as you'd expect. 
  mcp = ModelCheckpoint(filepath= checkpoints_folder + '/' + str(Path(model_location).name).replace(".h5", str(i)) + "_{val_accuracy:.5f}_{accuracy:.5f}_{epoch:02d}" + ".h5", 
                        monitor='accuracy', 
                        verbose=1, 
                        save_best_only=False)
  
  # Train on the augmented dataset. 
  history = model.fit(X, Y, shuffle=True, 
                      epochs=loop_epochs, 
                      callbacks=[mcp], 
                      validation_split=validation_split, 
                      verbose=True, 
                      batch_size=batch_size)
  
  temp_model_location = checkpoints_folder + '/' + str(model_location.name).replace(".h5", str(i)) + "_temp.h5"
  save_model(model, temp_model_location)

  ret_dict = queue.get()
  ret_dict["model"] = temp_model_location
  queue.put(ret_dict)

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