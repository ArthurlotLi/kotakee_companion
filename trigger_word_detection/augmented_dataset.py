#
# augmented_dataset.py
#
# Companion to augmented_train, allowing for the creation of datasets
# in much the same manner as the main training harness, with the 
# addition of audio augmentation. 

from augmented_params import *
from td_utils import load_raw_audio, match_target_amplitude, graph_spectrogram

from pathlib import Path
import numpy as np
import os
import sox
import random
from tqdm import tqdm

def create_augmented_dataset():
  """
  Given the parameters specified in the augmented_params, generates a
  dataset from the raw data folder much like the main training harness.
  A difference is that, for each 
  """
  print("[INFO] Augmented Dataset - Loading raw audio (This may take some time)...")
  activates, negatives, backgrounds = load_raw_audio(raw_data_folder)
  print("[INFO] Augmented Dataset - Raw audio loaded!")

  # To generate our dataset: select a random background and push that
  # into the create_training_example loop. Repeat this for as many times
  # as you'd like. Write all that stuff to a file and you're done? 
  clips_to_generate = dataset_size

  print("[INFO] Augmented Dataset - Initiating dataset generation of size " +str(clips_to_generate)+".")
  array_x = []
  array_y = []
  for i in tqdm(range(clips_to_generate)):
    #print("[DEBUG] Augmented Dataset - Generating clip " + str(i) + "...")
    random_indices = np.random.randint(len(backgrounds), size=1)
    random_background = random_indices[0]
    x, y, files_to_remove = create_training_example(backgrounds[random_background], activates, negatives, "train%d.wav" % i)
    for file in files_to_remove:
      os.remove(file)
    if x.shape == (101, 5511) and y.shape == (1, 1375):
      array_x.append(np.transpose(x, (1, 0)))
      array_y.append(np.transpose(y, (1, 0))) # We want to go from (1, 1375) to (1375, 1)
    else:
      pass
      #print("[WARNING] Augmented Dataset - Generated x and y of incorrect shapes! Discarding...")

  final_x = np.array(array_x)
  final_y = np.array(array_y)
  
  print("[DEBUG] Augmented Dataset - final_x.shape is:", final_x.shape)  
  print("[DEBUG] Augmented Dataset - final_y.shape is:", final_y.shape)    
    
  return final_x, final_y

def augment_wav(wav_location:str):
  """
  The heart of this entire harness, wherein a wav is augmented in
  various ways stochastically within set boundaries to produce a
  modified sample while wholly preserving the classes of each 
  timestep.
  """
  assert Path(wav_location).exists()

  # Our Transformer will have all the changes specified first. 
  tfm = sox.Transformer()

  # Pitch Shift
  tfm.pitch(n_semitones = sample_value(pitch_shift, pitch_shift_sampling))

  # Contrast (compression)
  tfm.contrast(amount = sample_value(contrast, contrast_sampling))

  # Equalizer 1
  tfm.equalizer(frequency = sample_value(equalizer_1, equalizer_1_sampling), width_q=equalizer_q, gain_db=equalizer_gain)

  # Equalizer 2
  tfm.equalizer(frequency = sample_value(equalizer_2, equalizer_2_sampling), width_q=equalizer_q, gain_db=equalizer_gain)

  # Reverb
  tfm.reverb(reverberance = sample_value(reverb, reverb_sampling))

  # Build the output file. Overwite the existing file. 
  output_wav = wav_location.rsplit(".wav", 1)[0] + "_augmented.wav"
  tfm.build_file(wav_location, output_wav)

  input()
  return output_wav


def sample_value(bounds, sampling):
  """
  Samples a value. Sampling options are "linear" and "log".
  """
  assert sampling == "linear" or sampling == "log"
  assert len(bounds)== 2
  lower_bound, upper_bound = bounds[0], bounds[1]

  if sampling == "linear":
    return random.uniform(lower_bound, upper_bound)
  elif sampling == "log":
    # Modifier is a float between 0 and 1. 
    modifier = np.random.lognormal()
    return modifier*random.uniform(lower_bound, upper_bound)

def get_random_time_segment(segment_ms):
  segment_start = np.random.randint(low=0, high=10000-segment_ms) 
  segment_end = segment_start + segment_ms - 1
  
  return (segment_start, segment_end)

def is_overlapping(segment_time, previous_segments): 
  segment_start, segment_end = segment_time
  
  overlap = False
  for previous_start, previous_end in previous_segments:
      if segment_start <= previous_end and segment_end >= previous_start:
          overlap = True

  return overlap

def insert_audio_clip(background, audio_clip, previous_segments):
  # Get the duration of the audio clip in ms
  segment_ms = len(audio_clip)
  segment_time = get_random_time_segment(segment_ms)
  numTries = 0
  while is_overlapping(segment_time, previous_segments):
      if numTries > 100:
        #print("[WARNING] insert_audio_clip failed to insert a segment!")
        # Return existing background and no segment time - we failed. 
        return background, None
      segment_time = get_random_time_segment(segment_ms)
      numTries = numTries + 1
  previous_segments.append(segment_time)
  
  new_background = background.overlay(audio_clip, position = segment_time[0])
  
  return new_background, segment_time

def insert_ones(y, segment_end_ms):
  segment_end_y = int(segment_end_ms * Ty / 10000.0)
  for i in range(segment_end_y + 1, segment_end_y + 51):
      if i < Ty:
          y[0, i] = 1
  return y

def create_training_example(background, activates, negatives, filename):
  # Make background quieter
  background = background - 20
  y = np.zeros((1, Ty))
  previous_segments = []
  
  # Select 0-4 random "activate" audio clips from the entire list of "activates" recordings
  number_of_activates = np.random.randint(min_positives, max_positives + 1)
  #print("[DEBUG] Attempting to insert", number_of_activates, "activates.")
  random_indices = np.random.randint(len(activates), size=number_of_activates)
  random_activates = [activates[i] for i in random_indices]
  
  for random_activate in random_activates:
    # Insert the audio clip on the background
    background, segment_time = insert_audio_clip(background, random_activate, previous_segments)
    # Handle the case where we simply could not insert another audio clip. 
    if(segment_time is not None):
      # Retrieve segment_start and segment_end from segment_time
      segment_start, segment_end = segment_time
      # Insert labels in "y"
      y = insert_ones(y, segment_end_ms=segment_end)

  number_of_negatives = np.random.randint(min_negatives, max_negatives + 1)
  random_indices = np.random.randint(len(negatives), size=number_of_negatives)
  random_negatives = [negatives[i] for i in random_indices]
  #print("[DEBUG] Attempting to insert", number_of_negatives, "negatives.")

  for random_negative in random_negatives:
    # Insert the audio clip on the background 
    background, _ = insert_audio_clip(background, random_negative, previous_segments)
  
  # Standardize the volume of the audio clip 
  background = match_target_amplitude(background, -20.0)

  # Export new training example 
  file_handle = background.export(filename, format="wav")

  # AUDIO AUGMENTATION - Here's the point where we've generated a wav
  # file that we can now augment. 
  output_wav = augment_wav(filename)
  
  # Get and plot spectrogram of the new recording (background with superposition of positive and negatives)
  x = graph_spectrogram(output_wav)

  # Remove the file. Do this outside of this function so we don't get
  # a win error.
  files_to_remove = [filename, output_wav]
  
  return x, y, files_to_remove