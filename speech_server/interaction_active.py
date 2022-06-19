#
# interaction_active.py
#
# Handling of command parsing given a recognized keyword, providing 
# harmonized functionality of abstracted active modules.
#
# Expects interaction_active.json specifying directories of 
# primary module classes. 

from module_active import ModuleActive

import json

class InteractionActive:
  # Flag to shut down the entire speech server. 
  stop_server = False

  interaction_active_json_location = "./interaction_active.json"

  # Constants that may be configured.
  cancel_words = ["cancel"] # stops query.
  stop_server_commands = ["goodnight", "good night", "freeze all motor functions", "turn yourself off", "shutdown", "deactivate"]
  stop_server_prompt = "Shutting down." # By default, don't say anything and just let the hotword chime indicate shutdown. 
  command_split_keywords = ["break", "brake", "also", "period", "comma"]

  speech_speak = None
  speech_listen = None
  web_server_status = None
  interaction_passive = None

  # List of ModuleActive objects. 
  module_active_list = [] 

  # Initialize all active modules implemented as specified in the 
  # "interaction_active.json" support document. 
  def __init__(self, speech_speak, speech_listen, web_server_status, interaction_passive):
    interaction_active_json = None
    interaction_active_active_modules = None

    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status
    self.interaction_passive = interaction_passive

    # Attempt to load the list of all active modules. 
    try:
      interaction_active_json_file = open(self.interaction_active_json_location)
      interaction_active_json = json.load(interaction_active_json_file)
    except:
      print("[ERROR] Interaction Active was unable to load json from: '" + str(self.interaction_active_json_location) + "'.")
      return
    
    # We expect a list of class names in an entry "active_modules".
    try:
      interaction_active_active_modules = interaction_active_json["active_modules"]
    except:
      print("[ERROR] Interaction Active was unable to parse active_modules json.")
      return
    
    # For each module in the list, load it and keep it in our list. 
    for class_location in interaction_active_active_modules:
      new_module = ModuleActive(
        class_location=class_location, 
        speech_speak=speech_speak, 
        speech_listen=speech_listen, 
        web_server_status=web_server_status,
        interaction_passive = interaction_passive)
      
      if new_module.valid_module is True:
        self.module_active_list.append(new_module)
      else:
        print("[WARNING] Interaction Active failed to load a module from '" + str(class_location) + "'.")
    
    print("[DEBUG] Initialized Interaction Active with " + str(len(self.module_active_list)) + " valid modules.")

  # Key method executing level one user interactions. 
  def listen_for_command(self):
    print("[INFO] Interaction Active initializing user command level 1 routine.")
    # Spawn a thread to run in the background querying the server for
    # it's status in advance of the command. 
    self.web_server_status.execute_query_server_thread()
    user_command = self.speech_listen.listen_response(execute_chime=True, indicate_led=True)
    if user_command is not None and user_command != "":
      # Abort if any key cancel words are present in registered text. 
      if any(x in user_command for x in self.cancel_words):
        print("[DEBUG] User requested cancellation. Stopping command parsing...")
        return
      self.parse_command(user_command)

  # Given a command, trickle down the list of active modules and test
  # to see if any of them activate. 
  def parse_command(self, full_command):
    valid_commands = False

    # Shutdown parsing. If any keyword is present, simply stop. 
    if any(x in full_command for x in self.stop_server_commands):
      print("[INFO] Shutdown query recieved. Stopping server.")
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=self.stop_server_prompt)
      self.stop_server = True
      return True

    # Multi-command parsing. Break the command phrase in two
    # given the array of keywords.
    commands = [full_command]
    for keyword in self.command_split_keywords:
      new_commands = []
      for i in range(0, len(commands)):
        split_commands = commands[i].split(keyword)
        for group in split_commands:
          new_commands.append(group)
      commands = new_commands

    # Parse command chronologically. Pass it through each module that
    # has been initialized in order of initialization (aka the order
    # in the json file interaction_active.json). If any module claims
    # the command as it's jurisdiction and acts upon it, stop parsing
    # and return as a successful command. 
    for command in commands:
      for module in self.module_active_list:
        valid_command = module.parse_command(command)
        if valid_command is True: 
          print("[DEBUG] Command jurisdiction claimed by module " + str(module.class_name) + ". Interaction complete.")
          break

    if valid_command != True:
      print("[DEBUG] No valid command was recognized from the spoken text.")
    return valid_command