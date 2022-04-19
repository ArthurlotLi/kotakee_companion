#
# module_active.py
#
# Harmonizing class for all active modules. Provides a layer of 
# abstraction between component modules and the calling class
# interaction_active. Utilizes standardized json files specifying
# the way the module should be handled. 
#
# The ultimate goal of this architecture is to eliminate necessary
# changes to the core components of the speech server when adding
# new capaabilities - only the supporting .json file specifying
# what modules are supported called "interaction_active.json".
#
# Emphasis on graceful failure - the core components should 
# continue to run in the event of a lower level module exception. 
# Error messages should allow for ease of debugging during future
# development. 

import json
import sys

class ModuleActive:
  # Indicates successful initialization. If at any point an exception
  # is encountered, this flag should prevent the calling class from 
  # utilizing this module anymore.
  valid_module = False

  module_active_json_filename = "module_active.json"

  # We expect all active module json files to provide these properties
  # with the exact same names. 
  require_online = None
  require_web_server = None
  dispose_timeout = None
  init_on_startup = None
  init_runtime_triggers = None
  init_runtime_message = None

  require_speech_speak = None
  require_speech_listen = None
  require_web_server_status = None
  require_interaction_passive = None

  # Variants derived from the class_location string provided on init. 
  class_location = None
  class_name = None
  module_location = None
  module_folder_location = None

  # Central class. We expect this class to have standard methods 
  # allowing us to interface with interaction_active from here.
  module_class = None
  module_class_instance = None

  # Static components - we will only populate these if we need to
  # initialize the class only when it is being used for the first
  # time (or after a while, potentially)
  speech_speak = None
  speech_listen = None
  web_server_status = None
  interaction_passive = None

  # Expects json from module_active.json in the subject directory.
  # If the json is malformatted, fails gracefully and keeps 
  # valid flag as false so the corrupted module is not used. 
  #
  # Expects input parameter class_location as a local path, for example,
  # "./home_automation/home_automation.HomeAutomation"
  # (folder/filename.ClassName). This specified class should be
  # the one designed to interface with interaction_active. 
  #
  # Also expects the 3 static handlers for speak, listen, and web
  # server status. If they are not necessary, they will not be used. 
  def __init__(self, class_location, speech_speak, speech_listen, web_server_status, interaction_passive):
    module_json = None
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status
    self.interaction_passive = interaction_passive

    self.class_location = class_location

    # Convert into a file path. Drop the class in the path to 
    # get the folder. Load the module_active.json file.
    try:
      split_class_path = self.class_location.rsplit(".", 1)
      self.module_location = split_class_path[0] 
      self.class_name = split_class_path[1]
      self.module_folder_location = self.module_location.rsplit("/", 1)[0]
    except:
      print("[ERROR] module_active was provided an invalid class string: '" + str(self.class_location) + "'.")
      return

    # Attempt to load the class. 
    self.module_class = self.load_class(self.module_location, self.class_name)

    if self.module_class is None:
      print("[ERROR] Was unable to load class: '" + str(self.class_location) + "'.")
      return

    module_json_file_location = self.module_folder_location + "/" + self.module_active_json_filename
    #module_json_file_location = module_json_file_location.replace(".","/")
    try:
      module_json_file = open(module_json_file_location)
      module_json = json.load(module_json_file)
    except:
      print("[ERROR] Unable to load module_json from: '" + str(module_json_file_location) + "'.")
      return

    # Extract module qualities from the module_active.json file. 
    # Convert types accordingly. 
    try:
      self.require_online = module_json["require_online"] == 'True'
      self.require_web_server = module_json["require_web_server"] == 'True'
      self.dispose_timeout = int(module_json["dispose_timeout"])
      self.init_on_startup = module_json["init_on_startup"] == 'True'
      self.init_runtime_message = module_json["init_runtime_message"]
      self.init_runtime_triggers = module_json["init_runtime_triggers"]

      self.require_speech_speak = module_json["require_speech_speak"] == 'True'
      self.require_speech_listen = module_json["require_speech_listen"] == 'True'
      self.require_web_server_status = module_json["require_web_server_status"] == 'True'
      self.require_interaction_passive = module_json["require_interaction_passive"] == 'True'
    except:
      print("[ERROR] Unacceptable module_json present in class location '" + str(self.class_location) + "'.")
      return

    # Initialize the class immediately if required.
    if self.init_on_startup is True:
      if self.initialize_class() is False:
        return # Failure. Return. 

    self.valid_module = True
    print("[DEBUG] Successfully loaded class " + str(self.class_name) + " from '" + str(self.class_location) + "'.")
      
  def load_class(self,  module_name, class_name):
    """
    Dynamic class import. Changes sys.path to navigate directories
    if necessary. Utilized for emotion detection and
    representation classes. 
   
    Expects module_name Ex) ./home_automation/home_automation
    and class_name Ex) HomeAutomation
    """
    module = None
    imported_class = None
    module_file_name = None

    sys_path_appended = False

    # Ex) ./home_automation - split by last slash. 
    # Don't bother if the original file is not within a subdirectory.
    split_module_name = module_name.rsplit("/", 1)
    module_folder_path = split_module_name[0]
    if(module_folder_path != "." and len(split_module_name) > 1):
      sys.path.append(module_folder_path)
      module_file_name = split_module_name[1]
      sys_path_appended = True
    else:
      module_file_name = module_name.replace("./", "")

    # Fetch the module first.
    try:
      module = __import__(module_file_name)
    except Exception as e:
      print("[ERROR] Failed to import module " + module_file_name + " from subdirectory '" + module_folder_path + "'.")
      print(e)
      return None

    # Return the class. 
    try:
      imported_class = getattr(module, class_name)
    except Exception as e:
      print("[ERROR] Failed to import class_name " + class_name + ".")
      print(e)
      return None

    if sys_path_appended is True:
      sys.path.remove(module_folder_path)

    return imported_class
  
  # Initialize the class. Provide arguments necessary according
  # to the json file. Unfortunately VERY clumsy, but for the 
  # sake of all possibilities we'll handle all 16 cases of the 4
  # binary conditions. 
  def initialize_class(self):
    try:
      if(self.require_speech_speak is True and
         self.require_speech_listen is True and
         self.require_web_server_status is True and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          speech_listen=self.speech_listen,
          web_server_status=self.web_server_status,
          interaction_passive=self.interaction_passive,
        )
      elif(self.require_speech_speak is True and
         self.require_speech_listen is True and
         self.require_web_server_status is True and
         self.require_interaction_passive is False):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          speech_listen=self.speech_listen,
          web_server_status=self.web_server_status,
        )
      elif(self.require_speech_speak is True and
         self.require_speech_listen is True and
         self.require_web_server_status is False and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          speech_listen=self.speech_listen,
          interaction_passive=self.interaction_passive,
        )
      elif(self.require_speech_speak is True and
         self.require_speech_listen is True and
         self.require_web_server_status is False and
         self.require_interaction_passive is False):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          speech_listen=self.speech_listen,
        )
      elif(self.require_speech_speak is True and
         self.require_speech_listen is False and
         self.require_web_server_status is True and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          web_server_status=self.web_server_status,
          interaction_passive=self.interaction_passive,
        )
      elif(self.require_speech_speak is True and
         self.require_speech_listen is False and
         self.require_web_server_status is True and
         self.require_interaction_passive is False):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          web_server_status=self.web_server_status,
        )
      elif(self.require_speech_speak is True and
         self.require_speech_listen is False and
         self.require_web_server_status is False and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          interaction_passive=self.interaction_passive,
        )
      elif(self.require_speech_speak is True and
         self.require_speech_listen is False and
         self.require_web_server_status is False and
         self.require_interaction_passive is False):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
        )
      elif(self.require_speech_speak is False and
         self.require_speech_listen is True and
         self.require_web_server_status is True and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          speech_listen=self.speech_listen,
          web_server_status=self.web_server_status,
          interaction_passive=self.interaction_passive,
        )
      elif(self.require_speech_speak is False and
         self.require_speech_listen is True and
         self.require_web_server_status is True and
         self.require_interaction_passive is False):
         self.module_class_instance = self.module_class(
          speech_listen=self.speech_listen,
          web_server_status=self.web_server_status,
        )
      elif(self.require_speech_speak is False and
         self.require_speech_listen is True and
         self.require_web_server_status is False and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          speech_listen=self.speech_listen,
          interaction_passive=self.interaction_passive,
        )
      elif(self.require_speech_speak is False and
         self.require_speech_listen is True and
         self.require_web_server_status is False and
         self.require_interaction_passive is False):
         self.module_class_instance = self.module_class(
          speech_listen=self.speech_listen,
        )
      elif(self.require_speech_speak is False and
         self.require_speech_listen is False and
         self.require_web_server_status is True and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          web_server_status=self.web_server_status,
          interaction_passive=self.interaction_passive,
        )
      elif(self.require_speech_speak is False and
         self.require_speech_listen is False and
         self.require_web_server_status is True and
         self.require_interaction_passive is False):
         self.module_class_instance = self.module_class(
          web_server_status=self.web_server_status,
        )
      elif(self.require_speech_speak is False and
         self.require_speech_listen is False and
         self.require_web_server_status is False and
         self.require_interaction_passive is True):
         self.module_class_instance = self.module_class(
          interaction_passive=self.interaction_passive,
        )
      else:
         self.module_class_instance = self.module_class()
    except Exception as e:
      print("[ERROR] Unable to load class " + str(self.class_name) + " from '" + str(self.class_location) + "'. Exception:")
      print(e)
      self.valid_module = False
      return False
    
    return True

  # Routine to be called for every active module when a user initiates
  # active interaction level 1. A command will be passed through all
  # modules until (if) one triggers. An input command should be handled
  # by a similarily labled function within the module class. 
  #
  # Return True if we have registered ownership of the command 
  # jurisdiction, halting further parsing. Return False otherwise. 
  def parse_command(self, command):
    action_triggered = False

    # Simply do not activate if we have been disabled.
    if self.valid_module is False:
      return False

    # Prohibit execution of modules that have connection requirements
    if self.require_online is True and self.web_server_status.online_status is False:
      print("[DEBUG] Skipping active module " + str(self.class_name) + " due to online requirement.")
      return False
    if self.require_web_server is True and self.web_server_status.web_server_status is False:
      print("[DEBUG] Skipping active module " + str(self.class_name) + " due to web server requirement.")
      return False

    # If the user says any of the keywords triggering initialization
    if self.init_on_startup is False and self.module_class_instance is None and any(x in command for x in self.init_runtime_triggers):
      # Initialize upon first usage. Execute message if present. This
      # is useful for confirming to the user the command has registered
      # and to let them know for long wait periods.  
      print("[DEBUG] Runtime initializing active module class " + str(self.class_name) + " from '" + str(self.class_location) + "'.")
      if self.init_runtime_message != "":
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=self.init_runtime_message)
      if self.initialize_class() is False:
        return False

    # Initialization must occur before we try and parse things. 
    if self.module_class_instance is None:
      return False

    action_triggered = self.module_class_instance.parse_command(command)
    # For development purposes, allow module failures to hard stop. 
    """
    try:
      action_triggered = self.module_class_instance.parse_command(command)
    except Exception as e:
      # Upon any exception, something went wrong with the class
      # initialization. Perhaps the method is missing from the class? 
      print("[ERROR] Exception parsing command with active module class " + str(self.class_name) + " from '" + str(self.class_location) + "'. Disabling module. Exception:")
      print(e)
      self.valid_module = False
    """

    return action_triggered
