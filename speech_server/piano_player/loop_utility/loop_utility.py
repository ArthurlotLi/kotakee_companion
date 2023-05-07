#
# loop_utility.py
#
# Passive module dynamically added by active module SimpleUtilties
# upon user command. When the event happens, check to see if the
# server is currently playing a song. If not, play the next song
# in line. 

import time
import random

class LoopUtility:
  # Management dict checked via passive_module by the interaction
  # passive thread. If this dict holds an action, the parent of
  # the parent will respond accordingly. 
  module_management = {}

  duration_seconds = 1 # Be responsible and check every _ seconds.
  duration_seconds_after_starting_playing = 40 # We wait this long until seeing if the song has finished playing.
  
  speech_speak = None
  # Passed by calling modules, whether active or passive. This
  # Allows us to send post queries with the midi file over to the
  # web server. 
  web_server_status = None

  virtual = None

  piano_player = None
  songs = None
  piano_songs_location = None
  current_song = 0
  played_songs = 0
  max_songs = None

  def __init__(self, speech_speak, web_server_status):
    self.speech_speak = speech_speak
    self.web_server_status = web_server_status

  # Standard routine in the case that we expect additional data for
  # a passive module instantiated during runtime. 
  def provide_additional_data(self, additional_data):
    self.piano_player = additional_data["piano_player"]
    self.songs = additional_data["songs"]
    self.virtual = additional_data["virtual"]
    self.piano_songs_location = additional_data["piano_songs_location"]
    self.max_songs = additional_data["max_songs"]
    random.shuffle(self.songs)

    assert len(self.songs) > 0

  # Standard routine triggered when the event time is triggered
  # by the passive interaction thread. 
  def activate_event(self):
    print("[INFO] Piano Loop event triggered. Checking if server is playing a song.")

    wait_duration = self.duration_seconds

    # Check if server is playing.
    if self.web_server_status.query_speech_server_piano_status() is False:
      # If not playing, choose a song. 
      # If we need to start from beginning again, shuffle. 
      if self.current_song == len(self.songs):
        self.current_song = 0
        random.shuffle(self.songs)
      else:
        self.current_song += 1

      song_file_to_play = self.songs[self.current_song]

      print("[DEBUG] Piano Loop now playing: %s." % song_file_to_play)
      if self.virtual:
        self.piano_player.local_load_and_play(self.piano_songs_location + "/" + song_file_to_play)
      else:
        self.piano_player.send_midi_to_web_server(self.piano_songs_location + "/" + song_file_to_play)

      self.played_songs+=1
      wait_duration = self.duration_seconds_after_starting_playing

    if self.played_songs < self.max_songs:
      # Keep going. 
      self.module_management["add_module_passive"] = {
        "duration_seconds" : wait_duration
      }
    else:
      print("[DEBUG] Max songs played. All done.")
      self.module_management["clear_module"] = True