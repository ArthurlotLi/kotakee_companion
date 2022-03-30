#
# alarm_utility.py
#
# Passive module dynamically added by active module SimpleUtilties
# upon user command. When the event happens, play a jingle and 
# announce that the alarm has rung. Interact with the user
# and ask for a snooze or cancel. If no response is heard, 
# cancellation will be assumed. 
# 
# If we are connected to the web server (optional, detected via 
# static object), trigger specific lights to turn on. Remember 
# which lights were on so we can keep them on and turn the rest
# off when the user completes interaction.
#
# Because waking up requires drastic measures, like blasting your
# irises with all your house lights. 

import time

class AlarmUtility:
  # Management dict checked via passive_module by the interaction
  # passive thread. If this dict holds an action, the parent of
  # the parent will respond accordingly. 
  module_management = {}

  snooze_confirmation_words = ["sure", "yep", "go ahead", "okay", "yeah", "affirm", "that's it", "ok", "yes", "go for it", "snooze", "please", "more minutes"]

  # Expects a dictionary structured as such:
  # roomid_actionid : onstate_offstate
  # Ex) { 2_50:1_0, 2_350:22:20 }
  #
  # All listed actions will be turned ON when the alarm goes 
  # off. When the alarm is cancelled or snoozed, all actions
  # will be reverted to the states that they had before the
  # alarm had gone off. 
  action_dict = None

  def __init__(self, speech_speak, speech_listen, web_server_status):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status

  # Standard routine in the case that we expect additional data for
  # a passive module instantiated during runtime. 
  def provide_additional_data(self, additional_data):
    self.additional_data = additional_data
    self.alarm_name = additional_data["alarm_name"]
    self.alarm_hour = additional_data["alarm_hour"]
    self.alarm_minute = additional_data["alarm_minute"]
    self.snooze_remaining = additional_data["snooze_remaining"]
    self.snooze_duration_seconds = additional_data["snooze_duration_seconds"]
    self.action_dict = additional_data["action_dict"]
    self.repeating_alarm = additional_data["repeating_alarm"]

  # Standard routine triggered when the event time is triggered
  # by the passive interaction thread. Execute an alarm once. 
  # If the user snoozes, this event will be re-registered and
  # will trigger again in the specified duration.
  def activate_event(self):
    print("[INFO] Alarm event triggered. Executing alarm.")
 
    pre_event_action_states = None

    # Trigger all actions first. Requries that we're connected
    # to the home automation system and that we have things to 
    # actually trigger. 
    if self.web_server_status.web_server_status is True and len(self.action_dict.keys()) > 0:
      # Update the most recent action states if we're connected to
      # the home automation system. Blocking action, so this
      # may delay the alarm by just a bit.
      self.web_server_status.query_action_states()

      # Save the most recent action states so we can return all
      # of the actions to their original states after the event is
      # complete. 
      pre_event_action_states = self.web_server_status.action_states

      # Trigger all the actions to turn on. 
      for roomid_actionid in self.action_dict:
        split_ids = roomid_actionid.split("_")
        room_id = split_ids[0]
        action_id = split_ids[1]
        split_states = self.action_dict[roomid_actionid].split("_")
        on_state = split_states[0]
        #off_state = split_states[1] Not necessary!

        self.web_server_status.query_speech_server_module_toggle(
          toState=on_state, roomId=room_id, actionId=action_id)
      
    # Play the alarm sound. 
    self.speech_speak.blocking_speak_event(event_type="execute_alarm")

    # Execute alarm message, asking for snooze. 
    snooze_requested = False

    alarm_message = "Your alarm, " + str(self.alarm_name) + ", has activated."
    if self.snooze_remaining > 0:
      alarm_message = alarm_message + " Do you wish to snooze?"
      user_response = self.speech_listen.listen_response(prompt=alarm_message, execute_chime = True)
      if user_response is not None and any(x in user_response for x in self.snooze_confirmation_words):
        snooze_message = "Snoozing, " + str(self.alarm_name) + ", for " + str(int(int(self.snooze_duration_seconds)/60)) + " more minutes."
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=snooze_message)
        self.snooze_remaining = self.snooze_remaining - 1
        snooze_requested = True
      else:
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Alarm finished.")
    else:
      # If no snoozes remaining, simply notify the user. 
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=alarm_message)
    
    if self.web_server_status.web_server_status is True and len(self.action_dict.keys()) > 0:
      # Alarm routine has finished. Return pre_event action_states. 
      for roomid_actionid in self.action_dict:
        split_ids = roomid_actionid.split("_")
        room_id = split_ids[0]
        action_id = split_ids[1]
        split_states = self.action_dict[roomid_actionid].split("_")
        revert_state = pre_event_action_states[str(room_id)][str(action_id)]

        self.web_server_status.query_speech_server_module_toggle(
          toState=revert_state, roomId=room_id, actionId=action_id)

    # Refer to the passed in calling_class pointer (interaction_passive)
    # and toss yourself back into the queue. 
    if snooze_requested is True:
      print("[DEBUG] Setting snoozed alarm for " + str(self.snooze_duration_seconds) + " seconds.")
      self.module_management["add_module_passive"] = {
        "duration_seconds" : self.snooze_duration_seconds
      }
    else:
      # Handle a recurring alarm. 
      if self.repeating_alarm:
        duration_seconds = 0
        current_seconds = time.strftime("%S", time.localtime())
        current_minutes = time.strftime("%M", time.localtime())
        current_hours = time.strftime("%H", time.localtime())
        current_time_since_midnight = int(current_seconds) + int(current_minutes) * 60 + int(current_hours) * 3600

        # Check if our time is going to put us before or after now. 
        alarm_time_since_midnight = self.alarm_minute*60 + self.alarm_hour*3600
        print("[DEBUG] Current time is " + str(current_time_since_midnight) + ". Alarm time is " + str(alarm_time_since_midnight) + ".")

        if alarm_time_since_midnight < current_time_since_midnight:
          # Alarm will be for tomorrow.
          remainder_time_today = 86400 - current_time_since_midnight 
          duration_seconds = remainder_time_today + alarm_time_since_midnight
        else:
          duration_seconds = alarm_time_since_midnight - current_time_since_midnight

        current_time = time.time()
        first_event_time = current_time + (float(duration_seconds)) # Append seconds. 
        print("[DEBUG] Setting recurring alarm for " + str(duration_seconds) + " seconds. Current time: " + str(current_time) + ". Targeted time: " + str(first_event_time) + ".")

        self.module_management["add_module_passive"] = {
          "duration_seconds" : duration_seconds
        }
      else:
        self.module_management["clear_module"] = True
        