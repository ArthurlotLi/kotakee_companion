#
# timer_utility.py
#
# Passive module dynamically added by active module SimpleUtilties
# upon user command. When the event happens, play a jingle and 
# announce that the timer has completed. Simple.

class TimerUtility:
  # Management dict checked via passive_module by the interaction
  # passive thread. If this dict holds an action, the parent of
  # the parent will respond accordingly. 
  module_management = {}
  
  speech_speak = None

  timer_duration = None
  timer_seconds = None
  timer_units = None

  def __init__(self, speech_speak):
    self.speech_speak = speech_speak

  # Standard routine in the case that we expect additional data for
  # a passive module instantiated during runtime. 
  def provide_additional_data(self, additional_data):
    self.timer_duration = additional_data["timer_duration"]
    self.timer_seconds = additional_data["timer_seconds"]
    self.timer_units = additional_data["timer_units"]

  # Standard routine triggered when the event time is triggered
  # by the passive interaction thread. 
  def activate_event(self):
    print("[INFO] Timer event triggered. Executing timer and text.")
    timer_message = None
    if self.timer_duration is None or self.timer_units is None:
      timer_message = "Timer finished."
    else:
      timer_message = "Timer for " + str(self.timer_duration) + " " + str(self.timer_units) + " has finished."

    self.speech_speak.blocking_speak_event(event_type="execute_timer")
    self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=timer_message)
    print("[DEBUG] Timer event complete.")
    self.module_management["clear_module"] = True