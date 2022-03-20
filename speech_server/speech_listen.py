#
# speech_listen.py
#
# Implements verbal input from the user utilizing assorted speech 
# recognition methods. A single static class should be utilized for
# all speech_server interactions. 
#
# Requries a SpeechSpeak object to be passed on initialization, 
# utilized in the case that a prompt is passed to listen_for_response.

import speech_recognition as sr
import time

class SpeechListen:
  led_state_on = None
  led_state_off = None
  led_room_id = None
  led_action_id = None

  r2 = None
  speech_speak = None
  web_server_status = None

  # A flag for hotword_trigger_word to halt operations in the case
  # that a separate thread is using the microphone. 
  speech_listen_active = False

  # An list of timestamps that serve as unique IDs for events that
  # must be queued. 
  speech_listen_queued = []

  # Configuration parameters
  default_pause_threshold = 1.0
  default_max_response_attempts = 1
  default_response_timeout = 5
  default_response_phrase_timeout = 5
  default_ambient_noise_duration = 0.3

  def __init__(self, speech_speak, web_server_status, led_state_on, led_state_off, led_room_id, led_action_id):
    self.speech_speak = speech_speak
    self.r2 = sr.Recognizer()
    self.web_server_status = web_server_status

    self.led_state_on = led_state_on
    self.led_state_off = led_state_off
    self.led_room_id = led_room_id
    self.led_action_id = led_action_id

  # Attempt to listen for valid text using Google speech recogntiion.
  # Returns valid text if recieved and None if not recieved. 
  # May provide a verbal prompt every loop. Can be specified with a
  # sleep duration (how long to wait before starting to listen)
  #
  # Can also take in a delay before attempting to take control of
  # the microphone - useful for other threads that need to wait for
  # hotword_tirgger_word to release the mic stream. Delay is in 
  # seconds (float).
  #
  # In the edge case of multiple threads attempting to listen at the
  # same time, this function blocks the calling thread until the
  # active interaction completes. 
  def listen_response(self, prompt = None, indicate_led = True, execute_chime = False, pause_threshold = None, max_response_attempts = None, response_timeout = None, response_phrase_timeout = None, ambient_noise_duration = None, start_delay = None):
    user_response_text = None

    if len(self.speech_listen_queued) > 0:
      # Another thread is currently using this function. Insert
      # a ticket and wait for your name to be called. Your unique
      # id is the current system time down to the ms. Events coming
      # in on the same ms is an edge case we're accepting. 
      timestamp = round(time.time() * 1000)
      self.speech_listen_queued.append(timestamp)
      print("[DEBUG] Blocking thread given that Speech Listen is currently active.")
      while self.speech_listen_queued[0] != timestamp:
        # Block the thread and wait until you are first in line 
        # and the function is no longer in use. 
        time.sleep(0.10)
      # Clear yourself from the list. 
      print("[DEBUG] Thread block lifted given that Speech Listen is no longer active.")
    else:
      # Insert yourself into the empty speech_listen_queued. Since
      # there's only one of us, there's no need for a unique ID. 
      self.speech_listen_queued.append("-1") 

    # Inidicate that we're active. Tells the hotword parsing to 
    # stop listening if we're being called from a separate thread.
    self.speech_listen_active = True

    if start_delay is not None:
      print("[DEBUG] Speech Listen pausing for " + str(start_delay) + " seconds.")
      time.sleep(start_delay)

    # Use defaults if not specified by the caller. 
    if pause_threshold is None:
      pause_threshold = self.default_pause_threshold
    if max_response_attempts is None:
      max_response_attempts = self.default_max_response_attempts
    if response_timeout is None:
      response_timeout = self.default_response_timeout
    if response_phrase_timeout is None:
      response_phrase_timeout = self.default_response_phrase_timeout
    if ambient_noise_duration is None:
      ambient_noise_duration = self.default_ambient_noise_duration

    self.r2.pause_threshold = pause_threshold

    with sr.Microphone() as source2:
      self.r2.adjust_for_ambient_noise(source2, duration=ambient_noise_duration)

      # Try for as many attempts as allowed. 
      for i in range(max_response_attempts): 
        try:
          if prompt is not None:
            # Prompt the user each loop attempt if specified. 
            self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=prompt)
          if execute_chime is True:
            self.speech_speak.background_speak_event(event_type="execute_chime")

          # Attempt to have the speech speak indicate listening emotion
          # given emotion representation "frontend".
          self.speech_speak.background_speak_event(event_type="emote", event_content="listen")

          # Indicate that you are currently active. 
          if indicate_led is True:
            self.web_server_status.query_speech_server_module_toggle(self.led_state_on, self.led_room_id, self.led_action_id)

          use_google = self.web_server_status.online_status is True

          if use_google is True: print("[INFO] Speech Listen (Online: Google) now awaiting user response...")
          else: print("[INFO] Speech Listen (Offline: Pocket Sphinx) now awaiting user response...")

          start = time.time()
          audio2 = self.r2.listen(source2, timeout=response_timeout,phrase_time_limit=response_phrase_timeout)
          if use_google is True:
            # Use Google's API to recognize the audio.
            user_response_text = self.r2.recognize_google(audio2)
          else:
            # Use offline CMU Sphinx recognizer
            user_response_text = self.r2.recognize_sphinx(audio2)
          # String cleanup
          user_response_text = user_response_text.lower()
          end = time.time()
          print("[INFO] Recognized response audio: '" + user_response_text + "' in " + str(end-start) + " ")
          # All done, let's return the text. 
          break
        except sr.RequestError as e:
          print("[ERROR] Speech Listen could not request results from speech_recognition; {0}.format(e)")
        except sr.UnknownValueError:
          print("[WARNING] Speech Listen did not understand the last sentence.")
        except sr.WaitTimeoutError:
          print("[WARNING] Speech Listen limeout occured.")

      # Indicate that you are currently inactive. 
      if indicate_led is True:
        self.web_server_status.query_speech_server_module_toggle(self.led_state_off, self.led_room_id, self.led_action_id)
      
      # Attempt to have the speech speak show idle anmiation
      # given emotion representation "frontend".
      self.speech_speak.background_speak_event(event_type="emote_stop")
  
    # All done. Disable the flag and let the hotword parsing continue.
    # Note however that if we were not the only one in the queue someone
    # else is going to be using this function right after, so don't
    # let hotword parsing continue and just exit. 
    del self.speech_listen_queued[0] 
    if len(self.speech_listen_queued) == 0:
      self.speech_listen_active = False

    return user_response_text