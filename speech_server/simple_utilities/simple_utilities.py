#
# simple_utilities.py
#
# Module allowing for simple assistant tasks that do not require
# internet connectivity nor the presence of the home automation
# web server. 

import time
from datetime import date

class SimpleUtilities:
  # Paths relative to where interaction_active is. 
  timer_class_location = "./simple_utilities/timer_utility/timer_utility.TimerUtility"
  timer_confirmation_threshold = 7200 # Amount of time required to ask for confirmation of new timer. Seconds.
  timer_ids = [] # Note this may contain stale data - need to check each id, asking if they exist first.  

  alarm_class_location = "./simple_utilities/alarm_utility/alarm_utility.AlarmUtility"
  alarm_snooze_remaining = 3 # Maximum snoozes for an alarm. 
  alarm_snooze_duration_seconds = 300 # Time for a snooze in seconds. 
  # Standard actions to accompany an alarm with. 
  alarm_action_dict = { 
    "2_50": "1_0",
    "1_50": "1_0",
    "1_1000" : "107_100",
    "2_1000" : "107_100",
  }
  alarm_ids = [] # Note this may contain stale data - need to check each id, asking if they exist first. 

  speech_speak = None
  speech_listen = None
  web_server_status = None
  interaction_passive = None

  user_confirmation_words = ["sure", "yep", "go ahead", "okay", "yeah", "affirm", "that's it", "ok", "yes", "go for it"]
  user_cancel_words = ["stop", "cancel", "no", "wrong"] 

  def __init__(self, speech_speak, speech_listen, web_server_status, interaction_passive):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status
    self.interaction_passive = interaction_passive

  # Level 1 standard routine.
  def parse_command(self, command):
    valid_command = False

    # Check timer first, then time (because timer has time in it).
    # List timers command lists all timers and then asks the user
    # if they want to clear all timers. 
    if("list timers" in command or "list all timers" in command 
    or "all timers" in command or "delete timers" in command 
    or "clear timers" in command or "clear all timers" in command 
    or "delete all timers" in command):
      valid_command = True
      timer_list_prompt = ""
      # List all active timers. Ask the user if they want to delete
      # any afterwards. 
      for i in range(len(self.timer_ids)-1,-1,-1):
        # Check if it exists. If not, delete it. 
        timer_module, timer_activation_time = self.interaction_passive.get_module_by_id(self.timer_ids[i])
        if timer_module is None:
          del self.timer_ids[i]
        else:
          timer_time_left = int(timer_activation_time - time.time())
          timer_list_prompt = timer_list_prompt + "The " + str(timer_module.additional_data["timer_duration"]) + " " + str(timer_module.additional_data["timer_units"]) + " timer has " + str(timer_time_left) + " seconds remaining" + ", "
      
      if timer_list_prompt == "":
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="There are currently no active timers.")
      else:
        # List all timers and ask if they want to clear all timers. 
        # Singular vs plural.
        num_timers = len(self.timer_ids)
        timer_list_prompt = timer_list_prompt + ". Would you like to clear all timers?"  
        if num_timers == 1:
          timer_list_prompt = "There is a single active timer. " + timer_list_prompt
        else:  
          timer_list_prompt = "There are " + str(num_timers) + " active timers. " + timer_list_prompt
        user_response = self.speech_listen.listen_response(prompt=timer_list_prompt, execute_chime = True)

        if user_response is not None and any(x in user_response for x in self.user_confirmation_words):
          # Got confirmation. Delete all timers. 
          for timer_id in self.timer_ids:
            self.interaction_passive.clear_module_by_id(timer_id)
          self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="All timers have now been deleted.")

    elif("timer" in command):
      valid_command = True

      duration, duration_seconds, units = self.parse_duration_from_command(command)
      if duration is not None and units is not None:
        # Level 2 subroutine for confirming the parsed information. 
        # Only activated if threshold is exceeded (don't sweat it 
        # for timers that are short.)
        user_response_requied = False
        user_response = None
        if int(duration_seconds) > self.timer_confirmation_threshold:
          user_response_requied = True
          user_prompt = "Confirm set timer for " + str(duration) + " " + str(units) + "?"
          user_response = self.speech_listen.listen_response(prompt=user_prompt, execute_chime = True)

        if user_response_requied is False or (user_response is not None and any(x in user_response for x in self.user_confirmation_words)):
          # Timer module will add the TimerUtility passive module to the 
          # passive_thrd routine with a first_event time equivalent to the
          # specified time. 
          current_time = time.time()
          first_event_time = current_time + (float(duration_seconds)) # Append seconds. 
          print("[DEBUG] Setting timer for " + str(duration_seconds) + " seconds. Current time: " + str(current_time) + ". Targeted time: " + str(first_event_time) + ".")
          timer_additional_data = { "timer_duration" : duration, "timer_seconds":duration_seconds, "timer_units": units }

          # Create a timer that we can add to our list of known timers. 
          # Later on if asked, we can ping interaction_passive with the
          # id to retrive the additional data dict and report it's info.
          # Before it's triggered, naturally. 
          timer_id = "simple_utilities_timer_" + str(first_event_time)
          self.timer_ids.append(timer_id)
 
          # Create a new passive module given the path to this folder.
          self.interaction_passive.create_module_passive(
            class_location = self.timer_class_location,
            first_event = first_event_time,
            additional_data=timer_additional_data,
            id = timer_id)

          self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Timer set for " + str(duration) + " " + str(units) + ".")

    elif("time" in command):
      current_hours = int(time.strftime("%H", time.localtime()))
      current_minutes = time.strftime("%M", time.localtime())
      am_pm = "a.m."
      if current_hours > 11:
        current_hours = current_hours - 12
        am_pm = "p.m."
      time_string = "It is currently " + str(current_hours) + ":" + str(current_minutes).zfill(2) + " " + am_pm +"."
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=time_string)
      valid_command = True

    # List all alarms and delete them all if desired. 
    elif("list alarms" in command or "list all alarms" in command 
    or "all alarms" in command or "delete alarms" in command 
    or "clear alarms" in command or "clear all alarms" in command 
    or "delete all alarms" in command):
      valid_command = True

      alarm_list_prompt = ""
      # List all active alarms. Ask the user if they want to delete
      # any afterwards. 
      for i in range(len(self.alarm_ids)-1,-1,-1):
        # Check if it exists. If not, delete it. 
        alarm_module = self.interaction_passive.get_module_by_id(self.alarm_ids[i])
        if alarm_module is None:
          del self.alarm_ids[i]
        else:
          am_pm = "a.m."
          alarm_hours = alarm_module.additional_data["alarm_hour"]
          if alarm_hours > 11:
            alarm_hours = alarm_hours - 12
            am_pm = "p.m."
          alarm_list_prompt = alarm_list_prompt + ", " + str(alarm_module.additional_data["alarm_name"]) + ", at " + str(alarm_hours) + ":" + str(alarm_module.additional_data["alarm_minute"]).zfill(2) + " " + am_pm + ", "
      
      if alarm_list_prompt == "":
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="There are currently no active alarms.")
      else:
        # List all alarms and ask if they want to clear all alarms. 
        # Singular vs plural.
        num_alarms = len(self.alarm_ids)
        alarm_list_prompt = alarm_list_prompt + ". Would you like to clear all alarms?"  
        if num_alarms == 1:
          alarm_list_prompt = "There is currently one active alarm: " + alarm_list_prompt
        else:  
          alarm_list_prompt = "There are currently " + str(num_alarms) + " active alarms: " + alarm_list_prompt
        user_response = self.speech_listen.listen_response(prompt=alarm_list_prompt, execute_chime = True)

        if user_response is not None and any(x in user_response for x in self.user_confirmation_words):
          # Got confirmation. Delete all alarms. 
          for alarm_id in self.alarm_ids:
            self.interaction_passive.clear_module_by_id(alarm_id)
          self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="All alarms have now been deleted.")

    # Set up alarms.Require a name for each alarm in a way of 
    # confirming that the registered time was correct. 
    elif("alarm" in command):
      valid_command = True
      
      alarm_hours, alarm_minutes, alarm_am = self.parse_alarm_time_from_command(command)

      if alarm_hours is not None and alarm_minutes is not None and alarm_am is not None:
        # Level 2 subroutine for confirming the parsed information
        # by asking for a alarm name. If a cancel word is detected,
        # abort. 
        user_response = None
        alarm_hours_24 = alarm_hours
        if alarm_am is False: alarm_hours_24 = alarm_hours + 12

        user_prompt = "Please give a name for the " + str(alarm_hours) + ":" + str(alarm_minutes)
        if alarm_am is True: user_prompt = user_prompt + " a.m. alarm."
        else: user_prompt = user_prompt + " p.m. alarm."
        user_response = self.speech_listen.listen_response(prompt=user_prompt, execute_chime = True)

        if user_response is not None and not any(x in user_response for x in self.user_cancel_words):
          # No cancel words detected, valid name given. Let's apply
          # the alarm by setting a new passive module.  Calculate the
          # amount of time remaining between now and the alarm time,
          # ensuring to convert it into tick units at the end. 
          duration_seconds = 0
          current_seconds = time.strftime("%S", time.localtime())
          current_minutes = time.strftime("%M", time.localtime())
          current_hours = time.strftime("%H", time.localtime())
          current_time_since_midnight = int(current_seconds) + int(current_minutes) * 60 + int(current_hours) * 3600

          # Check if our time is going to put us before or after now. 
          alarm_time_since_midnight = alarm_minutes*60 + alarm_hours_24*3600
          print("[DEBUG] Current time is " + str(current_time_since_midnight) + ". Alarm time is " + str(alarm_time_since_midnight) + ".")

          if alarm_time_since_midnight < current_time_since_midnight:
            # Alarm will be for tomorrow.
            remainder_time_today = 86400 - current_time_since_midnight 
            duration_seconds = remainder_time_today + alarm_time_since_midnight
          else:
            duration_seconds = alarm_time_since_midnight - current_time_since_midnight

          current_time = time.time()
          first_event_time = current_time + (float(duration_seconds)) # Append seconds. 
          print("[DEBUG] Setting alarm for " + str(duration_seconds) + " seconds. Current time: " + str(current_time) + ". Targeted time: " + str(first_event_time) + ".")

          additional_data = {
            "alarm_name" : user_response,
            "alarm_hour" : alarm_hours_24,
            "alarm_minute" : alarm_minutes,
            "snooze_remaining" : self.alarm_snooze_remaining,
            "snooze_duration_seconds" : self.alarm_snooze_duration_seconds,
            "action_dict" : self.alarm_action_dict,
          }

          # Create a alarm that we can add to our list of known alarm. 
          # Later on if asked, we can ping interaction_passive with the
          # id to retrive the additional data dict and report it's info.
          # Before it's triggered, naturally. 
          alarm_id = "simple_utilities_alarm_" + str(first_event_time)
          self.alarm_ids.append(alarm_id)
 
          # Create a new passive module given the path to this folder.
          self.interaction_passive.create_module_passive(
            class_location = self.alarm_class_location,
            first_event = first_event_time,
            additional_data=additional_data,
            id = alarm_id)

          self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Setting alarm, " +str(user_response)+ ", for " + str(alarm_hours) + ":" + str(alarm_minutes) + ".") 

    elif("date" in command or "day" in command or "month" in command or "today" in command):
      dateToday = date.today()
      dateString = "Today is "+ time.strftime("%A", time.localtime()) + ", " + time.strftime("%B", time.localtime()) + " " + str(dateToday.day) + ", " + str(dateToday.year)
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=dateString)
      valid_command = True

    elif("calculator" in command or "calculate" in command):
      # Get the first number and then the second number in the query. Ignore
      # all others if there are any. Fail if there are not enough numbers.
      # Fail if there is not a specifying operator. 
      first_term = None
      second_term = None
      operator = None # Term used in final message as well. 
      negative_term = False
      for word in command.split():
        # Test as an operator.
        if operator is None:
          if word == "add" or word == "plus" or word == "+":
            operator = "plus"
            continue
          elif word == "subtract" or word == "minus" or word == "-":
            operator = "minus"
            continue
          elif word == "multiply" or word == "times" or word == "*" or word == "x":
            operator = "times"
            continue
          elif word == "divide" or word == "divided" or word == "/":
            operator = "divided by"
            continue
        # Test as a number or a "negative" term.
        if first_term is None or second_term is None:
          if word == "negative":
            negative_term = True
          else:
            # Parse as a number. 
            possible_term = self.text2int(word)
            if possible_term != 0:
              if negative_term is True:
                possible_term = -possible_term
                negative_term = False
              if first_term is None:
                first_term = possible_term
              else:
                second_term = possible_term
              
      # We've now theoretically gotten everything.
      if first_term is not None and second_term is not None and operator is not None:
        solution = None
        if operator == "plus":
          solution = first_term + second_term
        elif operator == "minus":
          solution = first_term - second_term
        elif operator == "times":
          solution = first_term * second_term
        else:
          solution = first_term / second_term
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=str(first_term) + " " + operator + " " + str(second_term) + " equals {:.2f}.".format(solution)) 
        valid_command = True
    
    return valid_command

  # Given a command, parse a duration in seconds. This can be a rather
  # painful non-trivial task. Return a tuple of 
  # (duration, duration in seconds, units string). Returns a none tuple otherwise.
  def parse_duration_from_command(self, command):
    units = "seconds"
    duration = self.text2int(command)
    if duration is not None and int(duration) > 0:
      # TODO: For now we only support a single denomination
      # Ex) 50 minutes, 120 minutes, 1 hour, etc. We don't
      # yet support multiple, Ex) 1 minute, 20 seconds. 
      if "minutes" in command or "minute" in command:
        if duration > 1: 
          units = "minutes"
        else:
          units = "minute"
        duration_seconds = duration * 60
      elif "hours" in command or "hour" in command:
        if duration > 1:
          units = "hours"
        else:
          units = "hour"
        duration_seconds = duration * 3600
      else:
        # Otherwise we assume the units are seconds. 
        duration_seconds = duration
        if duration == 1:
          units = "second" # Not that I'd know why a 1 second timer would be useful. 


      return duration, duration_seconds, units

    return None, None, None

  # Given a command, parse the alarm time. 
  #
  # We always expect the user to specify the time in
  # 12 hr format, honing in on a.m. or p.m. The a.m. or p.m.
  # specification must be directly to the left of the actual time. 
  # The actual time may or may not contain a colon. 
  #
  # Some example strings:
  # Ex) Set an alarm for 6 p.m.
  # Ex) Set an alarm for 6:30 p.m.
  #
  # Returns alarm_hours, alarm_minutes, am (True/false). 
  def parse_alarm_time_from_command(self, command):
    alarm_hours = None
    alarm_minutes = None
    alarm_am = None

    if "a.m."  in command or "p.m." in command:
      split_command = command.split()
      for i in range(1, len(split_command)):
        if split_command[i] == "a.m." or split_command[i] == "p.m.":
          if split_command[i] == "a.m.":
            alarm_am = True
          elif split_command[i] == "p.m.":
            alarm_am = False
          alarm_time_string = split_command[i-1]
          if ":" in alarm_time_string:
            split_alarm_time_string = alarm_time_string.split(":")
            alarm_hours = int(split_alarm_time_string[0])
            alarm_minutes = int(split_alarm_time_string[1])
          else:
            alarm_hours = int(alarm_time_string)
            alarm_minutes = 0

    return alarm_hours, alarm_minutes, alarm_am
        
    
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