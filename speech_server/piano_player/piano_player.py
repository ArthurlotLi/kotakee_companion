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

import pygame
import base64

class PianoPlayer:

  # Passed by calling modules, whether active or passive. This
  # Allows us to send post queries with the midi file over to the
  # web server. 
  web_server_status = None

  def __init__(self, web_server_status):
    print("[DEBUG] Initializing PianoPlayer...")
    pygame.init()
    self.web_server_status = web_server_status
    print("[DEBUG] PianoPlayer initialized successfully.")

  # Given a directory path, load and play a midi file locally on
  # this computer. 
  def local_load_and_play(self, location, block=False):
    print("[INFO] PianoPlayer playing song located: " + str(location) + ".")
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

  # Given a directory path, load a midi file and send it over HTTP
  # POST to the web server so that it can play it on the connected
  # Yamaha. 
  def send_midi_to_web_server(self, location):
    if self.web_server_status.web_server_status is False:
      print("[WARNING] PianoPlayer unable to send song to web server - web server not connected. Using virtual play.")
      self.local_load_and_play(location)
    else:
      print("[INFO] PianoPlayer sending song located at: "+ str(location) + " to web server.")

      try:
        with open(location, "rb") as midi_file:
          # Encode the midi as a base 64 string so that it can be sent over POST.
          encoded_midi_file = base64.b64encode(midi_file.read())
          data_to_send = {
            "song_name":location.rsplit("/",1)[1].replace(".mid", "").replace(" ", "_"), # Just leave the complete song name. Replace all spaces.
            "midi_contents":str(encoded_midi_file, "utf-8")
          }

          self.web_server_status.query_speech_server_piano_play(data_to_send=data_to_send)
      except Exception as e:
        print("[ERROR] PianoPlayer was unable to transmit song from location '" + str(location) + "'. Exception: ")
        print(e)
