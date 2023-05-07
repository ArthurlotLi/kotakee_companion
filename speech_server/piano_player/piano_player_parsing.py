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
  looper_class_location = "./piano_player/loop_utility/loop_utility.LoopUtility"
  looper_subprocess_id = "piano_player_looper"

  piano_player = None

  speech_speak = None
  speech_listen = None
  web_server_status = None
  interaction_passive = None

  def __init__(self, speech_speak, speech_listen, web_server_status,interaction_passive):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status
    self.interaction_passive = interaction_passive

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
          piano_song_names.append(file.replace(".midi","").replace(".mid",""))

      # Check if the command includes a song name. 
      song_file_to_play = None
      for song_name in piano_song_names:
        if song_file_to_play is None and song_name in command:
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

    elif("list piano" in command or "list songs" in command):
      # If not, ask the user which file they want to play. 
      piano_song_prompt = "Here are all the piano songs I know: "
      for song_name in piano_song_names:
        piano_song_prompt = piano_song_prompt + song_name + ", "

      self.speech_listen.blocking_speak_event(event_type="speak_text", event_content=piano_song_prompt)
      valid_command=True

    elif ("stop piano" in command or "stop the piano" in command or "stop playing" in command):
      valid_command = True
      self.web_server_status.query_speech_server_piano_stop()


    elif ("loop piano" in command or "loop play the piano" in command 
          or "loop the piano" in command or "loop piano songs" in command
          or "play background piano" in command or "play me something" in command):
      
      # Get how many times to loop.
      loop_amount = self.text2int(command)
      print("[DEBUG] Parsed number " + str(loop_amount) + " from loop request.")
      if loop_amount > 0:
        # Get all the valid songs in the piano_songs_directory. 
        piano_song_filenames = []
        piano_songs_contents = os.listdir(self.piano_songs_location)
        for file in piano_songs_contents:
          if file.endswith(".mid") or file.endswith("midi"):
            piano_song_filenames.append(file)

        # Create a passive module that will loop through all of our songs. 
        loop_additional_data = {
          "piano_player" : self.piano_player,
          "songs" : piano_song_filenames,
          "virtual" : "virtual" in command,
          "piano_songs_location" : self.piano_songs_location,
          "max_songs" : loop_amount,
        }

        # Create a new passive module given the path to this folder.
        self.interaction_passive.create_module_passive(
          class_location = self.looper_class_location,
          first_event = 0,
          additional_data=loop_additional_data,
          id = self.looper_subprocess_id)
        
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Okay playing %d songs on the piano." % loop_amount)

    return valid_command
  


  # Helper function I got off stack overflow - really sweet code!
  # Slightly modified to allow non-number characters. 
  # https://stackoverflow.com/questions/493174/is-there-a-way-to-convert-number-words-to-integers
  def text2int(self, textnum, numwords={}):
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
          print("[DEBUG] text2int parsing invalid word: " + str(word))
          if self.intTryParse(word) is True:
            return int(word)
          continue
          #raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current
    
  # Dunno why this isn't standard. 
  def intTryParse(self, value):
    try:
      int(value)
      return True
    except ValueError:
      return False