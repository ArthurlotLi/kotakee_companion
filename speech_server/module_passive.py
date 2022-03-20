#
# module_passive.py
#
# Harmonizing class for all passive modules. Provides a layer of 
# abstraction for all "events" occuring on a passive basis via the
# passive interaction thread in interaction_passive. Utilizes 
# standardized json files specifying the way the module should be 
# handled.
#
# Has special handling for the case of runtime generated passive
# modules, as oppposed to those created on startup. For example,
# an alarm event that needs to execute once in the future. 
#
# The ultimate goal of this architecture is to eliminate necessary
# changes to the core components of the speech server when adding
# new capaabilities - only the supporting .json file specifying
# what modules are supported called "interaction_passive.json".
#
# Emphasis on graceful failure - the core components should 
# continue to run in the event of a lower level module exception. 
# Error messages should allow for ease of debugging during future
# development. 

import json
import sys

class ModulePassive:
  # Indicates successful initialization. If at any point an exception
  # is encountered, this flag should prevent the calling class from 
  # utilizing this module anymore.
  valid_module = False

  module_management = {}

  module_passive_json_filename = "module_passive.json"

  # We expect all passive module json files to provide these properties
  # with the exact same names, with the exception of first_event in 
  # the case it was specified on initialization. 
  require_online = None
  require_web_server = None
  init_on_startup = None
  first_event = None

  require_speech_speak = None
  require_speech_listen = None
  require_web_server_status = None

  # Variants derived from the class_location string provided on init. 
  class_location = None
  class_name = None
  module_location = None
  module_folder_location = None

  # Central class. We expect this class to have standard methods 
  # allowing us to interface with interaction_passive from here.
  module_class = None
  module_class_instance = None
  additional_data = None

  # Static components.
  speech_speak = None
  speech_listen = None
  web_server_status = None

  # Identifier that is assigned to a module on startup. May
  # be specified for runtime modules. Otherwise, if not
  # specified, will be the class name. 
  id = None

  # Expects json from module_passive.json in the subject directory.
  # If the json is malformatted, fails gracefully and keeps 
  # valid flag as false so the corrupted module is not used. 
  #
  # Expects input parameter class_location as a local path, for example,
  # "./home_automation/home_automation.HomeAutomation"
  # (folder/filename.ClassName). This specified class should be
  # the one designed to interface with interaction_passive. 
  #
  # Also expects the 3 static handlers for speak, listen, and web
  # server status. If they are not necessary, they will not be used. 
  #
  # Finally, expects first_event in the event (haha) that the module
  # is being defined programatically with a variable first event time. 
  #
  # In this case, it is also possible to provide the module with
  # a dictionary additional_data. This is useful for runtime 
  # generated passive modules. 
  def __init__(self, class_location, speech_speak, speech_listen, web_server_status, first_event = None, additional_data = None, id=None):
    module_json = None
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status

    self.additional_data = additional_data
    self.class_location = class_location

    # Convert into a file path. Drop the class in the path to 
    # get the folder. Load the module_passive.json file.
    try:
      split_class_path = self.class_location.rsplit(".", 1)
      self.module_location = split_class_path[0] 
      self.class_name = split_class_path[1]
      self.module_folder_location = self.module_location.rsplit("/", 1)[0]
    except:
      print("[ERROR] module_passive was provided an invalid class string: '" + str(self.class_location) + "'.")
      return

    # Assign identifier if it was passed to us. Otherwise it's just
    # the class name. 
    if id is None: self.id = self.class_name
    else: self.id = id

    # Attempt to load the class. 
    self.module_class = self.load_class(self.module_location, self.class_name)

    if self.module_class is None:
      print("[ERROR] Was unable to load class: '" + str(self.class_location) + "'.")
      return

    module_json_file_location = self.module_folder_location + "/" + self.module_passive_json_filename
    try:
      module_json_file = open(module_json_file_location)
      module_json = json.load(module_json_file)
    except:
      print("[ERROR] Unable to load module_json from: '" + str(module_json_file_location) + "'.")
      return

    # Extract module qualities from the module_passive.json file. 
    # Convert types accordingly. 
    try:
      if first_event is not None:
        self.first_event = first_event
      else:
        self.first_event = float(module_json["first_event"])

      self.init_on_startup = module_json["init_on_startup"] == 'True'
      self.require_online = module_json["require_online"] == 'True'
      self.require_web_server = module_json["require_web_server"] == 'True'

      self.require_speech_speak = module_json["require_speech_speak"] == 'True'
      self.require_speech_listen = module_json["require_speech_listen"] == 'True'
      self.require_web_server_status = module_json["require_web_server_status"] == 'True'
    except:
      print("[ERROR] Unacceptable module_json present in class location '" + str(self.class_location) + "'.")
      return

    # Initialize the class immediately if required.
    if self.init_on_startup is True:
      if self.initialize_class() is False:
        return # Failure. Return. 

    # Append additional info if we have it. 
    if additional_data is not None:
      self.module_class_instance.provide_additional_data(additional_data)

    self.valid_module = True
    print("[DEBUG] Successfully loaded class " + str(self.class_name) + " from '" + str(self.class_location) + "'.")

  # Dynamic class import. Changes sys.path to navigate directories
  # if necessary. 
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

  # Initialize the class. Provide arguments necessary according
  # to the json file. Unfortunately rather clumsy, but for the 
  # sake of all possibilities we'll handle all 8 cases of the 3
  # binary conditions. 
  def initialize_class(self):
    try:
      if(self.require_speech_speak is True and
         self.require_speech_listen is True and
         self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          speech_listen=self.speech_listen,
          web_server_status=self.web_server_status)
      elif(self.require_speech_speak is False and
           self.require_speech_listen is True and
           self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          speech_listen=self.speech_listen, 
          web_server_status=self.web_server_status)
      elif(self.require_speech_speak is True and
           self.require_speech_listen is False and
           self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          web_server_status=self.web_server_status)
      elif(self.require_speech_speak is True and
           self.require_speech_listen is True and
           self.require_web_server_status is False):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak, 
          speech_listen=self.speech_listen)
      elif(self.require_speech_speak is False and
           self.require_speech_listen is False and
           self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          web_server_status=self.web_server_status)
      elif(self.require_speech_speak is True and
           self.require_speech_listen is False and
           self.require_web_server_status is False):
         self.module_class_instance = self.module_class(
          speech_speak=self.speech_speak)
      elif(self.require_speech_speak is False and
           self.require_speech_listen is True and
           self.require_web_server_status is False):
         self.module_class_instance = self.module_class(
          speech_listen=self.speech_listen)
      else:
         self.module_class_instance = self.module_class()
    except Exception as e:
      print("[ERROR] Unable to load class " + str(self.class_name) + " from '" + str(self.class_location) + "'. Exception:")
      print(e)
      self.valid_module = False
      return False
    
    return True

  # Standard routine to check if there are any management events
  # that the child wants to push up to the parent. 
  def retrive_management_events(self):
    if self.valid_module is False:
      return None

    # Handle this class's management messages. 
    if len(self.module_management) > 0:
      module_management = self.module_management
      # Clear the management dict once the parent has recieved
      # it. 
      self.module_management = {}
      return module_management
    
    # Handle subclass's management messages. 
    if len(self.module_class_instance.module_management) > 0:
      module_management = self.module_class_instance.module_management
      # Clear the management dict once the parent has recieved
      # it. 
      self.module_class_instance.module_management = {}
      return module_management

  # Upon delete message, events up to the parent that it needs to be
  # removed from the list of initialized modules.  
  def clear_module(self):
    self.module_management["clear_module"] = True

  # Standardized routine to be called when the module is activated by
  # it's time requirement being hit in the passive_thrd. Executed in 
  # a separate thread in it's own vaccuum. 
  # 
  # Returns True if success is achieved - nobody is likely going to 
  # be listening, though. 
  def activate_event(self):
    # Simply do not activate if we have been disabled.
    if self.valid_module is False:
      return False

    # Prohibit execution of modules that have connection requirements
    if self.require_online is True and self.web_server_status.online_status is False:
      print("[DEBUG] Skipping passive module " + str(self.class_name) + " due to online requirement.")
      return False
    if self.require_web_server is True and self.web_server_status.web_server_status is False:
      print("[DEBUG] Skipping passive module " + str(self.class_name) + " due to web server requirement.")
      return False
    
    # If we need to initialize when the event itself is triggered. 
    if self.init_on_startup is False and self.module_class_instance is None:
      print("[DEBUG] Runtime initializing passive module class " + str(self.class_name) + " from '" + str(self.class_location) + "'.")
      if self.initialize_class() is False:
        return False
    
    # Initialization must occur before we try to execute the event.
    if self.module_class_instance is None:
      return False

    # All groundwork done. Go ahead and kick the event off. 
    self.module_class_instance.activate_event()
    # For development purposes, let exceptions occur. 
    """
    try:
      self.module_class_instance.activate_event()
    except Exception as e:
      # Upon any exception, something went wrong with the class
      # initialization. Perhaps the method is missing from the class? 
      print("[ERROR] Exception parsing command with passive module class " + str(self.class_name) + " from '" + str(self.class_location) + "'. Disabling module. Exception:")
      print(e)
      self.valid_module = False
    """
    
    return True