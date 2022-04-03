#
# web_server_status.py
#
# Implements interfacing with the KotakeeOS central home automation
# web server. A single static class should be utilized for all 
# speech_server interactions.

import threading
import requests
import json
import datetime

class WebServerStatus:
  web_server_ip_address = None

  action_states = None
  home_status = None
  action_states_last_update = 0
  home_status_last_update = 0

  # Tells other components if we believe we are connected to the 
  # internet and/or local web server. Latter is consistently
  # updated with each routine/unique interaction with the web
  # server. Former is checked on startup (for now, TODO)
  online_status = False
  web_server_status = False

  def __init__(self, ip_address):
    self.web_server_ip_address = ip_address

  # Non-blocking query to fill status objects as well as to 
  # check internet connectivity. 
  def execute_query_server_thread(self):
    query_action_states_thread = threading.Thread(target=self.query_action_states, daemon=True).start()
    query_home_status_thread = threading.Thread(target=self.query_home_status, daemon=True).start()
    test_wide_internet_thread = threading.Thread(target=self.test_wide_internet, daemon=True).start()

  # Queries server for states of all modules. 
  def query_action_states(self):
    query = self.web_server_ip_address + "/actionStates/" + str(self.action_states_last_update)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        self.action_states = json.loads(response.text)
        self.action_states_last_update = self.action_states['lastUpdate']
        print("[DEBUG] Action States request received successfully. action_states_last_update is now: " + str(self.action_states_last_update))
        #print(str(action_states))
      elif(response.status_code != 204):
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
      self.web_server_status = True
    except:
      print("[WARNING] query_action_states unable to connect to server.")
      self.web_server_status = False

  # Queries server for misc non-module information
  def query_home_status(self):
    query = self.web_server_ip_address + "/homeStatus/" + str(self.home_status_last_update)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        self.home_status = json.loads(response.text)
        self.home_status_last_update = self.home_status['lastUpdate']
        print("[DEBUG] Home Status request received successfully. home_status_last_update is now: " + str(self.home_status_last_update))
        #print(str(home_status))
      elif(response.status_code != 204):
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
      self.web_server_status = True
    except:
      print("[WARNING] query_home_status unable to connect to server.")
      self.web_server_status = False

  # Function to check true wide internet connectivity. 
  def test_wide_internet(self):
    connection_status = False
    try:
      requests.head('http://www.google.com/', timeout=3)
      connection_status = True
    except:
      pass
    self.online_status = connection_status
    return connection_status

  # Returns time of sunset and sunrise, but only if we're connected 
  # to the web server (which is our source for openweathermap API 
  # information).
  #
  # Converts from float time (since the beginning of time) to a more
  # tractable hours/minutes format. 
  def get_sunrise_sunset_time(self):
    if self.web_server_status is True:
      sunrise_hours = None
      sunrise_minutes = None
      sunset_hours = None
      sunset_minutes = None
      try:
        if self.home_status is not None:
          sunset_time = float(self.home_status["weatherData"]["sys"]["sunset"])
          sunrise_time = float(self.home_status["weatherData"]["sys"]["sunrise"])

          # Convert into seconds starting from 12:00am today. 
          sunset_datetime = datetime.datetime.fromtimestamp(sunset_time)
          sunrise_datetime = datetime.datetime.fromtimestamp(sunrise_time)

          sunset_hours = int(sunset_datetime.strftime("%H"))
          sunset_minutes = int(sunset_datetime.strftime("%M"))

          sunrise_hours = int(sunrise_datetime.strftime("%H"))
          sunrise_minutes = int(sunrise_datetime.strftime("%M"))

          print("[DEBUG] Web Server Status Sunset: " + str(sunset_hours) + ":" + str(sunset_minutes) + " Sunrise: " + str(sunrise_hours) + ":" + str(sunrise_minutes) + ".")

        return sunrise_hours, sunrise_minutes, sunset_hours, sunset_minutes
      except Exception as e:
        print("[ERROR] Web Server Status was unable to correctly parse sunset/sunrise time! Exception:")
        print(e)
    return None, None, None, None

  # Creates a thread that queries server to turn speech server signal 
  # light on/off. 
  def query_speech_server_module_toggle(self, toState, roomId, actionId):
    query = self.web_server_ip_address + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(toState)
    request_thread = threading.Thread(target=self.execute_get_query, args=(query,), daemon=True).start()

  # Creates a thread that queries server providing input. 
  def query_speech_server_input(self, toState, roomId, actionId):
    query = self.web_server_ip_address + "/moduleInput/"+str(roomId)+"/"+str(actionId)+"/" + str(toState)
    request_thread = threading.Thread(target=self.execute_get_query, args=(query,), daemon=True).start()

  # Formats, and creates a thread to query the server with a simple 
  # POST query.
  def query_speech_server_module_input_modify(self, data_to_send):
    query = self.web_server_ip_address + "/moduleInputModify"
    request_thread = threading.Thread(target=self.execute_post_query, args=(query,data_to_send), daemon=True).start()

  def query_speech_server_piano_play(self, data_to_send):
    query = self.web_server_ip_address + "/pianoPlayMidi"
    request_thread = threading.Thread(target=self.execute_post_query, args=(query,data_to_send), daemon=True).start()

  # Executes a simple GET query and expects the status code to be 200. 
  def execute_get_query(self, query):
    print("[DEBUG] Executing GET query: " + query + "\n")
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        print("[DEBUG] Request received successfully.")
      else:
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
      self.web_server_status = True
    except Exception as e:
      print("[WARNING] execute_get_query unable to connect to server. Exception:")
      print(e)
      self.web_server_status = False
  
  # Executes a simple POST query and expects the status code to be 200. 
  def execute_post_query(self, query, data_to_send):
    print("[DEBUG] Executing POST query: " + query + " with body:")
    print(data_to_send)
    try:
      response = requests.post(query, data=json.dumps(data_to_send, indent = 4), headers = {'Content-Type': 'application/json'}, timeout=5)
      if(response.status_code == 200):
        print("[DEBUG] Request received successfully.")
      else:
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
      self.web_server_status = True
    except Exception as e:
      print("[WARNING] execute_post_query unable to connect to server. Exception:")
      print(e)
      self.web_server_status = False

  # Given the possible command string, roomId, actionId, and 
  # a binary set of states, return a query. 
  # 
  # If the command contains the keyword "virtual", a virtual 
  # module toggle will be created instead of physical. 
  def generate_query(self, command, roomId, actionId, onState, offState):
    endpoint = "/moduleToggle/"
    if "virtual" in command:
      endpoint = "/moduleVirtualToggle/"
    if("off" in command or "deactivate" in command):
      return self.web_server_ip_address + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(offState)
    elif("on" in command or "activate" in command or "initialize" in command):
      return self.web_server_ip_address + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(onState)
    else:
      # No on or off specified. Check queried information. 
      if(self.action_states is not None):
        if(self.action_states[str(roomId)][str(actionId)] == int(onState)):
          return self.web_server_ip_address + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(offState)
        else:
          return self.web_server_ip_address + endpoint+str(roomId)+"/"+str(actionId)+"/" + str(onState)
