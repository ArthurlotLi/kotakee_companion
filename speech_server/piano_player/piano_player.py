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

# Avoid the pygame welcome prompt. 
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
import base64
from pathlib import Path
import time
import json

class PianoPlayer:
  # Cloud inference. 
  _cloud_inference_api = "/performMidi"

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

    # Machine Pianist Inference, if enabled. Cloud inference or local.
    use_temp_file = False
    if self._machine_pianist_utility is not None:
      temp_file = self.cloud_perform_midi(Path(location))
      if temp_file is None:
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

    # Machine Pianist Inference, if enabled. Cloud inference or local.
    use_temp_file = False
    if self._machine_pianist_utility is not None:
      temp_file = self.cloud_perform_midi(Path(location))
      if temp_file is None:
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

  def cloud_perform_midi(self, midi_file: Path):
    """
    Given a midi to perform, let the cloud inference server do the
    heavy lifting and perfomr the song. To do that, use base64 encoding
    on both ends. From an outside perspective, acts exactly the same
    as the perform_midi function. 

    Returns None or the location of the correctly performed midi in a
    temporary file. 
    """
    assert self.web_server_status is not None
    if self.web_server_status.cloud_inference_status is True:
      try:
        inference_start = time.time()
        with open(str(midi_file), "rb") as midi_file:
          # Encode the midi as a base 64 string so that it can be sent over POST.
          encoded_midi_file = base64.b64encode(midi_file.read())
          data_to_send = {
            "midi":str(encoded_midi_file, "utf-8"),
            "generate_wav": 0
          }
          query = self.web_server_status.cloud_inference_address + self._cloud_inference_api
          query_start = time.time()

          response = self.web_server_status.execute_post_query(
            query, 
            data_to_send = data_to_send,
            timeout= None,
            verbose=False)
          print("[DEBUG] PianoPlayer - Cloud inference query round trip took %.2f seconds." % (time.time() - query_start))

          if response is not None:
            response_dict = json.loads(response.text)
            decoding_start = time.time()
            #print(response_dict)
            assert len(response_dict) == 1
            for item in response_dict:
              decoded_midi_file = base64.b64decode(response_dict[item])
            new_song_file = open(self._machine_pianist_temp_file, "wb")
            new_song_file.write(decoded_midi_file)
            new_song_file.close()
            print("[DEBUG] PianoPlayer - Cloud inference decoding procedure took %.2f seconds." % (time.time() - decoding_start))
            print("[DEBUG] PianoPlayer - Total cloud inference time: %.2f seconds." % (time.time() - inference_start))
            return self._machine_pianist_temp_file

      except Exception as e:
        print("[WARNING] PianoPlayer - Error when executing Cloud Inference:")
        print(e)
    
    return None