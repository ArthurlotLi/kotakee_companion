#
# hotword_trigger_word.py
#
# Supporting class utilizing triggerWordDetection AI/ML project
# to detect when a user speaks the designated hotword. 
#
# Requires the iteration number when executing. 

import numpy as np
import matplotlib.mlab as mlab
import tensorflow as tf
from tensorflow.keras.models import load_model
import pyaudio
from queue import Queue
import time

class HotwordTriggerWord:
  models_path = None

  Tx = 5511 # The number of time steps input to the model from the spectrogram
  n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
  Ty = 1375# The number of time steps in the output of our model
  chunk_duration = 0.5 # Each read length in seconds from mic.
  fs = 44100 # sampling rate for mic
  chunk_samples = int(fs * chunk_duration) # Each read length in number of samples.
  silence_threshold = 100
  feed_duration = 10 # Each model input data duration in seconds, need to be an integer numbers of chunk_duration
  feed_samples = int(fs * feed_duration)
  
  activation_threshold = 0.1 # Lower values allow for more uncertain predictions to count as activated. 

  active_loop = True
  q = Queue() # Queue to communiate between the audio callback and main thread
  data = np.zeros(feed_samples, dtype='int16') # Data buffer for the input wavform

  model = None # Loaded Neural Network
  iternum = None # iternum for model
  interaction_active = None
  speech_listen = None
  speech_speak = None

  def __init__(self, interaction_active, speech_speak, speech_listen, model_path):
    self.models_path = model_path
    self.interaction_active = interaction_active
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen

  # Must be called. Returns False if failure occurs, otherwise returns True.
  def load_model(self, iternum):
    print("[INFO] Loading Trigger Word Detection model iteration " + str(iternum) + ".")
    if(int(iternum) <= 0):
      # If we're using 0 or less, we're using the pretrained model.
      # If so, we need to adjust becuase it was trained in tf1 and
      # we're using tf2. 
      tf.compat.v1.disable_v2_behavior()
      self.model = tf.compat.v1.keras.models.load_model(self.models_path + '/tr_model_'+str(iternum) +'.h5')
    else:
      # Load our model with tf2. 
      self.model = load_model(self.models_path + '/tr_model_'+str(iternum) +'.h5')
    if(self.model is None):
      print('[ERROR] Unable to load Trigger Word Detection model. Path: '+self.models_path +'/tr_model_'+str(iternum) +'.h5.')
      return False
    self.iternum = iternum
    return True

  # Listens for a single command and executes acceptable ones accordingly. 
  def listen_hotword(self):
    print("[INFO] Initializing Hotword Detection...")
    if self.model is None:
      print("[ERROR] No Trigger Word Detection model loaded!")
      return
    stream = self.get_audio_input_stream(self.callback)
    stream.start_stream()
    print("[INFO] Now listening for Trigger Word with model iteration " + str(self.iternum) + ".")
    # Audio cue for the user upon startup. 
    self.speech_speak.background_speak_event(event_type="execute_startup")
    try:
      # Primary listening loop. Application should spend most of it's
      # lifetime in here. 
      while self.active_loop and self.interaction_active.stop_server is False:
        # Halt indefinitely if the speech_listen is triggered by
        # another thread. Check every second to see if they've
        # finished. When it's finished, restart the stream. 
        stream_stopped = False
        while self.speech_listen.speech_listen_active is True:
          if stream_stopped is False: 
            # Only output one message. 
            print("[DEBUG] Trigger Word Parsing halted: Speech Listen called from another thread.")
          stream.stop_stream()
          stream.close()
          stream_stopped = True
          time.sleep(1)
        if stream_stopped is True:
          # Once the command loop finishes. resume.
          stream = self.get_audio_input_stream(self.callback)
          stream.start_stream()
          print("[DEBUG] Trigger Word Parsing resumed: Speech Listen in different thread terminated.")

        data = self.q.get()
        spectrum = self.get_spectrogram(data)
        preds = self.detect_triggerword_spectrum(spectrum)
        new_trigger = self.has_new_triggerword(preds, self.chunk_duration, self.feed_duration, self.activation_threshold)
        if new_trigger:
          print('1')
          # Plunges code into server logic loop. 
          print("[INFO] Trigger Word recognized!")
          # Stop the stream momentarily. 
          stream.stop_stream()
          stream.close()
          self.interaction_active.listen_for_command()
          # Once the command loop finishes. resume.
          stream = self.get_audio_input_stream(self.callback)
          stream.start_stream()
    except (KeyboardInterrupt, SystemExit):
      self.active_loop = False
    stream.stop_stream()
    stream.close()
    # Execute a shutdown chime. Blocking, so we can make sure it
    # finishes before we shutdown fully. 
    self.speech_speak.blocking_speak_event(event_type="execute_shutdown")
    return

  # Audio parsing callback. 
  def callback(self, in_data, frame_count, time_info, status):
    data0 = np.frombuffer(in_data, dtype='int16')
    if np.abs(data0).mean() < self.silence_threshold:
      print('-', end='')
      return (in_data, pyaudio.paContinue)
    else:
      print('.', end='')
    self.data = np.append(self.data,data0)    
    if len(self.data) > self.feed_samples:
      self.data = self.data[-self.feed_samples:]
      # Process data async by sending a queue.
      self.q.put(self.data)
    return (in_data, pyaudio.paContinue)
  
  # Predicts the location of the trigger word. Expects the shape of the
  # spectrum in a tuple (freqs, Tx) - number of frequencies, the 
  # number of timestamps. 
  def detect_triggerword_spectrum(self, x):
    # the spectogram outputs  and we want (Tx, freqs) to input into the model
    x  = x.swapaxes(0,1)
    x = np.expand_dims(x, axis=0)
    predictions = self.model.predict(x)
    return predictions.reshape(-1)

  # Detects whether the latest chunk of input audio contains a trigger word. 
  # Looks to see if the "rising edge" of the prediction data belongs to the 
  # latest chunk. 
  #
  # Expects labeled predictions from the model, time in each chunk, time in 
  # each second of input, and the threshold for the probability to be 
  # considered probablity (default 1/2). Returns True if found.
  def has_new_triggerword(self, predictions, chunk_duration, feed_duration, threshold=0.5):
    predictions = predictions > threshold
    chunk_predictions_samples = int(len(predictions) * chunk_duration / feed_duration)
    chunk_predictions = predictions[-chunk_predictions_samples:]
    level = chunk_predictions[0]
    for pred in chunk_predictions:
      if pred > level:
        return True
      else:
        level = pred
    return False

  # Standard function to execute fourier transform on an audio stream,
  # producing a frequency spectrogram that we can then submit to the model. 
  #
  # Uses mlab. 
  def get_spectrogram(self, data):
    nfft = 200 # Length of each window segment
    fs = 8000 # Sampling frequencies
    noverlap = 120 # Overlap between windows
    nchannels = data.ndim
    if nchannels == 1:
        pxx, _, _ = mlab.specgram(data, nfft, fs, noverlap = noverlap)
    elif nchannels == 2:
        pxx, _, _ = mlab.specgram(data[:,0], nfft, fs, noverlap = noverlap)
    return pxx

  # Initial stream definition. Expects the callback function. 
  def get_audio_input_stream(self, callback):
    # Try multiple times - this depends on the hardware. 
    # We take the scatterblast approach. 
    max_channels_tested = 5
    max_input_device_indices_tested = 5
    stream = None
    for i in range(1, max_channels_tested):
      for j in range(0, max_input_device_indices_tested):
        if stream is None:
          try:
            stream = pyaudio.PyAudio().open(
              format=pyaudio.paInt16,
              channels=i,
              rate=self.fs,
              input=True,
              frames_per_buffer=self.chunk_samples,
              input_device_index=j,
              stream_callback=callback)
          except:
            stream = None

    assert stream is not None

    return stream