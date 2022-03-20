#
# evaluate_model.py
#
# Given a dataset iteration number and and model parameters,
# execute 10-fold cross validation to observe performance. 

import argparse
import numpy as np
import os

# Model declaration
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Activation, Dropout, Input, Conv1D, TimeDistributed, GRU, BatchNormalization
from tensorflow.keras.optimizers import Adam

# Model validation
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
from sklearn.model_selection import KFold, cross_val_score

class EvaluateModel:
  Tx = 5511 # The number of time steps input to the model from the spectrogram
  n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
  Ty = 1375 # The number of time steps in the output of our model

  learning_rate = None
  loss_function = None
  epochs = None
  batch_size = None
  validation_split = None
  opt = None
  verbose = True

  def __init__(self, model_arguments):
    self.learning_rate = model_arguments["learning_rate"] 
    self.loss_function = model_arguments["loss_function"]
    self.epochs = model_arguments["epochs"]
    self.batch_size = model_arguments["batch_size"]
    self.validation_split = model_arguments["validation_split"]
    self.opt = Adam(learning_rate=self.learning_rate)

  # Given the iternum, load a model. 
  def main(self, iternum):
    print("[INFO] Starting evaluate_model procedure with iternum " + str(iternum) + "...")

    # What we output for the model to use. 
    final_x = None
    final_y = None

    print("[INFO] Loading existing dataset file ./XY_train/X_"+str(iternum)+".npy...")
    final_x = np.load("./XY_train/X_"+str(iternum)+".npy")
    print("[INFO] Loading existing dataset file ./XY_train/Y_"+str(iternum)+".npy...")
    final_y = np.load("./XY_train/Y_"+str(iternum)+".npy")
    print("[DEBUG] final_x.shape is:", final_x.shape)  
    print("[DEBUG] final_y.shape is:", final_y.shape)

    if final_x is not None and final_y is not None:
      print("[INFO] Beginning evaluation... ")
      kfold = KFold(n_splits=2, shuffle=True)

      # cross_val_score expects a 2D y, so remove the final dimension of the Y array. 
      final_y_reshaped = final_y[:, :, 0]

      results = cross_val_score(KerasClassifier(build_fn=self.model_fn, epochs=self.epochs, batch_size=self.batch_size, validation_split=self.validation_split, shuffle=True, verbose=self.verbose), final_x, final_y_reshaped, cv=kfold)
      print("[INFO] Execution complete! Results: %.2f (%.2f)" % (results.mean()*100,results.std()*100))
      return results
    else:
      print("[ERROR] datasets x and/or y was None! Execution failed.")
      return None

  def model_fn(self):
    model = self.define_model(input_shape = (self.Tx, self.n_freq))
    model.compile(loss=self.loss_function, optimizer=self.opt, metrics=["accuracy"])
    return model

  # TODO: We've copied over model declaration, but ideally we'd 
  # have this in a class to share between the two files. 
  def define_model(self, input_shape):
      """
      Function creating the model's graph in Keras.
      
      Argument:
      input_shape -- shape of the model's input data (using Keras conventions)

      Returns:
      model -- Keras model instance
      """
      
      X_input = Input(shape = input_shape)
      
      # Step 1: CONV layer (≈4 lines)
      X = Conv1D(196, kernel_size=15, strides=4)(X_input)                                 # CONV1D
      X = BatchNormalization()(X)                                 # Batch normalization
      X = Activation('relu')(X)                                 # ReLu activation
      X = Dropout(0.8)(X)                                 # dropout (use 0.8).
      # TODO note: changed all dropouts from 0.8 to 0.5

      # Step 2: First GRU Layer (≈4 lines)
      X = GRU(units = 128, return_sequences = True)(X) # GRU (use 128 units and return the sequences)
      X = Dropout(0.8)(X)                                 # dropout (use 0.8)
      X = BatchNormalization()(X)                                 # Batch normalization
      
      # Step 3: Second GRU Layer (≈4 lines)
      X = GRU(units = 128, return_sequences = True)(X)   # GRU (use 128 units and return the sequences)
      X = Dropout(0.8)(X)                                 # dropout (use 0.8)
      X = BatchNormalization()(X)                                  # Batch normalization
      X = Dropout(0.8)(X)                                  # dropout (use 0.8)
      
      # Step 4: Time-distributed dense layer (≈1 line)
      X = TimeDistributed(Dense(1, activation = "sigmoid"))(X) # time distributed  (sigmoid)

      model = Model(inputs = X_input, outputs = X)
      
      return model 

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('iternum')
  parser.add_argument('-g', action='store_true', default=False)
  args = parser.parse_args()

  iternum = int(args.iternum)
  stopGpu = args.g

  if(stopGpu is True or stopGpu is None):
    # In case you have a CUDA enabled GPU and don't want to use it. 
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 

  model_arguments = {
    "learning_rate" : 0.0001,
    "loss_function" : 'binary_crossentropy',
    "epochs" : 1,
    "batch_size" : 32, 
    "validation_split" : 0.2,
  }

  evaluate_model = EvaluateModel(model_arguments)
  evaluate_model.main(iternum)