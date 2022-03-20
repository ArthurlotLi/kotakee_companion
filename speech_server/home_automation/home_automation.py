#
# home_automation.py
#
# All interactions related to the manipulation or querying of the
# KotakeeOS home automation web server. 

class HomeAutomation:
  successful_command_prompt = "" # By default, don't say anything and just activate something. 

  speech_speak = None
  web_server_status = None

  def __init__(self, speech_speak, web_server_status):
    self.speech_speak = speech_speak
    self.web_server_status = web_server_status

  # Level 1 standard routine. 
  def parse_command(self, command):
    confirmation_prompt = self.successful_command_prompt
    valid_command = False

    queries = []
    if("weather" in command or "like outside" in command or "how hot" in command or "how cold" in command):
      if(self.web_server_status.home_status is not None):
        weatherString = "It is currently " + str(int(self.web_server_status.home_status["weatherData"]["main"]["temp"])) + " degrees Fahrenheit, " +str(self.web_server_status.home_status["weatherData"]["weather"][0]["description"]) + ", with a maximum of " + str(int(self.web_server_status.home_status["weatherData"]["main"]["temp_max"])) + " and a minimum of " + str(int(self.web_server_status.home_status["weatherData"]["main"]["temp_min"])) + ". Humidity is " +  str(self.web_server_status.home_status["weatherData"]["main"]["humidity"]) + " percent."
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=weatherString)
        valid_command = True
    elif("everything" in command or "all modules" in command):
      if(self.web_server_status.action_states is not None):
        if("off" in command or "on" in command):
          # Manage prompt. 
          promptOnOff = "on"
          toState = 1
          if("off" in command):
            promptOnOff = "off"
            toState = 0
          confirmation_prompt = "Turning everything " + promptOnOff + "."
          queries.append(self.web_server_status.web_server_ip_address + "/moduleToggleAll/" + str(toState))
    elif("thermostat" in command):
      if(self.web_server_status.home_status is not None and self.web_server_status.home_status["moduleInput"] is not None and self.web_server_status.home_status["moduleInput"]['2'] is not None):
        if(self.web_server_status.home_status["moduleInput"]['2']['5251'] is not None and self.web_server_status.home_status["moduleInput"]['2']['5251']["offHeat"] is not None and self.web_server_status.home_status["moduleInput"]['2']['5251']["onHeat"] is not None):
          onHeat = self.web_server_status.home_status["moduleInput"]['2']['5251']["onHeat"]
          offHeat = self.web_server_status.home_status["moduleInput"]['2']['5251']["offHeat"]
          newTemp = self.text2int(command)
          print("[DEBUG] Parsed number " + str(newTemp) + " from thermostat request.")
          if(newTemp > 30 and newTemp < 100):
            onHeat = newTemp+1
            offHeat = onHeat-2
            newHomeStatus = self.web_server_status.home_status["moduleInput"]['2']
            newHomeStatus['5251']["onHeat"] = onHeat
            newHomeStatus['5251']["offHeat"] = offHeat
            data_to_send = {
              "roomId": 2,
              "newModuleInput": newHomeStatus
            }
            self.web_server_status.query_speech_server_module_input_modify(data_to_send)

            self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Setting thermostat to " + str(newTemp) + ".")
            valid_command = True
    elif("temperature" in command):
      # Handle temperatures. Expects a state like "27.70_42.20".
      lr_2_state = self.web_server_status.action_states["2"]["5251"].split("_")
      br_state = self.web_server_status.action_states["1"]["5250"].split("_")
      # Convert to Farenheit. 
      lr_2_temp = str(round(((float(lr_2_state[0]) * 9) / 5) + 32))
      br_temp = str(round(((float(br_state[0]) * 9) / 5) + 32))

      # Operational server status
      statusString = "The Living Room is currently " + lr_2_temp + " degrees. The Bedroom is currently " + br_temp + " degrees."
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=statusString)
      valid_command = True
    elif(("auto" in command or "input" in command or "automatic" in command) and ("off" in command or "on" in command or "enable" in command or "disable" in command)):
      if(self.web_server_status.home_status is not None and self.web_server_status.home_status["moduleInputDisabled"] is not None):
        newState = "true"
        if("activate" in command or "turn on" in command or "enable" in command):
          newState = "false"
        queries.append(self.web_server_status.web_server_ip_address + "/moduleInputDisabled/" + newState)
        # Manage prompt. 
        if(newState == "false"):
          confirmation_prompt = "Enabling automatic server actions."
        else:
          confirmation_prompt = "Disabling automatic server actions."
    elif(("server" in command or "service" in command) and ("off" in command or "on" in command or "enable" in command or "disable" in command)):
      if(self.web_server_status.home_status is not None and self.web_server_status.home_status["serverDisabled"] is not None):
        newState = "true"
        if("activate" in command or "turn on" in command or "enable" in command):
          newState = "false"
        queries.append(self.web_server_status.web_server_ip_address + "/serverDisabled/" + newState)
        # Manage prompt. 
        if(newState == "false"):
          confirmation_prompt = "Enabling central server operations."
        else:
          confirmation_prompt = "Disabling central server operations."
    elif("status" in command and ("home" in command or "system" in command or "server" in command)):
      if(self.web_server_status.home_status is not None and self.web_server_status.action_states is not None):
        # Report all information. 
        serverDisabled = "enabled"
        if(self.web_server_status.home_status["serverDisabled"] == "true" or self.web_server_status.home_status['serverDisabled'] == True):
          serverDisabled = "disabled"
        moduleInputDisabled = "enabled"
        if(self.web_server_status.home_status["moduleInputDisabled"] == "true" or self.web_server_status.home_status['moduleInputDisabled'] == True):
          moduleInputDisabled = "disabled"
        onHeat = int(self.web_server_status.home_status["moduleInput"]['2']['5251']["onHeat"])

        # Handle temperatures. Expects a state like "27.70_42.20".
        lr_2_state = self.web_server_status.action_states["2"]["5251"].split("_")
        br_state = self.web_server_status.action_states["1"]["5250"].split("_")
        # Convert to Farenheit. 
        lr_2_temp = str(round(((float(lr_2_state[0]) * 9) / 5) + 32))
        br_temp = str(round(((float(br_state[0]) * 9) / 5) + 32))

        # Operational server status
        statusString = "KotakeeOS is currently " + serverDisabled + " with automatic actions " + moduleInputDisabled + ". There are " + str(self.web_server_status.home_status["modulesCount"]) + " connected modules. The thermostat is currently set to " + str(onHeat - 1) + " degrees."
        # Action states status
        statusString = statusString + " The Living Room is currently " + lr_2_temp + " degrees. The Bedroom is currently " + br_temp + " degrees."
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=statusString)
        valid_command = True
    else:
      if("bedroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.web_server_status.generate_query(command, 1, 50, 1, 0))
      if("living" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.web_server_status.generate_query(command, 2, 50, 1, 0))
      if("speaker" in command or "soundbar" in command or ("sound" in command and "bar" in command)):
        queries.append(self.web_server_status.generate_query(command, 2, 250, 12, 10))
      if("ceiling" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.web_server_status.generate_query(command, 2, 251, 12, 10))
      if("kitchen" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.web_server_status.generate_query(command, 2, 350, 22, 20))
      if("bathroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.web_server_status.generate_query(command, 3, 350, 22, 20))
      if("bathroom" in command and ("fan" in command or "vent")):
        queries.append(self.web_server_status.generate_query(command, 3, 351, 22, 20))
      if("bathroom" in command and ("led" in command or "night" in command)):
        queries.append(self.web_server_status.generate_query(command, 3, 50, 1, 0))
      if("printer" in command):
        queries.append(self.web_server_status.generate_query(command, 2, 252, 12, 10))
      if("bedroom" in command and ("night" in command or "red led" in command or "red leds" in command)):
        queries.append(self.web_server_status.generate_query(command, 1, 1000, 108, 100))
      if("living" in command and ("night" in command or "red led" in command or "red leds" in command)):
        queries.append(self.web_server_status.generate_query(command, 2, 1000, 108, 100))
      if("bedroom" in command and ("led" in command or "party" in command or "rgb" in command)):
        queries.append(self.web_server_status.generate_query(command, 1, 1000, 107, 100))
      if("living" in command and ("led" in command or "party" in command or "rgb" in command)):
        queries.append(self.web_server_status.generate_query(command, 2, 1000, 107, 100))

    if len(queries) > 0:
      # We have received at least one valid command. Query the server. 
      for query in queries:
        self.web_server_status.execute_get_query(query)

      if(confirmation_prompt is not None and confirmation_prompt != ""):
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=confirmation_prompt)
      valid_command = True

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