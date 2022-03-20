#
# interaction_passive.py
#
# Management of passive module instances, providing abstracted
# methods to allow their specified routine functionality. 
#
# Expects interaction_passive.json specifying directories of 
# primary module classes. 

from module_passive import ModulePassive

import json
import threading
import time

class InteractionPassive:
  interaction_passive_json_location = "./interaction_passive.json"

  # Run rate of the passive_thrd. How many seconds the 
  # loop waits before checking passive_module_events for 
  # valid events. The base units that define the quanities
  # present in that array. 
  #
  # Modifying this value will increase/decrease the rate at
  # which passive events are checked. This may affect the
  # performance of passive events and how precisely their
  # activation time requirements are met (based on local
  # hardware). 
  passive_thrd_tick = 0.5 # 500 ms

  # The main passive thread that runs in tandem with the main
  # active processing loop in hotword_trigger_word. Spawns
  # new threads to fufill passive modules when their event
  # time requirements are met. 
  passive_thrd_instance = None
  passive_thrd_stop = False

  # Like-indexed lists. Events consists of relative timestamps
  # from the startup time of the thread, in the quanity of 
  # 'ticks' (defined as a constant above as the run rate of
  # the passive_thrd). The passive_thrd consistently checks
  # the events list every tick after startup.
  passive_module_events = []
  passive_module_list = []
  passive_module_ids = []

  # Managed list of all active modules. May contain modules 
  # actively running, or modules still in the event queue. 
  initialized_passive_modules = []

  # Pointers to "subthreads" - threads executing passive modules
  # for proper memory utilization purposes. 
  passive_thrd_subthrds = []

  speech_speak = None
  speech_listen = None
  web_server_status = None

  # On initialization, initializes all passive modules specified
  # by the interaction_passive.json file. Starts up the passive
  # thrd once it's done. 
  def __init__(self, speech_speak, speech_listen, web_server_status):
    interaction_passive_json = None
    interaction_passive_modules = None

    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status

    # Attempt to load the list of all passive modules. 
    try:
      interaction_passive_json_file = open(self.interaction_passive_json_location)
      interaction_passive_json = json.load(interaction_passive_json_file)
    except:
      print("[ERROR] Interaction passive was unable to load json from: '" + str(self.interaction_passive_json_location) + "'.")
      return
    # We expect a list of class names in an entry "passive_modules".
    try:
      interaction_passive_modules = interaction_passive_json["passive_modules"]
    except:
      print("[ERROR] Interaction passive was unable to parse passive_modules.json.")
      return
    
    # For each module in the list, load it and keep it in our list. 
    for class_location in interaction_passive_modules:
      self.create_module_passive(class_location=class_location)

    # Kick off the thread and get the show on the road. 
    self.begin_passive_thrd()

    print("[DEBUG] Initialized Interaction Passive with " + str(len(self.passive_module_list)) + " valid modules.")

  # Creates a new passive module, appending it to our lists shared
  # with the passive_thrd for eventing. May take in a first_event
  # parameter for passive modules created during runtime via passive
  # interactions. 
  # 
  # If no first_event is specified, expects the
  # first_event to be specified in the moduele_passive.json as well. 
  def create_module_passive(self, class_location, first_event=None, additional_data=None, id=None, duration_seconds = None):
    if first_event is None and duration_seconds is not None:
      current_time = time.time()
      first_event_time = current_time + (float(duration_seconds)) # Append seconds. 
      first_event = first_event_time

    new_module = ModulePassive(
      class_location=class_location, 
      speech_speak=self.speech_speak, 
      speech_listen=self.speech_listen, 
      web_server_status=self.web_server_status,
      first_event = first_event,
      additional_data = additional_data,
      id = id)
    if new_module.valid_module is True and new_module.first_event is not None:
      self.passive_module_list.append(new_module)
      self.passive_module_events.append(new_module.first_event)
      self.passive_module_ids.append(new_module.id)
      self.initialized_passive_modules.append(new_module)
    else:
      print("[WARNING] Interaction Passive failed to load a module from '" + str(class_location) + "'.")
    
  # Add already created modules to the queue. This is used 
  # by executed modules that wish to re-add themselves to the
  # queue. 
  def add_module_passive(self, new_module, first_event=None, id=None, duration_seconds = None):
    if duration_seconds is not None:
      current_time = time.time()
      first_event_time = current_time + (float(duration_seconds)) # Append seconds. 
      new_module.first_event = first_event_time
    elif first_event is not None:
      new_module.first_event = first_event

    if id is not None:
      new_module.id = id

    if new_module.valid_module is True and new_module.first_event is not None:
      self.passive_module_list.append(new_module)
      self.passive_module_events.append(new_module.first_event)
      self.passive_module_ids.append(new_module.id)
      print("[DEBUG] Interaction Passive successfully readded a module '" + str(new_module.class_location) + "' provided to add_module_passive.")
    else:
      print("[WARNING] Interaction Passive failed to load a module provided to add_module_passive.")

  # Allows existing modules to event requests up to us, the
  # parent, so we can manage them properly. 
  def handle_module_management(self, management_dict, module, initialized_passive_modules_index):
    for event in management_dict:
      if event == "clear_module":
        print("[DEBUG] Module Management - Initialized passive module '" + str(module.class_name) + "' being deleted.")
        del self.initialized_passive_modules[initialized_passive_modules_index]
      elif event == "add_module_passive":
        first_event = None
        id = None
        duration_seconds = None
        # We expect a dict in this case. 
        add_module_dict = management_dict[event]
        if "duration_seconds" in add_module_dict:
          duration_seconds = add_module_dict["duration_seconds"]
        if "first_event" in add_module_dict:
          first_event = add_module_dict["first_event"]
        if "id" in add_module_dict:
          id = add_module_dict["id"]
        
        self.add_module_passive(module, first_event=first_event, id=id, duration_seconds=duration_seconds)

  # Allows other classes to ask for certain modules by id. If they
  # do not exist, None will be returned. Otherwise, the module object
  # will be returned, alongside the time when it will be activated.
  # (Since epoch in seconds.)
  def get_module_by_id(self, id):
    for i in range(0, len(self.passive_module_events)):
      if id == self.passive_module_ids[i]:
        # Return the module object + when it will be activated. 
        return self.passive_module_list[i], self.passive_module_events[i]
    return None, None

  # Given an id, clears an event (if it hasn't been executed yet)
  # from the queue. Returns status of deletion (if it was found)
  def clear_module_by_id(self, id):
    for i in range(len(self.passive_module_events)-1,-1,-1):
      if id == self.passive_module_ids[i]:
        module = self.passive_module_list[i]
        module.clear_module()
        del self.passive_module_list[i]
        del self.passive_module_events[i]
        del self.passive_module_ids[i]
        print("[DEBUG] Interaction Passive removed module '"+str(module.class_name)+"' (id"+str(id)+").")
    return False 

  # Kicks off the thread.
  def begin_passive_thrd(self):
    print("[DEBUG] Starting Passive Thread.")
    self.passive_thrd_instance = threading.Thread(target=self.passive_thrd, args=(self.passive_thrd_tick,), daemon=True).start()

  # The passive thread. Loops every 'tick' seconds and checks
  # if any events need to occur. If any do need to be occur, the 
  # corresponding passive module will be given a thread to run from
  # here. Expects the tick value when starting. 
  def passive_thrd(self, passive_thread_tick):
    while self.passive_thrd_stop is False:

      # Every run, check all modules for management events. 
      # Note this checks all initialized modules - not just
      # modules that have an upcoming event. 
      for i in range(len(self.initialized_passive_modules)-1,-1,-1):
        module = self.initialized_passive_modules[i]
        management_dict = module.retrive_management_events()
        if management_dict is not None and len(management_dict) > 0:
          self.handle_module_management(management_dict, module, i)

      # Clear the executed modules once done. 
      indices_to_drop = []

      # Use current timestamp in seconds. 
      current_time = time.time()

      for i in range(0, len(self.passive_module_events)):
        time_req = self.passive_module_events[i]
        if current_time >= time_req:
          # An event time has been triggered. Kick off the thread,
          # passing in the module object in the like-indexed module
          # list. 
          self.activate_module_passive(self.passive_module_list[i])
          indices_to_drop.append(i)
      
      # Clear the queue once completed. Go backwards from the back
      # of the to-delete list.
      for i in range(len(indices_to_drop)-1, -1, -1):
        # Remove it from the list.
        # TODO: Support recurrent events. 
        del self.passive_module_list[indices_to_drop[i]]
        del self.passive_module_events[indices_to_drop[i]]
        del self.passive_module_ids[indices_to_drop[i]]

      time.sleep(passive_thread_tick)

  # Initializes a new thread for a passive module whose time has come.
  # Expects the module to have a standard function name 
  # "activate_event()".
  def activate_module_passive(self, module):
    print("[DEBUG] Event triggered for passive module '"+str(module.class_name)+"' (id"+str(module.id)+"). Beginning thread.")
    self.passive_thrd_subthrds.append(threading.Thread(target=module.activate_event, daemon=True).start())