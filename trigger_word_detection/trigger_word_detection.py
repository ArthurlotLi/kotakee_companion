#
# trigger_word_detection.py
#
# Keras deep learning model designed to detect a specific
# tigger word in a live audio stream. Model is designed to
# take in a 10 second spectrograph and output predictions
# of which timesteps immediately floow a trigger word. 
# This model is then adapted for use with a live audio
# stream by feeding model 10 second audio clips with
# differences of 0.5 second steps. 
#
# Reference code is below.
#
# Initial code and model concept from:
# https://www.dlology.com/blog/how-to-do-real-time-trigger-word-detection-with-keras/
# https://github.com/Tony607/Keras-Trigger-Word 
#
# Usage Examples: 
# python3 trigger_word_detection.py 25 1  <- Creates dataset of size 10 iter 1
# python3 trigger_word_detection.py -d 0 1 <- -d Specifies not to create a dataset and loads dataset with iter 1. 
#

import os
import argparse
import numpy as np
import os
from td_utils import * # The file we're using directly from the ref project.

from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Activation, Dropout, Input, TimeDistributed, Conv1D
from tensorflow.keras.layers import GRU, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.regularizers import l2

from matplotlib import pyplot as plt


class TriggerWordDetection:
  # Constants
  Tx = 5511 # The number of time steps input to the model from the spectrogram
  n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
  Ty = 1375 # The number of time steps in the output of our model

  # Configuration of attempts. Windows may sometimes have hiccups
  # and not properly allocate enough RAM for our python program. 
  data_generation_x_attempts = 10 # For attempting to allocate numpy array for X. 
  data_generation_y_attempts = 2 # For attempting to allocate numpy array for y.
  data_writing_x_attempts = 10 # For attempting to write X to file.
  data_writing_y_attempts = 2 # For attempting to write y to file.

  # Directories
  models_location = "./models"
  model_history_location = "./model_histories"
  raw_data_folder = "./raw_data"
  raw_data_dev_folder = "./raw_data_dev"
  dataset_output_folder = "./XY_train"
  X_dev_location = "./XY_dev_kotakee/X_dev_kotakee.npy"
  Y_dev_location = "./XY_dev_kotakee/Y_dev_kotakee.npy"

  # The following are parameters that may be provided programatically 
  # to the class. Defaults are used if none are provided. 

  # Dataset generation parameters
  dataset_size = 10
  min_positives = 0
  max_positives = 4
  min_negatives = 0
  max_negatives = 2
  force_create = False # We'll overwrite an existing dataset if exists. 

  # Model hyperparameters + architecture
  model_learning_rate = 0.0001
  model_loss_function = 'binary_crossentropy'
  model_epochs = 5
  model_batch_size = 32
  model_validation_split = 0.2
  model_conv1d = 196
  model_gru_1 = 128
  model_gru_2 = 128
  model_gru_3 = 0
  model_gru_4 = 0
  model_gru_5 = 0

  # Model (additional) regularization
  model_hidden_dropout = 0.8
  model_input_dropout = 0.8 
  model_l2 = False # False means no penalty is applied. 
  model_l2_influence = 0.01 # Default modifier multiplied by regularizer. 

  # Optimization
  mcp_save_best_only = False
  use_adam_instead_of_rmsprop = True
  adam_beta_1 = None 
  adam_beta_2 = None
  adam_decay = None
  #adam_beta_1 = 0.9 
  #adam_beta_2 = 0.999
  #adam_decay = 0.01
  
  # All arguments are optional. 
  def __init__(self, model_parameters = None):
    if model_parameters is not None:
      if "dataset_size" in model_parameters: self.dataset_size = model_parameters["dataset_size"]
      if "min_positives" in model_parameters: self.min_positives = model_parameters["min_positives"]
      if "max_positives" in model_parameters: self.max_positives = model_parameters["max_positives"]
      if "min_negatives" in model_parameters: self.min_negatives = model_parameters["min_negatives"]
      if "max_negatives" in model_parameters: self.max_negatives = model_parameters["max_negatives"]
      if "force_create" in model_parameters: self.force_create = model_parameters["force_create"]

      if "model_learning_rate" in model_parameters: self.model_learning_rate = model_parameters["model_learning_rate"]
      if "model_loss_function" in model_parameters: self.model_loss_function = model_parameters["model_loss_function"]
      if "model_epochs" in model_parameters: self.model_epochs = model_parameters["model_epochs"]
      if "model_batch_size" in model_parameters: self.model_batch_size = model_parameters["model_batch_size"]
      if "model_validation_split" in model_parameters: self.model_validation_split = model_parameters["model_validation_split"]
      if "model_conv1d" in model_parameters: self.model_conv1d = model_parameters["model_conv1d"]
      if "model_gru_1" in model_parameters: self.model_gru_1 = model_parameters["model_gru_1"]
      if "model_gru_2" in model_parameters: self.model_gru_2 = model_parameters["model_gru_2"]
      if "model_gru_3" in model_parameters: self.model_gru_3 = model_parameters["model_gru_3"]
      if "model_gru_4" in model_parameters: self.model_gru_4 = model_parameters["model_gru_4"]
      if "model_gru_5" in model_parameters: self.model_gru_5 = model_parameters["model_gru_5"]

      if "model_hidden_dropout" in model_parameters: self.model_hidden_dropout = model_parameters["model_hidden_dropout"]
      if "model_input_dropout" in model_parameters: self.model_input_dropout = model_parameters["model_input_dropout"]
      if "model_l2" in model_parameters: self.model_l2 = model_parameters["model_l2"]
      if "model_l2_influence" in model_parameters: self.model_l2_influence = model_parameters["model_l2_influence"]

      if "mcp_save_best_only" in model_parameters: self.mcp_save_best_only = model_parameters["mcp_save_best_only"]
      if "use_adam_instead_of_rmsprop" in model_parameters: self.use_adam_instead_of_rmsprop = model_parameters["use_adam_instead_of_rmsprop"]
      if "adam_beta_1" in model_parameters: self.adam_beta_1 = model_parameters["adam_beta_1"]
      if "adam_beta_2" in model_parameters: self.adam_beta_2 = model_parameters["adam_beta_2"]
      if "adam_decay" in model_parameters: self.adam_decay = model_parameters["adam_decay"]

  # Primary function that executes the main steps:
  # A) Dataset Processing
  #   1. Load the wav files that will make the dataset.
  #   2. Dynamically generate the dataset.
  # B) Model Processing
  #    3. Train the model with the generated dataset.
  #    4. Save the model.
  def main(self, iternum, outputnum = None, stopGpu = False, generateDevSetOnly = False):
    print("[INFO] Initializing main...")
    if(stopGpu is True or stopGpu is None):
      # In case you have a CUDA enabled GPU and don't want to use it. 
      os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 

    x = None
    y = None
    x, y = self.create_dataset(self.dataset_size, iternum, generateDevSetOnly)

    if x is not None and y is not None:
      if generateDevSetOnly:
        print("[INFO] Dev set generated successfully! Goodnight...")
        return
      if outputnum is None:
        outputnum = iternum

      model = None
      model, best_accuracy, acc, history = self.train_model(X=x, Y=y, modelnum = outputnum, iternum=iternum)

      if model is not None:
        result = self.save_model(model, outputnum)

        self.graph_model_history(iternum=outputnum, history=history)

        print("[INFO] Training all done! Goodnight...")
        return best_accuracy, acc
      else:
        print("[ERROR] model was None! Execution failed.")
    else:
      print("[ERROR] datasets x and/or y was None! Execution failed.")
    return None, None

  #
  # A) DATASET CREATION AND PROCESSING
  #

  # 1. Load wav files that will make the dataset
  # 2. Dynamically generate the dataset.
  # Expects raw data to be in the raw_data folder in subfolders
  # named activates, backgrounds, and negatives. 
  def create_dataset(self, datasetSize, iternum, generateDevSetOnly = False):
    print("[INFO] Running create_dataset...")

    # What we output for the model to use. 
    final_x = None
    final_y = None

    # On principle, we will not overwrite an existing dataset. If it
    # does not exist, we'll create it according to the given parameters. 
    if (final_x is None and final_y is None) and (self.force_create is False):
      try:
        print("[INFO] Attempting to load existing dataset file ./XY_train/X_"+str(iternum)+".npy...")
        final_x = np.load(self.dataset_output_folder + "/X_"+str(iternum)+".npy")
        print("[INFO] Attempting to load existing dataset file ./XY_train/Y_"+str(iternum)+".npy...")
        final_y = np.load(self.dataset_output_folder + "/Y_"+str(iternum)+".npy")
        print("[DEBUG] final_x.shape is:", final_x.shape)  
        print("[DEBUG] final_y.shape is:", final_y.shape) 
      except:
        print("[INFO] Dataset file not found! Initiating dataset generation process...")
        final_x = None
        final_y = None

    # Dataset does not exist, let's create a new dataset. 
    if (final_x is None and final_y is None) or (self.force_create is True):
      print("[INFO] Loading raw audio (This may take some time)...")
      activates = None
      negatives = None
      backgrounds = None
      # Load audio segments using pydub 
      if(generateDevSetOnly):
        activates, negatives, backgrounds = load_raw_audio(self.raw_data_dev_folder)
      else:
        activates, negatives, backgrounds = load_raw_audio(self.raw_data_folder)
      print("[INFO] Raw audio loaded!")

      # To generate our dataset: select a random background and push that
      # into the create_training_example loop. Repeat this for as many times
      # as you'd like. Write all that stuff to a file and you're done? 
      clips_to_generate = datasetSize

      print("[INFO] Initiating dataset generation of size " +str(clips_to_generate)+".")
      array_x = []
      array_y = []
      for i in range(clips_to_generate):
        print("[DEBUG] Generating clip " + str(i) + "...")
        random_indices = np.random.randint(len(backgrounds), size=1)
        random_background = random_indices[0]
        x, y = self.create_training_example(backgrounds[random_background], activates, negatives)
        if x.shape == (101, 5511) and y.shape == (1, 1375):
          array_x.append(np.transpose(x, (1, 0)))
          array_y.append(np.transpose(y, (1, 0))) # We want to go from (1, 1375) to (1375, 1)
        else:
          print("[WARNING] Generated x and y of incorrect shapes! Discarding...")

      # Addressing how Windows sometimes fails to allocate enough RAM.
      generation_x_attempts = 0
      generation_y_attempts = 0
      writing_x_attempts = 0
      writing_y_attempts = 0
      writing_x_success = False
      writing_y_success = False

      # Attempt to combine X until maximum attempts reached. 
      while final_x is None:
        if generation_x_attempts >= self.data_generation_x_attempts:
          print("[ERROR] Maximum X generation attempts reached. Aborting...")
          return None, None
        print("[INFO] Combining all generated x arrays...")
        try:
          final_x = np.array(array_x)
        except:
          print("[WARNING] Error encountered when generating X during attempt " + str(generation_x_attempts) + ".")
        generation_x_attempts = generation_x_attempts + 1

      # Attempt to combine y until maximum attempts reached. 
      while final_y is None:
        if generation_y_attempts >= self.data_generation_y_attempts:
          print("[ERROR] Maximum y generation attempts reached. Aborting...")
          return None, None
        print("[INFO] Combining all generated y arrays...")
        try:
          final_y = np.array(array_y)
        except:
          print("[WARNING] Error encountered when generating y during attempt " + str(generation_y_attempts) + ".")
        generation_y_attempts = generation_y_attempts + 1
      
      print("[DEBUG] final_x.shape is:", final_x.shape)  
      print("[DEBUG] final_y.shape is:", final_y.shape)    

      # Attempt to write X until maximum attempts reached. 
      while writing_x_success is False:
        if(writing_x_attempts >= self.data_writing_x_attempts):
          print("[ERROR] Maximum x writing attempts reached. Aborting...")
          return None, None
        try:
          if(generateDevSetOnly):
            print("[INFO] Saving dev_X to file...")
            np.save(self.X_dev_location, final_x)
          else:
            print("[INFO] Saving final_x to file...")
            np.save(self.dataset_output_folder + "/X_"+str(iternum)+".npy", final_x)
          writing_x_success = True
        except:
          print("[WARNING] Error encountered when writing X during attempt " + str(writing_x_attempts) + ".")
        writing_x_attempts = writing_x_attempts + 1
        
      # Attempt to write y until maximum attempts reached. 
      while writing_y_success is False:
        if(writing_y_attempts >= self.data_writing_y_attempts):
          print("[ERROR] Maximum y writing attempts reached. Aborting...")
          return None, None
        try:
          if(generateDevSetOnly):
            print("[INFO] Saving dev_Y to file...")
            np.save(self.Y_dev_location, final_y)
          else:
            print("[INFO] Saving final_y to file...")
            np.save(self.dataset_output_folder + "/Y_"+str(iternum)+".npy", final_y)
          writing_y_success = True
        except:
          print("[WARNING] Error encountered when writing y during attempt " + str(writing_y_attempts) + ".")
        writing_y_attempts = writing_y_attempts + 1

      if(generateDevSetOnly):
        print("[INFO] Successfully saved dev sets.")
      else:
        print("[INFO] Successfully saved X_"+str(iternum)+".npy and Y_"+str(iternum)+".npy to XY_train folder.")

    return final_x, final_y

  def get_random_time_segment(self, segment_ms):
    """
    Gets a random time segment of duration segment_ms in a 10,000 ms audio clip.
    
    Arguments:
    segment_ms -- the duration of the audio clip in ms ("ms" stands for "milliseconds")
    
    Returns:
    segment_time -- a tuple of (segment_start, segment_end) in ms
    """
    
    # TODO: Here I just randomly threw in 1000 so as to make sure that, if
    # a positive is inserted into the latest possible moment, there will
    # still be silence left over to fill with positive labels. 
    #segment_start = np.random.randint(low=0, high=10000-segment_ms-1000)   # Make sure segment doesn't run past the 10sec background 
    segment_start = np.random.randint(low=0, high=10000-segment_ms) # Maybe this change was causing the model to freak out? 
    segment_end = segment_start + segment_ms - 1
    
    return (segment_start, segment_end)

  def is_overlapping(self, segment_time, previous_segments):
    """
    Checks if the time of a segment overlaps with the times of existing segments.
    
    Arguments:
    segment_time -- a tuple of (segment_start, segment_end) for the new segment
    previous_segments -- a list of tuples of (segment_start, segment_end) for the existing segments
    
    Returns:
    True if the time segment overlaps with any of the existing segments, False otherwise
    """
    
    segment_start, segment_end = segment_time
    
    ### START CODE HERE ### (≈ 4 line)
    # Step 1: Initialize overlap as a "False" flag. (≈ 1 line)
    overlap = False
    
    # Step 2: loop over the previous_segments start and end times.
    # Compare start/end times and set the flag to True if there is an overlap (≈ 3 lines)
    for previous_start, previous_end in previous_segments:
        if segment_start <= previous_end and segment_end >= previous_start:
            overlap = True
    ### END CODE HERE ###

    return overlap

  def insert_audio_clip(self, background, audio_clip, previous_segments):
    """
    Insert a new audio segment over the background noise at a random time step, ensuring that the 
    audio segment does not overlap with existing segments.
    
    Arguments:
    background -- a 10 second background audio recording.  
    audio_clip -- the audio clip to be inserted/overlaid. 
    previous_segments -- times where audio segments have already been placed
    
    Returns:
    new_background -- the updated background audio
    """
    
    # Get the duration of the audio clip in ms
    segment_ms = len(audio_clip)
    
    ### START CODE HERE ### 
    # Step 1: Use one of the helper functions to pick a random time segment onto which to insert 
    # the new audio clip. (≈ 1 line)
    segment_time = self.get_random_time_segment(segment_ms)
    
    # Step 2: Check if the new segment_time overlaps with one of the previous_segments. If so, keep 
    # picking new segment_time at random until it doesn't overlap. (≈ 2 lines)
    numTries = 0
    while self.is_overlapping(segment_time, previous_segments):
        if numTries > 100:
          print("[WARNING] insert_audio_clip failed to insert a segment!")
          # Return existing background and no segment time - we failed. 
          return background, None
        segment_time = self.get_random_time_segment(segment_ms)
        numTries = numTries + 1


    # Step 3: Add the new segment_time to the list of previous_segments (≈ 1 line)
    previous_segments.append(segment_time)
    ### END CODE HERE ###
    
    # Step 4: Superpose audio segment and background
    new_background = background.overlay(audio_clip, position = segment_time[0])
    
    return new_background, segment_time

  def insert_ones(self, y, segment_end_ms):
    """
    Update the label vector y. The labels of the 50 output steps strictly after the end of the segment 
    should be set to 1. By strictly we mean that the label of segment_end_y should be 0 while, the
    50 followinf labels should be ones.
    
    
    Arguments:
    y -- numpy array of shape (1, Ty), the labels of the training example
    segment_end_ms -- the end time of the segment in ms
    
    Returns:
    y -- updated labels
    """
    
    # duration of the background (in terms of spectrogram time-steps)
    segment_end_y = int(segment_end_ms * self.Ty / 10000.0)
    
    # Add 1 to the correct index in the background label (y)
    ### START CODE HERE ### (≈ 3 lines)
    for i in range(segment_end_y + 1, segment_end_y + 51):
        if i < self.Ty:
            y[0, i] = 1
    ### END CODE HERE ###
    
    return y

  def create_training_example(self, background, activates, negatives):
    """
    Creates a training example with a given background, activates, and negatives.
    
    Arguments:
    background -- a 10 second background audio recording
    activates -- a list of audio segments of the word "activate"
    negatives -- a list of audio segments of random words that are not "activate"
    
    Returns:
    x -- the spectrogram of the training example
    y -- the label at each time step of the spectrogram
    """
    
    # Set the random seed
    #np.random.seed(18)
    
    # Make background quieter
    background = background - 20
    # Step 1: Initialize y (label vector) of zeros (≈ 1 line)
    y = np.zeros((1, self.Ty))

    # Step 2: Initialize segment times as empty list (≈ 1 line)
    previous_segments = []
    
    # Select 0-4 random "activate" audio clips from the entire list of "activates" recordings
    number_of_activates = np.random.randint(self.min_positives, self.max_positives + 1)
    print("[DEBUG] Attempting to insert", number_of_activates, "activates.")
    random_indices = np.random.randint(len(activates), size=number_of_activates)
    random_activates = [activates[i] for i in random_indices]
    
    # Step 3: Loop over randomly selected "activate" clips and insert in background
    for random_activate in random_activates:
        # Insert the audio clip on the background
        background, segment_time = self.insert_audio_clip(background, random_activate, previous_segments)
        # Handle the case where we simply could not insert another audio clip. 
        if(segment_time is not None):
          # Retrieve segment_start and segment_end from segment_time
          segment_start, segment_end = segment_time
          # Insert labels in "y"
          y = self.insert_ones(y, segment_end_ms=segment_end)

    # Select 0-2 random negatives audio recordings from the entire list of "negatives" recordings
    number_of_negatives = np.random.randint(self.min_negatives, self.max_negatives + 1)
    random_indices = np.random.randint(len(negatives), size=number_of_negatives)
    random_negatives = [negatives[i] for i in random_indices]
    print("[DEBUG] Attempting to insert", number_of_negatives, "negatives.")

    # Step 4: Loop over randomly selected negative clips and insert in background
    for random_negative in random_negatives:
        # Insert the audio clip on the background 
        background, _ = self.insert_audio_clip(background, random_negative, previous_segments)
    
    # Standardize the volume of the audio clip 
    background = match_target_amplitude(background, -20.0)

    # Export new training example 
    file_handle = background.export("train" + ".wav", format="wav")
    
    # Get and plot spectrogram of the new recording (background with superposition of positive and negatives)
    x = graph_spectrogram("train.wav")
    
    return x, y

  #
  # B) MODEL CREATION AND TRAINING
  #

  # 3. Train the model with the generated model. Returns the model, 
  # best train acc, test acc, and model history. 
  def train_model(self, X, Y, modelnum, iternum):
    print("[INFO] Running train_model...")

    # L2 regularization (weight decay)
    if(self.model_l2 is True):
      print("[DEBUG] L2 Regularization enabled with weight " + str(self.model_l2_influence) + ".")
      l2(l2=self.model_l2_influence)

    # Define the model. 
    model = self.define_model(input_shape = (self.Tx, self.n_freq))

    # Output number of parameters. 
    model.summary()

    # TODO: Hard coded verbose. 
    verbose = True

    # Optimizer cration
    opt = None
    if(self.use_adam_instead_of_rmsprop):
      if (self.adam_beta_1 is not None and self.adam_beta_2 is not None):
        opt = Adam(learning_rate=self.model_learning_rate, beta_1=self.adam_beta_1, beta_2=self.adam_beta_2)
      elif(self.adam_beta_1 is not None and self.adam_beta_2 is not None and self.adam_decay is not None):
        opt = Adam(learning_rate=self.model_learning_rate, beta_1=self.adam_beta_1, beta_2=self.adam_beta_2, decay=self.adam_decay)
      else:
        opt = Adam(learning_rate=self.model_learning_rate)
    else:
      opt = RMSprop(learning_rate=self.model_learning_rate)

    # Compile the model. 
    model.compile(optimizer=opt, loss = self.model_loss_function, metrics=["accuracy"])

    # Apply MCP
    mcp = ModelCheckpoint(filepath='./model_checkpoints/tr_model_'+str(modelnum)+'_{val_accuracy:.5f}_{accuracy:.5f}_{epoch:02d}' + ".h5", 
                          monitor='accuracy', 
                          verbose=1, 
                          save_best_only=self.mcp_save_best_only)
    # Train. 
    history = model.fit(X, Y, shuffle=True, 
                        epochs=self.model_epochs, 
                        callbacks=[mcp], 
                        validation_split=self.model_validation_split, 
                        verbose=verbose, 
                        batch_size=self.model_batch_size)

    # Output best accuracy and attempt to test it with the test set. 
    best_accuracy = max(history.history['accuracy'])
    print("\nModel training complete. Best accuracy: " + str(best_accuracy))
    try:
      print("[INFO] Loading dev dataset X file " + self.X_dev_location + "...")
      X_dev = np.load(self.X_dev_location)
      print("[INFO] Loading dev dataset Y file " + self.Y_dev_location + "...")
      Y_dev = np.load(self.Y_dev_location)
      print("[DEBUG] X_dev.shape is:", X_dev.shape)  
      print("[DEBUG] Y_dev.shape is:", Y_dev.shape) 
      loss, acc = model.evaluate(X_dev, Y_dev)
      print("[INFO] Dev set accuracy is: ", acc) 
    except:
      print("[WARN] Error loading X_dev and/or Y/dev.")

    return model, best_accuracy, acc, history

  # Model definition. Class variables dictate the number of neurons in the 
  # layers for chain train configuration. 
  def define_model(self, input_shape):
      X_input = Input(shape = input_shape)
      X = None
      
      # Convolutional Layer 
      if(self.model_l2 is True):
        X = Conv1D(self.model_conv1d, kernel_size=15, strides=4, kernel_regularizer='l2')(X_input) 
      else:
        X = Conv1D(self.model_conv1d, kernel_size=15, strides=4)(X_input) 
      X = BatchNormalization()(X)
      X = Activation('relu')(X) 
      X = Dropout(self.model_input_dropout)(X)

      # First GRU Layer
      if(self.model_gru_1 is not None and self.model_gru_1 > 0):
        if(self.model_l2 is True):
          X = GRU(units = self.model_gru_1, kernel_regularizer='l2', return_sequences = True)(X)
        else:
          X = GRU(units = self.model_gru_1, return_sequences = True)(X)
        X = Dropout(self.model_hidden_dropout)(X)
        X = BatchNormalization()(X)
      
      # Second GRU Layer
      if(self.model_gru_2 is not None and self.model_gru_2 > 0):
        if(self.model_l2 is True):
          X = GRU(units = self.model_gru_2, kernel_regularizer='l2', return_sequences = True)(X)
        else:
          X = GRU(units = self.model_gru_2, return_sequences = True)(X)
        X = Dropout(self.model_hidden_dropout)(X)
        X = BatchNormalization()(X)

      # Third GRU Layer
      if(self.model_gru_3 is not None and self.model_gru_3 > 0):
        if(self.model_l2 is True):
          X = GRU(units = self.model_gru_3, kernel_regularizer='l2', return_sequences = True)(X)
        else:
          X = GRU(units = self.model_gru_3, return_sequences = True)(X)
        X = Dropout(self.model_hidden_dropout)(X)
        X = BatchNormalization()(X)
    
      # Fourth GRU Layer
      if(self.model_gru_4 is not None and self.model_gru_4 > 0):
        if(self.model_l2 is True):
          X = GRU(units = self.model_gru_4, kernel_regularizer='l2', return_sequences = True)(X)
        else:
          X = GRU(units = self.model_gru_4, return_sequences = True)(X)
        X = Dropout(self.model_hidden_dropout)(X)
        X = BatchNormalization()(X)

      # Fifth GRU Layer
      if(self.model_gru_5 is not None and self.model_gru_5 > 0):
        if(self.model_l2 is True):
          X = GRU(units = self.model_gru_5, kernel_regularizer='l2', return_sequences = True)(X)
        else:
          X = GRU(units = self.model_gru_5, return_sequences = True)(X)
        X = Dropout(self.model_hidden_dropout)(X)
        X = BatchNormalization()(X)
        
      # Add a final dropout before we get to the final layer.
      X = Dropout(self.model_hidden_dropout)(X)
      # Sigmoid output layer. 
      X = TimeDistributed(Dense(1, activation = "sigmoid"))(X) 

      model = Model(inputs = X_input, outputs = X)
      return model 

  # 4. Save the model.
  #
  # Returns true or false depending on execution status. 
  def save_model(self, model, iternum):
    print("[INFO] Running save_model...")
    try:
      location = self.models_location + '/tr_model_'+str(iternum)+'.h5'
      model.save(location)
      print('[INFO] model successfully saved at: ' + location + '.')
      return True
    except Exception as e:
      print("[ERROR] Exception occurred when saving model: ")
      print(e)
    return False

  # 5. Graph History
  #
  # Graphs and saves training history. Two graphs are generated and
  # saved - one for accuracy, the other for loss. 
  def graph_model_history(self, iternum, history):
    print("[INFO] Generating model history graph for model " + str(iternum) + ".")

    # Constants for both graphs.
    graph_width_inches = 13
    graph_height_inches = 7
    print("DEBNUGGGGE: ")
    print(history.history)

    # Generate accuracy graph
    title = "Iternum " + str(iternum) + " Training History [Accuracy]"
    fig = plt.figure(1)
    fig.suptitle(title)
    fig.set_size_inches(graph_width_inches,graph_height_inches)
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['train', 'val'], loc="upper left")

    # Save the graph. 
    location = self.model_history_location + "/" + str(iternum) + "_acc"
    try:
      fig.savefig(location)
      print("[DEBUG] Graph successfully saved to: " + str(location) + ".")
    except Exception as e:
      print("[ERROR] Unable to save graph at location: " + str(location) + ". Exception:")
      print(e)
    
    plt.close("all")

    # Generate loss graph
    title = "Iternum " + str(iternum) + " Training History [Loss]"
    fig = plt.figure(1)
    fig.suptitle(title)
    fig.set_size_inches(graph_width_inches,graph_height_inches)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['train', 'val'], loc="upper left")

    # Save the graph. 
    location = self.model_history_location + "/" + str(iternum) + "_loss"
    try:
      fig.savefig(location)
      print("[DEBUG] Graph successfully saved to: " + str(location) + ".")
    except Exception as e:
      print("[ERROR] Unable to save graph at location: " + str(location) + ". Exception:")
      print(e)
    
    plt.close("all")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('datasetSize')
  parser.add_argument('iternum')
  parser.add_argument('-g', action='store_true', default=False)
  parser.add_argument('-t', action='store_true', default=False)
  args = parser.parse_args()

  datasetSize = int(args.datasetSize)
  iternum = int(args.iternum)
  stopGpu = args.g
  generateDevSetOnly = args.t

  """
  model_parameters = {
    "dataset_size": datasetSize
  }
  """

  # For Manual one-off creation like for dev sets. keep this commented
  # out for defaults otherwise. 
  #
  # Ex) python trigger_word_detection.py 800 10 -t (iternum is ignored.)
  model_parameters = {
      "dataset_size": datasetSize,
      "max_positives" : 4,
      "min_positives" : 0,
      "max_negatives" : 4,
      "min_negatives" : 0,
      "force_create" : True,
  }

  trigger_word_detection = TriggerWordDetection(model_parameters)
  trigger_word_detection.main(iternum, stopGpu = stopGpu, generateDevSetOnly = generateDevSetOnly)