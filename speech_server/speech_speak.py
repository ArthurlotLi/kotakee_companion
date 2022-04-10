#
# speech_speak.py
#
# Implements verbal output to the user utilizing pyttsx3 module for 
# speech synthesis. A single static class should be utilized for all 
# speech_server interactions. 
#
# Manages a single thread with a queue, handling the edge case of 
# multiple threads requesting to speak or output sounds at the same 
# time. 
#
# All interactions should occur via the speak thread - none of the
# other methods in this class should be called directly to avoid
# threading issues with pyaudio and to handle race conditions properly.
#
# Utilizes multiprocessing to execute pyttsx3 interactions. Required
# in order to iteratively execute text output without blocking and 
# also without initializing the engine needlessly (which has 
# significant overhead). In this respect, the overhead for socket
# interactions with the subprocess is preferred. 

from subprocess import Popen, PIPE
from multiprocessing.connection import Client
import threading
import wave
import pyaudio
import time
import sys

class SpeechSpeak:
  # We use multiprocessing to output pyttsx3 text.
  subprocess_location = "speech_speak_subprocess.py"
  subprocess_address = "localhost"
  subprocess_port = 0 # OS Selected - we expect this from the subprocess on startup. 
  subprocess_key = b"speech_speak"
  subprocess_instance = None
  subprocess_shutdown_code = "SHUTDOWN" # No incoming text should be uppercase. 

  # Addressing the command line call to execute the subprocess.
  # Try using python3 first, and if that fails, remember and use
  # python instead.
  use_python3 = True

  # Primary thread that executes all output. Any requests that 
  # come in must come in via the speech_speak_events thread and
  # will be processed first-come-first-served.
  speak_thrd_instance = None

  # Like-indexed lists that act as a joint queue for incoming
  # speak events. event_types provides the event type, while 
  # event_contents is optional depending on the type. 
  speak_thrd_event_types = []
  speak_thrd_event_contents = []
  speak_thrd_tick = 0.10 # How many seconds the thread sleeps for. 
  speak_thrd_stop = False

  chime_location = None
  startup_location = None
  shutdown_location = None
  timer_location = None
  alarm_location = None
  wait_location = None

  web_server_status = None

  # Emotion detection + representation classes and instances. 
  emotion_detection_representation_enabled = False
  emotion_detection_model_num = None
  emotion_detection_location = None
  emotion_representation_location = None
  emotion_representation_media_location = None
  emotion_detection_class_name = None
  emotion_representation_class_name = None
  emotion_detection_model_variants_location = None
  # Time in seconds to process and send the subprocess a new video 
  # location - this allows us to update the idle animation (if
  # enabled) so that daylight may tick over to sunset and to
  # night, etc. If the video is the same location in the subprocess,
  # the subprocess will not make any further action. 
  emotion_representation_update_idle_duration = 60
  emotion_detection_class = None
  emotion_representation_class = None
  emotion_detection = None
  emotion_representation = None

  # Multispeaker Text To Speech Synthesis calsses and instances.
  multispeaker_synthesis_enabled = False
  multispeaker_synthesis = None
  multispeaker_synthesis_class = None
  multispeaker_synthesis_location = None
  multispeaker_synthesis_class_name = None
  multispeaker_synthesis_inference_location = None
  multispeaker_synthesis_inference_class_name = None
  multispeaker_synthesis_model_num = None
  multispeaker_synthesis_speaker = None
  multispeaker_synthesis_models_location = None
  multispeaker_synthesis_speakers_location = None

  def __init__(self, web_server_status, chime_location, startup_location, shutdown_location, timer_location, alarm_location, wait_location,
               emotion_detection_location, emotion_detection_class_name, emotion_detection_model_variants_location,
               emotion_representation_location, emotion_representation_class_name,
               emotion_representation_media_location, 
               multispeaker_synthesis_location, multispeaker_synthesis_class_name,
               multispeaker_synthesis_inference_location, multispeaker_synthesis_inference_class_name,
               multispeaker_synthesis_models_location, multispeaker_synthesis_speakers_location,
               use_python3 = True, 
               emotion_detection_model_num = -1, 
               use_emotion_representation = True, 
               use_emotion_representation_reduced = False, 
               use_multispeaker_synthesis = True,
               multispeaker_synthesis_model_num = -1,
               multispeaker_synthesis_speaker = None):

    self.web_server_status = web_server_status

    self.chime_location = chime_location
    self.startup_location = startup_location
    self.shutdown_location = shutdown_location
    self.timer_location = timer_location
    self.alarm_location = alarm_location
    self.wait_location = wait_location

    self.use_python3 = use_python3
    self.use_emotion_representation_reduced = use_emotion_representation_reduced

    self.emotion_detection_model_num = emotion_detection_model_num
    self.emotion_detection_location = emotion_detection_location
    self.emotion_detection_class_name = emotion_detection_class_name
    self.emotion_representation_location = emotion_representation_location
    self.emotion_representation_class_name = emotion_representation_class_name
    self.emotion_detection_model_variants_location = emotion_detection_model_variants_location
    self.emotion_representation_media_location = emotion_representation_media_location

    self.multispeaker_synthesis_location = multispeaker_synthesis_location
    self.multispeaker_synthesis_class_name = multispeaker_synthesis_class_name
    self.multispeaker_synthesis_inference_location = multispeaker_synthesis_inference_location
    self.multispeaker_synthesis_inference_class_name = multispeaker_synthesis_inference_class_name
    self.multispeaker_synthesis_model_num = multispeaker_synthesis_model_num
    self.multispeaker_synthesis_speaker = multispeaker_synthesis_speaker
    self.multispeaker_synthesis_models_location = multispeaker_synthesis_models_location
    self.multispeaker_synthesis_speakers_location = multispeaker_synthesis_speakers_location

    # Emotion Detection + Representation.
    if (self.intTryParse(self.emotion_detection_model_num) and int(self.emotion_detection_model_num) < 0) or use_emotion_representation is False:
      # Disable emotion detection.
      print("[DEBUG] Emotion Detection + Representation disabled for Speech Server.")
    else:
      print("[DEBUG] Importing Emotion Detection + Representation classes.")
      self.emotion_detection_class = self.load_class(module_name=self.emotion_detection_location, 
                                                     class_name=self.emotion_detection_class_name)
      self.emotion_representation_class = self.load_class(module_name=self.emotion_representation_location, 
                                                          class_name=self.emotion_representation_class_name)
      if self.emotion_detection_class is not None and self.emotion_representation_class is not None:
        print("[DEBUG] Initializing Emotion Detection + Representation.")
        self.emotion_detection = self.emotion_detection_class(model_num=self.emotion_detection_model_num, 
                                                              model_variants_location=emotion_detection_model_variants_location)
        self.emotion_representation = self.emotion_representation_class(use_python3=self.use_python3, 
                                                                        use_emotion_representation_reduced = self.use_emotion_representation_reduced,
                                                                        emotion_videos_location = emotion_representation_media_location)
        # Successful initialization.
        self.emotion_detection_representation_enabled = True
      else:
        print("[ERROR] Failed to import Emotion Detection + Representation.")

    # Multispeaker Text-To-Speech Synthesis
    if use_multispeaker_synthesis is False or (self.intTryParse(self.multispeaker_synthesis_model_num) and int(self.multispeaker_synthesis_model_num) < 0):
      # Disable multispeaker synthesis
      print("[DEBUG] Multispeaker Synthesis disabled for Speech Server.")
    else:
      print("[DEBUG] Importing Multispeaker Synthesis class.")
      self.multispeaker_synthesis_class = self.load_class(module_name=self.multispeaker_synthesis_location, 
                                                          class_name=self.multispeaker_synthesis_class_name)
      if self.multispeaker_synthesis_class is not None:
        print("[DEBUG] Initializing Multispeaker Synthesis.")
        self.multispeaker_synthesis = self.multispeaker_synthesis_class(model_num=self.multispeaker_synthesis_model_num,
                                                                        model_variants_location = self.multispeaker_synthesis_models_location,
                                                                        speakers_location = self.multispeaker_synthesis_speakers_location,
                                                                        inference_location = multispeaker_synthesis_inference_location,
                                                                        inference_class_name = multispeaker_synthesis_inference_class_name,
                                                                        web_server_status = web_server_status)
        # Successful initialization.
        self.multispeaker_synthesis_enabled = True
      else:
        print("[ERROR] Failed to import Multispeaker Synthesis.")

    # Initialize pyttsx3 subprocess if we are not using multispeaker 
    # synthesis. 
    if self.multispeaker_synthesis_enabled is False:
      if self.initialize_subprocess() is False:
        print("[ERROR] Failed to initialize subprocess. Speech Server initialization failed.")  
        return

    # Get the show on the road!
    self.initialize_speak_thrd()

    # Submit a request to ourselves to display idle animation.
    if self.emotion_detection_representation_enabled and (use_emotion_representation_reduced is False):
      self.background_speak_event(event_type="emote_stop")

    print("[DEBUG] Speech Server initialization complete.")

  # Initializes the subprocess.
  def initialize_subprocess(self):
    # Use subprocess Popen as we don't want to block for a 
    # process we want to keep running. We'll interact with it
    # using multiprocessing's wrapped sockets. 

    if self.use_python3 is True:
      self.subprocess_instance = Popen(["python3", self.subprocess_location, ""], stdout=PIPE, bufsize=1, universal_newlines=True)
    else:
      self.subprocess_instance = Popen(["python", self.subprocess_location, ""], stdout=PIPE, bufsize=1, universal_newlines=True)

    print("[DEBUG] Speak Text subprocess spawned successfully.")
    self.wait_for_subprocess_port()

    return True

  # Read the stdout of the subprocess until we get a complete port. 
  # output should be terminated by / character. Ex) 42312/
  def wait_for_subprocess_port(self):
    print("[DEBUG] Waiting for subprocess port number...")
    read_full_output = False
    complete_output = ""
    while read_full_output is False:
      output = self.subprocess_instance.stdout.readline()
      if output:
        complete_output = complete_output + output
        if "/" in complete_output:
          port_number = int(complete_output.replace("/", ""))
          print("[DEBUG] Successfully recieved subprocess port number: " + str(port_number))
          self.subprocess_port = port_number
          read_full_output = True
          return True
    return False
    
  def shutdown_process(self):
    print("[DEBUG] Speak Text shutting down existing process.")
    # Socket interaction using multiprocessing library. 
    address = (self.subprocess_address, self.subprocess_port)
    connection = Client(address, authkey=self.subprocess_key)
    connection.send(self.subprocess_shutdown_code)
    connection.close()

  # Kicks off the thread. 
  def initialize_speak_thrd(self):
    print("[DEBUG] Starting Speak Thread.")
    self.speak_thrd_instance = threading.Thread(target=self.speak_thrd, daemon=True).start()

  # Primary function that allows other classes to append new events
  # for the thread to process in due time. Importantly, this method
  # BLOCKS their respective processing until it has been completed. 
  # An alternate method is available for non-blocking processing
  # called background_speak_event.
  def blocking_speak_event(self, event_type, event_content=None):
    print("[DEBUG] Creating new blocking speak event of type '" + event_type + "'.")
    self.speak_thrd_event_types.append(event_type)
    self.speak_thrd_event_contents.append(event_content)

    # Wait for the thread to execute all events. 
    while len(self.speak_thrd_event_types) > 0:
      time.sleep(0.1) # Check every 100ms until we're finished.

    print("[DEBUG] Speak event queue clean. Blocking operation complete.") 

  # Non-blocking processing. Kick it off and let it run - useful for
  # operations like playing sounds that don't have any immediate
  # follow-ups. 
  def background_speak_event(self, event_type, event_content=None):
    print("[DEBUG] Creating new background speak event of type '" + event_type + "'.")
    self.speak_thrd_event_types.append(event_type)
    self.speak_thrd_event_contents.append(event_content)

  # Shuts down both the thread and the process. Blocking behavior
  # ensures that the process is fully shut down before we close. 
  def shutdown_speak_thrd(self):
    self.speak_thrd_stop = True
    self.shutdown_process()
    if self.emotion_representation is not None:
      self.emotion_representation.shutdown_process()

  def list_all_speakers(self):
    """
    For multispeaker synthesis, make the speaker list available here.
    """
    if self.multispeaker_synthesis_enabled:
      return self.multispeaker_synthesis.list_all_speakers()
    else:
      return []

  # The Speak thread. Loops every 'tick' seconds and checks if any 
  # events needs to occur. 
  def speak_thrd(self):
    time_next_idle_update = time.time() + self.emotion_representation_update_idle_duration
    while self.speak_thrd_stop is False:

      # Clear the executed events once done. We don't just clear the
      # entire array at the end in the edge case that a new event 
      # comes in during the for loop. (More likely if executing
      # long strings of text.)
      indices_to_drop = []

      # Handle everything in the queue. 
      for i in range(0, len(self.speak_thrd_event_types)):
        event_type = self.speak_thrd_event_types[i]
        event_content = self.speak_thrd_event_contents[i]
        self.handle_speak_event(event_type = event_type, event_content = event_content)
        indices_to_drop.append(i)

      # Clear the queue once completed. Go backwards from the back
      # of the to-delete list.
      for i in range(len(indices_to_drop)-1, -1, -1):
        del self.speak_thrd_event_types[indices_to_drop[i]]
        del self.speak_thrd_event_contents[indices_to_drop[i]]

      # Handle idle animation update.
      if self.emotion_detection_representation_enabled:
        # Only update if it's time AND the emotion
        current_time = time.time()
        if current_time >= time_next_idle_update :
          if self.emotion_representation.subprocess_emotion_state == "idle1":
            self.emote_stop()
          time_next_idle_update = current_time + self.emotion_representation_update_idle_duration
      
      time.sleep(self.speak_thrd_tick)
      
    # Shutdown has occured. Stop the process.
    print("[DEBUG] Speech Thread closed successfully. ")

  # Given an event type (string) and event_content (can be None),
  # execute the action. 
  def handle_speak_event(self, event_type, event_content):
    if event_type == "speak_text":
      if self.multispeaker_synthesis_enabled:
        self.synthesize_text(event_content)
      else:
        self.speak_text(event_content)
    elif event_type == "change_speaker":
      self.change_multispeaker_synthesis_speaker(event_content)
    elif event_type == "emote":
      self.emote(event_content)
    elif event_type == "emote_stop":
      self.emote_stop()
    elif event_type == "emote_clear":
      self.emote_clear()
    elif event_type == "execute_startup":
      self.execute_startup()
    elif event_type == "execute_shutdown":
      self.execute_shutdown()
    elif event_type == "execute_chime":
      self.execute_chime()
    elif event_type == "execute_timer":
      self.execute_timer()
    elif event_type == "execute_alarm":
      self.execute_alarm()
    elif event_type == "execute_waiting":
      self.execute_waiting()
    else:
      print("[ERROR] Speak thrd recieved an unknown event type '" + str(event_type)+ "'!")

  def change_multispeaker_synthesis_speaker(self, new_speaker):
    """
    Allows for the user to select a new speaker. 
    """
    if self.multispeaker_synthesis_enabled:
      new_speaker = new_speaker.upper()

      # Allow random speakers functionality to be enabled here. 
      if new_speaker == "RANDOM SINGLE" or new_speaker == "SINGLE RANDOM":
        new_speaker = self.multispeaker_synthesis.random_speaker()
        speaker_exists = True
      elif new_speaker == "RANDOM":
        speaker_exists = True
      else:
        new_speaker = self.multispeaker_synthesis.replace_common_misdetections(new_speaker)
        speaker_exists = self.multispeaker_synthesis.check_speaker_exists(new_speaker)
        
      if speaker_exists:
        self.multispeaker_synthesis_speaker = new_speaker
        self.synthesize_text("Okay companion speaker has been changed to %s." % new_speaker)
      else:
        self.synthesize_text("I'm sorry, I wasn't able to find a speaker called %s." % new_speaker)

  # Converts text to speech using multispeaker synthesis project.
  # Emotion Detection may be used in this routine for two reasons -
  # Emotion Representation or to inject an emotion prior into the 
  # speaker synthesis process. 
  def synthesize_text(self, output_text):
    if(output_text is not None and output_text != ""):
      print("[DEBUG] Speech Speak - Synthesizing output text: \"%s\"." % (output_text))

      # Ping a noise to indicate that we're processing the output
      # text. 
      self.execute_waiting()

      emotion_category = "neutral"

      if False is True: # TODO: Enable this if statement if emotion priors are enabled.
        emotion_category = self._emotion_detection_representation(output_text, represent=False)
      
      # First try inference with the cloud inference server. If it
      # has been disabled or we're not connected, wavs will be
      # None. 
      wavs = self.multispeaker_synthesis.cloud_synthesize_speech(texts=[output_text], 
                                                                 speaker_id = self.multispeaker_synthesis_speaker,
                                                                 utterance_id = emotion_category)
      if wavs is None:
        wavs = self.multispeaker_synthesis.speaker_synthesize_speech(texts=[output_text], 
                                                                    speaker_id = self.multispeaker_synthesis_speaker,
                                                                    utterance_id = emotion_category)
                                                                    
      # Execute representation.
      # TODO: This should probably happen in a different thread.
      if self.emotion_detection_representation_enabled:
        if False is True:
          self._emotion_detection_representation(output_text, emotion_category = emotion_category)
        else:
          self._emotion_detection_representation(output_text)
    
      self.multispeaker_synthesis.play_wav(wavs)

      self.emote_stop()
      print("[DEBUG] Speak Speak text synthesis complete.")

  # Convert text to speech using pyttsx3 engine. Note calling this by 
  # itself causes a block on the main thread. 
  #
  # Whenever text is executed, if text emotion detection and emotion
  # representation is enabled, a corresponding emotion category will
  # be predicted by the model and represented by a video for the 
  # duration of the video.
  def speak_text(self, output_text):
    if(output_text is not None and output_text != ""):
      print("[DEBUG] Speech Speak executing output text: '"+output_text+"'")

      # Socket interaction using multiprocessing library. 
      address = (self.subprocess_address, self.subprocess_port)
      connection = Client(address, authkey=self.subprocess_key)
      connection.send(output_text)

      # While the text is outputting, predict the emotion category
      # of the text (if enabled)
      if self.emotion_detection_representation_enabled:
        self._emotion_detection_representation(output_text, represent=True)

      # Wait for the subprocess to reply with anything. When you
      # do get that message, continue. Contents are ignored. 
      print("[DEBUG] Speech Speak thread blocking until text execution complete...")    
      start_time = time.time()
      _ = connection.recv()
      # Stop the thread immediately. 
      self.emote_stop()
      connection.close()
      end_time = time.time()
      print("[DEBUG] Speak Speak text output complete. Blocking duration: " + str(end_time-start_time) + " seconds.")

  # Allows for emotion representation to take place. Alternatively, if
  # represent is false, only predicts the emotion and provides the emotion
  # category as a return value. Allows users to specify an emotion
  # category in advance as well.
  def _emotion_detection_representation(self, output_text, represent=True, emotion_category=None):
    start_time = time.time()
    # Pass in sunrise/sunset info from web server. 
    if emotion_category is None:
      emotion_category = self.emotion_detection.predict_emotion(text=output_text)
    if represent:
      sunrise_hours, sunrise_minutes, sunset_hours, sunset_minutes = self.web_server_status.get_sunrise_sunset_time()
      self.emotion_representation.start_display_emotion(
        emotion_category=emotion_category, 
        sunrise_hours=sunrise_hours, 
        sunrise_minutes=sunrise_minutes, 
        sunset_hours=sunset_hours, 
        sunset_minutes=sunset_minutes)
    end_time = time.time()
    print("[DEBUG] Speech Speak Emotion Detection + Representation routine duration: %.4f seconds." % (end_time-start_time))
    return emotion_category

  # Allows other classes to direct emotion representation output.
  # For example, Speech Listen wanting to change the played video
  # to one indicating the server is listening. 
  def emote(self, emotion_category):
    if self.emotion_detection_representation_enabled:
      start_time = time.time()
      # Pass in sunrise/sunset info from web server. 
      sunrise_hours, sunrise_minutes, sunset_hours, sunset_minutes = self.web_server_status.get_sunrise_sunset_time()
      self.emotion_representation.start_display_emotion(
          emotion_category=emotion_category, 
          sunrise_hours=sunrise_hours, 
          sunrise_minutes=sunrise_minutes, 
          sunset_hours=sunset_hours, 
          sunset_minutes=sunset_minutes)
      end_time = time.time()
      print("[DEBUG] Speech Speak Emotion Representation routine duration: " + str(end_time-start_time) + " seconds.")

  # Returns to Idle animation
  def emote_stop(self):
    if self.emotion_detection_representation_enabled:
      # Pass in sunrise/sunset info from web server. 
      sunrise_hours, sunrise_minutes, sunset_hours, sunset_minutes = self.web_server_status.get_sunrise_sunset_time()
      self.emotion_representation.stop_display_emotion(
          sunrise_hours=sunrise_hours, 
          sunrise_minutes=sunrise_minutes, 
          sunset_hours=sunset_hours, 
          sunset_minutes=sunset_minutes)

  # Stops animation and closes window (does not close subprocess)
  def emote_clear(self):
    if self.emotion_detection_representation_enabled:
      self.emotion_representation.clear_display_emotion()

  def execute_startup(self):
    self.execute_sound(self.startup_location)

  def execute_shutdown(self):
    self.execute_sound(self.shutdown_location)

  def execute_chime(self):
    self.execute_sound(self.chime_location)

  def execute_timer(self):
    self.execute_sound(self.timer_location)

  def execute_alarm(self):
    self.execute_sound(self.alarm_location)
  
  def execute_waiting(self):
    self.execute_sound(self.wait_location)

  # Let out a chime to indicate that you're listening. Source:
  # stack overflow
  def execute_sound(self, location):
    chunk = 1024
    f = wave.open(location, "rb")
    p = pyaudio.PyAudio()
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                channels = f.getnchannels(),  
                rate = f.getframerate(),  
                output = True) 
    data = f.readframes(chunk)
    while data:  
      stream.write(data)  
      data = f.readframes(chunk)
    stream.stop_stream()  
    stream.close()  

    #close PyAudio  
    p.terminate()

  # Dunno why this isn't standard. 
  def intTryParse(self, value):
    try:
      int(value)
      return True
    except ValueError:
      return False

  # Dynamic class import. Changes sys.path to navigate directories
  # if necessary. Utilized for emotion detection and
  # representation classes. 
  #
  # Expects module_name Ex) ./home_automation/home_automation
  # and class_name Ex) HomeAutomation
  def load_class(self,  module_name, class_name):
    module = None
    imported_class = None
    module_file_name = None

    # Ex) ./home_automation - split by last slash. 
    # Don't bother if the original file is not within a subdirectory.
    split_module_name = module_name.rsplit("/", 1)
    module_folder_path = split_module_name[0]
    if(module_folder_path != "." and len(split_module_name) > 1):
      sys.path.append(module_folder_path)
      module_file_name = split_module_name[1]
    else:
      module_file_name = module_name.replace("./", "")

    # Fetch the module first.
    try:
      module = __import__(module_file_name)
    except:
      print("[ERROR] Failed to import module " + module_file_name + " from subdirectory '" + module_folder_path + "'.")
      return None

    # Return the class. 
    try:
      imported_class = getattr(module, class_name)
    except:
      print("[ERROR] Failed to import class_name " + class_name + ".")
      return None

    return imported_class