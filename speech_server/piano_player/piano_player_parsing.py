#
# piano_player_parsing.py
#
# Active speech_server module that allows for a user to interact
# directly with piano_player, specifying a saved song to be 
# played either on the speech server or on the Yamaha connected
# via USB to the web server (if connected).

import os

from piano_player import PianoPlayer

class PianoPlayerParsing:
  # Paths are relative to where interaction_active is. 
  piano_songs_location = "./piano_player/now_playing"
  
  piano_player = None

  speech_speak = None
  speech_listen = None
  web_server_status = None

  def __init__(self, speech_speak, speech_listen, web_server_status):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status

    self.piano_player = PianoPlayer(web_server_status)

  # Level 1 standard routine. 
  def parse_command(self, command):
    valid_command = False

    # If "virtual" is in command, later on, distinguish between playing
    # the song locally or on the web server. 
    if ("play piano" in command or "play the piano" in command or "play a piano" in command):
      valid_command = True

      # Get all the valid songs in the piano_songs_directory. 
      piano_song_names = []
      piano_song_filenames = []
      piano_songs_contents = os.listdir(self.piano_songs_location)
      for file in piano_songs_contents:
        if file.endswith(".mid") or file.endswith("midi"):
          piano_song_filenames.append(file)
          piano_song_names.append(file.replace(".mid","").replace(".midi",""))

      if len(piano_song_names) == 0:
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="I don't have any piano songs right now.")
      else:
        # Check if the command includes a song name. 
        song_file_to_play = None
        for song_name in piano_song_names:
            if song_file_to_play is None and song_name in command:
              # Found a matching song.
              song_file_to_play = piano_song_filenames[piano_song_names.index(song_name)]

        if song_file_to_play is None:
          # If not, ask the user which file they want to play. 
          piano_song_prompt = "Please pick a song: "
          for song_name in piano_song_names:
            piano_song_prompt = piano_song_prompt + song_name + ", "
          
          user_response = self.speech_listen.listen_response(prompt=piano_song_prompt, execute_chime = True)
          if user_response is not None:
            for song_name in piano_song_names:
              if song_file_to_play is None and song_name in user_response:
                # Found a matching song.
                song_file_to_play = piano_song_filenames[piano_song_names.index(song_name)]
          
        if song_file_to_play is not None:
          # Found a song. Play it.
          if "virtual" in command or "local" in command:
            self.piano_player.local_load_and_play(self.piano_songs_location + "/" + song_file_to_play)
          else:
            self.piano_player.send_midi_to_web_server(self.piano_songs_location + "/" + song_file_to_play)
        else:
          # No song found.
          self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Sorry, I couldn't find that song.")

    return valid_command