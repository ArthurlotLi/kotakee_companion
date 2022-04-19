# 
# piano_player.py
#
# Given a MIDI file, play the song either virtually on the speech
# server itself, or send the song to the web server (if connected)
# to play on the Yamaha piano over USB via MIDI in. Utilizes
# the Mido python library. 
# 
# With this player, any piano songs generated as part of the 
# Kotakee generative piano ML solutions may be played seamlessly
# without human intervention. 
#
# Westworld who? 

from machine_pianist_utility import MachinePianistUtility

import pygame
import base64
import os
from pathlib import Path

class PianoPlayer:

  # Enables the use of the machine pianist to "perform" songs, adding
  # human-like performance data.
  _use_machine_pianist = True
  _machine_pianist_model_path = "../../machine_pianist/production_models/model1/machine_pianist.h5"
  _machine_pianist_inference_folder = "../../machine_pianist/machine_pianist_inference"
  _machine_pianist_inference_class = "MachinePianist"
  _machine_pianist_utility = None
  _machine_pianist_temp_file = "temp_file_midi"

  # Passed by calling modules, whether active or passive. This
  # Allows us to send post queries with the midi file over to the
  # web server. 
  web_server_status = None

  def __init__(self, web_server_status):
    print("[DEBUG] PianoPlayer - Initializing PianoPlayer...")
    pygame.init()
    self.web_server_status = web_server_status

    if self._use_machine_pianist is True:
      print("[DEBUG] PianoPlayer - Machine Pianist enabled: loading Machine Pianist Utility.")
      self._machine_pianist_utility = MachinePianistUtility(model_path=self._machine_pianist_model_path,
                                                            inference_folder=self._machine_pianist_inference_folder,
                                                            inference_class= self._machine_pianist_inference_class)
    print("[DEBUG] PianoPlayer - Initialized successfully.")

  # Given a directory path, load and play a midi file locally on
  # this computer. 
  def local_load_and_play(self, location, block=False):
    print("[INFO] PianoPlayer playing song located: " + str(location) + ".")

    # Machine Pianist Inference, if enabled. 
    use_temp_file = False
    if self._machine_pianist_utility is not None:
      temp_file = self._machine_pianist_utility.perform_midi(Path(location), Path(self._machine_pianist_temp_file))
      if temp_file is not None:
        location = temp_file
        use_temp_file = True

    try:
      pygame.mixer.music.load(location)
      pygame.mixer.music.play()
      if block:
        # If we're blocking, wait until we're done. 
        print("[DEBUG] PianoPlayer blocking until song complete...")
        while pygame.mixer.music.get_busy():
          pygame.time.wait(500)
        print("[DEBUG] PianoPlayer song complete.")
    except Exception as e:
      print("[ERROR] PianoPlayer was unable to locally play song from location '" + str(location) + "'. Exception: ")
      print(e)

    # Remove the temp file after it's been used.
    if use_temp_file:
      os.remove(location)

  # Given a directory path, load a midi file and send it over HTTP
  # POST to the web server so that it can play it on the connected
  # Yamaha. 
  def send_midi_to_web_server(self, location):
    if self.web_server_status.web_server_status is False:
      print("[WARNING] PianoPlayer unable to send song to web server - web server not connected. Using virtual play.")
      self.local_load_and_play(location)
      return

    print("[INFO] PianoPlayer sending song located at: "+ str(location) + " to web server.")

    # Machine Pianist Inference, if enabled. 
    use_temp_file = False
    if self._machine_pianist_utility is not None:
      temp_file = self._machine_pianist_utility.perform_midi(Path(location), Path(self._machine_pianist_temp_file))
      if temp_file is not None:
        location = temp_file
        use_temp_file = True

    try:
      with open(location, "rb") as midi_file:
        # Encode the midi as a base 64 string so that it can be sent over POST.
        encoded_midi_file = base64.b64encode(midi_file.read())
        data_to_send = {
          "song_name":Path(location).name.replace(".mid", "").replace(" ", "_"), # Just leave the complete song name. Replace all spaces.
          "midi_contents":str(encoded_midi_file, "utf-8")
        }

        self.web_server_status.query_speech_server_piano_play(data_to_send=data_to_send)
    except Exception as e:
      print("[ERROR] PianoPlayer was unable to transmit song from location '" + str(location) + "'. Exception: ")
      print(e)

    # Remove the temp file after it's been used.
    if use_temp_file:
      os.remove(location)